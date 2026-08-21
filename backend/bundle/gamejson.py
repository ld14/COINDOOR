from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")


def build_gamejson(game: Mapping[str, Any], system_name: str) -> dict[str, Any]:
    """Construye game.json segun el contrato COINDOOR -> ATTRACT (ADR-0027).

    Campos obligatorios: schema_version, system, set, title.
    """
    identity = game.get("identity", {})
    if not isinstance(identity, Mapping):
        identity = {}

    result: dict[str, Any] = {
        "schema_version": "1",
        "system": system_name,
        "set": str(game.get("id", "")),
        "title": str(identity.get("title", "")),
    }

    for json_key, id_key in (
        ("developer", "developer"),
        ("publisher", "publisher"),
        ("genre", "genre"),
        ("release", "year"),
    ):
        val = str(identity.get(id_key, "")).strip()
        if val:
            result[json_key] = val

    players = str(identity.get("players", "")).strip()
    if players:
        result["players"] = _players_int(players)

    fmt = str(identity.get("format", "")).strip()
    if fmt:
        result["format"] = fmt

    file_format = str(game.get("file_format", "")).strip()
    if file_format:
        result["file_format"] = file_format

    tratamiento = str(game.get("tratamiento", "")).strip()
    if tratamiento:
        result["tratamiento"] = tratamiento

    summary = _extract_summary(game)
    if summary:
        result["summary"] = summary

    return result


def _players_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 1


def _extract_summary(game: Mapping[str, Any]) -> str:
    texts = game.get("texts", {})
    if not isinstance(texts, Mapping):
        return ""
    sinopsis = texts.get("sinopsis")
    if not isinstance(sinopsis, Mapping):
        return ""
    return str(sinopsis.get("value", "")).strip()


def validate_accent(value: str) -> bool:
    """Valida que un color sea hex #rrggbb (6 digitos)."""
    return isinstance(value, str) and bool(HEX6.match(value))
