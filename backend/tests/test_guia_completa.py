from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from backend.bundle.datajson import build_datajson
from backend.bundle.seleccion import compute_seleccion
from backend.config import Settings
from backend.lib.domain.guia import lineas, modo_desde_ficha, perifericos_desde
from backend.lib.providers.base import Consulta, Limite
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.registro import providers_for
from backend.store.cuotas import QuotasStore

TODO = {"objetivo", "primerosPasos", "reglasEsenciales", "modo"}


def _texto(valor: str, status: str = "manual") -> dict[str, str]:
    return {"status": status, "value": valor}


def _arkanoid(**texts: Any) -> dict[str, Any]:
    """Arkanoid (arkanoidu) como lo publica ArcadeDB: dial, 2P por turnos, sin botones."""
    return {
        "identity": {"title": "Arkanoid", "players": "2"},
        "texts": {"objetivo": _texto("Romper los ladrillos."), **texts},
        "cabinet": {"controls": "dial", "nplayers": "2P alt", "buttons": 1, "button_list": []},
    }


@pytest.mark.parametrize(
    ("controles", "esperado"),
    [
        ("dial", ["dial"]),
        ("[es] joystick (8-way)", ["joy"]),
        ("trackball", ["trackball"]),
        ("joystick (4-way), trackball", ["trackball", "joy"]),
        ("spinner", ["dial"]),
        ("palanca rara", []),
        ("", []),
    ],
)
def test_perifericos_se_derivan_del_control_de_arcadedb(
    controles: str, esperado: list[str]
) -> None:
    assert perifericos_desde(controles) == esperado


def test_lineas_quita_vinetas_numeracion_y_vacios() -> None:
    texto = "- Uno\n\n  2. Dos\n• Tres\n3) Cuatro  \n"
    assert lineas(texto) == ["Uno", "Dos", "Tres", "Cuatro"]


@pytest.mark.parametrize(
    ("jugadores", "nplayers", "modo"),
    [("1", "", "individual"), ("2", "2P alt", "individual"), ("2", "2P sim", ""), ("2", "", "")],
)
def test_modo_derivado_solo_cuando_es_un_hecho(jugadores: str, nplayers: str, modo: str) -> None:
    assert modo_desde_ficha(jugadores, nplayers) == modo


def test_arkanoid_exporta_perifericos_y_modo_derivados() -> None:
    guia = build_datajson(_arkanoid(), {"objetivo"})["guia"]
    assert guia["perifericos"] == ["dial"]
    assert guia["multijugador"] == {"jugadores": 2, "modo": "individual"}
    # ArcadeDB no publica acciones para este juego: no se inventan.
    assert "acciones" not in guia


def test_listas_viajan_solo_si_se_incluyen() -> None:
    game = _arkanoid(
        primerosPasos=_texto("- Mover la paleta\n- Romper ladrillos"),
        reglasEsenciales=_texto("Perder la pelota cuesta una vida"),
    )
    sin = build_datajson(game, {"objetivo"})["guia"]
    assert "primerosPasos" not in sin
    assert "reglasEsenciales" not in sin
    con = build_datajson(game, TODO)["guia"]
    assert con["primerosPasos"] == ["Mover la paleta", "Romper ladrillos"]
    assert con["reglasEsenciales"] == ["Perder la pelota cuesta una vida"]


def test_modo_elegido_gana_sobre_el_derivado_y_debe_estar_en_vocabulario() -> None:
    game = _arkanoid(modo=_texto("Cooperativo"))
    assert build_datajson(game, TODO)["guia"]["multijugador"]["modo"] == "cooperativo"
    assert build_datajson(game, {"objetivo"})["guia"]["multijugador"]["modo"] == "individual"
    raro = _arkanoid(modo=_texto("equipos"))
    assert build_datajson(raro, TODO)["guia"]["multijugador"]["modo"] == "individual"


def test_modo_simultaneo_sin_eleccion_se_omite() -> None:
    game = _arkanoid()
    game["cabinet"]["nplayers"] = "2P sim"
    assert "modo" not in build_datajson(game, {"objetivo"})["guia"]["multijugador"]


def test_revision_exige_que_todo_lo_que_viaja_sea_manual() -> None:
    game = _arkanoid(primerosPasos=_texto("Mover la paleta", status="suggested"))
    assert build_datajson(game, {"objetivo"})["guia"]["revision"] == "revisado"
    assert build_datajson(game, TODO)["guia"]["revision"] == "borrador"
    game["texts"]["primerosPasos"] = _texto("Mover la paleta")
    assert build_datajson(game, TODO)["guia"]["revision"] == "revisado"


def test_ficha_sin_gabinete_ni_textos_nuevos_exporta_igual() -> None:
    game = {"identity": {"players": "2"}, "texts": {"objetivo": _texto("Ganar.")}}
    assert build_datajson(game, TODO)["guia"] == {
        "objetivo": "Ganar.",
        "multijugador": {"jugadores": 2},
        "revision": "revisado",
    }


def test_seleccion_ofrece_los_textos_de_la_guia_como_opcionales(tmp_path: Path) -> None:
    items = {i.key: i for i in compute_seleccion(Settings(data_dir=tmp_path / "d"), _arkanoid())}
    for clave in ("primerosPasos", "reglasEsenciales", "modo"):
        assert items[clave].required is False
        assert items[clave].disponible is False


def _http(
    tmp_path: Path, respuesta: str, visto: dict[str, str] | None = None
) -> ProviderHttpClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if visto is not None:
            visto["p"] = json.loads(request.content)["messages"][0]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": respuesta}}]})

    return ProviderHttpClient(
        "ia:t",
        Limite(),
        QuotasStore(tmp_path / "c.json"),
        timeout=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _generar(tmp_path: Path, clave: str, respuesta: str) -> Any:
    config = AiModelConfig("https://api.test/v1", "k", "t")
    generador = IaGenerador(config, _http(tmp_path, respuesta))
    return generador.buscar(Consulta("arkanoidu", clave, "Arkanoid", "Arcade", "1986"))


def test_ia_primeros_pasos_devuelve_lineas_limpias(tmp_path: Path) -> None:
    resultado = _generar(tmp_path, "primerosPasos", "1. Mover la paleta\n- Romper ladrillos\n")
    assert resultado.candidatos[0].value == "Mover la paleta\nRomper ladrillos"
    assert resultado.candidatos[0].generado_por_ia is True


@pytest.mark.parametrize(
    "respuesta",
    ["DESCONOCIDO", "a\nb\nc\nd\ne\nf", "x" * 201],
)
def test_ia_listas_invalidas_no_generan_candidato(tmp_path: Path, respuesta: str) -> None:
    assert _generar(tmp_path, "reglasEsenciales", respuesta).candidatos == ()


@pytest.mark.parametrize("respuesta", ["versus", " Cooperativo.\n", "INDIVIDUAL"])
def test_ia_modo_acepta_solo_el_vocabulario(tmp_path: Path, respuesta: str) -> None:
    resultado = _generar(tmp_path, "modo", respuesta)
    assert resultado.candidatos[0].value == respuesta.strip().lower().rstrip(".")


@pytest.mark.parametrize("respuesta", ["equipos", "DESCONOCIDO", "Es cooperativo porque..."])
def test_ia_modo_fuera_de_vocabulario_no_genera_candidato(
    tmp_path: Path, respuesta: str
) -> None:
    assert _generar(tmp_path, "modo", respuesta).candidatos == ()


def test_los_textos_de_la_guia_solo_consultan_a_la_ia(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        ai_primary_base_url="https://api.test/v1",
        ai_primary_api_key="key",
        ai_primary_model="m1",
    )
    for clave in ("primerosPasos", "reglasEsenciales", "modo"):
        assert [p.nombre for p in providers_for(clave, settings)] == ["IA · m1"]


def test_el_prompt_de_modo_pide_una_palabra_del_vocabulario(tmp_path: Path) -> None:
    visto: dict[str, str] = {}
    config = AiModelConfig("https://api.test/v1", "k", "t")
    IaGenerador(config, _http(tmp_path, "individual", visto)).buscar(
        Consulta("a", "modo", "Arkanoid", "Arcade", "1986", "jugadores: 2 (por turnos)"),
    )
    for palabra in ("individual", "cooperativo", "versus", "jugadores: 2 (por turnos)"):
        assert palabra in visto["p"]


def _estados(game: dict[str, Any]) -> dict[str, dict[str, Any]]:
    from backend.lib.domain.guia import guia_checklist

    return {item["key"]: item for item in guia_checklist(game)}


def test_checklist_de_arkanoid_dice_que_hay_y_que_falta_y_por_que() -> None:
    items = _estados(_arkanoid())
    assert items["objetivo"]["estado"] == "ok"
    assert items["objetivo"]["requerido"] is True
    assert items["perifericos"] == {
        "key": "perifericos", "label": "Periféricos", "estado": "ok",
        "detalle": "dial", "requerido": False,
    }
    assert items["modo"]["estado"] == "ok"
    assert "por turnos" in items["modo"]["detalle"]
    assert items["acciones"]["estado"] == "falta"
    assert "ArcadeDB no publica botones" in items["acciones"]["detalle"]
    assert items["primerosPasos"]["estado"] == "falta"
    assert items["reglasEsenciales"]["estado"] == "falta"


def test_checklist_sin_objetivo_marca_lo_requerido() -> None:
    game = _arkanoid()
    del game["texts"]["objetivo"]
    objetivo = _estados(game)["objetivo"]
    assert objetivo["estado"] == "falta"
    assert objetivo["requerido"] is True
    assert "no se exporta" in objetivo["detalle"]


def test_checklist_modo_simultaneo_pide_elegir_y_el_elegido_cuenta() -> None:
    game = _arkanoid()
    game["cabinet"]["nplayers"] = "2P sim"
    pendiente = _estados(game)["modo"]
    assert pendiente["estado"] == "falta"
    assert "cooperativo o versus" in pendiente["detalle"]
    game["texts"]["modo"] = _texto("versus")
    elegido = _estados(game)["modo"]
    assert elegido["estado"] == "ok"
    assert "elegido a mano" in elegido["detalle"]


def test_checklist_distingue_manual_de_sugerido_y_cuenta_items() -> None:
    game = _arkanoid(primerosPasos=_texto("Uno\nDos", status="suggested"))
    paso = _estados(game)["primerosPasos"]
    assert paso["estado"] == "ok"
    assert paso["detalle"] == "2 ítem(s), sugerido, sin revisar"


def test_checklist_ficha_sin_gabinete_explica_cada_ausencia() -> None:
    items = _estados({"identity": {"players": "1-2"}, "texts": {}})
    assert items["perifericos"]["detalle"] == "ArcadeDB no publicó el control de este juego"
    assert "1-2" in items["jugadores"]["detalle"]
    assert items["jugadores"]["estado"] == "falta"


def test_la_ficha_que_devuelve_la_api_incluye_el_checklist() -> None:
    from backend.api.schemas import GameOut, StoredGame

    game = StoredGame.model_validate({
        "id": "x", "systemId": "arcade", "romSource": "path", "romRef": "",
        "identity": {"title": "X", "year": "", "developer": "", "publisher": "",
                     "genre": "", "players": "2", "format": ""},
        "texts": {"objetivo": {"status": "manual", "value": "Ganar."}},
    })
    claves = [item.key for item in GameOut.from_stored(game).guiaChecklist]
    assert claves == [
        "objetivo", "primerosPasos", "reglasEsenciales", "jugadores", "modo",
        "perifericos", "acciones",
    ]
