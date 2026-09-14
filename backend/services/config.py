from __future__ import annotations

from backend.api.errors import BadRequest
from backend.api.schemas import ConfigOut, ConfigPatch
from backend.config import Settings
from backend.lib.domain.validation import ABSOLUTE_PATH_MESSAGE, validate_absolute_path
from backend.store.config import ConfigStore


class ConfigService:
    def __init__(self, settings: Settings) -> None:
        self.store = ConfigStore(settings.config_path)

    def get(self) -> ConfigOut:
        return self.store.get()

    def update(self, payload: ConfigPatch) -> ConfigOut:
        value = payload.attractDir.strip()
        if value:
            try:
                validate_absolute_path(value)
            except ValueError as exc:
                raise BadRequest(ABSOLUTE_PATH_MESSAGE) from exc
        return self.store.set_attract_dir(value or None)
