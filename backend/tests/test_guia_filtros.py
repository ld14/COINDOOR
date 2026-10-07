from __future__ import annotations

from typing import Any

import pytest

from backend.api.schemas import StoredGame
from backend.bundle.datajson import build_datajson
from backend.bundle.seleccion import compute_seleccion
from backend.config import Settings
from backend.lib.domain.guia import (
    es_placeholder,
    guia_checklist,
    nombre_interno_en,
    nombres_internos,
    problema_texto,
)
from backend.store.migracion import CURRENT_VERSION, migrate

TODO = {"objetivo", "primerosPasos", "reglasEsenciales", "modo"}


def _texto(valor: str, status: str = "manual") -> dict[str, str]:
    return {"status": status, "value": valor}


def _arkanoid(objetivo: str = "Romper todos los ladrillos.", **texts: Any) -> dict[str, Any]:
    return {
        "id": "arkanoidu",
        "dirName": "arkanoidu",
        "romRef": "/mnt/d/COINDOOR/games/juegos/mame/arkanoidu.zip",
        "identity": {"title": "Arkanoid", "players": "2"},
        "texts": {"objetivo": _texto(objetivo), **texts},
        "cabinet": {"controls": "dial", "nplayers": "2P alt"},
    }


# --- 1. Placeholder: estructuralmente imposible que llegue al paquete -----------------------


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("EJEMPLO: Mover la paleta", True),
        ("ejemplo: algo", True),
        ("  - Ejemplo : algo", True),
        ("Uno\nEJEMPLO: dos", True),
        ("1. EJEMPLO: tres", True),
        ("Un ejemplo de cómo se juega", False),
        ("Mover la paleta", False),
    ],
)
def test_es_placeholder(texto: str, esperado: bool) -> None:
    assert es_placeholder(texto) is esperado


@pytest.mark.parametrize("clave", ["objetivo", "primerosPasos", "reglasEsenciales"])
def test_un_placeholder_nunca_llega_al_bloque(clave: str) -> None:
    texts = {"primerosPasos": _texto("Paso real"), "reglasEsenciales": _texto("Regla real")}
    game = _arkanoid(**texts)
    game["texts"][clave] = _texto("EJEMPLO: texto sin reemplazar")
    guia = build_datajson(game, TODO).get("guia", {})
    assert "EJEMPLO" not in str(guia)
    if clave == "objetivo":
        assert guia == {}
    else:
        assert clave not in guia


def test_un_placeholder_en_una_sola_linea_excluye_el_campo_entero() -> None:
    game = _arkanoid(primerosPasos=_texto("Paso real\nEJEMPLO: otro paso"))
    assert "primerosPasos" not in build_datajson(game, TODO)["guia"]


def test_el_placeholder_tampoco_cuenta_en_la_revision_ni_en_el_checklist() -> None:
    game = _arkanoid(primerosPasos=_texto("EJEMPLO: x"))
    assert build_datajson(game, TODO)["guia"]["revision"] == "revisado"
    paso = {i["key"]: i for i in guia_checklist(game)}["primerosPasos"]
    assert paso["estado"] == "falta"
    assert "EJEMPLO" in paso["detalle"]


def test_la_seleccion_no_ofrece_un_texto_de_ejemplo(tmp_path: Any) -> None:
    game = _arkanoid(primerosPasos=_texto("EJEMPLO: x"))
    items = {i.key: i for i in compute_seleccion(Settings(data_dir=tmp_path / "d"), game)}
    assert items["primerosPasos"].disponible is False
    assert items["objetivo"].disponible is True


# --- 3. Objetivo con el nombre interno del juego ---------------------------------------------


def test_nombres_internos_descartan_el_que_coincide_con_el_titulo() -> None:
    assert nombres_internos(_arkanoid()) == ["arkanoidu"]
    xevious = {"id": "xevious", "romRef": "/r/xevious.zip", "identity": {"title": "Xevious"}}
    assert nombres_internos(xevious) == []


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("En arkanoidu el jugador destruye ladrillos.", "arkanoidu"),
        ("EN ARKANOIDU hay que ganar", "arkanoidu"),
        ("Se juega en Arkanoidu.", "arkanoidu"),
        ("En Arkanoid el jugador destruye ladrillos.", None),
        ("Arkanoidus es otra cosa", None),
    ],
)
def test_nombre_interno_en_el_texto(texto: str, esperado: str | None) -> None:
    assert nombre_interno_en(texto, _arkanoid()) == esperado


def test_el_caso_real_de_arkanoid_se_excluye_del_export() -> None:
    game = _arkanoid("En arkanoidu el jugador debe destruir todos los ladrillos.")
    assert "guia" not in build_datajson(game, TODO)
    assert "arkanoidu" in (problema_texto(game, "objetivo") or "")
    objetivo = {i["key"]: i for i in guia_checklist(game)}["objetivo"]
    assert objetivo["estado"] == "falta"
    assert "arkanoidu" in objetivo["detalle"]


def test_el_nombre_interno_solo_se_controla_en_el_objetivo() -> None:
    game = _arkanoid(primerosPasos=_texto("Jugar a arkanoidu"))
    assert build_datajson(game, TODO)["guia"]["primerosPasos"] == ["Jugar a arkanoidu"]


def test_un_romset_igual_al_titulo_no_es_sospechoso() -> None:
    game = {
        "id": "xevious",
        "romRef": "/r/xevious.zip",
        "identity": {"title": "Xevious"},
        "texts": {"objetivo": _texto("En Xevious hay que destruir a los Bacura.")},
    }
    assert build_datajson(game, TODO)["guia"]["objetivo"].startswith("En Xevious")


# --- 2. Migración: lo «revisado» por el proceso viejo baja a borrador -------------------------


def _ficha_v1() -> dict[str, Any]:
    return {
        "version": 1,
        "id": "arkanoidu",
        "systemId": "arcade",
        "romSource": "path",
        "romRef": "",
        "identity": {
            "title": "Arkanoid", "year": "", "developer": "", "publisher": "",
            "genre": "", "players": "2", "format": "",
        },
        "texts": {
            "sinopsis": _texto("Sinopsis a mano"),
            "objetivo": _texto("Texto marcado por el proceso viejo"),
            "primerosPasos": _texto("Paso", status="suggested"),
            "modo": _texto("versus"),
        },
    }


def test_la_migracion_baja_los_textos_de_la_guia_de_manual_a_sugerido() -> None:
    migrada = migrate(_ficha_v1())
    assert migrada["version"] == CURRENT_VERSION == 2
    assert migrada["texts"]["objetivo"]["status"] == "suggested"
    assert migrada["texts"]["modo"]["status"] == "suggested"
    assert migrada["texts"]["primerosPasos"]["status"] == "suggested"
    # La sinopsis no es de la guía: no se toca.
    assert migrada["texts"]["sinopsis"]["status"] == "manual"


def test_tras_migrar_la_guia_exportada_dice_borrador() -> None:
    antes = _ficha_v1()
    assert build_datajson(antes, {"objetivo"})["guia"]["revision"] == "revisado"
    despues = StoredGame.model_validate(migrate(_ficha_v1())).model_dump()
    assert build_datajson(despues, {"objetivo"})["guia"]["revision"] == "borrador"


def test_la_migracion_se_aplica_una_sola_vez() -> None:
    una = migrate(_ficha_v1())
    # Una persona vuelve a guardar el objetivo ya con las reglas nuevas: queda a mano.
    una["texts"]["objetivo"]["status"] = "manual"
    dos = migrate(una)
    assert dos["texts"]["objetivo"]["status"] == "manual"


def test_una_ficha_nueva_nace_en_la_version_actual() -> None:
    game = StoredGame.model_validate({
        "id": "x", "systemId": "arcade", "romSource": "path", "romRef": "",
        "identity": {
            "title": "X", "year": "", "developer": "", "publisher": "",
            "genre": "", "players": "", "format": "",
        },
    })
    assert game.version == CURRENT_VERSION
