from __future__ import annotations

from typing import Any

import pytest

from backend.bundle.gamejson import build_gamejson
from backend.bundle.identidad import set_exportado
from backend.bundle.manifest import build_manifest


def _game(id_: str, rom_ref: str, source: str = "mame") -> dict[str, Any]:
    return {
        "id": id_,
        "identitySource": source,
        "romRef": rom_ref,
        "identity": {"title": id_, "players": "2", "format": "Arcade"},
    }


@pytest.mark.parametrize(
    ("slug", "rom_ref", "esperado"),
    [
        ("street-fighter-alpha-2", "/roms/sfa2.zip", "sfa2"),
        ("mortal-kombat-2", "D:\\roms\\MK2.zip", "mk2"),
        ("the-simpsons", "/roms/simpsons.zip", "simpsons"),
        ("pacman", "/roms/pacman.zip", "pacman"),
        ("shufshot", "/roms/shufshot", "shufshot"),
    ],
)
def test_mame_con_romref_usa_el_romset(slug: str, rom_ref: str, esperado: str) -> None:
    assert set_exportado(_game(slug, rom_ref)) == esperado


def test_sin_romref_cae_al_slug() -> None:
    assert set_exportado(_game("the-simpsons", "")) == "the-simpsons"


@pytest.mark.parametrize("source", ["manual", "screenscraper"])
def test_identidad_no_mame_cae_al_slug(source: str) -> None:
    assert set_exportado(_game("the-simpsons", "/roms/simpsons.zip", source)) == "the-simpsons"


def test_carpeta_con_nombre_no_romset_cae_al_slug() -> None:
    assert set_exportado(_game("juego", "/roms/mi juego.v2")) == "juego"


def test_gamejson_y_manifest_coinciden() -> None:
    game = _game("street-fighter-alpha-2", "/roms/sfa2.zip")
    verificado = {"por": "attract doctor", "contrato": "1", "ok": True}
    manifest = build_manifest(game, "Arcade", [], None, None, verificado)
    assert build_gamejson(game, "arcade")["set"] == manifest["set"] == "sfa2"
