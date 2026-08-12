from __future__ import annotations

import json
from pathlib import Path

from backend.api.errors import BadRequest
from backend.api.schemas import GameOut
from backend.config import Settings
from backend.store.juegos import GamesStore, to_out

ROOT = Path(__file__).resolve().parents[2]
FIELDDEFS_PATH = ROOT / "frontend" / "src" / "lib" / "domain" / "fielddefs.json"


class FieldsService:
    def __init__(self, settings: Settings) -> None:
        self.store = GamesStore(settings.games_dir)
        self.valid_keys = _field_keys()

    def set_value(self, game_id: str, key: str, value: str) -> GameOut:
        self._validate_key(key)
        return to_out(self.store.set_text_field(game_id, key, value))

    def delete(self, game_id: str, key: str) -> GameOut:
        self._validate_key(key)
        return to_out(self.store.delete_field(game_id, key))

    def _validate_key(self, key: str) -> None:
        if key not in self.valid_keys:
            raise BadRequest(f"Campo inválido: {key}")


def _field_keys() -> set[str]:
    with FIELDDEFS_PATH.open(encoding="utf-8") as file:
        fielddefs = json.load(file)
    keys: set[str] = set()
    for section in ("images", "videos", "texts", "rich"):
        keys.update(str(field["key"]) for field in fielddefs[section])
    return keys
