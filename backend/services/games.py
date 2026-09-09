from __future__ import annotations

import shutil
from pathlib import Path

from backend.api.errors import BadRequest, Conflict
from backend.api.schemas import (
    CreateGame,
    GameOut,
    GamesPage,
    GameSummary,
    PatchGame,
    StoredGame,
)
from backend.config import Settings
from backend.lib.domain.completeness import compute_game_status, missing_required
from backend.store.archivo import safe_id
from backend.store.juegos import GamesStore, to_out
from backend.store.sistemas import SystemsStore


class GamesService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
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
        game = self.store.create(payload, dir_name=self._dir_name(payload))
        return to_out(self._adoptar_rom_suelta(game))

    def _relativa_al_sistema(self, payload: CreateGame) -> tuple[Path, ...] | None:
        """Tramos del `romRef` dentro de `juegos/<sistema>/`, o None si apunta afuera."""
        if payload.romSource != "path" or not payload.romRef:
            return None
        system_dir = self.settings.games_dir / safe_id(payload.systemId)
        try:
            relativa = Path(payload.romRef).resolve().relative_to(system_dir.resolve())
        except (OSError, ValueError):
            return None
        return relativa.parts or None

    def _dir_name(self, payload: CreateGame) -> str:
        """Carpeta donde va el `game.json` (ADR-0017).

        Si la ROM ya vive en una carpeta bajo `juegos/<sistema>/`, la ficha se guarda
        adentro de esa carpeta: renombrarla se lleva la ficha con ella, y el
        descubrimiento la deja de ofrecer sin depender de ningun nombre.
        """
        partes = self._relativa_al_sistema(payload)
        if partes is None:
            return ""
        if len(partes) == 1 and Path(payload.romRef).is_file():
            return ""  # ROM suelta: se adopta despues, en la carpeta derivada del id
        return partes[0]

    def _adoptar_rom_suelta(self, game: StoredGame) -> StoredGame:
        """Mueve una ROM suelta de la raiz del sistema a la carpeta de su ficha.

        Un archivo no puede contener el `game.json`, asi que la unica forma de que
        deje de estar suelto —y de dejar de ofrecerse como candidato— es que pase a
        vivir adentro de la carpeta del juego, igual que una ROM subida.
        """
        if game.dirName or game.romSource != "path":
            return game
        origen = Path(game.romRef)
        if not origen.is_file():
            return game
        system_dir = self.settings.games_dir / safe_id(game.systemId)
        try:
            if origen.resolve().parent != system_dir.resolve():
                return game
        except OSError:
            return game
        destino = self.store.dir_de(game) / origen.name
        if destino.exists():
            raise Conflict(f"Ya existe un archivo en '{destino}'")
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(origen), str(destino))
        return self.store.set_rom_ref(game.id, str(destino))

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
