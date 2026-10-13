from __future__ import annotations

from typing import Any

import pytest

from backend.bundle.gamejson import build_gamejson
from backend.bundle.identidad import set_exportado
from backend.bundle.manifest import build_manifest


def _game(
    id_: str,
    rom_ref: str,
    source: str = "mame",
    system_id: str = "arcade",
) -> dict[str, Any]:
    return {
        "id": id_,
        "systemId": system_id,
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


@pytest.mark.parametrize("source", ["mame", "manual", "screenscraper"])
def test_el_set_no_depende_de_identity_source(source: str) -> None:
    assert set_exportado(_game("the-simpsons", "/roms/simpsons.zip", source)) == "simpsons"


@pytest.mark.parametrize("system_id", ["arcade", "mame", "Arcade", "MAME"])
def test_arcade_y_mame_son_el_mismo_sistema(system_id: str) -> None:
    game = _game("street-fighter-alpha-2", "/roms/sfa2.zip", system_id=system_id)
    assert set_exportado(game) == "sfa2"


def test_carpeta_con_nombre_no_romset_cae_al_slug() -> None:
    assert set_exportado(_game("juego", "/roms/mi juego.v2")) == "juego"


def test_set_estable_al_editar_un_campo_de_identidad_a_mano() -> None:
    game = _game("street-fighter-alpha-2", "/roms/sfa2.zip", source="mame")
    antes = set_exportado(game)
    # `apply_identity_suggestion` pisa identitySource con la fuente del ultimo campo editado.
    game["identitySource"] = "manual"
    game["identity"]["players"] = "1"
    assert set_exportado(game) == antes == "sfa2"


@pytest.mark.parametrize("system_id", ["MS-DOS", "msdos", "", "nes"])
def test_otros_sistemas_usan_el_slug(system_id: str) -> None:
    game = _game("mission-impossible", "/roms/Mission_Impossible_1991", system_id=system_id)
    assert set_exportado(game) == "mission-impossible"
    # Aunque el nombre de la carpeta sea un romset valido.
    game["romRef"] = "/roms/mission_impossible_1991"
    assert set_exportado(game) == "mission-impossible"


def test_gamejson_y_manifest_coinciden() -> None:
    game = _game("street-fighter-alpha-2", "/roms/sfa2.zip")
    verificado = {"por": "attract doctor", "contrato": "1", "ok": True}
    manifest = build_manifest(game, "Arcade", [], None, None, verificado)
    assert build_gamejson(game, "arcade")["set"] == manifest["set"] == "sfa2"
