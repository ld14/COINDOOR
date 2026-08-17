from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.api.schemas import GameOut, MagazineAppearance
from backend.config import get_settings
from backend.services.magazine_search import (
    MagazineSearchResult,
    build_magazine_links,
    search_magazines,
)
from backend.store.juegos import GamesStore, to_out

router = APIRouter(prefix="/api/games/{game_id}/magazines", tags=["magazines"])


@router.get("/search")
def search_game_magazines(game_id: str) -> list[dict[str, Any]]:
    settings = get_settings()
    game = GamesStore(settings.games_dir).get(game_id)
    results: list[MagazineSearchResult] = search_magazines(
        game.identity.title,
        game.systemId,
        settings,
    )
    output: list[dict[str, Any]] = []
    for r in results:
        item: dict[str, Any] = {
            "title": r.title,
            "url": r.url,
            "source": r.source,
            "magazine": r.magazine,
        }
        if r.appearance:
            app = r.appearance.model_dump(mode="json")
            app.pop("volume", None)
            item["appearance"] = app
            item["links"] = build_magazine_links(r.appearance)
        else:
            item["appearance"] = None
            item["links"] = {}
        output.append(item)
    return output


@router.post("/appearances")
def add_appearance(game_id: str, appearance: MagazineAppearance) -> GameOut:
    settings = get_settings()
    store = GamesStore(settings.games_dir)
    game = store.add_magazine_appearance(game_id, appearance)
    return to_out(game)


@router.delete("/appearances/{appearance_id}")
def remove_appearance(game_id: str, appearance_id: str) -> GameOut:
    settings = get_settings()
    store = GamesStore(settings.games_dir)
    game = store.remove_magazine_appearance(game_id, appearance_id)
    return to_out(game)
