from __future__ import annotations

from backend.config import Settings
from backend.lib.providers.base import Candidato, Consulta, Limite, ProviderResult, ProviderTrace
from backend.store.juegos import GamesStore

_SOURCE_LABELS = {
    "manual": "Manual",
    "mame": "MAME",
    "screenscraper": "ScreenScraper",
}


class IdentityActualProvider:
    nombre = "Identidad actual"
    tipo = "api"
    campos = frozenset({"title", "year", "developer", "publisher", "genre", "players", "format"})
    timeout = 1.0
    limite = Limite()

    def __init__(self, settings: Settings) -> None:
        self.games = GamesStore(settings.games_dir)

    def buscar(self, consulta: Consulta) -> ProviderResult:
        trace = ProviderTrace(self.nombre, self.tipo, "ok", datos_obtenidos=(consulta.key,))
        game = self.games.get(consulta.game_id)
        value = getattr(game.identity, consulta.key, "")
        if not value:
            return ProviderResult((), trace)
        source = _SOURCE_LABELS[game.identitySource]
        return ProviderResult(
            (
                Candidato(
                    f"identity-actual:{consulta.key}:{value}",
                    consulta.key,
                    "identity",
                    value,
                    source,
                    "aplicable",
                    value=value,
                    trace=trace,
                ),
            ),
            trace,
        )
