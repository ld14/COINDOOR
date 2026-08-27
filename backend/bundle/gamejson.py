from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from backend.api.errors import BadRequest

HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")

# Soporte fisico del juego original. Enum cerrado del contrato ATTRACT
# (game.json schema_version "1"), case-sensitive. NO es el formato del archivo:
# eso es ``file_format`` y es texto libre.
FORMATOS_FISICOS = ("Arcade", "GD-ROM", "PCB", "Cartucho", "Diskette", "CD", "DVD")
_POR_NOMBRE = {f.lower(): f for f in FORMATOS_FISICOS}

# Sistemas cuyo soporte fisico es conocido sin que el usuario lo declare.
_FORMATO_POR_SISTEMA = {"mame": "Arcade", "arcade": "Arcade"}


def build_gamejson(
    game: Mapping[str, Any],
    system_name: str,
    rom_file: str | None = None,
) -> dict[str, Any]:
    """Construye game.json segun el contrato COINDOOR -> ATTRACT (ADR-0027).

    Campos obligatorios: schema_version, system, set, title.

    ``rom_file`` es el nombre del archivo tal como viaja dentro de ``juego/``.
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

    fmt = _formato_fisico(str(identity.get("format", "")).strip(), system_name)
    if fmt:
        result["format"] = fmt

    file_format = str(game.get("file_format") or "").strip() or _extension(rom_file)
    if file_format:
        result["file_format"] = file_format

    if rom_file:
        result["file"] = rom_file

    tratamiento = str(game.get("tratamiento", "")).strip() if rom_file else ""
    if tratamiento:
        result["tratamiento"] = tratamiento

    summary = _extract_summary(game)
    if summary:
        result["summary"] = summary

    return result


def _formato_fisico(declarado: str, system_name: str) -> str:
    """Devuelve el soporte fisico canonico, o falla si el declarado no es del enum."""
    if not declarado:
        return _FORMATO_POR_SISTEMA.get(system_name.strip().lower(), "")
    canonico = _POR_NOMBRE.get(declarado.lower())
    if canonico is None:
        raise BadRequest(
            f"El formato '{declarado}' no es un soporte fisico conocido "
            f"(conocidos: {list(FORMATOS_FISICOS)}). Corregilo en la identidad del juego. "
            f"El formato del archivo ('zip', 'chd', 'iso') va en 'Formato de archivo', "
            f"no en 'Formato'."
        )
    return canonico


def _extension(rom_file: str | None) -> str:
    if not rom_file or "." not in rom_file:
        return ""
    return rom_file.rsplit(".", 1)[-1].lower()


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
