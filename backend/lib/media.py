"""Deteccion de tipo de archivo por magic bytes y normalizacion de imagenes bajadas.

Existe porque las dos puntas la necesitan y antes solo la tenia una: al bajar de
ArcadeDB (que sirve los videos como ``application/octet-stream`` desde un
``download_file.php``, sin extension util en la URL) y al armar el staging del
export (donde los archivos en disco pueden tener nombre con hash).
"""

from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp"})
VIDEO_EXTS = frozenset({".mp4", ".webm", ".ogg", ".avi", ".mkv"})


def ext_por_magic(header: bytes) -> str:
    """Extension segun los primeros bytes. ``""`` si no reconoce el formato."""
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if header[:2] == b"\xff\xd8":
        return ".jpg"
    if header[:4] == b"GIF8":
        return ".gif"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp"
    if header[:4] == b"\x1a\x45\xdf\xa3":
        return ".webm"
    # ISO BMFF (mp4/m4v/mov): el marcador es ``ftyp`` en el offset 4. El tamaño
    # del box que lo precede es variable — mirarlo a el en vez del marcador
    # dejaba pasar como ".bin" cualquier mp4 con un box distinto de 0x18/0x1c.
    if header[4:8] == b"ftyp":
        return ".mp4"
    if header[:4] == b"OggS":
        return ".ogg"
    return ""


class GifAnimado(ValueError):
    """Un GIF de varios cuadros: no entra a la ficha, ni congelado ni como video."""


def sin_gif(contenido: bytes, suffix: str) -> tuple[bytes, str]:
    """Un GIF de un cuadro pasa a PNG; uno animado se rechaza; otra imagen conserva sus bytes.

    El contrato de ATTRACT no admite ``.gif`` y ``attract doctor`` lo rechaza en la galeria,
    pero casi todas las capturas de DOS de myabandonware son GIF de un cuadro. Si ffmpeg falla,
    levanta la excepcion: mejor una imagen menos que una que ATTRACT rechaza.
    """
    if contenido[:4] != b"GIF8":
        # Un sitio puede declarar image/gif y servir un JPEG: manda el contenido.
        return contenido, (ext_por_magic(contenido[:16]) or ".jpg") if suffix == ".gif" else suffix
    salida = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", "pipe:0", "-frames:v", "2",
         "-fps_mode", "passthrough", "-f", "image2pipe", "-c:v", "png", "pipe:1"],
        input=contenido,
        check=True,
        capture_output=True,
        timeout=30,
    )
    if salida.stdout.count(b"\x89PNG\r\n\x1a\n") > 1:
        raise GifAnimado
    return salida.stdout, ".png"


def colores_dominantes(ruta: Path, cuantos: int = 2) -> list[str]:
    """Los colores mas frecuentes de una imagen, en ``#rrggbb``, los que tienen color primero.

    Misma cuantizacion que ``useDominantColors``, para que coincidan con los que ofrece la
    ficha. Sin preferir la saturacion, casi toda caja daria negro.
    """
    salida = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(ruta), "-vf", "scale=64:64", "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout
    conteo = Counter(
        (salida[i] // 32 * 32 + 16, salida[i + 1] // 32 * 32 + 16, salida[i + 2] // 32 * 32 + 16)
        for i in range(0, len(salida) - 2, 3)
    )
    colores = [color for color, _ in conteo.most_common()]
    colores.sort(key=lambda c: max(c) - min(c) < 48)  # estable: conserva la frecuencia
    return ["#{:02x}{:02x}{:02x}".format(*color) for color in colores[:cuantos]]


def ext_de_archivo(path: Path, media_type: str) -> str:
    """Extension real de un archivo en disco, ignorando sufijos hash del nombre."""
    nombre = path.name.lower()
    conocidas = IMAGE_EXTS if media_type == "images" else VIDEO_EXTS
    for ext in conocidas:
        if nombre.endswith(ext):
            return ext
    try:
        with path.open("rb") as archivo:
            header = archivo.read(16)
    except OSError:
        return ".bin"
    return ext_por_magic(header) or ".bin"
