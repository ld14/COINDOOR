from __future__ import annotations

from typing import Any

from backend.bundle.datajson import build_datajson

# Espejo de ../attract/library/arcade/media/goldnaxe/data.json, menos "mags" (ADR:
# el bundle nunca lleva mags[]). Es el caso de referencia que exige plan.md: "equivalente
# al de goldnaxe menos mags[]".
GOLDNAXE_EXPECTED: dict[str, Any] = {
    "accent": "#d4a017",
    "accent2": "#3d2f08",
    "review": {
        "score": 88,
        "cats": {"graficos": 85, "adiccion": 92, "sonido": 84},
    },
    "cheats": {
        "combos": [
            {"name": "Ataque hacia atrás", "input": "[←] [←] + [ATAQUE]"},
            {"name": "Embestida con hombro", "input": "[→] [→] + [ATAQUE]"},
            {"name": "Salto de cabeza", "input": "[→] [→] + [SALTO]"},
            {"name": "Magia", "input": "MAGIA (según las pociones acumuladas)"},
        ],
        "codes": [
            {
                "name": "9 créditos",
                "input": "En la selección de personaje: mantener [←] + [↓] y pulsar [A] + [C] + [START] simultáneamente",  # noqa: E501
            },
        ],
        "secretos": [
            {"name": "Pociones de magia", "input": "Golpear a los ladrones azules durante las fases de bonus para obtener pociones mágicas"},  # noqa: E501
            {"name": "Comida para recuperar vida", "input": "Golpear a los ladrones verdes durante las fases de bonus para obtener comida y recuperar vida"},  # noqa: E501
            {"name": "Montar criaturas", "input": "Derribar a los enemigos que montan criaturas y subir sobre ellas para utilizarlas en combate"},  # noqa: E501
            {"name": "Dragón rojo", "input": "En la fase 3 del arcade aparece un dragón rojo que puede utilizarse para facilitar gran parte del nivel"},  # noqa: E501
        ],
        "dos_jugadores": [
            {"name": "Restaurar vida", "input": "Durante la fase de bonus, un jugador puede golpear cuidadosamente al otro hasta dejar su vida en cero. Si termina el bonus sin morir, comenzará la siguiente fase con la vida completamente restaurada"},  # noqa: E501
            {"name": "Cooperación", "input": "Usar a los dos jugadores para atacar desde lados opuestos y evitar que los enemigos puedan rodearlos"},  # noqa: E501
            {"name": "Cuidado con el daño aliado", "input": "Los jugadores pueden golpearse entre sí, por lo que deben atacar con cuidado para no eliminar accidentalmente al compañero"},  # noqa: E501
        ],
        "servicio": [
            {"name": "Free Play", "input": "En el menú de servicio de la máquina, activar FREE PLAY para jugar sin insertar créditos"},  # noqa: E501
        ],
    },
    "manual": [
        {
            "file": "manual.pdf",
            "pages": [f"p{i:03d}.png" for i in range(1, 27)],
        },
    ],
}


def _goldnaxe_game() -> dict[str, Any]:
    return {
        "accentValue": "#d4a017",
        "accent2Value": "#3d2f08",
        "review": {
            "status": "manual",
            "score": 88,
            "cats": {"graficos": 85, "adiccion": 92, "sonido": 84},
        },
        "cheats": {
            "status": "manual",
            "groups": [
                {
                    "name": "combos",
                    "entries": [
                        {"name": "Ataque hacia atrás", "input": "[←] [←] + [ATAQUE]"},
                        {"name": "Embestida con hombro", "input": "[→] [→] + [ATAQUE]"},
                        {"name": "Salto de cabeza", "input": "[→] [→] + [SALTO]"},
                        {"name": "Magia", "input": "MAGIA (según las pociones acumuladas)"},
                    ],
                },
                {
                    "name": "codes",
                    "entries": [
                        {
                            "name": "9 créditos",
                            "input": "En la selección de personaje: mantener [←] + [↓] y pulsar [A] + [C] + [START] simultáneamente",  # noqa: E501
                        },
                    ],
                },
                {
                    "name": "secretos",
                    "entries": [
                        {"name": "Pociones de magia", "input": "Golpear a los ladrones azules durante las fases de bonus para obtener pociones mágicas"},  # noqa: E501
                        {"name": "Comida para recuperar vida", "input": "Golpear a los ladrones verdes durante las fases de bonus para obtener comida y recuperar vida"},  # noqa: E501
                        {"name": "Montar criaturas", "input": "Derribar a los enemigos que montan criaturas y subir sobre ellas para utilizarlas en combate"},  # noqa: E501
                        {"name": "Dragón rojo", "input": "En la fase 3 del arcade aparece un dragón rojo que puede utilizarse para facilitar gran parte del nivel"},  # noqa: E501
                    ],
                },
                {
                    "name": "dos_jugadores",
                    "entries": [
                        {"name": "Restaurar vida", "input": "Durante la fase de bonus, un jugador puede golpear cuidadosamente al otro hasta dejar su vida en cero. Si termina el bonus sin morir, comenzará la siguiente fase con la vida completamente restaurada"},  # noqa: E501
                        {"name": "Cooperación", "input": "Usar a los dos jugadores para atacar desde lados opuestos y evitar que los enemigos puedan rodearlos"},  # noqa: E501
                        {"name": "Cuidado con el daño aliado", "input": "Los jugadores pueden golpearse entre sí, por lo que deben atacar con cuidado para no eliminar accidentalmente al compañero"},  # noqa: E501
                    ],
                },
                {
                    "name": "servicio",
                    "entries": [
                        {"name": "Free Play", "input": "En el menú de servicio de la máquina, activar FREE PLAY para jugar sin insertar créditos"},  # noqa: E501
                    ],
                },
            ],
        },
        "manuals": [
            {"id": "m1", "fileName": "manual.pdf", "status": "processed", "pages": 26},
        ],
    }


def test_goldnaxe_equivale_al_data_json_real_menos_mags() -> None:
    game = _goldnaxe_game()
    incluir = {"accent2", "review", "cheats", "manual"}
    assert build_datajson(game, incluir) == GOLDNAXE_EXPECTED


def test_review_vacio_se_escribe_null_no_se_omite() -> None:
    game = {"accentValue": "#000000", "review": {"status": "empty"}}
    data = build_datajson(game, incluir=set())
    assert "review" in data
    assert data["review"] is None


def test_review_deseleccionado_tambien_null() -> None:
    game = {"accentValue": "#000000", "review": {"status": "manual", "score": 90, "cats": {}}}
    data = build_datajson(game, incluir=set())
    assert data["review"] is None


def test_cats_parcial_no_se_completa_con_ceros() -> None:
    game = {
        "accentValue": "#000000",
        "review": {"status": "manual", "score": 50, "cats": {"sonido": 70}},
    }
    data = build_datajson(game, incluir={"review"})
    assert data["review"]["cats"] == {"sonido": 70}


def test_accent2_vacio_se_omite() -> None:
    game = {"accentValue": "#000000", "accent2Value": "", "review": {"status": "empty"}}
    data = build_datajson(game, incluir={"accent2"})
    assert "accent2" not in data


def test_cheats_deseleccionado_se_omite_aunque_tenga_datos() -> None:
    game = {
        "accentValue": "#000000",
        "review": {"status": "empty"},
        "cheats": {"status": "manual", "groups": [{"name": "combos", "entries": []}]},
    }
    data = build_datajson(game, incluir=set())
    assert "cheats" not in data


def test_manual_sin_procesar_no_aparece() -> None:
    game = {
        "accentValue": "#000000",
        "review": {"status": "empty"},
        "manuals": [{"id": "m1", "fileName": "manual.pdf", "status": "unprocessed", "pages": 0}],
    }
    data = build_datajson(game, incluir={"manual"})
    assert "manual" not in data


def test_nunca_escribe_mags() -> None:
    game = _goldnaxe_game()
    data = build_datajson(game, incluir={"accent2", "review", "cheats", "manual"})
    assert "mags" not in data
