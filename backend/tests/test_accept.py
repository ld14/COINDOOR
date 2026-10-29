from __future__ import annotations

import zipfile
from pathlib import Path

from backend.api.schemas import FieldProvenance
from backend.config import Settings
from backend.store.juegos import GamesStore
from backend.tests.test_api import _create_arcade_game, _export_sync, _make_exportable, client


def _store(tmp_path: Path) -> GamesStore:
    return GamesStore(Settings(data_dir=tmp_path / "data").games_dir)


def test_edicion_manual_escribe_source_manual(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    base = f"/api/games/{game_id}"
    assert api.put(f"{base}/fields/sinopsis", json={"value": "Hola"}).status_code == 200
    api.put(f"{base}/fields/review", json={"score": 80, "cats": {"sonido": 70}})
    api.put(f"{base}/fields/cheats", json={"groups": []})
    api.put(f"{base}/media/caratula", files={"file": ("c.jpg", b"c", "image/jpeg")})
    game = _store(tmp_path).get(game_id)
    assert game.texts["sinopsis"].source == "manual"
    assert game.review.source == "manual"
    assert game.cheats.source == "manual"
    assert game.images["caratula"].source == "manual"


def test_accept_conserva_source_y_pasa_a_manual(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    store = _store(tmp_path)
    prov = FieldProvenance(source="ArcadeDB")
    store.apply_text_suggestion(game_id, "sinopsis", "Texto", prov)
    store.apply_media_suggestion(game_id, "caratula", "/media/x.jpg", prov)
    store.apply_rich_suggestion(game_id, "review", {"score": 90, "cats": {}}, prov)
    store.apply_rich_suggestion(game_id, "cheats", {"groups": []}, prov)
    base = f"/api/games/{game_id}/fields"
    for key in ("sinopsis", "caratula", "review", "cheats"):
        assert api.post(f"{base}/{key}/accept").status_code == 200
    game = _store(tmp_path).get(game_id)
    assert game.texts["sinopsis"].status == "manual"
    assert game.texts["sinopsis"].source == "ArcadeDB"
    assert game.texts["sinopsis"].value == "Texto"
    assert game.images["caratula"].status == "manual"
    assert game.images["caratula"].source == "ArcadeDB"
    assert game.images["caratula"].url == "/media/x.jpg"
    assert game.review.status == "manual" and game.review.source == "ArcadeDB"
    assert game.review.score == 90
    assert game.cheats.status == "manual" and game.cheats.source == "ArcadeDB"


def test_accept_sobre_campo_no_sugerido_falla_sin_tocar(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    base = f"/api/games/{game_id}/fields"
    api.put(f"{base}/sinopsis", json={"value": "Mano"})
    before = _store(tmp_path).get(game_id).model_dump()
    assert api.post(f"{base}/sinopsis/accept").status_code == 409
    assert api.post(f"{base}/objetivo/accept").status_code == 409
    assert api.post(f"{base}/review/accept").status_code == 409
    assert api.post(f"{base}/noexiste/accept").status_code == 422
    assert _store(tmp_path).get(game_id).model_dump() == before


def test_export_no_incluye_source_de_campos(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    api.put(f"/api/games/{game_id}/fields/review", json={"score": 80, "cats": {"sonido": 70}})
    api.put(f"/api/games/{game_id}/fields/cheats", json={"groups": []})
    result = _export_sync(api, game_id)
    with zipfile.ZipFile(result["file"]) as bundle:
        blobs = {n: bundle.read(n) for n in bundle.namelist() if n.endswith(".json")}
    assert blobs
    for name, blob in blobs.items():
        assert b'"source"' not in blob, name


def test_resena_con_solo_nota_conserva_las_categorias(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    cats = {
        "adiccion": 85,
        "animacion": 75,
        "dificultad": 60,
        "graficos": 80,
        "originalidad": 90,
        "sonido": 70,
    }
    cargada = api.put(f"/api/games/{game_id}/fields/review", json={"score": 70, "cats": cats})
    assert cargada.status_code == 200
    store = _store(tmp_path)

    store.apply_rich_suggestion(
        game_id, "review", {"score": 82}, FieldProvenance(source="MobyGames")
    )

    game = _store(tmp_path).get(game_id)
    assert game.review.score == 82
    assert game.review.cats == cats
    assert game.review.status == "suggested"
    assert game.review.source == "MobyGames"


def test_resena_con_categorias_explicitas_las_reemplaza(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    cargada = api.put(
        f"/api/games/{game_id}/fields/review", json={"score": 70, "cats": {"sonido": 70}}
    )
    assert cargada.status_code == 200
    store = _store(tmp_path)

    store.apply_rich_suggestion(
        game_id, "review", {"score": 90, "cats": {"sonido": 10}}, FieldProvenance(source="IA")
    )

    assert _store(tmp_path).get(game_id).review.cats == {"sonido": 10}


def test_resena_con_solo_nota_sobre_ficha_sin_resena(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    store = _store(tmp_path)

    store.apply_rich_suggestion(
        game_id, "review", {"score": 82}, FieldProvenance(source="MobyGames")
    )

    game = _store(tmp_path).get(game_id)
    assert game.review.score == 82
    assert game.review.cats == {}
