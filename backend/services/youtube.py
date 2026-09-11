"""Descarga del video de un juego desde una URL de YouTube (feature 011, ADR-0020).

La URL y el juego se validan antes de encolar: un error de entrada responde 422/404
en vez de aparecer como un job fallido.
"""

from __future__ import annotations

import logging
import shutil
import time
from collections.abc import Callable

from yt_dlp.utils import DownloadCancelled
from yt_dlp.version import __version__ as yt_dlp_version

from backend.api.errors import BadRequest
from backend.api.schemas import FieldProvenance
from backend.config import Settings
from backend.lib.domain.fielddefs import contract_asset
from backend.lib.jobs.registro import JobState
from backend.lib.youtube import descargar, validar_url
from backend.store.archivo import mover_binario, safe_id
from backend.store.juegos import GamesStore

log = logging.getLogger(__name__)


class YoutubeVideoService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, game_id: str, url: str) -> Callable[[JobState], dict[str, str]]:
        try:
            canonica = validar_url(url)
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc
        GamesStore(self.settings.games_dir).get(game_id)

        def job_fn(job: JobState) -> dict[str, str]:
            return self._execute(game_id, canonica, job)

        return job_fn

    def _execute(self, game_id: str, url: str, job: JobState) -> dict[str, str]:
        def progreso(valor: int) -> None:
            job.progress = valor

        tmp = self.settings.tmp_dir / f"youtube-{job.job_id}"
        tmp.mkdir(parents=True, exist_ok=True)
        inicio = time.monotonic()
        log.info("YouTube %s: bajando %s con yt-dlp %s", game_id, url, yt_dlp_version)
        try:
            archivo = descargar(url, tmp, job.cancel_event, progreso)
            if job.cancel_event.is_set():
                return {}
            megas = archivo.stat().st_size / 1_048_576
            # Store nuevo: la descarga pudo durar minutos y el índice de uno viejo
            # pisaría lo que el usuario editó mientras tanto.
            games = GamesStore(self.settings.games_dir)
            game = games.get(game_id)
            carpeta = f"{safe_id(game.systemId)}/{safe_id(game.id)}"
            nombre = f"{contract_asset('videos', 'video')}.mp4"
            mover_binario(archivo, self.settings.media_dir / carpeta / nombre)
            local_url = f"/media/{carpeta}/{nombre}"
            games.apply_media_suggestion(
                game_id, "video", local_url, FieldProvenance(source="YouTube", originUrl=url)
            )
            log.info("YouTube %s: %.1f MB en %.1f s", game_id, megas, time.monotonic() - inicio)
            return {"url": local_url}
        except DownloadCancelled:
            # yt-dlp también usa subclases de DownloadCancelled para cortes propios
            # (RejectedVideoReached, MaxDownloadsReached): esos son fallas, no cancelaciones.
            if not job.cancel_event.is_set():
                raise
            # Cancelar es un pedido del usuario, no una falla: sin esto el ejecutor lo
            # registra como ERROR con traceback.
            return {}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
