from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from backend.config import Settings, set_settings
from backend.lib.providers.myabandonware import cliente as myabandonware
from backend.lib.providers.referencia import images as busqueda_de_imagenes


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
    # Un Chromium instalado en la máquina haría que el registro construya MobyGames y que
    # un test salga a scrapear de verdad. Los tests del proveedor lo arman a mano.
    monkeypatch.setattr("backend.lib.providers.registro.navegador_disponible", lambda: False)
    monkeypatch.setattr("backend.services.msdos.navegador_disponible", lambda: False)
    monkeypatch.setattr("backend.services.precalentar.navegador_disponible", lambda: False)
    # myabandonware va por HTTP común (ADR-0027): sin índice no encuentra ningún juego y no
    # baja nada. Los tests del cliente le dan un índice a mano.
    monkeypatch.setattr(
        "backend.lib.providers.myabandonware.cliente.indice", lambda _http, _carpeta: ()
    )
    myabandonware.olvidar()
    busqueda_de_imagenes.olvidar()
    set_settings(None)
    yield
    set_settings(None)
