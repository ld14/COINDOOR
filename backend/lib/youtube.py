"""Descarga de video de YouTube con yt-dlp, para el campo ``video`` (ADR-0017).

No conoce HTTP ni el store: recibe una URL ya validada y un directorio, deja
``video.mp4`` adentro y devuelve la ruta. Los mensajes de ``YoutubeError`` están
escritos para mostrarse tal cual al usuario.
"""

from __future__ import annotations

import logging
import re
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled, DownloadError

log = logging.getLogger(__name__)

MAX_DURACION_S = 600
# Red de seguridad: con el tope de duración, un 720p ronda los 90 MB.
MAX_BYTES = 500 * 1024 * 1024
# H.264 + AAC es lo único verificado reproduciendo en el Pegasus del gabinete.
FORMATO = "bv*[vcodec^=avc1][height<=720]+ba[acodec^=mp4a]/b[vcodec^=avc1][height<=720]"
URL_INVALIDA = "La URL tiene que ser de un video de youtube.com o youtu.be."

_HOSTS = frozenset({"youtube.com", "www.youtube.com", "m.youtube.com"})
_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


class YoutubeError(Exception):
    """Falla con un mensaje para el usuario."""


def validar_url(url: str) -> str:
    """Devuelve la URL canónica ``watch?v=<id>`` o levanta ``ValueError``.

    Reconstruirla deja afuera listas, canales y parámetros de seguimiento: yt-dlp
    nunca recibe otra cosa que un video.
    """
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    video_id = ""
    if parsed.scheme in {"http", "https"}:
        if host == "youtu.be":
            video_id = parsed.path.strip("/")
        elif host in _HOSTS and parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
    if not _VIDEO_ID.fullmatch(video_id):
        raise ValueError(URL_INVALIDA)
    return f"https://www.youtube.com/watch?v={video_id}"


def descargar(
    url: str,
    destino: Path,
    cancel: threading.Event,
    on_progress: Callable[[int], None],
) -> Path:
    """Baja ``url`` a ``destino/video.mp4``. Cancelar levanta ``DownloadCancelled``."""
    total = 0
    bajados: dict[str, int] = {}

    def hook(estado: dict[str, Any]) -> None:
        if cancel.is_set():
            raise DownloadCancelled()
        bajados[str(estado.get("filename"))] = int(estado.get("downloaded_bytes") or 0)
        if total:
            on_progress(min(95, sum(bajados.values()) * 95 // total))

    opciones: dict[str, Any] = {
        "format": FORMATO,
        "merge_output_format": "mp4",
        "outtmpl": "video.%(ext)s",
        "paths": {"home": str(destino), "temp": str(destino)},
        "noplaylist": True,
        "allowed_extractors": ["youtube"],
        "socket_timeout": 30,
        "max_filesize": MAX_BYTES,
        "quiet": True,
        "noprogress": True,
        "logger": _Logger(),
        "progress_hooks": [hook],
    }
    try:
        with YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=False)
            _validar(info)
            formatos = info.get("requested_formats") or [info]
            total = sum(int(f.get("filesize") or f.get("filesize_approx") or 0) for f in formatos)
            ydl.process_ie_result(info, download=True)
    except DownloadError as exc:
        raise YoutubeError(_legible(str(exc))) from exc

    archivo = destino / "video.mp4"
    if not archivo.is_file():
        # max_filesize saltea el video sin levantar error.
        raise YoutubeError("La descarga terminó sin archivo.")
    return archivo


def _validar(info: dict[str, Any]) -> None:
    if info.get("is_live") or not info.get("duration"):
        raise YoutubeError("No se pueden descargar transmisiones en vivo.")
    if info["duration"] > MAX_DURACION_S:
        raise YoutubeError("El video dura más de 10 minutos.")


def _legible(error: str) -> str:
    texto = _ANSI.sub("", error).removeprefix("ERROR: ").strip()
    if "not a bot" in texto:
        return "YouTube pidió verificación anti-bot. Probá más tarde o actualizá yt-dlp."
    if "Requested format is not available" in texto:
        return "Este video no tiene versión H.264 de 720p o menos."
    return texto


class _Logger:
    """Sin logger, yt-dlp escribe en stdout; así queda en el log del proceso."""

    def debug(self, msg: str) -> None:
        log.debug(msg)

    def warning(self, msg: str) -> None:
        log.warning(msg)

    def error(self, msg: str) -> None:
        log.error(msg)
