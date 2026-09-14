from __future__ import annotations

from fastapi import APIRouter

from backend.api.schemas import ConfigOut, ConfigPatch
from backend.config import get_settings
from backend.services.config import ConfigService

router = APIRouter(prefix="/api/config", tags=["config"])


def _service() -> ConfigService:
    return ConfigService(get_settings())


@router.get("")
def get_config() -> ConfigOut:
    return _service().get()


@router.patch("")
def update_config(payload: ConfigPatch) -> ConfigOut:
    return _service().update(payload)
