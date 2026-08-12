from __future__ import annotations

from fastapi import APIRouter, UploadFile

from backend.api.schemas import GameOut
from backend.config import get_settings
from backend.services.media import MediaService

router = APIRouter(prefix="/api/games/{game_id}/media", tags=["media"])


def _service() -> MediaService:
    return MediaService(get_settings())


@router.put("/{key}")
def put_media(game_id: str, key: str, file: UploadFile) -> GameOut:
    data = file.file.read()
    return _service().upload(game_id, key, file.filename or "", data)
