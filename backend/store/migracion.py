from __future__ import annotations

from collections.abc import Callable
from typing import Any

CURRENT_VERSION = 2
Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _v1(document: dict[str, Any]) -> dict[str, Any]:
    document["version"] = 1
    return document


# Textos de la guia «Como se juega». Antes de v2 un texto `manual` contaba como revisado sin
# mas: lo marcaba un proceso viejo, sin que nadie lo mirara con las reglas de ahora.
_TEXTOS_GUIA = ("objetivo", "primerosPasos", "reglasEsenciales", "modo")


def _v2(document: dict[str, Any]) -> dict[str, Any]:
    """Los textos de la guia marcados a mano pasan a «sugerido, sin revisar».

    Asi la guia exportada baja de `revisado` a `borrador` hasta que una persona vuelva a
    guardarlos: ya con el seguimiento por campo, y no por un proceso anterior.
    """
    texts = document.get("texts")
    if isinstance(texts, dict):
        for clave in _TEXTOS_GUIA:
            campo = texts.get(clave)
            if isinstance(campo, dict) and campo.get("status") == "manual":
                campo["status"] = "suggested"
    document["version"] = 2
    return document


MIGRATIONS: dict[int, Migration] = {0: _v1, 1: _v2}


def migrate(document: dict[str, Any]) -> dict[str, Any]:
    version = int(document.get("version", 0))
    while version < CURRENT_VERSION:
        migration = MIGRATIONS.get(version)
        if migration is None:
            raise ValueError(f"No migration for version {version}")
        document = migration(document)
        version = int(document.get("version", version + 1))
    return document
