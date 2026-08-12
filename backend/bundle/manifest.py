from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import UTC, datetime
from typing import Any

# Placeholder hasta que ATTRACT publique su propia versión de contrato (ADR-0001,
# ver spec.md 001 §Decisiones resueltas antes de implementar).
CONTRATO_VERSION = "1"
BUNDLE_VERSION = 1


def build_manifest(
    game: Mapping[str, Any],
    coleccion: str,
    incluye: Collection[str],
    rom_archivo: str | None,
    rom_tratamiento: str | None,
    verificado: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "bundle": BUNDLE_VERSION,
        "generado": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "contrato": CONTRATO_VERSION,
        "coleccion": coleccion,
        "set": str(game.get("id", "")),
        "identidad": {
            "origen": _origen(game),
            "campos": _identity_fields(game),
        },
        "artefactos": _artefactos(rom_archivo, rom_tratamiento),
        "incluye": sorted(incluye),
        "verificado": dict(verificado),
    }


def _origen(game: Mapping[str, Any]) -> str:
    # ponytail: no hay tracking de "identidad editada a mano después de precargarse
    # desde MAME" (ADR-0004 regla 1) — StoredGame no guarda los valores originales
    # para diffear. Mientras tanto, solo identitySource=='mame' produce origen 'mame';
    # cualquier otra cosa (incluida una edición real) cae en 'declarada', que es el
    # lado seguro: nunca le dice a install que consulte MAME sobre algo que no confirmó.
    return "mame" if game.get("identitySource") == "mame" else "declarada"


def _identity_fields(game: Mapping[str, Any]) -> dict[str, Any]:
    identity = game.get("identity", {})
    if not isinstance(identity, Mapping):
        identity = {}
    return {
        "title": str(identity.get("title", "")),
        "developer": str(identity.get("developer", "")),
        "publisher": str(identity.get("publisher", "")),
        "genre": str(identity.get("genre", "")),
        "release": str(identity.get("year", "")),
        "players": _players_int(identity.get("players", "")),
        "x-formato": str(identity.get("format", "")),
    }


def _players_int(value: Any) -> int:
    # Mismo criterio que ATTRACT (CONVENCION.md Nota 1): si no parsea a entero limpio
    # ("1-2", "2 alternados"), se escribe 1 en vez de fallar o inventar un rango.
    try:
        return int(str(value).strip())
    except ValueError:
        return 1


def _artefactos(rom_archivo: str | None, rom_tratamiento: str | None) -> list[dict[str, str]]:
    if rom_archivo is None or rom_tratamiento is None:
        return []
    return [
        {
            "archivo": rom_archivo,
            "destino": rom_archivo.split("/", 1)[-1],
            "tratamiento": rom_tratamiento,
        }
    ]
