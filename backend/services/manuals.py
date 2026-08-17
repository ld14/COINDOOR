from __future__ import annotations

import uuid

from backend.api.errors import BadRequest, NotFound
from backend.api.schemas import GameManual, GameOut
from backend.config import Settings
from backend.store.archivo import escribir_binario, safe_id
from backend.store.juegos import GamesStore, to_out


class ManualsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = GamesStore(settings.games_dir)

    def upload(self, game_id: str, filename: str, data: bytes) -> GameOut:
        if not data:
            raise BadRequest("Archivo vacío")
        if not filename.lower().endswith(".pdf"):
            raise BadRequest("Solo se aceptan archivos PDF")
        game = self.store.get(game_id)
        system_dir = safe_id(game.systemId)
        game_dir = safe_id(game.id)
        manual_id = uuid.uuid4().hex[:12]
        dest = self.settings.media_dir / system_dir / game_dir / "_manual" / f"{manual_id}.pdf"
        escribir_binario(dest, data)
        manual = GameManual(id=manual_id, fileName=filename, status="unprocessed", pages=0)
        return to_out(self.store.add_manual(game_id, manual))

    def delete(self, game_id: str, manual_id: str) -> GameOut:
        game = self.store.get(game_id)
        manual = next((m for m in game.manuals if m.id == manual_id), None)
        if manual is None:
            raise NotFound(f"Manual no encontrado: {manual_id}")
        system_dir = safe_id(game.systemId)
        game_dir = safe_id(game.id)
        pdf_path = self.settings.media_dir / system_dir / game_dir / "_manual" / f"{manual_id}.pdf"
        if pdf_path.exists():
            pdf_path.unlink()
        return to_out(self.store.remove_manual(game_id, manual_id))
