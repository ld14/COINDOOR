from __future__ import annotations

from backend.api.errors import BadRequest
from backend.api.schemas import GameOut
from backend.config import Settings
from backend.lib.domain.fielddefs import image_keys, rich_keys, text_keys, video_keys
from backend.store.juegos import GamesStore, to_out


class FieldsService:
    def __init__(self, settings: Settings) -> None:
        self.store = GamesStore(settings.games_dir)
        self.valid_keys = image_keys() | video_keys() | text_keys() | rich_keys()

    def set_value(self, game_id: str, key: str, value: str) -> GameOut:
        self._validate_key(key)
        return to_out(self.store.set_text_field(game_id, key, value))

    def delete(self, game_id: str, key: str) -> GameOut:
        self._validate_key(key)
        return to_out(self.store.delete_field(game_id, key))

    def _validate_key(self, key: str) -> None:
        if key not in self.valid_keys:
            raise BadRequest(f"Campo inválido: {key}")
