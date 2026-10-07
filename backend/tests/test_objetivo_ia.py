from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend.config import Settings
from backend.lib.providers.base import Consulta, Limite
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.registro import providers_for
from backend.store.cuotas import QuotasStore


def _generar(tmp_path: Path, respuesta: str) -> tuple[object, str]:
    visto = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal visto
        visto = json.loads(request.content)["messages"][0]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": respuesta}}]})

    http = ProviderHttpClient(
        "ia:test-model",
        Limite(),
        QuotasStore(tmp_path / "cuotas.json"),
        timeout=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    config = AiModelConfig("https://api.test/v1", "key", "test-model")
    resultado = IaGenerador(config, http).buscar(
        Consulta("sfa2", "objetivo", "Street Fighter Alpha 2", "Arcade", "1996"),
    )
    return resultado, visto


def test_objetivo_valido_es_un_candidato_aplicable_de_ia(tmp_path: Path) -> None:
    resultado, prompt = _generar(tmp_path, "  Vencer a todos los rivales del torneo.  ")
    candidato = resultado.candidatos[0]  # type: ignore[attr-defined]
    assert candidato.key == "objetivo"
    assert candidato.kind == "text"
    assert candidato.clase == "aplicable"
    assert candidato.generado_por_ia is True
    assert candidato.value == "Vencer a todos los rivales del torneo."
    assert "Street Fighter Alpha 2" in prompt
    assert "No nombres botones" in prompt
    assert "DESCONOCIDO" in prompt


@pytest.mark.parametrize("respuesta", ["", "   ", "DESCONOCIDO", "desconocido.", "x" * 601])
def test_objetivo_invalido_no_genera_candidato(tmp_path: Path, respuesta: str) -> None:
    resultado, _ = _generar(tmp_path, respuesta)
    assert resultado.candidatos == ()  # type: ignore[attr-defined]
    assert "respuesta inválida" in resultado.trace.estado  # type: ignore[attr-defined]


def test_objetivo_solo_consulta_a_la_ia(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        ai_primary_base_url="https://api.test/v1",
        ai_primary_api_key="key",
        ai_primary_model="m1",
    )
    nombres = [p.nombre for p in providers_for("objetivo", settings)]
    assert nombres == ["IA · m1"]


def _juego(tmp_path: Path) -> tuple[Settings, str]:
    from backend.api.schemas import CreateGame, Identity, NewSystem
    from backend.store.juegos import GamesStore
    from backend.store.sistemas import SystemsStore

    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="arcade", shortName="arcade", launchCmd="/bin/echo"),
    )
    game = GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="arcade", romSource="path", romRef="/roms/goldnaxe.zip",
            identity=Identity(title="Golden Axe", year="1989", developer="Sega",
                              publisher="Sega", genre="Beat em up", players="2", format="Arcade"),
        )
    )
    return settings, game.id


def test_objetivo_se_guarda_y_se_borra_como_la_sinopsis(tmp_path: Path) -> None:
    from backend.services.fields import FieldsService

    settings, game_id = _juego(tmp_path)
    service = FieldsService(settings)
    guardado = service.set_value(game_id, "objetivo", "Rescatar a los enanos.")
    assert guardado.texts["objetivo"].status == "manual"
    assert guardado.texts["objetivo"].value == "Rescatar a los enanos."
    assert guardado.status == "incomplete"  # sigue faltando lo requerido, no por objetivo
    borrado = service.delete(game_id, "objetivo")
    assert borrado.texts["objetivo"].status == "empty"


def test_objetivo_lleva_el_contexto_de_la_ficha_al_prompt(tmp_path: Path) -> None:
    from backend.api.schemas import StoredGame
    from backend.lib.providers.orquestador import _contexto_guia

    game = StoredGame.model_validate({
        "id": "arkanoidu", "systemId": "arcade", "romSource": "path",
        "romRef": "/roms/arkanoidu.zip",
        "identity": {"title": "Arkanoidu", "year": "1986", "developer": "Taito America",
                     "publisher": "", "genre": "Breakout", "players": "2", "format": ""},
    })
    contexto = _contexto_guia(game)
    assert "desarrollador: Taito America" in contexto
    assert "género: Breakout" in contexto
    assert "romset de MAME: arkanoidu" in contexto

    visto = {}

    def handler(request: httpx.Request) -> httpx.Response:
        visto["prompt"] = json.loads(request.content)["messages"][0]["content"]
        cuerpo = {"choices": [{"message": {"content": "Romper ladrillos."}}]}
        return httpx.Response(200, json=cuerpo)

    http = ProviderHttpClient(
        "ia:t", Limite(), QuotasStore(tmp_path / "c.json"), timeout=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    IaGenerador(AiModelConfig("https://api.test/v1", "k", "t"), http).buscar(
        Consulta("arkanoidu", "objetivo", "Arkanoidu", "Arcade", "1986", contexto),
    )
    assert "Taito America" in visto["prompt"]
    assert "romset de MAME: arkanoidu" in visto["prompt"]
