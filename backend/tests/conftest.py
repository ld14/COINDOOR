from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from backend.config import Settings, set_settings


@pytest.fixture(autouse=True)
def entorno_hermetico(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Ningún test lee el `.env` real.

    `Settings` tiene `env_file=".env"`, así que sin esto un test que construya
    `Settings()` hereda las credenciales de la máquina y sale a la red de verdad.
    Anular campo por campo en cada test no alcanza: basta olvidarse de uno nuevo
    para que vuelva a pasar.
    """
    for name in list(os.environ):
        if name.startswith("COINDOOR_"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    set_settings(None)
    yield
    set_settings(None)
