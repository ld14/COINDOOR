from __future__ import annotations

from typing import Any

from backend.bundle.manifest import build_manifest


def _game(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "goldnaxe",
        "identitySource": "mame",
        "identity": {
            "title": "Golden Axe", "year": "1989", "developer": "Sega",
            "publisher": "Sega", "genre": "Beat em up", "players": "2", "format": "Arcade",
        },
    }
    base.update(overrides)
    return base


def _verificado(ok: bool = True) -> dict[str, Any]:
    return {"por": "attract doctor", "contrato": "1", "ok": ok}


def test_origen_mame_cuando_identitysource_es_mame() -> None:
    manifest = build_manifest(_game(identitySource="mame"), "Arcade", [], None, None, _verificado())
    assert manifest["identidad"]["origen"] == "mame"


def test_origen_declarada_cuando_identitysource_es_screenscraper() -> None:
    manifest = build_manifest(_game(identitySource="screenscraper"), "NES", [], None, None, _verificado())  # noqa: E501
    assert manifest["identidad"]["origen"] == "declarada"


def test_origen_declarada_cuando_identitysource_es_manual() -> None:
    manifest = build_manifest(_game(identitySource="manual"), "DOS", [], None, None, _verificado())
    assert manifest["identidad"]["origen"] == "declarada"


def test_campos_de_identidad_traducidos_al_contrato() -> None:
    manifest = build_manifest(_game(), "Arcade", [], None, None, _verificado())
    assert manifest["identidad"]["campos"] == {
        "title": "Golden Axe",
        "developer": "Sega",
        "publisher": "Sega",
        "genre": "Beat em up",
        "release": "1989",
        "players": 2,
        "x-formato": "Arcade",
    }


def test_players_no_entero_cae_a_1() -> None:
    game = _game(identity={
        "title": "Contra", "year": "1987", "developer": "Konami", "publisher": "Konami",
        "genre": "Run and gun", "players": "1-2", "format": "Cartucho",
    })
    manifest = build_manifest(game, "SNES", [], None, None, _verificado())
    assert manifest["identidad"]["campos"]["players"] == 1


def test_artefactos_vacio_sin_juego() -> None:
    manifest = build_manifest(_game(), "Arcade", [], None, None, _verificado())
    assert manifest["artefactos"] == []


def test_artefactos_con_juego_copiar() -> None:
    manifest = build_manifest(_game(), "Arcade", ["juego"], "juego/goldnaxe.zip", "copiar", _verificado())  # noqa: E501
    assert manifest["artefactos"] == [
        {"archivo": "juego/goldnaxe.zip", "destino": "goldnaxe.zip", "tratamiento": "copiar"},
    ]


def test_artefactos_con_juego_descomprimir() -> None:
    manifest = build_manifest(_game(), "DOS", ["juego"], "juego/dot.zip", "descomprimir", _verificado())  # noqa: E501
    assert manifest["artefactos"][0]["tratamiento"] == "descomprimir"


def test_incluye_ordenado() -> None:
    manifest = build_manifest(_game(), "Arcade", ["video", "cheats", "manual"], None, None, _verificado())  # noqa: E501
    assert manifest["incluye"] == ["cheats", "manual", "video"]


def test_verificado_se_embebe_tal_cual() -> None:
    manifest = build_manifest(_game(), "Arcade", [], None, None, _verificado(ok=False))
    assert manifest["verificado"] == {"por": "attract doctor", "contrato": "1", "ok": False}


def test_bundle_y_contrato_y_coleccion_y_set() -> None:
    manifest = build_manifest(_game(), "Arcade", [], None, None, _verificado())
    assert manifest["bundle"] == 1
    assert manifest["contrato"] == "1"
    assert manifest["coleccion"] == "Arcade"
    assert manifest["set"] == "goldnaxe"
    assert manifest["generado"].endswith("Z")
