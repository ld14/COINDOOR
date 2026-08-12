from __future__ import annotations

from backend.api.errors import BadRequest
from backend.api.schemas import NewSystem, System
from backend.config import Settings
from backend.lib.domain.validation import ABSOLUTE_PATH_MESSAGE, validate_absolute_path
from backend.store.sistemas import SystemsStore


class SystemsService:
    def __init__(self, settings: Settings) -> None:
        self.store = SystemsStore(settings.systems_path)

    def list(self) -> list[System]:
        return self.store.list()

    def create(self, payload: NewSystem) -> System:
        try:
            validate_absolute_path(payload.launchCmd)
        except ValueError as exc:
            raise BadRequest(ABSOLUTE_PATH_MESSAGE) from exc
        return self.store.create(payload)
