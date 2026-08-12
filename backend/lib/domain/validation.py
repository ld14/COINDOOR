from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

ABSOLUTE_PATH_MESSAGE = (
    "La ruta debe ser absoluta (ej: /opt/emulador/bin o C:\\Emuladores\\bin.exe). "
    "Si no, el juego no arranca en el gabinete sin avisar."
)
HEX_COLOR_MESSAGE = "Formato inválido (ej: #2F6FED)"
YEAR_MESSAGE = "Debe ser un número de 4 dígitos (contrato ATTRACT)."


def validate_absolute_path(value: str) -> str:
    if value.startswith("/") or re.match(r"^[A-Za-z]:\\", value):
        return value
    raise ValueError(ABSOLUTE_PATH_MESSAGE)


def validate_hex_color(value: str) -> str:
    if re.fullmatch(r"#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})", value):
        return value
    raise ValueError(HEX_COLOR_MESSAGE)


def validate_year(value: str) -> str:
    if re.fullmatch(r"\d{4}", value):
        return value
    raise ValueError(YEAR_MESSAGE)


class NewSystem(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    short_name: Annotated[str, Field(min_length=1)]
    launch_cmd: str

    @field_validator("launch_cmd")
    @classmethod
    def launch_cmd_must_be_absolute(cls, value: str) -> str:
        return validate_absolute_path(value)
