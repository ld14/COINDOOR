"""Descarga de video de YouTube con yt-dlp, para el campo ``video`` (ADR-0020).

No conoce HTTP ni el store: recibe una URL ya validada y un directorio, deja
``video.mp4`` adentro y devuelve la ruta. Un video de más de ``MAX_DURACION_S`` se
guarda con sus primeros ``RECORTE_S`` segundos (ADR-0029). Los mensajes de
``YoutubeError`` están escritos para mostrarse tal cual al usuario.
"""

from __future__ import annotations

import logging
import re
import subprocess
import threading
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled, DownloadError

log = logging.getLogger(__name__)

MAX_DURACION_S = 600
RECORTE_S = 180
# Red de seguridad: con el tope de duración, un 720p ronda los 90 MB.
MAX_BYTES = 500 * 1024 * 1024
# H.264 + AAC es lo único verificado reproduciendo en el Pegasus del gabinete.
FORMATO = "bv*[vcodec^=avc1][height<=720]+ba[acodec^=mp4a]/b[vcodec^=avc1][height<=720]"
URL_INVALIDA = "La URL tiene que ser de un video de youtube.com o youtu.be."
SIN_FFMPEG = "Falta ffmpeg en el equipo: instalalo para descargar video de YouTube."

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
            if info["duration"] > MAX_DURACION_S:
                _bajar_el_comienzo(formatos, destino / "video.mp4", cancel, on_progress)
            else:
                total = sum(
                    int(f.get("filesize") or f.get("filesize_approx") or 0) for f in formatos
                )
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


def _comando_del_comienzo(formatos: list[dict[str, Any]], archivo: Path) -> list[str]:
    comando = ["ffmpeg", "-nostdin", "-v", "error", "-progress", "pipe:1", "-y"]
    for formato in formatos:
        cabeceras = "".join(f"{k}: {v}\r\n" for k, v in (formato.get("http_headers") or {}).items())
        if cabeceras:
            comando += ["-headers", cabeceras]
        comando += ["-rw_timeout", "30000000", "-t", str(RECORTE_S), "-i", formato["url"]]
    for indice in range(len(formatos)):
        comando += ["-map", str(indice)]
    return [*comando, "-c", "copy", "-movflags", "+faststart", str(archivo)]


def _bajar_el_comienzo(
    formatos: list[dict[str, Any]],
    archivo: Path,
    cancel: threading.Event,
    on_progress: Callable[[int], None],
) -> None:
    """Baja los primeros ``RECORTE_S`` segundos sin pasar por el resto del video.

    Con ffmpeg directo y no con ``download_ranges`` de yt-dlp, que lo corre sin avisar nada hasta
    el final: la barra quedaría en 0% y cancelar tardaría lo mismo que la descarga (ADR-0029).
    """
    errores: deque[str] = deque(maxlen=5)
    try:
        proceso = subprocess.Popen(
            _comando_del_comienzo(formatos, archivo),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise YoutubeError(SIN_FFMPEG) from exc

    with proceso:
        threading.Thread(target=_cortar_si_cancelan, args=(proceso, cancel), daemon=True).start()
        for linea in proceso.stdout or ():
            clave, _, valor = linea.strip().partition("=")
            if clave == "out_time_us" and valor.isdigit():
                on_progress(min(95, int(valor) * 95 // (RECORTE_S * 1_000_000)))
            elif not valor:
                errores.append(clave)

    if cancel.is_set():
        raise DownloadCancelled()
    if proceso.returncode != 0 or not archivo.is_file():
        log.warning("ffmpeg no pudo bajar el comienzo del video: %s", " | ".join(errores))
        raise YoutubeError("No se pudo bajar el comienzo del video.")


def _cortar_si_cancelan(proceso: subprocess.Popen[str], cancel: threading.Event) -> None:
    while proceso.poll() is None:
        if cancel.wait(0.2):
            proceso.terminate()
            return


def _legible(error: str) -> str:
    texto = _ANSI.sub("", error).removeprefix("ERROR: ").strip()
    if "not a bot" in texto:
        return "YouTube pidió verificación anti-bot. Probá más tarde o actualizá yt-dlp."
    if "Requested format is not available" in texto:
        return "Este video no tiene versión H.264 de 720p o menos."
    if "ffmpeg is not installed" in texto:
        return SIN_FFMPEG
    return texto


class _Logger:
    """Sin logger, yt-dlp escribe en stdout; así queda en el log del proceso."""

    def debug(self, msg: str) -> None:
        log.debug(msg)

    def warning(self, msg: str) -> None:
        log.warning(msg)

    def error(self, msg: str) -> None:
        log.error(msg)
