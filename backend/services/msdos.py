"""Precarga de datos para juegos MSDOS/DOS/PC/Windows.

Cada campo de identidad vacío se llena con MobyGames, después con Launchbox y, si ninguno
lo tiene, con la IA, que solo recibe los campos que quedaron vacíos (ADR-0024, punto 4).
Cada campo escrito deja su fuente en la procedencia. Las imágenes salen de Launchbox.
Solo escribe campos vacíos, igual que ArcadeDB.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from backend.api.errors import BadRequest
from backend.config import Settings
from backend.lib.domain.fielddefs import contract_asset, image_keys, max_length_for
from backend.lib.domain.plataformas import nombre_en
from backend.lib.jobs.registro import JobState
from backend.lib.media import ext_por_magic
from backend.lib.providers.base import Limite
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.client import OpenAiCompatibleClient
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.ia.traductor import traductor_configurado
from backend.lib.providers.launchbox.cliente import fetch_images, search_game
from backend.lib.providers.mobygames.cliente import FichaCompleta, buscar_ficha
from backend.lib.providers.politica import ProviderHttpError
from backend.lib.providers.scraping import ScrapingClient, navegador_disponible
from backend.store.archivo import escribir_binario, media_path, safe_id
from backend.store.cuotas import QuotasStore
from backend.store.juegos import GamesStore

log = logging.getLogger(__name__)

_SOURCE = "Launchbox"
_SOURCE_IA = "IA"
_SOURCE_MOBYGAMES = "MobyGames"
_URL_MOBYGAMES = "mobygames.com/game/"
# Identidad que la IA puede completar cuando ninguna fuente factual la tiene. Ni el año ni el
# formato: la IA no los propone.
_CAMPOS_IA = ("developer", "publisher", "genre", "players")
_DESCRIPCION_IA = {
    "developer": "nombre del desarrollador",
    "publisher": "nombre del editor/publicador",
    "genre": "género del juego",
    "players": 'número de jugadores (ej: "1", "1-2", "1-4")',
}
# Un valor de identidad con su fuente: (valor, fuente, enlace de origen, tipo de fuente).
_Valor = tuple[str, str, str | None, str]
_SINOPSIS_MAX = max_length_for("texts", "sinopsis") or 700
_LIMITE = Limite()

# Sistemas que se consideran "MS-DOS" para precarga.
_MSDOS_MARKERS = ("msdos", "ms-dos", "dos", "pc", "windows")

# Mapeo de categorías Launchbox → campos COINDOOR para imágenes.
_IMAGENES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("caratula", ("box - front", "box - 3d", "box - front - reconstructed", "cart - front")),
    ("poster", ("poster", "advertisement flyer - front")),
    ("marquesina", ("arcade - marquee", "banner")),
    ("captura", ("screenshot - gameplay", "screenshot - game title")),
    ("logo", ("clear logo",)),
)

_CONTENT_TYPE_SUFFIX: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def soporta_msdos(system_id: str) -> bool:
    """True si el sistema es MSDOS/DOS/PC/Windows."""
    nombre = system_id.lower()
    return any(marker in nombre for marker in _MSDOS_MARKERS)


class MsdosPrecargaService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.games = GamesStore(settings.games_dir)

    def run(
        self,
        game_id: str,
        *,
        force: bool = False,
    ) -> Callable[[JobState], dict[str, object]]:
        def job_fn(job: JobState) -> dict[str, object]:
            return self._execute(game_id, job, force=force)

        return job_fn

    def _execute(
        self,
        game_id: str,
        job: JobState,
        *,
        force: bool,
    ) -> dict[str, object]:
        game = self.games.get(game_id)

        # Gate por sistema.
        if not soporta_msdos(game.systemId):
            return {"estado": "sistema-no-soportado", "escritos": [], "omitidos": []}

        # Gate por título: Launchbox busca por título.
        if not game.identity.title:
            return {"estado": "sin-titulo", "escritos": [], "omitidos": []}

        # 1. Buscar en Launchbox.
        job.progress = 10
        launchbox_result = search_game(game.identity.title, game.systemId)
        launchbox_year = launchbox_result.year if launchbox_result else ""
        launchbox_images = (
            fetch_images(launchbox_result.game_id, launchbox_result.slug)
            if launchbox_result
            else []
        )

        if job.cancel_event.is_set():
            job.status = "cancelled"
            return {"estado": "cancelado", "escritos": [], "omitidos": []}

        # 2. MobyGames: identidad factual para PC/DOS. El año de Launchbox ayuda a elegir la
        # ficha cuando la del juego todavía no tiene año.
        job.progress = 20
        anio_buscado = game.identity.year or launchbox_year
        moby = self._fetch_mobygames(game, anio_buscado, job)
        genero, genero_traducido = self._genero(moby, game.identity.title, job)

        if job.cancel_event.is_set():
            job.status = "cancelled"
            return {"estado": "cancelado", "escritos": [], "omitidos": []}

        valores = self._valores(moby, genero, genero_traducido, launchbox_year, anio_buscado)

        # 3. IA solo para lo que ni MobyGames ni Launchbox dieron.
        job.progress = 30
        faltan = self._faltan_para_ia(game, valores)
        ia_data = (
            self._fetch_ia_data(game_id, game.identity.title, game.systemId, job, faltan)
            if faltan
            else {}
        )
        for key in _CAMPOS_IA:
            if key not in valores and ia_data.get(key):
                valores[key] = (ia_data[key], _SOURCE_IA, None, "api")

        if job.cancel_event.is_set():
            job.status = "cancelled"
            return {"estado": "cancelado", "escritos": [], "omitidos": []}

        # 4. Escribir campos.
        return self._escribir_campos(
            game_id, game, job,
            valores=valores,
            launchbox_images=launchbox_images,
            ia_data=ia_data,
        )

    def _fetch_mobygames(
        self,
        game: Any,
        anio: str,
        job: JobState,
    ) -> FichaCompleta | None:
        """La ficha de MobyGames, o ``None`` si no hay equivalencia, Chromium o resultado."""
        plataforma = nombre_en(game.systemId, "mobygames")
        if plataforma is None:
            return None
        client = self._cliente_scraping(job)
        if client is None:
            log.info("Sin Chromium: la precarga de %s sigue sin MobyGames", game.id)
            return None
        ficha_url = next(
            (
                p.originUrl
                for p in game.provenance.values()
                if p.originUrl and _URL_MOBYGAMES in p.originUrl
            ),
            None,
        )
        try:
            with client:
                return buscar_ficha(
                    client, game.identity.title, anio or None, plataforma, ficha_url=ficha_url,
                )
        except ProviderHttpError as exc:
            log.warning("MobyGames falló para %s: %s", game.id, exc)
        except Exception:
            log.warning("MobyGames falló para %s", game.id, exc_info=True)
        return None

    def _cliente_scraping(self, job: JobState) -> ScrapingClient | None:
        if not navegador_disponible():
            return None
        return ScrapingClient(
            "mobygames",
            Limite(espera_min=self.settings.scraping_pace),
            QuotasStore(self.settings.quotas_path),
            timeout=self.settings.scraping_timeout,
            cancel_event=job.cancel_event,
            perfil=self.settings.browser_profile_dir,
        )

    def _genero(
        self,
        moby: FichaCompleta | None,
        titulo: str,
        job: JobState,
    ) -> tuple[str, bool]:
        """El género de MobyGames llega en inglés: se traduce si hay IA y, si no, queda así."""
        genero = moby.ficha.genre if moby else ""
        if not genero:
            return "", False
        traductor = traductor_configurado(self.settings, job.cancel_event)
        if traductor is None:
            return genero, False
        try:
            traducido = traductor.lote([genero], titulo=titulo)[0].strip()
        except Exception:
            log.warning("No se pudo traducir el género de MobyGames", exc_info=True)
            return genero, False
        return (traducido, True) if traducido else (genero, False)

    @staticmethod
    def _valores(
        moby: FichaCompleta | None,
        genero: str,
        genero_traducido: bool,
        launchbox_year: str,
        anio_buscado: str = "",
    ) -> dict[str, _Valor]:
        valores: dict[str, _Valor] = {}
        if moby is not None:
            origen = moby.ficha.url or None
            fuente = _SOURCE_MOBYGAMES
            # Si la ficha se eligió por año aproximado (Monkey Island 1990 → la edición VGA
            # CD-ROM, DOS 1992), su año y su soporte son de otra edición: no se toman.
            # Desarrollador, editor, género y jugadores son del juego y sí.
            aproximada = bool(
                anio_buscado and moby.ficha.year and moby.ficha.year != anio_buscado
            )
            unico_formato = moby.specs.formatos[0] if len(moby.specs.formatos) == 1 else ""
            for key, valor in (
                ("year", "" if aproximada else moby.ficha.year),
                ("developer", moby.ficha.developer),
                ("publisher", moby.ficha.publisher),
                ("players", moby.specs.players),
                # Con más de un soporte (disquete y CD) no se elige por el usuario.
                ("format", "" if aproximada else unico_formato),
            ):
                if valor:
                    valores[key] = (valor, fuente, origen, "scrape")
            if genero:
                fuente_genero = f"{fuente} · traducido por IA" if genero_traducido else fuente
                valores["genre"] = (genero, fuente_genero, origen, "scrape")
        if "year" not in valores and launchbox_year:
            valores["year"] = (launchbox_year, _SOURCE, None, "scrape")
        return valores

    @staticmethod
    def _faltan_para_ia(game: Any, valores: dict[str, _Valor]) -> list[str]:
        faltan = [
            key
            for key in _CAMPOS_IA
            if key not in valores and not getattr(game.identity, key, "")
        ]
        sinopsis = game.texts.get("sinopsis")
        if sinopsis is None or not sinopsis.value:
            faltan.append("sinopsis")
        return faltan

    def _fetch_ia_data(
        self,
        game_id: str,
        title: str,
        system_id: str,
        job: JobState,
        campos: list[str],
    ) -> dict[str, str]:
        """Usa IA para completar solo los ``campos`` que ninguna otra fuente tuvo."""
        from backend.store.cuotas import QuotasStore

        quotas = QuotasStore(self.settings.quotas_path)

        # Buscar modelo IA configurado.
        configs = (
            AiModelConfig(
                self.settings.ai_primary_base_url,
                self.settings.ai_primary_api_key,
                self.settings.ai_primary_model,
            ),
            AiModelConfig(
                self.settings.ai_backup_base_url,
                self.settings.ai_backup_api_key,
                self.settings.ai_backup_model,
            ),
        )

        for config in configs:
            if not (config.base_url and config.api_key and config.model):
                continue

            try:
                return self._call_ia(config, quotas, title, system_id, job, campos)
            except Exception:
                log.warning("IA call failed for %s", game_id, exc_info=True)
                continue

        log.info("Sin IA configurada para precarga MSDOS de %s", game_id)
        return {}

    def _call_ia(
        self,
        config: AiModelConfig,
        quotas: QuotasStore,
        title: str,
        system_id: str,
        job: JobState,
        campos: list[str],
    ) -> dict[str, str]:
        """Llama a IA para generar los campos pedidos."""
        http = ProviderHttpClient(
            f"ia:{config.model}",
            IaGenerador.limite,
            quotas,
            timeout=IaGenerador.timeout,
            cancel_event=job.cancel_event,
        )

        lineas = [f"- {k}: {_DESCRIPCION_IA[k]}" for k in campos if k in _DESCRIPCION_IA]
        if "sinopsis" in campos:
            lineas.append(
                f"- sinopsis: sinopsis del juego en español, máximo {_SINOPSIS_MAX} caracteres"
            )
        prompt = (
            f'Para el juego "{title}" de {system_id}, devuelve un JSON con:\n'
            + "\n".join(lineas)
            + "\n\nSolo el JSON, sin texto adicional."
        )

        with http:
            client = OpenAiCompatibleClient(
                config.base_url, config.api_key, config.model, http
            )
            response = client.complete(prompt)

        # Parsear respuesta.
        import json
        import re

        # Limpiar respuesta: quitar markdown fences si existen.
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```\w*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            log.warning("IA response not valid JSON for %s", title)
            return {}

        result: dict[str, str] = {}
        for key in campos:
            value = str(data.get(key, "")).strip()
            if value:
                result[key] = value
        return result

    def _escribir_campos(
        self,
        game_id: str,
        game: Any,
        job: JobState,
        *,
        valores: dict[str, _Valor],
        launchbox_images: list[Any],
        ia_data: dict[str, str],
    ) -> dict[str, Any]:
        from backend.api.schemas import StoredGame

        game_data = self.games.get(game_id)
        data = game_data.model_dump()
        escritos: list[str] = []
        omitidos: list[str] = []

        # Identity: cada campo con la fuente que lo dio.
        self._escribir_identity(data, valores, escritos, omitidos)

        # Texts: sinopsis de IA.
        self._escribir_texts(data, ia_data, escritos, omitidos)

        # Images: de Launchbox.
        job.progress = 50
        self._escribir_images(game_id, data, launchbox_images, escritos, omitidos, job)

        # Guardar.
        updated = StoredGame.model_validate(data)
        self.games.save(updated)

        job.progress = 100
        return {
            "estado": "ok",
            "escritos": escritos,
            "omitidos": omitidos,
        }

    def _escribir_identity(
        self,
        data: dict[str, Any],
        valores: dict[str, _Valor],
        escritos: list[str],
        omitidos: list[str],
    ) -> None:
        from backend.api.schemas import FieldProvenance

        for key, (valor, fuente, origen, tipo) in valores.items():
            if not valor:
                continue
            actual = data["identity"].get(key, "")
            if actual:
                omitidos.append(key)
                continue
            data["identity"][key] = valor
            data.setdefault("provenance", {})[key] = FieldProvenance(
                source=fuente, originUrl=origen, sourceType=tipo,
            ).model_dump(mode="json")
            escritos.append(key)

    def _escribir_texts(
        self,
        data: dict[str, Any],
        ia_data: dict[str, str],
        escritos: list[str],
        omitidos: list[str],
    ) -> None:
        sinopsis = ia_data.get("sinopsis", "")
        if not sinopsis:
            return
        actual = data.get("texts", {}).get("sinopsis", {})
        if actual.get("value"):
            omitidos.append("sinopsis")
            return
        data.setdefault("texts", {})["sinopsis"] = {
            "status": "suggested",
            "value": sinopsis,
            "source": _SOURCE_IA,
        }
        escritos.append("sinopsis")

    def _escribir_images(
        self,
        game_id: str,
        data: dict[str, Any],
        launchbox_images: list[Any],
        escritos: list[str],
        omitidos: list[str],
        job: JobState,
    ) -> None:
        if not launchbox_images:
            return

        # Indexar imágenes por categoría Launchbox.
        by_category: dict[str, list[Any]] = {}
        for img in launchbox_images:
            by_category.setdefault(img.category, []).append(img)

        total = len(_IMAGENES)
        escritos_imgs = 0
        for field_key, candidatos in _IMAGENES:
            if job.cancel_event.is_set():
                return
            # Buscar la primera imagen que matchee alguna categoría.
            img = None
            for cat in candidatos:
                if cat in by_category:
                    img = by_category[cat][0]
                    break
            if img is None:
                continue

            actual = data.get("images", {}).get(field_key, {})
            actual_url = actual.get("url", "")
            if actual_url:
                local = media_path(self.settings.media_dir, actual_url)
                if local is not None and local.exists():
                    if field_key not in omitidos:
                        omitidos.append(field_key)
                    continue

            try:
                local_url = self._download_media(game_id, field_key, img.media_url)
            except Exception:
                log.warning("Failed to download image %s for %s", img.category, game_id)
                continue

            data.setdefault("images", {})[field_key] = {
                "status": "suggested",
                "url": local_url,
                "source": _SOURCE,
            }
            if field_key not in escritos:
                escritos.append(field_key)
            escritos_imgs += 1
            job.progress = 50 + int(escritos_imgs / total * 40)

    def _download_media(self, game_id: str, key: str, url: str) -> str:
        """Descarga media y devuelve la URL local."""
        game = self.games.get(game_id)
        headers = {
            "User-Agent": "COINDOOR/0.1 (+local research)",
            "Accept": "image/*,*/*",
        }
        response = httpx.get(url, timeout=60.0, follow_redirects=True, headers=headers)
        if response.status_code >= 400:
            raise BadRequest(f"Error descargando {url}: {response.status_code}")

        suffix = (
            _suffix_from_content_type(response.headers.get("content-type", ""))
            or ext_por_magic(response.content[:16])
            or Path(httpx.URL(url).path).suffix.lower()
            or ".jpg"
        )

        system_dir = safe_id(game.systemId)
        game_dir = safe_id(game.id)
        section = "images" if key in image_keys() else "videos"
        asset_name = contract_asset(section, key)
        path = self.settings.media_dir / system_dir / game_dir / f"{asset_name}{suffix}"

        escribir_binario(path, response.content)
        return f"/media/{system_dir}/{game_dir}/{asset_name}{suffix}"


def _suffix_from_content_type(content_type: str) -> str:
    """Deriva extensión del content-type."""
    mime = content_type.split(";", 1)[0].strip().lower()
    return _CONTENT_TYPE_SUFFIX.get(mime, "")
