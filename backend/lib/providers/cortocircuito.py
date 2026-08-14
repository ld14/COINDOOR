from __future__ import annotations

import threading

STRIKES_TO_OPEN = 2


class CircuitBreaker:
    """Cuenta reintentos agotados, no intentos sueltos. Un proveedor con
    STRIKES_TO_OPEN búsquedas que agotaron sus reintentos queda fuera del resto
    de la sesión del proceso, hasta un reset() explícito (botón Reintentar)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._strikes: dict[str, int] = {}

    def is_open(self, provider: str) -> bool:
        with self._lock:
            return self._strikes.get(provider, 0) >= STRIKES_TO_OPEN

    def strike(self, provider: str) -> None:
        with self._lock:
            self._strikes[provider] = self._strikes.get(provider, 0) + 1

    def reset(self, provider: str) -> None:
        with self._lock:
            self._strikes.pop(provider, None)


breaker = CircuitBreaker()
