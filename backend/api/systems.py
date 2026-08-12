from __future__ import annotations

from fastapi import APIRouter

from backend.api.schemas import NewSystem, System
from backend.config import get_settings
from backend.services.systems import SystemsService

router = APIRouter(prefix="/api/systems", tags=["systems"])


def _service() -> SystemsService:
    return SystemsService(get_settings())


@router.get("")
def list_systems() -> list[System]:
    return _service().list()


@router.post("")
def create_system(payload: NewSystem) -> System:
    return _service().create(payload)
