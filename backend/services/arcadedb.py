"""Precarga de datos de ArcadeDB al crear un juego arcade.

Consulta ArcadeDB por el romset y escribe solo campos vacíos. El job termina
``succeeded`` incluso si el romset no se encuentra (``estado: "no-encontrado"``).
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx

from backend.api.errors import BadRequest
from backend.config import Settings
from backend.lib.domain.arcade import soporta_arcadedb
from backend.lib.domain.fielddefs import contract_asset, image_keys, max_length_for
from backend.lib.jobs.registro import JobState
from backend.lib.media import ext_por_magic
from backend.lib.providers.arcadedb.cliente import ArcadeGame, fetch_con_padre
from backend.lib.providers.arcadedb.parser import truncar_en_oracion
from backend.lib.providers.base import Limite
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.client import OpenAiCompatibleClient
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.ia.traductor import Traductor
from backend.store.archivo import escribir_binario, media_path, safe_id
from backend.store.juegos import GamesStore

log = logging.getLogger(__name__)

_SOURCE = "ArcadeDB"
_SOURCE_TRADUCIDO = "ArcadeDB · traducido por IA"
# La sinopsis de ArcadeDB comparte limite con la generada por IA: lo dice fielddefs.
_SINOPSIS_MAX = max_length_for("texts", "sinopsis") or 700
# Largo maximo del prefijo que ``_tip_a_entry`` acepta como nombre de truco.
# Los titulos reales de arcade-history rondan los 16-32 caracteres.
_TITULO_MAX = 60
_LIMITE = Limite()

# Campo de COINDOOR -> tipos de ArcadeDB, en orden de preferencia.
#
# ArcadeDB no publica los mismos tipos para todos los romsets: ``snowbros`` trae
# flyer (846x1200) y marquee (1200x313), pero ``ffightub`` no trae ninguno de los
# dos. Por eso cada campo lista candidatos y se toma el primero disponible.
#
# La tabla vieja pedia ``screen1``, un tipo que ArcadeDB no publica para ningun
# juego (devuelve text/html): la captura nunca se cargaba. Y ``logo`` no estaba
# mapeado, asi que tampoco.
#
# Los candidatos estan ordenados por forma, no por peso: para caratula y poster
# van primero los verticales (flyer 0.70, cabinet 0.67) y recien despues
# ``artwork_preview``, que es apaisado y solo entra cuando no hay nada mejor.
# Marquesina no acepta suplentes: lo mas ancho despues de marquee (4:1) es decal
# (1.78) y estirarlo se ve peor que dejar el campo vacio para que lo cargue el
# usuario.
_IMAGENES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("caratula", ("flyer", "cabinet", "artwork_preview")),
    ("poster", ("flyer", "cabinet", "artwork_preview")),
    ("marquesina", ("marquee",)),
    ("captura", ("ingame", "title", "boss", "gameover")),
    ("logo", ("logo", "title")),
)

_CONTENT_TYPE_SUFFIX: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}


class ArcadeDbPrecargaService:
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
        if not soporta_arcadedb(game.systemId):
            return {"estado": "sistema-no-soportado", "romset": "", "escritos": [], "omitidos": []}

        # Derivar romset.
        romset = Path(game.romRef).stem.lower() if game.romRef else ""
        if not romset:
            return {"estado": "sin-romset", "romset": "", "escritos": [], "omitidos": []}

        # Fetch con memo.
        from backend.store.cuotas import QuotasStore

        quotas = QuotasStore(self.settings.quotas_path)

        def http_factory() -> ProviderHttpClient:
            # Uno nuevo por peticion: ProviderHttpClient cierra su cliente al salir.
            return ProviderHttpClient(
                "arcadedb",
                _LIMITE,
                quotas,
                timeout=10.0,
                cancel_event=job.cancel_event,
            )

        # Con el padre: un clon publica menos tipos de imagen. ``ffightub`` no trae
        # flyer ni marquee y su padre ``ffight`` si, que es lo que dejaba a Final
        # Fight con la caratula y la marquesina vacias. La identidad no se fusiona.
        arcade_game, _ = fetch_con_padre(romset, http_factory)
        if arcade_game is None:
            return {"estado": "no-encontrado", "romset": romset, "escritos": [], "omitidos": []}

        if job.cancel_event.is_set():
            job.status = "cancelled"
            return {"estado": "cancelado", "romset": romset, "escritos": [], "omitidos": []}

        # ArcadeDB publica todo en ingles y la ficha es en español.
        job.progress = 20
        arcade_game, traducido = self._traducir(arcade_game, game.systemId, job)

        return self._escribir_campos(game_id, arcade_game, job, traducido=traducido)

    def _traducir(
        self,
        game: ArcadeGame,
        system_id: str,
        job: JobState,
    ) -> tuple[ArcadeGame, bool]:
        """Devuelve el juego con sus textos en español, y si la traduccion ocurrio.

        Dos llamadas al modelo como maximo: la sinopsis va sola porque ademas de
        traducir hay que condensarla a la spec de ``sinopsis.v1.md``, y el resto
        (trucos, genero, gabinete) va en un lote porque son strings cortos.

        No filtra por campos ya cargados a proposito: sumar un string al lote no
        cuesta una llamada mas, y filtrar si costaria complejidad.

        El limite de la sinopsis se aplica en todos los caminos, incluso sin IA:
        ArcadeDB devuelve la entrada entera de arcade-history (2250 caracteres en
        Super Pang) y ``fielddefs.json`` declara 700.
        """
        tips, genero, controles, orientacion = (
            game.history.tips,
            game.genre,
            game.input_controls,
            game.screen_orientation,
        )
        sinopsis = game.history.sinopsis
        traducido = False

        traductor = self._traductor(job)
        cortos = [*tips, genero, controles, orientacion]
        if traductor is None:
            log.info("Sin IA configurada: los textos de ArcadeDB quedan en ingles")
        elif any(texto.strip() for texto in cortos) or sinopsis.strip():
            traducidos = traductor.lote(cortos, titulo=game.title or game.romset)
            n = len(tips)
            tips = tuple(traducidos[:n])
            genero, controles, orientacion = traducidos[n], traducidos[n + 1], traducidos[n + 2]

            if not job.cancel_event.is_set():
                job.progress = 25
                sinopsis = traductor.sinopsis(
                    sinopsis,
                    titulo=game.title or game.romset,
                    sistema=system_id,
                    anio=game.year,
                    max_length=_SINOPSIS_MAX,
                )
            traducido = (tips, genero, controles, sinopsis) != (
                game.history.tips,
                game.genre,
                game.input_controls,
                game.history.sinopsis,
            )

        # Ultimo, y pase lo que pase antes: manda fielddefs, no el prompt ni el modelo.
        sinopsis = truncar_en_oracion(sinopsis, _SINOPSIS_MAX)
        return (
            replace(
                game,
                genre=genero,
                input_controls=controles,
                screen_orientation=orientacion,
                history=replace(game.history, sinopsis=sinopsis, tips=tips),
            ),
            traducido,
        )

    def _traductor(self, job: JobState) -> Traductor | None:
        """Primer modelo configurado (primario, si no el de respaldo)."""
        from backend.store.cuotas import QuotasStore

        quotas = QuotasStore(self.settings.quotas_path)
        candidatos = (
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
        for config in candidatos:
            if not (config.base_url and config.api_key and config.model):
                continue

            def fabricar(config: AiModelConfig = config) -> OpenAiCompatibleClient:
                # Un ProviderHttpClient nuevo por llamada: el anterior queda cerrado.
                http = ProviderHttpClient(
                    f"ia:{config.model}",
                    IaGenerador.limite,
                    quotas,
                    timeout=IaGenerador.timeout,
                    cancel_event=job.cancel_event,
                )
                return OpenAiCompatibleClient(
                    config.base_url, config.api_key, config.model, http
                )

            return Traductor(fabricar, config.model)
        return None

    def _escribir_campos(
        self,
        game_id: str,
        game: ArcadeGame,
        job: JobState,
        *,
        traducido: bool = False,
    ) -> dict[str, Any]:
        from backend.api.schemas import StoredGame

        game_data = self.games.get(game_id)
        data = game_data.model_dump()
        escritos: list[str] = []
        omitidos: list[str] = []
        # Deja registrado en la ficha si el texto paso por el traductor o quedo
        # en ingles porque la IA no estaba disponible.
        fuente_texto = _SOURCE_TRADUCIDO if traducido else _SOURCE

        # Identity
        self._escribir_identity(data, game, escritos, omitidos)

        # Texts (sinopsis)
        self._escribir_texts(data, game, escritos, omitidos, fuente_texto)

        # Rich (cheats)
        self._escribir_cheats(data, game, escritos, omitidos, fuente_texto)

        # Images (descarga y escribe)
        job.progress = 30
        self._escribir_images(game_id, data, game, escritos, omitidos, job)

        # Video
        job.progress = 70
        self._escribir_video(game_id, data, game, escritos, omitidos)

        # Cabinet
        self._escribir_cabinet(data, game, escritos, omitidos)

        # Guardar
        updated = StoredGame.model_validate(data)
        self.games.save(updated)

        job.progress = 100
        return {
            "estado": "ok",
            "romset": game.romset,
            "escritos": escritos,
            "omitidos": omitidos,
        }

    def _escribir_identity(
        self,
        data: dict[str, Any],
        game: ArcadeGame,
        escritos: list[str],
        omitidos: list[str],
    ) -> None:
        mapping = {
            "title": game.short_title or game.title,
            "year": game.year,
            "developer": game.manufacturer,
            "publisher": game.manufacturer,
            "genre": game.genre,
            "players": game.players,
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
        game: ArcadeGame,
        escritos: list[str],
        omitidos: list[str],
        fuente: str = _SOURCE,
    ) -> None:
        if not game.history.sinopsis:
            return
        actual = data.get("texts", {}).get("sinopsis", {})
        if actual.get("value"):
            omitidos.append("sinopsis")
            return
        data.setdefault("texts", {})["sinopsis"] = {
            "status": "suggested",
            "value": game.history.sinopsis,
            "source": fuente,
        }
        escritos.append("sinopsis")

    def _escribir_cheats(
        self,
        data: dict[str, Any],
        game: ArcadeGame,
        escritos: list[str],
        omitidos: list[str],
        fuente: str = _SOURCE,
    ) -> None:
        if not game.history.tips:
            return
        actual = data.get("cheats", {})
        if actual.get("groups"):
            omitidos.append("cheats")
            return
        groups = [{"name": "ArcadeDB", "entries": [_tip_a_entry(tip) for tip in game.history.tips]}]
        data["cheats"] = {"status": "suggested", "source": fuente, "groups": groups}
        escritos.append("cheats")

    def _escribir_images(
        self,
        game_id: str,
        data: dict[str, Any],
        game: ArcadeGame,
        escritos: list[str],
        omitidos: list[str],
        job: JobState,
    ) -> None:
        total = len(_IMAGENES)
        escritos_imgs = 0
        for field_key, candidatos in _IMAGENES:
            if job.cancel_event.is_set():
                return
            # ``image`` toma el primero que el romset realmente publique. Pedir un
            # tipo que la API no listo devuelve un PNG placeholder de 30.975 bytes,
            # asi que nunca se arma la URL a mano.
            url = game.image(*candidatos)
            if not url:
                continue
            arcade_key = next(t for t in candidatos if game.images.get(t) == url)
            actual = data.get("images", {}).get(field_key, {})
            actual_url = actual.get("url", "")
            if actual_url:
                local = media_path(self.settings.media_dir, actual_url)
                if local is not None and local.exists():
                    if field_key not in omitidos:
                        omitidos.append(field_key)
                    continue
            try:
                local_url = self._download_media(game_id, field_key, url)
            except Exception:
                log.warning("Failed to download image %s for %s", arcade_key, game_id)
                continue
            data.setdefault("images", {})[field_key] = {
                "status": "suggested",
                "url": local_url,
                "source": _SOURCE,
            }
            if field_key not in escritos:
                escritos.append(field_key)
            escritos_imgs += 1
            job.progress = 30 + int(escritos_imgs / total * 40)

    def _escribir_video(
        self,
        game_id: str,
        data: dict[str, Any],
        game: ArcadeGame,
        escritos: list[str],
        omitidos: list[str],
    ) -> None:
        if not game.video_url:
            return
        actual = data.get("video", {}).get("video", {})
        actual_url = actual.get("url", "")
        if actual_url:
            # Si la URL apunta a un archivo local que existe, no re-descargar.
            local = media_path(self.settings.media_dir, actual_url)
            if local is not None and local.exists():
                omitidos.append("video")
                return
        try:
            local_url = self._download_media(game_id, "video", game.video_url)
        except Exception:
            log.warning("Failed to download video for %s", game_id)
            return
        data.setdefault("video", {})["video"] = {
            "status": "suggested",
            "url": local_url,
            "source": _SOURCE,
        }
        escritos.append("video")

    def _escribir_cabinet(
        self,
        data: dict[str, Any],
        game: ArcadeGame,
        escritos: list[str],
        omitidos: list[str],
    ) -> None:
        if not game.screen_resolution and not game.input_controls:
            return
        actual = data.get("cabinet", {})
        if actual.get("resolution") or actual.get("controls"):
            omitidos.append("cabinet")
            return
        from backend.api.schemas import CabinetButton, CabinetInfo

        button_list = [
            CabinetButton(control=b.control, color=b.color, action=b.action)
            for b in game.buttons
        ]
        cabinet = CabinetInfo(
            resolution=game.screen_resolution,
            orientation=game.screen_orientation,
            controls=game.input_controls,
            buttons=game.input_buttons,
            button_list=button_list,
        )
        data["cabinet"] = cabinet.model_dump(mode="json")
        escritos.append("cabinet")

    def _download_media(self, game_id: str, key: str, url: str) -> str:
        """Descarga media y devuelve la URL local."""
        game = self.games.get(game_id)
        headers = {
            "User-Agent": "COINDOOR/0.1 (+local research)",
            "Accept": "image/*,video/*,*/*",
        }
        response = httpx.get(url, timeout=60.0, follow_redirects=True, headers=headers)
        if response.status_code >= 400:
            raise BadRequest(f"Error descargando {url}: {response.status_code}")

        # Derivar extensión del content-type.
        # El path de la URL va ultimo: ArcadeDB sirve los videos desde
        # ``download_file.php`` como ``application/octet-stream``, asi que sin
        # mirar el contenido el archivo terminaba llamandose ``video.php``.
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

        # Los videos ArcadeDB vienen en H.264 High 4:4:4 (yuv444p) que los
        # navegadores no reproducen. Re-codificamos a yuv420p con ffmpeg.
        if section == "videos" and suffix in (".mp4", ".webm", ".avi"):
            data = self._transcode_yuv420p(response.content, suffix)
        else:
            data = response.content

        escribir_binario(path, data)
        return f"/media/{system_dir}/{game_dir}/{asset_name}{suffix}"

    def _transcode_yuv420p(self, raw: bytes, suffix: str) -> bytes:
        """Re-codifica video a H.264 yuv420p compatible con navegadores."""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
            tmp_in.write(raw)
            tmp_in_path = tmp_in.name
        tmp_out_path = tmp_in_path + ".out" + suffix
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", tmp_in_path,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "23", "-preset", "fast",
                    tmp_out_path,
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
            return Path(tmp_out_path).read_bytes()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            log.warning("ffmpeg transcode failed for %s, using original", suffix)
            return raw
        finally:
            Path(tmp_in_path).unlink(missing_ok=True)
            Path(tmp_out_path).unlink(missing_ok=True)


def _tip_a_entry(tip: str) -> dict[str, str]:
    """Adapta un truco de arcade-history al ``CheatEntry`` del schema.

    Antes se escribia ``{"text": tip}`` dentro de ``items``, dos claves que
    ``CheatGroup`` no tiene: Pydantic las descartaba y los trucos se perdian
    aunque la precarga los reportara como escritos.

    arcade-history suele redactarlos como "Titulo: como se hace", pero no
    siempre: hay trucos que son un parrafo corrido con un ":" enterrado en el
    medio (en ``snowbros`` cae recien en el caracter 328). Partir por el primer
    ":" a ciegas dejaba ese parrafo entero como nombre del truco.

    Por eso el prefijo solo se acepta como titulo si parece uno: corto y sin
    punto, que es lo que separa un encabezado de una oracion cualquiera.
    """
    nombre, sep, instruccion = tip.partition(":")
    nombre, instruccion = nombre.strip(), instruccion.strip()
    parece_titulo = bool(sep) and 0 < len(nombre) <= _TITULO_MAX and "." not in nombre
    if parece_titulo and instruccion:
        return {"name": nombre, "input": instruccion}
    return {"name": "Truco", "input": tip.strip()}


def _suffix_from_content_type(content_type: str) -> str:
    """Deriva extensión del content-type. ArcadeDB no pone extensión en las URLs."""
    mime = content_type.split(";", 1)[0].strip().lower()
    return _CONTENT_TYPE_SUFFIX.get(mime, "")
