from __future__ import annotations

from fastapi import APIRouter, UploadFile

from backend.api.schemas import GameOut
from backend.config import get_settings
from backend.services.roms import RomService

router = APIRouter(prefix="/api/games", tags=["roms"])


def _service() -> RomService:
    return RomService(get_settings())


@router.post("/{game_id}/rom")
def upload_rom(game_id: str, file: UploadFile) -> GameOut:
    data = file.file.read()
    return _service().upload(game_id, file.filename or "", data)
