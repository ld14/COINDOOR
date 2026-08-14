from __future__ import annotations

import random
import threading
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from types import TracebackType
from typing import Any

import httpx

from backend.lib.providers.base import Limite
from backend.store.cuotas import QuotasStore


class ProviderHttpError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retry_exhausted: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_exhausted = retry_exhausted


class ProviderRejected(ProviderHttpError):
    pass


class ProviderQuotaExhausted(ProviderHttpError):
    pass


class ProviderNotFound(ProviderHttpError):
    pass


@dataclass(frozen=True)
class ProviderResponse:
    url: str
    status_code: int
    json: Any


class ProviderHttpClient:
    _lock = threading.Lock()
    _last_call: dict[str, float] = {}

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
        return self._request_json(lambda: self._client_or_raise().get(url, params=params))

    def post_json(
        self,
        url: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> ProviderResponse:
        return self._request_json(
            lambda: self._client_or_raise().post(url, json=json, headers=headers),
        )

    def _request_json(self, send: Callable[[], httpx.Response]) -> ProviderResponse:
        if not self.quotas.reserve(self.provider, self.limite.por_dia):
            raise ProviderQuotaExhausted("sin cuota")
        last_error: ProviderHttpError | None = None
        for attempt in range(3):
            self._wait_rate_limit()
            try:
                response = send()
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
                last_error = ProviderHttpError(str(exc))
                self._wait_backoff(attempt, None)
                continue
            if response.status_code in {401, 403}:
                raise ProviderRejected(
                    "sitio rechazó la solicitud",
                    status_code=response.status_code,
                )
            if response.status_code == 404:
                raise ProviderNotFound("sin resultados", status_code=404)
            if response.status_code == 429:
                self.quotas.mark_exhausted(self.provider)
                last_error = ProviderQuotaExhausted("sin cuota", status_code=429)
                self._wait_backoff(attempt, response.headers.get("Retry-After"))
                continue
            if 500 <= response.status_code < 600:
                last_error = ProviderHttpError("fallo pasajero", status_code=response.status_code)
                self._wait_backoff(attempt, response.headers.get("Retry-After"))
                continue
            response.raise_for_status()
            return ProviderResponse(
                str(response.url),
                response.status_code,
                response.json(),
            )
        if last_error is None:
            raise ProviderHttpError("fallo de proveedor", retry_exhausted=True)
        last_error.retry_exhausted = True
        raise last_error

    def _client_or_raise(self) -> httpx.Client:
        if self._client is None:
            raise RuntimeError("ProviderHttpClient must be used as a context manager")
        return self._client

    def _wait_rate_limit(self) -> None:
        delay = self.limite.espera_min
        if self.limite.por_segundo:
            delay = max(delay, 1 / self.limite.por_segundo)
        if delay <= 0:
            return
        with self._lock:
            now = monotonic()
            wait_for = max(0.0, self._last_call.get(self.provider, 0.0) + delay - now)
            self._last_call[self.provider] = now + wait_for
        if self.cancel_event.wait(wait_for):
            raise ProviderHttpError("cancelado")

    def _wait_backoff(self, attempt: int, retry_after: str | None) -> None:
        if attempt >= 2:
            return
        wait_for = _retry_after_seconds(retry_after) if retry_after else None
        if wait_for is None:
            wait_for = (1, 4, 16)[attempt] + random.random()
        if self.cancel_event.wait(wait_for):
            raise ProviderHttpError("cancelado")


def _retry_after_seconds(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return max(float(value), 0.0)
    except ValueError:
        return None
