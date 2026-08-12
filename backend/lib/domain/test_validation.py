from __future__ import annotations

import re

import pytest
from pydantic import ValidationError

from backend.lib.domain.validation import (
    ABSOLUTE_PATH_MESSAGE,
    HEX_COLOR_MESSAGE,
    YEAR_MESSAGE,
    NewSystem,
    validate_absolute_path,
    validate_hex_color,
    validate_year,
)


def test_absolute_path_accepts_posix_and_windows() -> None:
    assert validate_absolute_path("/opt/mame/mame64") == "/opt/mame/mame64"
    assert validate_absolute_path(r"C:\Emu\bin.exe") == r"C:\Emu\bin.exe"


def test_absolute_path_rejects_relative() -> None:
    with pytest.raises(ValueError, match=re.escape(ABSOLUTE_PATH_MESSAGE)):
        validate_absolute_path("emulators/snes9x")


def test_hex_color() -> None:
    assert validate_hex_color("#2F6FED") == "#2F6FED"
    with pytest.raises(ValueError, match=re.escape(HEX_COLOR_MESSAGE)):
        validate_hex_color("2F6FED")


def test_year() -> None:
    assert validate_year("1989") == "1989"
    with pytest.raises(ValueError, match=re.escape(YEAR_MESSAGE)):
        validate_year("197X")


def test_new_system() -> None:
    system = NewSystem(name="Arcade", short_name="arcade", launch_cmd="/usr/local/bin/mame")
    assert system.launch_cmd == "/usr/local/bin/mame"

    with pytest.raises(ValidationError):
        NewSystem(name="SNES", short_name="snes", launch_cmd="emulators/snes9x")
