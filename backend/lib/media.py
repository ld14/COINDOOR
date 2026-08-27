"""Deteccion de tipo de archivo por magic bytes.

Existe porque las dos puntas la necesitan y antes solo la tenia una: al bajar de
ArcadeDB (que sirve los videos como ``application/octet-stream`` desde un
``download_file.php``, sin extension util en la URL) y al armar el staging del
export (donde los archivos en disco pueden tener nombre con hash).
"""

from __future__ import annotations

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
