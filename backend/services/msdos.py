"""Precarga de datos para juegos MSDOS/DOS/PC/Windows.

Busca en Launchbox (imágenes + año) y usa IA para identidad y sinopsis.
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
from backend.lib.jobs.registro import JobState
from backend.lib.media import ext_por_magic
from backend.lib.providers.base import Consulta, Limite
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.client import OpenAiCompatibleClient
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.launchbox.cliente import fetch_images, search_game
from backend.store.archivo import escribir_binario, media_path, safe_id
from backend.store.cuotas import QuotasStore
from backend.store.juegos import GamesStore

log = logging.getLogger(__name__)

_SOURCE = "Launchbox"
_SOURCE_IA = "IA"
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

        # 2. IA para identidad y sinopsis.
        job.progress = 30
        ia_data = self._fetch_ia_data(game_id, game.identity.title, game.systemId, job)

        if job.cancel_event.is_set():
            job.status = "cancelled"
            return {"estado": "cancelado", "escritos": [], "omitidos": []}

        # 3. Escribir campos.
        return self._escribir_campos(
            game_id, game, job,
            launchbox_year=launchbox_year,
            launchbox_images=launchbox_images,
            ia_data=ia_data,
        )

    def _fetch_ia_data(
        self,
        game_id: str,
        title: str,
        system_id: str,
        job: JobState,
    ) -> dict[str, str]:
        """Usa IA para generar identidad y sinopsis."""
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
                return self._call_ia(config, quotas, title, system_id, job)
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
    ) -> dict[str, str]:
        """Llama a IA para generar identidad + sinopsis."""
        http = ProviderHttpClient(
            f"ia:{config.model}",
            IaGenerador.limite,
            quotas,
            timeout=IaGenerador.timeout,
            cancel_event=job.cancel_event,
        )

        prompt = f"""Para el juego "{title}" de {system_id}, devuelve un JSON con:
- developer: nombre del desarrollador
- publisher: nombre del editor/publicador
- genre: género del juego
- players: número de jugadores (ej: "1", "1-2", "1-4")
- sinopsis: sinopsis del juego en español, máximo {_SINOPSIS_MAX} caracteres

Solo el JSON, sin texto adicional."""

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
        for key in ("developer", "publisher", "genre", "players", "sinopsis"):
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
        launchbox_year: str,
        launchbox_images: list[Any],
        ia_data: dict[str, str],
    ) -> dict[str, Any]:
        from backend.api.schemas import StoredGame

        game_data = self.games.get(game_id)
        data = game_data.model_dump()
        escritos: list[str] = []
        omitidos: list[str] = []

        # Identity: year de Launchbox, el resto de IA.
        self._escribir_identity(data, launchbox_year, ia_data, escritos, omitidos)

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
        launchbox_year: str,
        ia_data: dict[str, str],
        escritos: list[str],
        omitidos: list[str],
    ) -> None:
        mapping = {
            "year": launchbox_year,
            "developer": ia_data.get("developer", ""),
            "publisher": ia_data.get("publisher", ""),
            "genre": ia_data.get("genre", ""),
            "players": ia_data.get("players", ""),
        }
        for key, value in mapping.items():
            if not value:
                continue
            actual = data["identity"].get(key, "")
            if actual:
                omitidos.append(key)
                continue
            data["identity"][key] = value
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
