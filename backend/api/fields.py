from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.schemas import GameOut
from backend.config import get_settings
from backend.services.fields import FieldsService

router = APIRouter(prefix="/api/games/{game_id}/fields", tags=["fields"])


class FieldValue(BaseModel):
    value: str = ""


def _service() -> FieldsService:
    return FieldsService(get_settings())


@router.put("/{key}")
def put_field(game_id: str, key: str, payload: FieldValue) -> GameOut:
    return _service().set_value(game_id, key, payload.value)


@router.delete("/{key}")
def delete_field(game_id: str, key: str) -> GameOut:
    return _service().delete(game_id, key)
