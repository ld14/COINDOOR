from __future__ import annotations

import shutil
import tempfile
import zipfile
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.bundle.datajson import build_datajson
from backend.bundle.gamejson import build_gamejson
from backend.config import Settings
from backend.lib.domain import fielddefs
from backend.store.archivo import escribir_json, media_path

IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp"})
VIDEO_EXTS = frozenset({".mp4", ".webm", ".ogg", ".avi", ".mkv"})


@dataclass(frozen=True)
class StagingResult:
    root: Path
    incluye: frozenset[str]
    rom_archivo: str | None
    rom_tratamiento: str | None


def build_staging(settings: Settings, game: Mapping[str, Any], incluir: Collection[str], system_name: str) -> StagingResult:  # noqa: E501
    """Arma el arbol temporal que ``attract import`` va a decodificar.

    Estructura del staging (igual al contrato del zip):
        game.json          <- raiz
        data.json          <- raiz
        media/             <- assets planos
    """
    root = Path(tempfile.mkdtemp(prefix="export-", dir=settings.tmp_dir))
    media_dir = root / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    efectivo = set(incluir)
    if not _manual_files_exist(settings, game):
        efectivo.discard("manual")

    _copy_assets(settings, game, media_dir, "images", fielddefs.fields("images"), efectivo)
    _copy_assets(settings, game, media_dir, "video", fielddefs.fields("videos"), efectivo)

    escribir_json(root / "data.json", build_datajson(game, efectivo))
    escribir_json(root / "game.json", build_gamejson(game, system_name))

    rom_archivo: str | None = None
    rom_tratamiento: str | None = None
    if "juego" in efectivo:
        resultado = _copy_rom(game, root / "juego")
        if resultado is not None:
            nombre, tratamiento = resultado
            rom_archivo = f"juego/{nombre}"
            rom_tratamiento = tratamiento
        else:
            efectivo.discard("juego")

    return StagingResult(root=root, incluye=frozenset(efectivo), rom_archivo=rom_archivo, rom_tratamiento=rom_tratamiento)  # noqa: E501


def _copy_assets(
    settings: Settings,
    game: Mapping[str, Any],
    media_dir: Path,
    game_key: str,
    defs: tuple[Mapping[str, Any], ...],
    incluir: Collection[str],
) -> None:
    container = game.get(game_key, {})
    if not isinstance(container, Mapping):
        return
    for field in defs:
        key = str(field["key"])
        if not field["required"] and key not in incluir:
            continue
        entry = container.get(key)
        if not isinstance(entry, Mapping) or entry.get("status") == "empty":
            continue
        url = entry.get("url")
        source = media_path(settings.media_dir, url) if isinstance(url, str) else None
        if source is None or not source.exists():
            continue
        ext = _real_extension(source, game_key)
        dest = media_dir / f"{field['contractAsset']}{ext}"
        shutil.copy2(source, dest)


def _real_extension(path: Path, media_type: str) -> str:
    """Extrae la extension real del archivo, ignorando sufijos hash.

    Archivos en disco pueden tener nombres como ``caratula.b8uycgdntcg6il6wunv8pwhajs``
    donde la extension real (jpg/png) no esta en el nombre. Primero intenta por el
    nombre; si no funciona, detecta por magic bytes.
    """
    name = path.name
    known = IMAGE_EXTS if media_type == "images" else VIDEO_EXTS
    for ext in known:
        if name.lower().endswith(ext):
            return ext
    return _detect_ext_by_magic(path)


def _detect_ext_by_magic(path: Path) -> str:
    """Detecta la extension por los primeros bytes del archivo (magic bytes)."""
    try:
        with open(path, "rb") as f:
            header = f.read(16)
    except OSError:
        return ".bin"
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if header[:2] == b"\xff\xd8":
        return ".jpg"
    if header[:4] == b"GIF8":
        return ".gif"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp"
    if header[:4] == b"\x1a\x45\xdf\xa3" or header[:3] == b"\x1a\x45\xdf":
        return ".webm"
    if header[:4] == b"\x00\x00\x00\x1c" or header[:4] == b"\x00\x00\x00\x18":
        return ".mp4"
    if header[:4] == b"OggS":
        return ".ogg"
    return ".bin"


def _copy_rom(game: Mapping[str, Any], juego_dir: Path) -> tuple[str, str] | None:
    rom_ref = str(game.get("romRef", ""))
    if not rom_ref:
        return None
    source = Path(rom_ref)
    if not source.exists():
        return None
    juego_dir.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        nombre = f"{source.name}.zip"
        with zipfile.ZipFile(juego_dir / nombre, "w", zipfile.ZIP_DEFLATED) as archivo:
            for entry in source.rglob("*"):
                if entry.is_file():
                    archivo.write(entry, entry.relative_to(source))
        return nombre, "descomprimir"
    shutil.copy2(source, juego_dir / source.name)
    return source.name, "copiar"


def _manual_files_exist(settings: Settings, game: Mapping[str, Any]) -> bool:
    return False
