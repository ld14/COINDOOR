from __future__ import annotations

from backend.api.errors import BadRequest
from backend.api.schemas import NewSystem, System
from backend.config import Settings
from backend.lib.domain.validation import ABSOLUTE_PATH_MESSAGE, validate_absolute_path
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore


class SystemsService:
    def __init__(self, settings: Settings) -> None:
        self.store = SystemsStore(settings.systems_path)
        self.games = GamesStore(settings.games_dir)

    def list(self) -> list[System]:
        # El contador se calcula al leer; nunca se persiste (queda en 0 en disco).
        conteo: dict[str, int] = {}
        for game in self.games.list():
            conteo[game.systemId] = conteo.get(game.systemId, 0) + 1
        return [s.model_copy(update={"gameCount": conteo.get(s.id, 0)}) for s in self.store.list()]

    def create(self, payload: NewSystem) -> System:
        try:
            validate_absolute_path(payload.launchCmd)
        except ValueError as exc:
            raise BadRequest(ABSOLUTE_PATH_MESSAGE) from exc
        created = self.store.create(payload)
        return next((s for s in self.list() if s.id == created.id), created)
