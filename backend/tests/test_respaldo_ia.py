"""ADR-0026: la IA como último recurso en "Sugerir" identidad; ADR-0027: antes que MobyGames."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from backend.lib.providers.base import (
    Candidato,
    Consulta,
    Limite,
    ProviderResult,
    ProviderTrace,
)
from backend.lib.providers.orquestador import SuggestionsService
from backend.tests.test_providers import _seeded_settings

IDENTIDAD_IA = {
    "developer": "Sega AM2",
    "publisher": "Sega",
    "genre": "beat 'em up",
    "players": "1-2",
    "format": "Arcade",
}


class _Factual:
    """Una fuente factual que solo conoce algunos campos."""

    tipo = "scrape"
    timeout = 1.0
    limite = Limite()

    def __init__(self, conoce: dict[str, str], nombre: str = "Launchbox") -> None:
        self.conoce = conoce
        self.campos = frozenset(conoce)
        self.nombre = nombre
        self.consultadas: list[str] = []

    def buscar(self, consulta: Consulta) -> ProviderResult:
        self.consultadas.append(consulta.key)
        trace = ProviderTrace(self.nombre, "scrape", "ok")
        valor = self.conoce.get(consulta.key)
        if not valor:
            return ProviderResult((), ProviderTrace(self.nombre, "scrape", "sin resultados"))
        candidato = Candidato(
            f"mg:{consulta.key}", consulta.key, "identity", consulta.key, self.nombre,
            "aplicable", value=valor, trace=trace,
        )
        return ProviderResult((candidato,), trace)


class _IaFalsa:
    nombre = "IA · modelo-test"
    tipo = "api"
    campos = frozenset({"identidad"})
    timeout = 1.0
    limite = Limite()
    llamadas = 0

    def buscar(self, consulta: Consulta) -> ProviderResult:
        type(self).llamadas += 1
        assert consulta.key == "identidad"
        trace = ProviderTrace(self.nombre, "api", "ok")
        candidato = Candidato(
            "ia:identidad", "identidad", "identity", "identidad", self.nombre, "aplicable",
            value=json.dumps(IDENTIDAD_IA), generado_por_ia=True, trace=trace,
        )
        return ProviderResult((candidato,), trace)


@pytest.fixture()
def ia(monkeypatch: pytest.MonkeyPatch) -> type[_IaFalsa]:
    _IaFalsa.llamadas = 0
    monkeypatch.setattr(
        "backend.lib.providers.orquestador.proveedores_ia",
        lambda _settings, _cancel=None: (_IaFalsa(),),
    )
    return _IaFalsa


def _con_factual(monkeypatch: pytest.MonkeyPatch, conoce: dict[str, str]) -> None:
    _con_cadena(monkeypatch, _Factual(conoce))


def _con_cadena(monkeypatch: pytest.MonkeyPatch, *proveedores: _Factual) -> None:
    monkeypatch.setattr(
        "backend.lib.providers.orquestador.providers_for",
        lambda _key, _settings, _cancel_event=None: proveedores,
    )


def _por_clave(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [c for c in payload["candidatos"] if c["key"] == key]


def test_sin_candidato_factual_sugiere_el_de_la_ia_marcado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa]
) -> None:
    _con_factual(monkeypatch, {})
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest("golden-axe", "developer")
    candidatos = _por_clave(payload, "developer")
    assert [c["value"] for c in candidatos] == ["Sega AM2"]
    assert candidatos[0]["generadoPorIa"] is True
    assert candidatos[0]["nombre"] == "Desarrollador (IA)"
    assert candidatos[0]["fuente"] == "IA · modelo-test"
    assert ia.llamadas == 1


def test_con_candidato_factual_la_ia_no_se_consulta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa]
) -> None:
    _con_factual(monkeypatch, {"developer": "Sega"})
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest("golden-axe", "developer")
    assert [c["value"] for c in payload["candidatos"]] == ["Sega"]
    assert ia.llamadas == 0


@pytest.mark.parametrize("key", ["title", "year", "format"])
def test_titulo_año_y_formato_nunca_salen_de_la_ia(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa], key: str
) -> None:
    _con_factual(monkeypatch, {})
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest("golden-axe", key)
    assert payload["candidatos"] == []
    assert ia.llamadas == 0


def test_una_consulta_a_la_ia_cubre_todos_los_campos_del_juego(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa]
) -> None:
    _con_factual(monkeypatch, {})
    service = SuggestionsService(_seeded_settings(tmp_path))
    for key in ("developer", "publisher", "genre", "players"):
        assert _por_clave(service.suggest("golden-axe", key), key)
    assert ia.llamadas == 1


def test_reintentar_una_fuente_puntual_no_consulta_a_la_ia(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa]
) -> None:
    _con_factual(monkeypatch, {})
    service = SuggestionsService(_seeded_settings(tmp_path))
    payload = service.suggest("golden-axe", "developer", source="Launchbox")
    assert payload["candidatos"] == []
    assert ia.llamadas == 0


def test_sin_ia_configurada_todo_sigue_igual(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _con_factual(monkeypatch, {})
    monkeypatch.setattr(
        "backend.lib.providers.orquestador.proveedores_ia", lambda _settings, _cancel=None: ()
    )
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest("golden-axe", "developer")
    assert payload["candidatos"] == []
    assert payload["consultados"] == 1


def test_el_bloque_completa_con_una_consulta_solo_lo_que_falta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa]
) -> None:
    _con_factual(monkeypatch, {"developer": "Sega", "genre": "Action"})
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest_identity_batch("golden-axe")
    por_clave = {c["key"]: c for c in payload["candidatos"]}
    assert por_clave["developer"]["value"] == "Sega"
    assert por_clave["developer"]["generadoPorIa"] is False
    assert por_clave["genre"]["value"] == "Action"
    assert por_clave["publisher"]["value"] == "Sega"
    assert por_clave["publisher"]["generadoPorIa"] is True
    assert por_clave["players"]["value"] == "1-2"
    assert "format" not in por_clave  # el formato nunca sale de la IA
    assert ia.llamadas == 1


# ── ADR-0027: MobyGames es el último recurso y la IA va antes que él ────────


def test_la_ia_va_antes_que_mobygames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa]
) -> None:
    moby = _Factual({"developer": "Brøderbund"}, nombre="MobyGames")
    _con_cadena(monkeypatch, _Factual({}), moby)
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest("golden-axe", "developer")
    assert [c["value"] for c in payload["candidatos"]] == ["Sega AM2"]
    assert ia.llamadas == 1
    assert moby.consultadas == []
    estados = {f["nombre"]: f["estado"] for f in payload["fuentes"]}
    assert estados["MobyGames"] == "no hizo falta"


def test_sin_respuesta_de_la_ia_queda_mobygames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "backend.lib.providers.orquestador.proveedores_ia", lambda _settings, _cancel=None: ()
    )
    moby = _Factual({"developer": "Brøderbund"}, nombre="MobyGames")
    _con_cadena(monkeypatch, _Factual({}), moby)
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest("golden-axe", "developer")
    assert [c["value"] for c in payload["candidatos"]] == ["Brøderbund"]
    assert moby.consultadas == ["developer"]


def test_mobygames_no_se_consulta_si_una_fuente_anterior_tiene_el_campo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    moby = _Factual({"format": "Diskette"}, nombre="MobyGames")
    _con_cadena(monkeypatch, _Factual({"format": "CD"}), moby)
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest("golden-axe", "format")
    assert [c["value"] for c in payload["candidatos"]] == ["CD"]
    assert moby.consultadas == []
    assert payload["consultados"] == 1  # lo salteado no cuenta como consultado


def test_el_buscador_que_va_despues_no_apaga_a_mobygames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # El último recurso se decide por posición: el buscador de imágenes siempre trae algo,
    # pero va después.
    moby = _Factual({"caratula": "moby.jpg"}, nombre="MobyGames")
    buscador = _Factual({"caratula": "web.jpg"}, nombre="Image Search")
    _con_cadena(monkeypatch, _Factual({}), moby, buscador)
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest("golden-axe", "caratula")
    assert [c["value"] for c in payload["candidatos"]] == ["moby.jpg", "web.jpg"]
    assert [f["nombre"] for f in payload["fuentes"]] == ["Launchbox", "MobyGames", "Image Search"]


def test_consultar_mobygames_a_pedido_lo_consulta_aunque_haya_candidatos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa]
) -> None:
    moby = _Factual({"developer": "Brøderbund"}, nombre="MobyGames")
    _con_cadena(monkeypatch, _Factual({"developer": "Sega"}), moby)
    service = SuggestionsService(_seeded_settings(tmp_path))
    payload = service.suggest("golden-axe", "developer", source="MobyGames", reintentar=True)
    assert [c["value"] for c in payload["candidatos"]] == ["Brøderbund"]
    assert ia.llamadas == 0


def test_el_bloque_consulta_mobygames_solo_para_lo_que_sigue_faltando(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ia: type[_IaFalsa]
) -> None:
    moby = _Factual(
        {"developer": "Brøderbund", "format": "Diskette", "players": "1"}, nombre="MobyGames"
    )
    _con_cadena(monkeypatch, _Factual({"developer": "Sega"}), moby)
    payload = SuggestionsService(_seeded_settings(tmp_path)).suggest_identity_batch("golden-axe")
    por_clave = {c["key"]: c for c in payload["candidatos"]}
    assert por_clave["developer"]["value"] == "Sega"
    assert por_clave["players"]["value"] == "1-2"  # la IA, antes que MobyGames
    assert por_clave["format"]["value"] == "Diskette"  # solo MobyGames tiene el formato
    assert moby.consultadas == ["format"]
    assert ia.llamadas == 1
