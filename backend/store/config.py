from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from backend.api.schemas import ConfigOut
from backend.store.archivo import escribir_json, leer_json


class ConfigDocument(BaseModel):
    version: int = 1
    attractDir: str | None = None


class ConfigStore:
    """Configuración no sensible de esta instalación (ADR-0022).

    Las credenciales siguen solo en `.env`; esto es para datos como rutas
    locales, que cambian sin reiniciar el proceso.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        if not path.exists():
            escribir_json(path, ConfigDocument())

    def get(self) -> ConfigOut:
        doc = leer_json(self.path, ConfigDocument)
        return ConfigOut(attractDir=doc.attractDir)

    def set_attract_dir(self, value: str | None) -> ConfigOut:
        escribir_json(self.path, ConfigDocument(attractDir=value))
        return ConfigOut(attractDir=value)

    def attract_dir(self) -> Path | None:
        value = leer_json(self.path, ConfigDocument).attractDir
        return Path(value) if value else None
