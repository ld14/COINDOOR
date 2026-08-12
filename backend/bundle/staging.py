from __future__ import annotations

import shutil
import tempfile
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

from backend.bundle.datajson import build_datajson
from backend.config import Settings
from backend.lib.domain import fielddefs
from backend.store.archivo import escribir_json, media_path


def build_staging(settings: Settings, game: Mapping[str, Any], incluir: Collection[str]) -> Path:
    """Arma el árbol temporal que `attract doctor` va a verificar. Los nombres ya son
    los del contrato (`caratula` -> `boxFront`, etc): la traducción ocurre acá y en
    ningún otro lado."""
    root = Path(tempfile.mkdtemp(prefix="export-", dir=settings.tmp_dir))
    media_dir = root / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    efectivo = set(incluir)
    if not _manual_files_exist(settings, game):
        # ponytail: sin endpoint que guarde manual.pdf ni sus páginas todavía (mismo
        # hueco de seleccion.py/datajson.py). Sin archivos reales que copiar, no se
        # incluye "manual" en data.json aunque el usuario lo haya pedido — nunca un
        # data.json que promete páginas que el zip no trae.
        efectivo.discard("manual")

    _copy_assets(settings, game, media_dir, "images", fielddefs.fields("images"), efectivo)
    _copy_assets(settings, game, media_dir, "video", fielddefs.fields("videos"), efectivo)

    escribir_json(media_dir / "data.json", build_datajson(game, efectivo))
    _write_synopsis(root, game)

    if "juego" in efectivo:
        _copy_rom(game, root / "juego")

    return root


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
        dest = media_dir / f"{field['contractAsset']}{source.suffix}"
        shutil.copy2(source, dest)


def _write_synopsis(root: Path, game: Mapping[str, Any]) -> None:
    texts = game.get("texts", {})
    sinopsis = texts.get("sinopsis") if isinstance(texts, Mapping) else None
    value = sinopsis.get("value", "") if isinstance(sinopsis, Mapping) else ""
    escribir_json(root / "_synopsis.json", {"summary": str(value)})


def _copy_rom(game: Mapping[str, Any], juego_dir: Path) -> None:
    rom_ref = str(game.get("romRef", ""))
    if not rom_ref:
        return
    source = Path(rom_ref)
    if not source.exists():
        return
    juego_dir.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, juego_dir / source.name)
    else:
        shutil.copy2(source, juego_dir / source.name)


def _manual_files_exist(settings: Settings, game: Mapping[str, Any]) -> bool:
    # ponytail: siempre False hasta que exista el endpoint que guarda manual.pdf y sus
    # páginas rasterizadas. Reemplazar por una comprobación real en disco cuando exista.
    return False
