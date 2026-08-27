from __future__ import annotations

from fastapi import APIRouter, UploadFile
from pydantic import BaseModel

from backend.api.schemas import GameOut
from backend.config import get_settings
from backend.services.manual_search import ManualResult, search_manuals
from backend.services.manuals import ManualsService

router = APIRouter(prefix="/api/games/{game_id}/manuals", tags=["manuals"])


def _service() -> ManualsService:
    return ManualsService(get_settings())


@router.post("")
def upload_manual(game_id: str, file: UploadFile) -> GameOut:
    data = file.file.read()
    return _service().upload(game_id, file.filename or "manual.pdf", data)


@router.post("/from-url")
class ManualFromUrl(BaseModel):
    url: str


def import_manual_from_url(game_id: str, payload: ManualFromUrl) -> GameOut:
    return _service().import_url(game_id, payload.url)


@router.delete("/{manual_id}")
def delete_manual(game_id: str, manual_id: str) -> GameOut:
    return _service().delete(game_id, manual_id)


@router.get("/search")
def search_game_manuals(game_id: str) -> list[dict[str, str]]:
    settings = get_settings()
    from backend.store.juegos import GamesStore

    game = GamesStore(settings.games_dir).get(game_id)
    results: list[ManualResult] = search_manuals(
        game.identity.title,
        game.systemId,
        settings,
    )
    return [{"title": r.title, "url": r.url, "source": r.source} for r in results]
