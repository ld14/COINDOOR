from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from backend.api.errors import NotFound
from backend.api.schemas import NewSystem, System
from backend.lib.domain.validation import ABSOLUTE_PATH_MESSAGE, validate_absolute_path
from backend.store.archivo import escribir_json, leer_json


class SystemsDocument(BaseModel):
    version: int = 1
    items: list[System] = Field(default_factory=list)


class SystemsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        if not path.exists():
            escribir_json(path, SystemsDocument())

    def list(self) -> list[System]:
        return leer_json(self.path, SystemsDocument).items

    def get(self, system_id: str) -> System:
        for system in self.list():
            if system.id == system_id:
                return system
        raise NotFound(f"Sistema no encontrado: {system_id}")

    def create(self, payload: NewSystem) -> System:
        items = self.list()
        valid = True
        error_msg = None
        try:
            validate_absolute_path(payload.launchCmd)
        except ValueError:
            valid = False
            error_msg = ABSOLUTE_PATH_MESSAGE
        system = System(
            id=payload.shortName,
            name=payload.name,
            shortName=payload.shortName,
            launchCmd=payload.launchCmd,
            valid=valid,
            errorMsg=error_msg,
            gameCount=0,
        )
        items = [item for item in items if item.id != system.id]
        items.append(system)
        escribir_json(self.path, SystemsDocument(items=items))
        return system
