from __future__ import annotations

import json
from typing import Any

from backend.bundle.datajson import build_datajson
from backend.bundle.seleccion import compute_seleccion
from backend.config import Settings

BOTONES = [
    {"control": "P1_BUTTON1", "color": "Blue", "action": "Jab Punch"},
    {"control": "P1_BUTTON2", "color": "", "action": "Strong Punch"},
]


def _game(objetivo: str = "", status: str = "manual") -> dict[str, Any]:
    texts: dict[str, Any] = {"sinopsis": {"status": "manual", "value": "SINOPSIS-GENERADA"}}
    if objetivo or status == "empty":
        texts["objetivo"] = {"status": status, "value": objetivo}
    return {
        "identity": {"title": "Street Fighter Alpha 2", "players": "2"},
        "texts": texts,
        "cabinet": {"resolution": "384x224", "button_list": BOTONES},
    }


def test_acciones_salen_de_button_list_con_los_mismos_campos() -> None:
    data = build_datajson(_game("Vencer a todos."), {"objetivo"})
    assert data["guia"]["acciones"] == [
        {"control": "P1_BUTTON1", "action": "Jab Punch", "color": "Blue"},
        {"control": "P1_BUTTON2", "action": "Strong Punch"},
    ]
    assert data["guia"]["objetivo"] == "Vencer a todos."
    assert data["guia"]["multijugador"] == {"jugadores": 2}


def test_sin_objetivo_no_hay_guia() -> None:
    assert "guia" not in build_datajson(_game("  "), {"objetivo"})
    assert "guia" not in build_datajson(_game(), {"objetivo"})
    assert "guia" not in build_datajson(_game("", status="empty"), {"objetivo"})


def test_no_incluida_no_viaja() -> None:
    assert "guia" not in build_datajson(_game("Vencer."), set())


def test_button_list_vacio_omite_acciones() -> None:
    game = _game("Vencer.")
    game["cabinet"]["button_list"] = []
    assert "acciones" not in build_datajson(game, {"objetivo"})["guia"]


def test_la_sinopsis_nunca_se_copia() -> None:
    texto = json.dumps(build_datajson(_game("Vencer."), {"objetivo"}))
    assert "SINOPSIS-GENERADA" not in texto


def test_jugadores_no_entero_limpio_se_omite() -> None:
    game = _game("Vencer.")
    game["identity"]["players"] = "1-2"
    assert "multijugador" not in build_datajson(game, {"objetivo"})["guia"]


def test_sin_claves_prohibidas_ni_metadatos_inventados() -> None:
    texto = json.dumps(build_datajson(_game("Vencer."), {"objetivo"}))
    assert "JOYCODE" not in texto
    guia = json.loads(texto)["guia"]
    assert "perifericos" not in guia
    assert "fuentes" not in guia
    assert "modo" not in guia.get("multijugador", {})
    assert "resolution" not in texto


def test_revision_depende_de_que_una_persona_lo_haya_guardado() -> None:
    manual = build_datajson(_game("X", status="manual"), {"objetivo"})["guia"]
    sugerido = build_datajson(_game("X", status="suggested"), {"objetivo"})["guia"]
    assert manual["revision"] == "revisado"
    assert sugerido["revision"] == "borrador"


def test_seleccion_ofrece_objetivo_como_opcional(tmp_path: Any) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    items = {i.key: i for i in compute_seleccion(settings, _game("Vencer."))}
    assert items["objetivo"].required is False
    assert items["objetivo"].disponible is True
    assert items["objetivo"].label == "Objetivo (Cómo se juega)"
    assert "guia" not in items
    sin = {i.key: i for i in compute_seleccion(settings, _game())}
    assert sin["objetivo"].disponible is False
