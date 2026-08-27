from __future__ import annotations

from fastapi import APIRouter

from backend.api.schemas import CreateGame, GameOut, GamesPage, PatchGame, SuggestionJob
from backend.config import get_settings
from backend.lib.jobs.ejecutor import submit
from backend.services.arcadedb import ArcadeDbPrecargaService
from backend.services.games import GamesService

router = APIRouter(prefix="/api/games", tags=["games"])


def _service() -> GamesService:
    return GamesService(get_settings())


@router.get("")
def list_games(q: str = "", systemId: str = "", status: str = "", page: int = 1, perPage: int = 50) -> GamesPage:  # noqa: E501
    return _service().list(q=q, system_id=systemId, status=status, page=page, per_page=perPage)


@router.get("/{game_id}")
def get_game(game_id: str) -> GameOut:
    return _service().get(game_id)


@router.post("")
def create_game(payload: CreateGame) -> GameOut:
    return _service().create(payload)


@router.patch("/{game_id}")
def patch_game(game_id: str, payload: PatchGame) -> GameOut:
    return _service().patch(game_id, payload)


@router.post("/{game_id}/mark-ready")
def mark_ready(game_id: str) -> GameOut:
    return _service().mark_ready(game_id)


@router.post("/{game_id}/arcadedb")
def precarga_arcadedb(game_id: str, force: bool = False) -> SuggestionJob:
    """Lanza la precarga de datos de ArcadeDB como un job."""
    service = ArcadeDbPrecargaService(get_settings())
    job = submit(service.run(game_id, force=force))
    return SuggestionJob(jobId=job.job_id)
