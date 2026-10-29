from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pytest

from backend.lib.providers.base import Limite
from backend.lib.providers.politica import (
    Politica,
    ProviderHttpError,
    ProviderNotFound,
    ProviderRejected,
)
from backend.lib.providers.scraping import ScrapingClient, SesionNavegador
from backend.store.cuotas import QuotasStore


class Pagina:
    def __init__(
        self,
        status: int,
        cuerpo: str = "<html></html>",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.body = cuerpo.encode()
        self.headers = headers or {}


DESAFIO = Pagina(403, "<title>Just a moment...</title>")


def _cliente(
    tmp_path: Path,
    http: list[Pagina],
    navegador: list[Pagina] | None = None,
    *,
    limite: Limite | None = None,
    cancel: threading.Event | None = None,
) -> tuple[ScrapingClient, dict[str, int]]:
    visto = {"http": 0, "navegador": 0}

    def hacer(nombre: str, respuestas: list[Pagina]) -> Any:
        def fetch(_url: str, _headers: dict[str, str] | None, _timeout: float) -> Pagina:
            visto[nombre] += 1
            return respuestas.pop(0)

        return fetch

    cliente = ScrapingClient(
        f"test-{tmp_path.name}",
        limite or Limite(),
        QuotasStore(tmp_path / "cuotas.json"),
        timeout=5,
        cancel_event=cancel,
        fetch_http=hacer("http", http),
        fetch_navegador=hacer("navegador", navegador or []),
    )
    return cliente, visto


@pytest.fixture(autouse=True)
def sin_esperas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Politica, "esperar_backoff", lambda *_a, **_k: None)


def test_con_http_que_responde_no_abre_el_navegador(tmp_path: Path) -> None:
    cliente, visto = _cliente(tmp_path, [Pagina(200)])
    with cliente:
        assert cliente.get_page("https://www.mobygames.com/x").status == 200
    assert visto == {"http": 1, "navegador": 0}


def test_ante_cloudflare_escala_al_navegador_y_recuerda_el_modo(tmp_path: Path) -> None:
    cliente, visto = _cliente(tmp_path, [DESAFIO], [Pagina(200), Pagina(200)])
    with cliente:
        cliente.get_page("https://www.mobygames.com/a")
        cliente.get_page("https://www.mobygames.com/b")
    assert visto == {"http": 1, "navegador": 2}


def test_si_el_navegador_tambien_es_rechazado_levanta_rejected(tmp_path: Path) -> None:
    cliente, _ = _cliente(tmp_path, [DESAFIO], [DESAFIO])
    with cliente, pytest.raises(ProviderRejected):
        cliente.get_page("https://www.mobygames.com/a")


def test_un_404_es_sin_resultados(tmp_path: Path) -> None:
    cliente, _ = _cliente(tmp_path, [Pagina(404)])
    with cliente, pytest.raises(ProviderNotFound):
        cliente.get_page("https://www.mobygames.com/a")


def test_un_5xx_se_reintenta_y_luego_agota(tmp_path: Path) -> None:
    cliente, visto = _cliente(tmp_path, [Pagina(503, "caído"), Pagina(500), Pagina(502)])
    with cliente, pytest.raises(ProviderHttpError) as info:
        cliente.get_page("https://www.mobygames.com/a")
    assert info.value.retry_exhausted is True
    assert visto["http"] == 3


def test_un_5xx_pasajero_se_recupera(tmp_path: Path) -> None:
    cliente, _ = _cliente(tmp_path, [Pagina(502), Pagina(200)])
    with cliente:
        assert cliente.get_page("https://www.mobygames.com/a").status == 200


def test_la_cancelacion_corta_antes_de_pedir(tmp_path: Path) -> None:
    cancel = threading.Event()
    cancel.set()
    cliente, visto = _cliente(
        tmp_path, [Pagina(200)], limite=Limite(espera_min=30.0), cancel=cancel
    )
    with cliente, pytest.raises(ProviderHttpError, match="cancelado"):
        cliente.get_page("https://www.mobygames.com/a")
    assert visto["http"] == 0


def test_dos_pedidos_al_mismo_sitio_quedan_separados_por_el_ritmo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    esperas: list[float] = []
    reloj = {"t": 100.0}
    monkeypatch.setattr("backend.lib.providers.politica.monotonic", lambda: reloj["t"])
    original = threading.Event.wait

    def wait(self: threading.Event, timeout: float | None = None) -> bool:
        if timeout:
            esperas.append(timeout)
        return original(self, 0)

    monkeypatch.setattr(threading.Event, "wait", wait)
    cliente, _ = _cliente(tmp_path, [Pagina(200), Pagina(200)], limite=Limite(espera_min=3.0))
    with cliente:
        cliente.get_page("https://www.mobygames.com/a")
        cliente.get_page("https://www.mobygames.com/b")
    assert esperas and esperas[-1] == pytest.approx(3.0)


class _FakeStealthySession:
    abiertas = 0
    cerradas = 0
    opciones: dict[str, Any] = {}

    def __init__(self, **kwargs: Any) -> None:
        type(self).opciones = kwargs

    def start(self) -> None:
        type(self).abiertas += 1

    def fetch(self, _url: str, **_kwargs: Any) -> Pagina:
        return Pagina(200)

    def close(self) -> None:
        type(self).cerradas += 1


def test_el_navegador_es_una_sola_sesion_para_todas_las_paginas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scrapling.fetchers

    _FakeStealthySession.abiertas = _FakeStealthySession.cerradas = 0
    monkeypatch.setattr(scrapling.fetchers, "StealthySession", _FakeStealthySession)
    sesion = SesionNavegador()
    for _ in range(3):
        sesion.fetch("https://www.mobygames.com/x", None, 5)
    sesion.close()
    sesion.close()  # cerrar dos veces no falla
    assert _FakeStealthySession.abiertas == 1
    assert _FakeStealthySession.cerradas == 1


def test_el_cliente_cierra_la_sesion_al_salir(tmp_path: Path) -> None:
    cliente, _ = _cliente(tmp_path, [Pagina(200)])
    cerrada: list[bool] = []
    cliente._sesion.close = lambda: cerrada.append(True)  # type: ignore[method-assign]
    with cliente:
        cliente.get_page("https://www.mobygames.com/a")
    assert cerrada == [True]


@pytest.fixture()
def sesion_falsa(monkeypatch: pytest.MonkeyPatch) -> type[_FakeStealthySession]:
    import scrapling.fetchers

    _FakeStealthySession.abiertas = _FakeStealthySession.cerradas = 0
    _FakeStealthySession.opciones = {}
    monkeypatch.setattr(scrapling.fetchers, "StealthySession", _FakeStealthySession)
    return _FakeStealthySession


def test_no_espera_la_red_y_usa_el_perfil(
    tmp_path: Path, sesion_falsa: type[_FakeStealthySession]
) -> None:
    perfil = tmp_path / "navegador"
    sesion = SesionNavegador(perfil)
    sesion.fetch("https://www.mobygames.com/x", None, 60)
    sesion.close()
    # Una página de desafío nunca deja de pedir: con network_idle Scrapling esperaba el
    # timeout entero antes de resolverla.
    assert sesion_falsa.opciones["network_idle"] is False
    assert sesion_falsa.opciones["solve_cloudflare"] is True
    assert sesion_falsa.opciones["timeout"] == 60_000
    assert sesion_falsa.opciones["user_data_dir"] == str(perfil)
    assert perfil.is_dir()


def test_sin_perfil_no_pasa_user_data_dir(sesion_falsa: type[_FakeStealthySession]) -> None:
    sesion = SesionNavegador()
    sesion.fetch("https://www.mobygames.com/x", None, 60)
    sesion.close()
    assert "user_data_dir" not in sesion_falsa.opciones


def test_dos_sesiones_con_perfil_van_de_a_una(
    tmp_path: Path, sesion_falsa: type[_FakeStealthySession]
) -> None:
    perfil = tmp_path / "navegador"
    primera = SesionNavegador(perfil)
    primera.fetch("https://www.mobygames.com/a", None, 60)

    segunda = SesionNavegador(perfil)
    abierta = threading.Event()

    def usar_segunda() -> None:
        segunda.fetch("https://www.mobygames.com/b", None, 60)
        abierta.set()

    hilo = threading.Thread(target=usar_segunda)
    hilo.start()
    assert not abierta.wait(1.5)  # espera mientras la primera tiene el perfil
    primera.close()
    assert abierta.wait(5)
    hilo.join()
    segunda.close()
    assert sesion_falsa.abiertas == 2 and sesion_falsa.cerradas == 2


def test_la_espera_del_perfil_se_puede_cancelar(
    tmp_path: Path, sesion_falsa: type[_FakeStealthySession]
) -> None:
    perfil = tmp_path / "navegador"
    primera = SesionNavegador(perfil)
    primera.fetch("https://www.mobygames.com/a", None, 60)
    cancel = threading.Event()
    cancel.set()
    try:
        with pytest.raises(ProviderHttpError, match="cancelado"):
            SesionNavegador(perfil, cancel).fetch("https://www.mobygames.com/b", None, 60)
    finally:
        primera.close()
    # el perfil quedó libre: otra sesión lo toma sin esperar
    tercera = SesionNavegador(perfil)
    tercera.fetch("https://www.mobygames.com/c", None, 60)
    tercera.close()


def test_si_el_navegador_no_arranca_el_perfil_queda_libre(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scrapling.fetchers

    class _NoArranca(_FakeStealthySession):
        def start(self) -> None:
            raise RuntimeError("sin Chromium")

    monkeypatch.setattr(scrapling.fetchers, "StealthySession", _NoArranca)
    perfil = tmp_path / "navegador"
    with pytest.raises(RuntimeError):
        SesionNavegador(perfil).fetch("https://www.mobygames.com/a", None, 60)

    monkeypatch.setattr(scrapling.fetchers, "StealthySession", _FakeStealthySession)
    otra = SesionNavegador(perfil)
    otra.fetch("https://www.mobygames.com/b", None, 60)  # no se queda esperando
    otra.close()


def test_el_modo_navegador_se_recuerda_entre_clientes_del_mismo_proveedor(
    tmp_path: Path,
) -> None:
    primero, visto1 = _cliente(tmp_path, [DESAFIO], [Pagina(200)])
    with primero:
        primero.get_page("https://www.mobygames.com/a")
    segundo, visto2 = _cliente(tmp_path, [], [Pagina(200)])
    with segundo:
        segundo.get_page("https://www.mobygames.com/b")
    assert visto1 == {"http": 1, "navegador": 1}
    assert visto2 == {"http": 0, "navegador": 1}  # ya no prueba HTTP
