from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Any

import httpx

from backend.lib.providers.base import Limite
from backend.lib.providers.politica import (
    INTENTOS,
    Politica,
    ProviderHttpError,
    ProviderNotFound,
    ProviderQuotaExhausted,
    ProviderRejected,
)
from backend.store.cuotas import QuotasStore

__all__ = [
    "ProviderHttpClient",
    "ProviderHttpError",
    "ProviderNotFound",
    "ProviderQuotaExhausted",
    "ProviderRejected",
    "ProviderResponse",
]


@dataclass(frozen=True)
class ProviderResponse:
    url: str
    status_code: int
    json: Any


class ProviderHttpClient:
    def __init__(
        self,
        provider: str,
        limite: Limite,
        quotas: QuotasStore,
        *,
        timeout: float,
        cancel_event: threading.Event | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.provider = provider
        self.limite = limite
        self.quotas = quotas
        self.timeout = timeout
        self.cancel_event = cancel_event or threading.Event()
        self._politica = Politica(provider, limite, quotas, self.cancel_event)
        self._client = client

    def __enter__(self) -> ProviderHttpClient:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": "COINDOOR/0.1 (+local research; contact: user-run app)"},
            )
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        if self._client is not None:
            self._client.close()

    def get_json(self, url: str, *, params: dict[str, str] | None = None) -> ProviderResponse:
        return _como_json(self._request(lambda: self._client_or_raise().get(url, params=params)))

    def post_json(
        self,
        url: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> ProviderResponse:
        return _como_json(
            self._request(lambda: self._client_or_raise().post(url, json=json, headers=headers)),
        )

    def get_text(self, url: str) -> str:
        """El cuerpo como texto: las páginas de un sitio que responde a HTTP común."""
        return self._request(lambda: self._client_or_raise().get(url)).text

    def get_bytes(self, url: str) -> bytes:
        """El cuerpo tal cual llega, para un archivo comprimido (un ``sitemap.xml.gz``)."""
        return self._request(lambda: self._client_or_raise().get(url)).content

    def _request(self, send: Callable[[], httpx.Response]) -> httpx.Response:
        self._politica.reservar()
        last_error: ProviderHttpError | None = None
        for attempt in range(INTENTOS):
            self._politica.esperar_ritmo()
            try:
                response = send()
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
                last_error = ProviderHttpError(str(exc))
                self._politica.esperar_backoff(attempt, None)
                continue
            if response.status_code in {401, 403}:
                raise ProviderRejected(
                    "sitio rechazó la solicitud",
                    status_code=response.status_code,
                )
            if response.status_code == 404:
                # El detalle importa: un 404 puede ser "ese romset no existe" o
                # "ese modelo ya no está disponible", y sin el mensaje del
                # proveedor los dos se leen como "sin resultados".
                raise ProviderNotFound(
                    f"sin resultados{_detalle_error(response)}",
                    status_code=404,
                )
            if response.status_code == 429:
                self._politica.marcar_agotada()
                last_error = ProviderQuotaExhausted("sin cuota", status_code=429)
                self._politica.esperar_backoff(attempt, response.headers.get("Retry-After"))
                continue
            if 500 <= response.status_code < 600:
                last_error = ProviderHttpError("fallo pasajero", status_code=response.status_code)
                self._politica.esperar_backoff(attempt, response.headers.get("Retry-After"))
                continue
            if 400 <= response.status_code < 500:
                # Un 4xx que llegó hasta acá es un pedido mal formado (modelo
                # inexistente, combinación de parámetros no soportada): no se cura
                # reintentando, y sin esta rama saldría como httpx.HTTPStatusError
                # —que no es ProviderHttpError— y el orquestador lo registraría como
                # "excepción inesperada", sin decir qué rechazó el proveedor.
                raise ProviderRejected(
                    f"solicitud rechazada {response.status_code}{_detalle_error(response)}",
                    status_code=response.status_code,
                    retry_exhausted=True,
                )
            response.raise_for_status()
            return response
        if last_error is None:
            raise ProviderHttpError("fallo de proveedor", retry_exhausted=True)
        last_error.retry_exhausted = True
        raise last_error

    def _client_or_raise(self) -> httpx.Client:
        if self._client is None:
            raise RuntimeError("ProviderHttpClient must be used as a context manager")
        return self._client


def _como_json(response: httpx.Response) -> ProviderResponse:
    return ProviderResponse(str(response.url), response.status_code, response.json())


def _detalle_error(response: httpx.Response) -> str:
    """El mensaje que el proveedor puso en el body, si lo puso y si es JSON."""
    try:
        cuerpo = response.json()
    except ValueError:
        return ""
    if isinstance(cuerpo, dict):
        error = cuerpo.get("error")
        if isinstance(error, dict):
            mensaje = error.get("message")
        else:
            mensaje = error if isinstance(error, str) else cuerpo.get("message")
        if isinstance(mensaje, str) and mensaje.strip():
            return f": {' '.join(mensaje.split())}"
    return ""
