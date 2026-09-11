from __future__ import annotations

from fastapi import APIRouter, UploadFile

from backend.api.schemas import GameOut, RomCandidate
from backend.config import get_settings
from backend.services.descubrimiento import DescubrimientoService
from backend.services.roms import RomService

router = APIRouter(prefix="/api/games", tags=["roms"])

# El descubrimiento no cuelga de un juego —justamente todavía no existe—, así que
# no puede vivir bajo el prefijo `/api/games` del router de arriba.
scan_router = APIRouter(prefix="/api/roms", tags=["roms"])


def _service() -> RomService:
    return RomService(get_settings())


@router.post("/{game_id}/rom")
def upload_rom(game_id: str, file: UploadFile) -> GameOut:
    data = file.file.read()
    return _service().upload(game_id, file.filename or "", data)


@scan_router.get("/candidates")
def list_rom_candidates(systemId: str = "") -> list[RomCandidate]:  # noqa: N803
    """Juegos instalados en `games/juegos/<sistema>/` que todavía no tienen ficha."""
    return DescubrimientoService(get_settings()).candidatos(systemId)
