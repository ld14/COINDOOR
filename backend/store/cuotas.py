from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from backend.store.archivo import escribir_json, leer_json


class QuotasDocument(BaseModel):
    version: int = 1
    providers: dict[str, Any] = Field(default_factory=dict)


class QuotasStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        if not path.exists():
            escribir_json(path, QuotasDocument())

    def read(self) -> QuotasDocument:
        return leer_json(self.path, QuotasDocument)
