from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.config import Settings
from backend.lib.domain import fielddefs
from backend.store.archivo import media_path

Medir = Callable[[Settings, Mapping[str, Any], str], tuple[bool, int]]


@dataclass(frozen=True)
class SeleccionItem:
    key: str
    label: str
    required: bool
    disponible: bool
    bytes: int


def compute_seleccion(settings: Settings, game: Mapping[str, Any]) -> list[SeleccionItem]:
    items = []
    for key, section, required, medir in _tabla():
        disponible, size = medir(settings, game, key)
        label = _label(section, key)
        items.append(SeleccionItem(key=key, label=label, required=required, disponible=disponible, bytes=size))  # noqa: E501
    return items


def _tabla() -> tuple[tuple[str, str, bool, Medir], ...]:
    filas: list[tuple[str, str, bool, Medir]] = [("identidad", "identidad", True, _medir_identidad)]  # noqa: E501
    filas += [(field["key"], "images", field["required"], _medir_media("images")) for field in fielddefs.fields("images")]  # noqa: E501
    filas += [(field["key"], "videos", field["required"], _medir_media("video")) for field in fielddefs.fields("videos")]  # noqa: E501
    filas += [(field["key"], "texts", field["required"], _medir_texto) for field in fielddefs.fields("texts")]  # noqa: E501
    filas.append(("review", "rich", False, _medir_review))
    filas.append(("cheats", "rich", False, _medir_cheats))
    filas.append(("accent", "rich", True, _medir_accent))
    filas.append(("accent2", "rich", False, _medir_accent2))
    filas.append(("manual", "rich", False, _medir_manual))
    filas.append(("juego", "juego", False, _medir_juego))
    return tuple(filas)


def _label(section: str, key: str) -> str:
    if section == "identidad":
        return "Identidad"
    if section == "juego":
        return "Archivo del juego"
    return fielddefs.label_for(section, key)


def _medir_identidad(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
    identity = game.get("identity", {})
    payload = identity if isinstance(identity, Mapping) else {}
    return True, len(json.dumps(payload).encode("utf-8"))


def _medir_media(section: str) -> Medir:
    def probe(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
        container = game.get(section, {})
        field = container.get(key) if isinstance(container, Mapping) else None
        if not isinstance(field, Mapping) or field.get("status") == "empty":
            return False, 0
        url = field.get("url")
        path = media_path(settings.media_dir, url) if isinstance(url, str) else None
        if path is None:
            return True, 0
        return True, _path_size(path)

    return probe


def _medir_texto(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
    container = game.get("texts", {})
    field = container.get(key) if isinstance(container, Mapping) else None
    if not isinstance(field, Mapping) or field.get("status") == "empty":
        return False, 0
    return True, len(str(field.get("value", "")).encode("utf-8"))


def _medir_review(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
    review = game.get("review", {})
    if not isinstance(review, Mapping) or review.get("status") == "empty":
        return False, 0
    payload = {"score": review.get("score"), "cats": review.get("cats", {})}
    return True, len(json.dumps(payload).encode("utf-8"))


def _medir_cheats(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
    cheats = game.get("cheats", {})
    if not isinstance(cheats, Mapping) or cheats.get("status") == "empty":
        return False, 0
    return True, len(json.dumps(cheats.get("groups", [])).encode("utf-8"))


def _medir_accent(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
    if game.get("accent") == "empty":
        return False, 0
    return True, len(str(game.get("accentValue", "")).encode("utf-8"))


def _medir_accent2(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
    value = str(game.get("accent2Value", ""))
    if not value.strip():
        return False, 0
    return True, len(value.encode("utf-8"))


def _medir_manual(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
    # ponytail: sin endpoint que persista el PDF ni sus páginas (mismo hueco que tenía
    # media antes de esta sesión). Cuando exista, sumar el tamaño real en vez de 0.
    manuals = game.get("manuals", [])
    return bool(manuals), 0


def _medir_juego(settings: Settings, game: Mapping[str, Any], key: str) -> tuple[bool, int]:
    # ponytail: romSource='upload' todavía no tiene endpoint que guarde el archivo en
    # disco. Si romRef no apunta a algo real, queda no disponible — no se inventa nada.
    rom_ref = str(game.get("romRef", ""))
    if not rom_ref:
        return False, 0
    path = Path(rom_ref)
    if not path.exists():
        return False, 0
    return True, _path_size(path)


def _path_size(path: Path) -> int:
    try:
        if path.is_dir():
            return sum(entry.stat().st_size for entry in path.rglob("*") if entry.is_file())
        return path.stat().st_size
    except OSError:
        return 0
