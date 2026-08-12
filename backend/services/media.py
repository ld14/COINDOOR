from __future__ import annotations

from pathlib import Path

from backend.api.errors import BadRequest
from backend.api.schemas import GameOut
from backend.config import Settings
from backend.lib.domain.fielddefs import image_keys, video_keys
from backend.store.archivo import escribir_binario, safe_id
from backend.store.juegos import GamesStore, to_out


class MediaService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = GamesStore(settings.games_dir)
        self.valid_keys = image_keys() | video_keys()

    def upload(self, game_id: str, key: str, filename: str, data: bytes) -> GameOut:
        if key not in self.valid_keys:
            raise BadRequest(f"Campo de media inválido: {key}")
        if not data:
            raise BadRequest("Archivo vacío")
        game = self.store.get(game_id)
        suffix = Path(filename).suffix.lower()
        system_dir = safe_id(game.systemId)
        game_dir = safe_id(game.id)
        path = self.settings.media_dir / system_dir / game_dir / f"{key}{suffix}"
        escribir_binario(path, data)
        url = f"/media/{system_dir}/{game_dir}/{key}{suffix}"
        return to_out(self.store.set_media_field(game_id, key, url))
