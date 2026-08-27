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
from backend.lib.media import ext_de_archivo
from backend.store.archivo import escribir_json, media_path


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

    galeria = _copy_galeria(settings, game, media_dir) if "galeria" in efectivo else []
    if not galeria:
        efectivo.discard("galeria")

    # El ROM se copia primero: game.json necesita su nombre real para el campo ``file``.
    rom_archivo: str | None = None
    rom_tratamiento: str | None = None
    rom_nombre: str | None = None
    if "juego" in efectivo:
        resultado = _copy_rom(game, root / "juego")
        if resultado is not None:
            rom_nombre, rom_tratamiento = resultado
            rom_archivo = f"juego/{rom_nombre}"
        else:
            efectivo.discard("juego")

    escribir_json(root / "data.json", build_datajson(game, efectivo, galeria))
    try:
        escribir_json(root / "game.json", build_gamejson(game, system_name, rom_nombre))
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise

    return StagingResult(root=root, incluye=frozenset(efectivo), rom_archivo=rom_archivo, rom_tratamiento=rom_tratamiento)  # noqa: E501


def _copy_galeria(
    settings: Settings,
    game: Mapping[str, Any],
    media_dir: Path,
) -> list[dict[str, str]]:
    """Copia el banco a ``media/_gallery/`` y devuelve lo que va en data.json.

    La subcarpeta con guion bajo sigue la marca de ``_manual/`` y ``_magazines/``
    del contrato de ATTRACT: dice "esto no es un asset auto-descubrible"
    (ADR-0016). Cada entrada declara un NOMBRE suelto, nunca una ruta.

    Una entrada cuyo archivo no esta en disco se omite: declararla dejaria un hueco
    del otro lado, que es donde peor se descubre.
    """
    imagenes = game.get("gallery", [])
    if not isinstance(imagenes, list):
        return []
    destino = media_dir / "_gallery"
    declaradas: list[dict[str, str]] = []
    for imagen in imagenes:
        if not isinstance(imagen, Mapping):
            continue
        url = imagen.get("url")
        source = media_path(settings.media_dir, url) if isinstance(url, str) else None
        if source is None or not source.exists():
            continue
        nombre = Path(str(imagen.get("file", ""))).name
        if not nombre:
            continue
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destino / nombre)
        declaradas.append({"file": nombre, "label": str(imagen.get("label", ""))})
    return declaradas


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
        ext = ext_de_archivo(source, game_key)
        dest = media_dir / f"{field['contractAsset']}{ext}"
        shutil.copy2(source, dest)


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
