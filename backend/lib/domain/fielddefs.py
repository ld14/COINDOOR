from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FIELDDEFS_PATH = ROOT / "frontend" / "src" / "lib" / "domain" / "fielddefs.json"


@lru_cache(maxsize=1)
def _load() -> Mapping[str, Any]:
    with FIELDDEFS_PATH.open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, Mapping):
        raise TypeError("fielddefs.json must contain an object")
    return value


def _keys(section: str) -> frozenset[str]:
    return frozenset(str(field["key"]) for field in _load()[section])


def fields(section: str) -> tuple[Mapping[str, Any], ...]:
    return tuple(_load()[section])


def label_for(section: str, key: str) -> str:
    for field in fields(section):
        if field["key"] == key:
            return str(field["label"])
    raise KeyError(f"{section}.{key} no está en fielddefs.json")


def identity_keys() -> frozenset[str]:
    return _keys("identity")


def image_keys() -> frozenset[str]:
    return _keys("images")


def video_keys() -> frozenset[str]:
    return _keys("videos")


def text_keys() -> frozenset[str]:
    return _keys("texts")


def rich_keys() -> frozenset[str]:
    return _keys("rich")


def max_length_for(section: str, key: str) -> int | None:
    """Limite de caracteres declarado en fielddefs.json, o ``None`` si no tiene."""
    for field in fields(section):
        if field["key"] == key:
            valor = field.get("maxLength")
            return int(valor) if valor is not None else None
    raise KeyError(f"{section}.{key} no esta en fielddefs.json")


def contract_asset(section: str, key: str) -> str:
    """Devuelve el nombre de asset del contrato ATTRACT para un key dado.

    Ejemplo: contract_asset("images", "caratula") → "boxFront"
    """
    for field in fields(section):
        if field["key"] == key:
            return str(field["contractAsset"])
    raise KeyError(f"{section}.{key} no tiene contractAsset en fielddefs.json")
