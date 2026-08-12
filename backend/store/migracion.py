from __future__ import annotations

from collections.abc import Callable
from typing import Any

CURRENT_VERSION = 1
Migration = Callable[[dict[str, Any]], dict[str, Any]]


def _v1(document: dict[str, Any]) -> dict[str, Any]:
    document["version"] = 1
    return document


MIGRATIONS: dict[int, Migration] = {0: _v1}


def migrate(document: dict[str, Any]) -> dict[str, Any]:
    version = int(document.get("version", 0))
    while version < CURRENT_VERSION:
        migration = MIGRATIONS.get(version)
        if migration is None:
            raise ValueError(f"No migration for version {version}")
        document = migration(document)
        version = int(document.get("version", version + 1))
    return document
