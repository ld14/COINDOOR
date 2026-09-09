from __future__ import annotations

from pathlib import Path

from backend.api.errors import BadRequest
from backend.api.schemas import GameOut
from backend.config import Settings
from backend.store.archivo import escribir_binario
from backend.store.juegos import GamesStore, to_out


class RomService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = GamesStore(settings.games_dir)

    def upload(self, game_id: str, filename: str, data: bytes) -> GameOut:
        if not data:
            raise BadRequest("Archivo vacío")
        if not filename:
            raise BadRequest("Nombre de archivo inválido")

        game = self.store.get(game_id)
        suffix = Path(filename).suffix.lower()
        if not suffix:
            raise BadRequest("El archivo debe tener extensión (ej: .zip, .nes, .sms)")

        # La carpeta la decide el store: puede ser la del propio juego (ADR-0017).
        rom_path = self.store.dir_de(game) / filename
        escribir_binario(rom_path, data)

        return to_out(self.store.set_rom_ref(game_id, str(rom_path)))
