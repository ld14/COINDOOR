"""Precalentamiento de MobyGames al arrancar COINDOOR (ADR-0025).

MobyGames está detrás de Cloudflare y la primera consulta paga el desafío (minutos). Al
arrancar, un hilo baja una página de búsqueda con el mismo cliente y el mismo perfil de
navegador que usan las consultas: la cookie que deja el desafío queda en el perfil y la
consulta que pida el usuario no lo vuelve a pagar. Si el usuario pide algo mientras tanto,
espera el perfil y reusa la cookie.

Es la segunda excepción a "todo lo que sale a la red es a pedido del usuario", y está
acotada: una página, un hilo, solo con Chromium y un sistema con equivalencia en MobyGames,
no más de una vez cada 6 horas, sin demorar ni romper el arranque, y desactivable.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from backend.config import Settings
from backend.lib.domain.plataformas import nombre_en
from backend.lib.providers.base import Limite
from backend.lib.providers.politica import ProviderHttpError
from backend.lib.providers.scraping import ScrapingClient, navegador_disponible
from backend.store.cuotas import QuotasStore
from backend.store.sistemas import SystemsStore

log = logging.getLogger(__name__)

URL = "https://www.mobygames.com/search/?q=dos&type=game"
# El modo desarrollo (`--reload`) reinicia el proceso en cada cambio de código: sin esta
# ventana, cada guardado le pegaría a MobyGames.
VIGENCIA_S = 6 * 3600
_MARCA = ".precalentado"

FabricaCliente = Callable[[threading.Event], ScrapingClient]


class PrecalentamientoMobyGames:
    def __init__(self, settings: Settings, fabrica: FabricaCliente | None = None) -> None:
        self.settings = settings
        self._cancel = threading.Event()
        self._fabrica = fabrica or self._cliente
        self.hilo: threading.Thread | None = None

    def iniciar(self) -> threading.Thread | None:
        """Arranca el hilo y vuelve enseguida; ``None`` si no corresponde salir a la red."""
        motivo = self._motivo_para_no_correr()
        if motivo:
            log.info("Precalentamiento de MobyGames omitido: %s", motivo)
            return None
        self.hilo = threading.Thread(
            target=self._correr, name="precalentar-mobygames", daemon=True
        )
        self.hilo.start()
        return self.hilo

    def detener(self) -> None:
        """Al cerrar la aplicación: corta las esperas y cierra el navegador al salir."""
        self._cancel.set()

    @property
    def marca(self) -> Path:
        return self.settings.browser_profile_dir / _MARCA

    def _motivo_para_no_correr(self) -> str:
        if not self.settings.scraping_warmup:
            return "desactivado (COINDOOR_SCRAPING_WARMUP)"
        if not navegador_disponible():
            return "sin Chromium"
        if not self._hay_sistema_con_mobygames():
            return "ningún sistema tiene equivalencia en MobyGames"
        if self._reciente():
            return "hubo uno hace menos de 6 horas"
        return ""

    def _hay_sistema_con_mobygames(self) -> bool:
        try:
            sistemas = SystemsStore(self.settings.systems_path).list()
        except Exception:
            log.warning("No se pudieron leer los sistemas", exc_info=True)
            return False
        return any(nombre_en(sistema.name, "mobygames") for sistema in sistemas)

    def _reciente(self) -> bool:
        try:
            return time.time() - self.marca.stat().st_mtime < VIGENCIA_S
        except OSError:
            return False

    def _cliente(self, cancel: threading.Event) -> ScrapingClient:
        return ScrapingClient(
            "mobygames",
            Limite(espera_min=self.settings.scraping_pace),
            QuotasStore(self.settings.quotas_path),
            timeout=self.settings.scraping_timeout,
            cancel_event=cancel,
            perfil=self.settings.browser_profile_dir,
        )

    def _correr(self) -> None:
        inicio = time.monotonic()
        try:
            with self._fabrica(self._cancel) as client:
                client.get_page(URL)
        except ProviderHttpError as exc:
            log.warning("El precalentamiento de MobyGames falló: %s", exc)
            return
        except Exception:
            log.warning("El precalentamiento de MobyGames falló", exc_info=True)
            return
        self.marca.parent.mkdir(parents=True, exist_ok=True)
        self.marca.touch()
        log.info("MobyGames precalentado en %.0f s", time.monotonic() - inicio)
