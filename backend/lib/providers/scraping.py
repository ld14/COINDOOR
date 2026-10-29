"""Cliente de scraping: baja páginas con Scrapling y aplica la política de los proveedores.

Es el único módulo que importa ``scrapling`` (ADR-0024): el resto del backend recibe un
``Selector`` y no sabe de navegadores. Prueba primero HTTP y, si el sitio responde con un
bloqueo de Cloudflare, escala a un navegador y recuerda el modo para ese host mientras
corra el proceso.

El navegador es una sesión por cliente: se abre en el primer pedido que lo necesita y se
cierra al salir del ``with``, también cuando se cancela. La cancelación se atiende entre
pedidos y durante las esperas; un pedido en curso espera, como mucho, su ``timeout``.

Con un perfil persistente, la cookie de Cloudflare sobrevive a la consulta y las siguientes
no repiten el desafío mientras no venza.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from backend.lib.providers.base import Limite
from backend.lib.providers.politica import (
    INTENTOS,
    Politica,
    ProviderHttpError,
    ProviderNotFound,
    ProviderRejected,
)
from backend.store.cuotas import QuotasStore

if TYPE_CHECKING:
    from scrapling.engines.toolbelt.custom import Response as Selector
    from scrapling.parser import Selector as Pagina

# Pagina solo existe para los tipos: los parsers la importan bajo TYPE_CHECKING.
__all__ = [
    "Pagina",
    "ScrapingClient",
    "SesionNavegador",
    "navegador_disponible",
    "pagina_desde_html",
]

Fetch = Callable[[str, dict[str, str] | None, float], "Selector"]

_MODO_HTTP = "http"
_MODO_NAVEGADOR = "navegador"
_DESAFIO = ("just a moment", "cf-challenge", "challenge-platform")

# Dos Chromium no pueden abrir el mismo perfil a la vez: las sesiones con perfil van de a una.
_PERFIL_EN_USO = threading.Lock()


def _fetch_http(url: str, headers: dict[str, str] | None, timeout: float) -> Selector:
    from scrapling.fetchers import Fetcher

    return Fetcher.get(url, headers=headers or {}, timeout=timeout, stealthy_headers=True)


def navegador_disponible() -> bool:
    """Si hay un Chromium instalado para Scrapling (``scrapling install``).

    Sin él, un proveedor que necesita navegador no se construye y la app arranca igual.
    """
    import os
    import sys
    from pathlib import Path

    raiz = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if raiz and raiz != "0":
        candidatos = [Path(raiz)]
    elif sys.platform == "win32":
        candidatos = [Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"]
    elif sys.platform == "darwin":
        candidatos = [Path.home() / "Library" / "Caches" / "ms-playwright"]
    else:
        candidatos = [Path.home() / ".cache" / "ms-playwright"]
    return any(any(c.glob("chromium-*")) for c in candidatos if c.is_dir())


class SesionNavegador:
    """Un solo Chromium para todas las páginas de una consulta.

    Cloudflare se resuelve en la primera página y las cookies sirven para las demás: con un
    navegador por página cada una repetía el desafío. Se abre al primer pedido y se cierra
    con ``close()``; Playwright ata el navegador al hilo que lo creó, así que se usa desde el
    hilo que llama a ``get_page``.

    Sin ``network_idle``: una página de desafío de Cloudflare nunca deja de pedir, y Scrapling
    esperaba el ``timeout`` entero antes de empezar a resolverla (medido el 2026-10-29: con
    60 s de timeout, ~70 s de espera; con 300 s, ~330 s). El contenido de MobyGames viene en
    el HTML del servidor, así que no hace falta esperar a la red.
    """

    def __init__(
        self,
        perfil: Path | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self._sesion: Any = None
        self._perfil = perfil
        self._cancel_event = cancel_event or threading.Event()
        self._con_perfil = False

    def fetch(self, url: str, headers: dict[str, str] | None, timeout: float) -> Selector:
        if self._sesion is None:
            self._abrir(timeout)
        extra = {"extra_headers": headers} if headers else {}
        page: Selector = self._sesion.fetch(url, **extra)
        return page

    def _abrir(self, timeout: float) -> None:
        from scrapling.fetchers import StealthySession

        opciones: dict[str, Any] = {
            "headless": True,
            "solve_cloudflare": True,
            "network_idle": False,
            "timeout": int(timeout * 1000),
        }
        if self._perfil is not None:
            self._esperar_perfil()
            self._perfil.mkdir(parents=True, exist_ok=True)
            opciones["user_data_dir"] = str(self._perfil)
        try:
            sesion = StealthySession(**opciones)
            sesion.start()
        except BaseException:
            self._soltar_perfil()
            raise
        self._sesion = sesion

    def _esperar_perfil(self) -> None:
        """Toma el perfil; si otra consulta lo usa, espera sin dejar de atender la cancelación."""
        while not _PERFIL_EN_USO.acquire(timeout=1.0):
            if self._cancel_event.is_set():
                raise ProviderHttpError("cancelado")
        self._con_perfil = True

    def _soltar_perfil(self) -> None:
        if self._con_perfil:
            self._con_perfil = False
            _PERFIL_EN_USO.release()

    def close(self) -> None:
        sesion, self._sesion = self._sesion, None
        try:
            if sesion is not None:
                sesion.close()
        finally:
            self._soltar_perfil()


def pagina_desde_html(html: str, url: str = "") -> Pagina:
    """Una página a partir de HTML guardado: los parsers se prueban con esto, sin red."""
    from scrapling.parser import Selector as _Pagina

    return _Pagina(html, url=url)


def _es_desafio(page: Selector) -> bool:
    if page.status not in {403, 429, 503}:
        return False
    crudo = page.body
    texto = crudo.decode("utf-8", errors="ignore") if isinstance(crudo, bytes) else crudo
    cuerpo = texto.lower()
    return any(marca in cuerpo for marca in _DESAFIO)


class ScrapingClient:
    # El modo de cada sitio se recuerda mientras corre el proceso, por proveedor: un sitio que
    # ya pidió navegador no recibe en cada consulta un pedido HTTP condenado al 403.
    _modo: dict[tuple[str, str], str] = {}

    def __init__(
        self,
        provider: str,
        limite: Limite,
        quotas: QuotasStore,
        *,
        timeout: float,
        cancel_event: threading.Event | None = None,
        perfil: Path | None = None,
        fetch_http: Fetch | None = None,
        fetch_navegador: Fetch | None = None,
    ) -> None:
        self.provider = provider
        self.timeout = timeout
        self.cancel_event = cancel_event or threading.Event()
        self._politica = Politica(provider, limite, quotas, self.cancel_event)
        self._sesion = SesionNavegador(perfil, self.cancel_event)
        self._fetch = {
            _MODO_HTTP: fetch_http or _fetch_http,
            _MODO_NAVEGADOR: fetch_navegador or self._sesion.fetch,
        }

    def __enter__(self) -> ScrapingClient:
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self._sesion.close()

    def get_page(self, url: str, *, headers: dict[str, str] | None = None) -> Selector:
        sitio = (self.provider, urlsplit(url).netloc)
        self._politica.reservar()
        last_error: ProviderHttpError | None = None
        for attempt in range(INTENTOS):
            self._politica.esperar_ritmo()
            modo = self._modo.get(sitio, _MODO_HTTP)
            try:
                page = self._fetch[modo](url, headers, self.timeout)
            except ProviderHttpError:
                raise
            except Exception as exc:  # scrapling/playwright no tienen jerarquía común
                last_error = ProviderHttpError(f"fallo al bajar la página: {exc}")
                self._politica.esperar_backoff(attempt, None)
                continue
            status = int(page.status)
            if _es_desafio(page) or status in {401, 403}:
                if modo == _MODO_HTTP:
                    self._modo[sitio] = _MODO_NAVEGADOR
                    continue
                raise ProviderRejected("sitio rechazó la solicitud", status_code=status)
            if status == 404:
                raise ProviderNotFound("sin resultados", status_code=404)
            if status == 429:
                self._politica.marcar_agotada()
                last_error = ProviderHttpError("sin cuota", status_code=429)
                self._politica.esperar_backoff(attempt, page.headers.get("Retry-After"))
                continue
            if 500 <= status < 600:
                last_error = ProviderHttpError("fallo pasajero", status_code=status)
                self._politica.esperar_backoff(attempt, page.headers.get("Retry-After"))
                continue
            if 400 <= status < 500:
                raise ProviderRejected(
                    f"solicitud rechazada {status}", status_code=status, retry_exhausted=True
                )
            return page
        if last_error is None:
            last_error = ProviderHttpError("fallo de proveedor")
        last_error.retry_exhausted = True
        raise last_error

