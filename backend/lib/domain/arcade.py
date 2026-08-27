"""Qué sistemas soportan precarga de ArcadeDB.

Espejo de ``frontend/src/lib/domain/arcade.ts``: ambos leen
``arcade-systems.json``, así que el backend no puede habilitar un sistema que el
frontend esconde ni al revés.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCADE_SYSTEMS_PATH = ROOT / "frontend" / "src" / "lib" / "domain" / "arcade-systems.json"


@lru_cache(maxsize=1)
def markers() -> frozenset[str]:
    with ARCADE_SYSTEMS_PATH.open(encoding="utf-8") as file:
        value = json.load(file)
    return frozenset(str(marker) for marker in value["markers"])


def soporta_arcadedb(system_id: str) -> bool:
    """``True`` si los juegos del sistema son romsets MAME (los que indexa ArcadeDB)."""
    nombre = system_id.lower()
    return any(marker in nombre for marker in markers())
