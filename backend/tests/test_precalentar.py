from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from types import TracebackType
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from backend.api.schemas import NewSystem
from backend.config import Settings
from backend.lib.providers.politica import ProviderHttpError
from backend.lib.providers.scraping import ScrapingClient
from backend.services import precalentar
from backend.services.precalentar import URL, VIGENCIA_S, PrecalentamientoMobyGames
from backend.store.sistemas import SystemsStore


class _Cliente:
    def __init__(self, cancel: threading.Event, falla: bool = False) -> None:
        self.cancel = cancel
        self.falla = falla
        self.pedidas: list[str] = []
        self.cerrado = False

    def __enter__(self) -> _Cliente:
        return self

    def __exit__(
        self,
        _t: type[BaseException] | None,
        _e: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        self.cerrado = True

    def get_page(self, url: str, **_k: Any) -> Any:
        self.pedidas.append(url)
        if self.falla:
            raise ProviderHttpError("sitio rechazó la solicitud")
        return object()


def _settings(tmp_path: Path, *sistemas: str, **extra: Any) -> Settings:
    settings = Settings(data_dir=tmp_path / "data", **extra)
    settings.data_dir.mkdir(parents=True)
    for nombre in sistemas:
        SystemsStore(settings.systems_path).create(
            NewSystem(name=nombre, shortName=nombre, launchCmd="/bin/echo"),
        )
    return settings


@pytest.fixture()
def con_chromium(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(precalentar, "navegador_disponible", lambda: True)


def _con_fake(
    settings: Settings, falla: bool = False
) -> tuple[PrecalentamientoMobyGames, list[_Cliente]]:
    creados: list[_Cliente] = []

    def fabrica(cancel: threading.Event) -> ScrapingClient:
        cliente = _Cliente(cancel, falla)
        creados.append(cliente)
        return cast("ScrapingClient", cliente)

    return PrecalentamientoMobyGames(settings, fabrica), creados


def test_baja_la_pagina_de_busqueda_y_deja_la_marca(tmp_path: Path, con_chromium: None) -> None:
    precal, creados = _con_fake(_settings(tmp_path, "msdos"))
    hilo = precal.iniciar()
    assert hilo is not None
    hilo.join(5)
    assert creados[0].pedidas == [URL]
    assert creados[0].cerrado  # el navegador se cierra al terminar
    assert precal.marca.exists()


def test_no_sale_a_la_red_sin_chromium(tmp_path: Path) -> None:
    precal, creados = _con_fake(_settings(tmp_path, "msdos"))
    assert precal.iniciar() is None  # conftest: navegador_disponible es False
    assert creados == []


def test_no_sale_a_la_red_si_ningun_sistema_tiene_mobygames(
    tmp_path: Path, con_chromium: None
) -> None:
    precal, creados = _con_fake(_settings(tmp_path, "arcade"))
    assert precal.iniciar() is None
    assert creados == []


def test_no_sale_a_la_red_sin_sistemas(tmp_path: Path, con_chromium: None) -> None:
    precal, creados = _con_fake(_settings(tmp_path))
    assert precal.iniciar() is None
    assert creados == []


def test_se_puede_apagar(tmp_path: Path, con_chromium: None) -> None:
    precal, creados = _con_fake(_settings(tmp_path, "msdos", scraping_warmup=False))
    assert precal.iniciar() is None
    assert creados == []


def test_no_se_repite_dentro_de_la_ventana_de_6_horas(
    tmp_path: Path, con_chromium: None
) -> None:
    settings = _settings(tmp_path, "msdos")
    precal, creados = _con_fake(settings)
    hilo = precal.iniciar()
    assert hilo is not None
    hilo.join(5)

    otra, otros = _con_fake(settings)
    assert otra.iniciar() is None  # el reinicio de --reload no vuelve a pegarle al sitio
    assert otros == []

    vieja = time.time() - VIGENCIA_S - 60
    os.utime(otra.marca, (vieja, vieja))
    hilo = otra.iniciar()
    assert hilo is not None
    hilo.join(5)
    assert len(otros) == 1


def test_un_fallo_queda_en_el_log_y_no_deja_marca(
    tmp_path: Path, con_chromium: None, caplog: pytest.LogCaptureFixture
) -> None:
    precal, creados = _con_fake(_settings(tmp_path, "msdos"), falla=True)
    hilo = precal.iniciar()
    assert hilo is not None
    hilo.join(5)
    assert not precal.marca.exists()
    assert "precalentamiento de MobyGames falló" in caplog.text
    assert creados[0].cerrado


def test_detener_cancela_el_cliente(tmp_path: Path, con_chromium: None) -> None:
    precal, creados = _con_fake(_settings(tmp_path, "msdos"))
    hilo = precal.iniciar()
    assert hilo is not None
    hilo.join(5)
    precal.detener()
    assert creados[0].cancel.is_set()


def test_la_app_lo_inicia_al_arrancar_y_lo_detiene_al_cerrar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from backend.main import create_app

    llamadas: list[str] = []
    monkeypatch.setattr(
        PrecalentamientoMobyGames, "iniciar", lambda self: llamadas.append("iniciar")
    )
    monkeypatch.setattr(
        PrecalentamientoMobyGames, "detener", lambda self: llamadas.append("detener")
    )
    app = create_app(_settings(tmp_path, "msdos"))
    with TestClient(app):
        assert llamadas == ["iniciar"]
    assert llamadas == ["iniciar", "detener"]
