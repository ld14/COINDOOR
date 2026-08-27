from __future__ import annotations

from pathlib import Path

from backend.api.errors import BadRequest, Conflict
from backend.api.schemas import CreateGame, GameOut, GamesPage, GameSummary, PatchGame
from backend.config import Settings
from backend.lib.domain.completeness import compute_game_status, missing_required
from backend.store.juegos import GamesStore, to_out
from backend.store.sistemas import SystemsStore


class GamesService:
    def __init__(self, settings: Settings) -> None:
        self.store = GamesStore(settings.games_dir)
        self.systems = SystemsStore(settings.systems_path)

    def list(self, q: str = "", system_id: str = "", status: str = "", page: int = 1, per_page: int = 50) -> GamesPage:  # noqa: E501
        systems = {system.id: system for system in self.systems.list()}
        games = self.store.list()
        if q:
            needle = q.lower()
            games = [game for game in games if needle in game.identity.title.lower()]
        if system_id:
            games = [game for game in games if game.systemId == system_id]
        if status:
            games = [
                game for game in games
                if compute_game_status(game.model_dump(mode="json")) == status
            ]
        total = len(games)
        start = max(page - 1, 0) * per_page
        page_items = games[start : start + per_page]
        return GamesPage(
            items=[
                GameSummary(
                    id=game.id,
                    title=game.identity.title,
                    year=game.identity.year,
                    systemName=systems[game.systemId].name if game.systemId in systems else game.systemId,  # noqa: E501
                    identitySource=game.identitySource,
                    status=compute_game_status(game.model_dump(mode="json")),
                    coverThumbUrl=game.coverThumbUrl,
                )
                for game in page_items
            ],
            page=page,
            perPage=per_page,
            total=total,
        )

    def get(self, game_id: str) -> GameOut:
        return to_out(self.store.get(game_id))

    def create(self, payload: CreateGame) -> GameOut:
        if payload.romSource == "path":
            _validar_rom_ref(payload.romRef)
        return to_out(self.store.create(payload))

    def patch(self, game_id: str, payload: PatchGame) -> GameOut:
        if payload.systemId is not None:
            self.systems.get(payload.systemId)
        if payload.romRef is not None:
            _validar_rom_ref(payload.romRef)
        return to_out(self.store.patch(game_id, payload))

    def mark_ready(self, game_id: str) -> GameOut:
        game = self.store.get(game_id)
        missing = missing_required(game.model_dump(mode="json"))
        if missing:
            raise Conflict("El juego está incompleto", detail={"missing": missing})
        if game.errors:
            raise Conflict("El juego tiene errores de formato", detail={"missing": []})
        return to_out(game)


def _validar_rom_ref(rom_ref: str) -> None:
    """Rechaza rutas que el export no va a poder leer.

    Sin esto la ficha se guarda con una ruta fantasma, el juego figura ``ready``
    (completitud no mira el ROM) y el error recien aparece en Exportar como
    "falta el archivo", lejos de donde se tipeo la ruta.

    Una carpeta es valida: MS-DOS y similares se entregan como archivos sueltos
    y el staging la comprime (ver ``_copy_rom``).
    """
    ruta = rom_ref.strip()
    if not ruta:
        raise BadRequest("Indica la ruta del archivo o carpeta del juego.")
    path = Path(ruta)
    if not path.is_absolute():
        raise BadRequest(
            f"La ruta del juego debe ser absoluta, no '{ruta}'. "
            f"Ejemplos: /roms/arcade/sf2.zip o /roms/msdos/dino (carpeta)."
        )
    if not path.exists():
        raise BadRequest(
            f"No existe nada en '{ruta}'. Revisa la ruta: si el juego son archivos "
            f"sueltos, apunta a la carpeta que los contiene."
        )
