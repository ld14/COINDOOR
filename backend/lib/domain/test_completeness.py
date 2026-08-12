from __future__ import annotations

from backend.lib.domain.completeness import compute_game_status, missing_required


def complete_game() -> dict[str, object]:
    return {
        "identity": {
            "title": "Golden Axe",
            "year": "1989",
            "developer": "Sega",
            "publisher": "Sega",
            "genre": "Beat 'em up",
            "players": "1-2",
            "format": "Arcade",
        },
        "errors": [],
        "images": {
            "caratula": {"status": "manual"},
            "marquesina": {"status": "empty"},
            "poster": {"status": "manual"},
            "logo": {"status": "empty"},
            "captura": {"status": "empty"},
        },
        "video": {"video": {"status": "empty"}},
        "texts": {"sinopsis": {"status": "manual", "value": "Texto"}},
        "accent": "manual",
    }


def test_complete_game_is_ready() -> None:
    game = complete_game()
    assert missing_required(game) == []
    assert compute_game_status(game) == "ready"


def test_missing_poster_is_incomplete() -> None:
    game = complete_game()
    images = game["images"]
    assert isinstance(images, dict)
    images["poster"] = {"status": "empty"}
    assert "Póster" in missing_required(game)
    assert compute_game_status(game) == "incomplete"


def test_errors_have_priority() -> None:
    game = complete_game()
    game["errors"] = [{"field": "Año", "message": "error"}]
    assert compute_game_status(game) == "error"
