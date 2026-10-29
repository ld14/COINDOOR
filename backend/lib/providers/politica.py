"""Política común de los clientes de proveedores: cuota, ritmo, backoff y cancelación.

La comparten ``ProviderHttpClient`` (APIs) y ``ScrapingClient`` (páginas): ningún
proveedor implementa la suya. El estado del ritmo es de clase, porque dos clientes del
mismo proveedor tienen que respetarse entre sí aunque sean instancias distintas.
"""

from __future__ import annotations

import random
import threading
from time import monotonic

from backend.lib.providers.base import Limite
from backend.store.cuotas import QuotasStore

# Espera entre reintentos, en segundos; un intento más se suma al azar hasta 1 s.
BACKOFF = (1, 4, 16)
INTENTOS = len(BACKOFF)


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


class Politica:
    _lock = threading.Lock()
    _last_call: dict[str, float] = {}

    def __init__(
        self,
        provider: str,
        limite: Limite,
        quotas: QuotasStore,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.provider = provider
        self.limite = limite
        self.quotas = quotas
        self.cancel_event = cancel_event or threading.Event()

    def reservar(self) -> None:
        if not self.quotas.reserve(self.provider, self.limite.por_dia):
            raise ProviderQuotaExhausted("sin cuota")

    def marcar_agotada(self) -> None:
        self.quotas.mark_exhausted(self.provider)

    def esperar_ritmo(self) -> None:
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

    def esperar_backoff(self, attempt: int, retry_after: str | None) -> None:
        if attempt >= INTENTOS - 1:
            return
        wait_for = retry_after_seconds(retry_after) if retry_after else None
        if wait_for is None:
            wait_for = BACKOFF[attempt] + random.random()
        if self.cancel_event.wait(wait_for):
            raise ProviderHttpError("cancelado")


def retry_after_seconds(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return max(float(value), 0.0)
    except ValueError:
        return None
