from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from backend.lib.providers.base import Consulta, Limite
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.client import ModelResponseError, OpenAiCompatibleClient
from backend.lib.providers.ia.trucos_web import (
    ResultadoWeb,
    TavilyClient,
    TrucosWebGenerador,
    _evidencia,
    _extraer_objeto_json,
)
from backend.store.cuotas import QuotasStore

Handler = Callable[[httpx.Request], httpx.Response]

TRUCOS = (
    '{"groups": [{"name": "Códigos", "entries":'
    ' [{"name": "Modo cheat", "input": "Shift+56"}]}]}'
)

RESULTADOS = {
    "results": [
        {
            "title": "Sid Meier's Civilization: Cheats - CivFanatics",
            "url": "https://civfanatics.com/civ1/cheats/",
            "content": "snippet corto",
            "raw_content": "Cheat Mode: Shift+56 revela el mapa entero.",
        },
        {
            "title": "Civilization - GameFAQs",
            "url": "https://gamefaqs.example/civ",
            "content": "Alt+R aleatoriza los líderes rivales.",
        },
    ],
}


def _cliente_http(tmp_path: Path, nombre: str, handler: Handler) -> ProviderHttpClient:
    return ProviderHttpClient(
        nombre,
        Limite(),
        QuotasStore(tmp_path / "cuotas.json"),
        timeout=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _buscador(tmp_path: Path, handler: Handler) -> TavilyClient:
    return TavilyClient("https://api.tavily.test", "tvly-k", _cliente_http(tmp_path, "t", handler))


def _modelo(
    tmp_path: Path,
    handler: Handler,
    model: str = "gpt-oss-120b",
) -> OpenAiCompatibleClient:
    return OpenAiCompatibleClient(
        "https://groq.test/v1", "k", model, _cliente_http(tmp_path, f"ia:{model}", handler),
    )


def _busca_ok(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=RESULTADOS)


def _responde(contenido: str) -> Handler:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": contenido}}]})

    return handler


def _consulta(system: str = "msdos") -> Consulta:
    return Consulta("civ", "cheats", "Sid Meier's Civilization", system, "1991")


def test_tavily_recibe_la_consulta_bien_formada(tmp_path: Path) -> None:
    visto: dict[str, object] = {}

    def buscar(request: httpx.Request) -> httpx.Response:
        visto["url"] = str(request.url)
        visto["auth"] = request.headers.get("authorization")
        visto["body"] = json.loads(request.content)
        return httpx.Response(200, json=RESULTADOS)

    generador = TrucosWebGenerador(
        _buscador(tmp_path, buscar), [_modelo(tmp_path, _responde(TRUCOS))],
    )
    generador.buscar(_consulta())

    assert visto["url"] == "https://api.tavily.test/search"
    assert visto["auth"] == "Bearer tvly-k"
    body = visto["body"]
    assert isinstance(body, dict)
    assert "Sid Meier's Civilization" in body["query"]
    assert "1991" in body["query"]
    assert "msdos" in body["query"]
    # Un crédito por búsqueda: "advanced" cuesta dos y no compensa.
    assert body["search_depth"] == "basic"
    assert body["include_raw_content"] == "text"


def test_trucos_web_estructura_lo_encontrado(tmp_path: Path) -> None:
    generador = TrucosWebGenerador(
        _buscador(tmp_path, _busca_ok), [_modelo(tmp_path, _responde(TRUCOS))],
    )
    result = generador.buscar(_consulta())

    assert result.trace.estado == "ok"
    assert len(result.candidatos) == 1
    candidato = result.candidatos[0]
    assert candidato.key == "cheats"
    assert candidato.fuente == "Búsqueda web + IA"
    assert candidato.generado_por_ia is True
    assert json.loads(candidato.value or "")["groups"][0]["entries"][0]["input"] == "Shift+56"
    assert candidato.meta["modelo"] == "gpt-oss-120b"


def test_trucos_web_deja_las_urls_reales_en_el_trace(tmp_path: Path) -> None:
    generador = TrucosWebGenerador(
        _buscador(tmp_path, _busca_ok), [_modelo(tmp_path, _responde(TRUCOS))],
    )
    trace = generador.buscar(_consulta()).trace

    assert any(dato.startswith("búsqueda: ") for dato in trace.datos_obtenidos)
    urls = [u.url for u in trace.urls_procesadas]
    assert "https://civfanatics.com/civ1/cheats/" in urls
    assert all(u.status is None for u in trace.urls_procesadas)


def test_trucos_web_sin_resultados_no_llama_al_modelo(tmp_path: Path) -> None:
    """Sin evidencia no hay candidato: un modelo sin texto inventa códigos."""
    llamadas = 0

    def modelo(_request: httpx.Request) -> httpx.Response:
        nonlocal llamadas
        llamadas += 1
        return httpx.Response(200, json={"choices": [{"message": {"content": TRUCOS}}]})

    def vacio(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    result = TrucosWebGenerador(
        _buscador(tmp_path, vacio), [_modelo(tmp_path, modelo)],
    ).buscar(_consulta())

    assert result.candidatos == ()
    # "Buscó y no encontró" es una respuesta: con estado != "ok" el modal lo
    # contaría como fuente caída y diría "error de la fuente externa".
    assert result.trace.estado == "ok"
    assert "la búsqueda no devolvió páginas con texto" in result.trace.datos_obtenidos
    assert llamadas == 0


def test_trucos_web_busco_pero_no_habia_trucos(tmp_path: Path) -> None:
    """Distinto de fallar: se buscó, se leyó, y no había nada de esta versión."""
    result = TrucosWebGenerador(
        _buscador(tmp_path, _busca_ok), [_modelo(tmp_path, _responde('{"groups": []}'))],
    ).buscar(_consulta())

    assert result.candidatos == ()
    assert result.trace.estado == "ok"
    assert any("no traían trucos" in d for d in result.trace.datos_obtenidos)
    # Aun sin candidato, queda registrado dónde se buscó.
    assert len(result.trace.urls_procesadas) == 2


def test_trucos_web_cae_al_modelo_de_respaldo(tmp_path: Path) -> None:
    result = TrucosWebGenerador(
        _buscador(tmp_path, _busca_ok),
        [
            _modelo(tmp_path, _responde("no es json"), model="gpt-oss-120b"),
            _modelo(tmp_path, _responde(TRUCOS), model="gpt-oss-20b"),
        ],
    ).buscar(_consulta())

    assert result.trace.estado == "ok"
    assert result.candidatos[0].meta["modelo"] == "gpt-oss-20b"


def test_trucos_web_sin_ningun_modelo_util_lo_dice(tmp_path: Path) -> None:
    result = TrucosWebGenerador(
        _buscador(tmp_path, _busca_ok), [_modelo(tmp_path, _responde("no es json"))],
    ).buscar(_consulta())

    assert result.candidatos == ()
    assert "no se pudo estructurar" in result.trace.estado


def test_trucos_web_recorta_la_evidencia_al_presupuesto(tmp_path: Path) -> None:
    """El techo de 8.000 TPM de Groq cuenta prompt + max_tokens: sin recorte, 429."""
    prompts: list[str] = []

    def modelo(request: httpx.Request) -> httpx.Response:
        prompts.append(json.loads(request.content)["messages"][0]["content"])
        return httpx.Response(200, json={"choices": [{"message": {"content": TRUCOS}}]})

    gigante = {
        "results": [
            {"title": "A", "url": "https://a.test", "raw_content": "truco " * 20_000},
            {"title": "B", "url": "https://b.test", "raw_content": "otro " * 20_000},
        ],
    }

    def buscar(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=gigante)

    TrucosWebGenerador(
        _buscador(tmp_path, buscar), [_modelo(tmp_path, modelo)],
    ).buscar(_consulta())

    prompt = prompts[0]
    assert len(prompt) < 16_000
    # Las dos páginas entran recortadas, y cada bloque lleva su URL para que el
    # modelo pueda descartar por sitio.
    assert "https://a.test" in prompt
    assert "https://b.test" in prompt


def test_evidencia_da_la_tajada_grande_a_los_primeros() -> None:
    """El buscador ya ordenó por relevancia: con un tope por página bajo, una del
    juego equivocado se llevaría la misma tajada que la fuente principal."""
    resultados = tuple(
        ResultadoWeb(f"R{i}", f"https://r{i}.test", "x" * 20_000) for i in range(4)
    )
    texto, usados = _evidencia(resultados)

    assert len(usados) == 2
    assert texto.count("x") == 10_000


def test_trucos_web_le_pasa_la_plataforma_y_la_evidencia_al_prompt(tmp_path: Path) -> None:
    prompts: list[str] = []

    def modelo(request: httpx.Request) -> httpx.Response:
        prompts.append(json.loads(request.content)["messages"][0]["content"])
        return httpx.Response(200, json={"choices": [{"message": {"content": TRUCOS}}]})

    TrucosWebGenerador(
        _buscador(tmp_path, _busca_ok), [_modelo(tmp_path, modelo)],
    ).buscar(_consulta("MAME (máquinas arcade)"))

    prompt = prompts[0]
    assert "MAME (máquinas arcade)" in prompt
    assert "Shift+56 revela el mapa entero" in prompt
    assert "No inventes ni completes" in prompt


def test_extractor_toma_el_objeto_externo_aunque_falte_el_prefijo() -> None:
    entero = _extraer_objeto_json(f"Acá van los trucos:\n```json\n{TRUCOS}\n```")
    assert json.loads(entero)["groups"][0]["name"] == "Códigos"

    recortado = _extraer_objeto_json('roups": []} ' + TRUCOS)
    assert json.loads(recortado)["groups"][0]["entries"][0]["name"] == "Modo cheat"


def test_extractor_falla_si_no_hay_objeto_con_groups() -> None:
    with pytest.raises(ModelResponseError):
        _extraer_objeto_json("No encontré trucos para este juego.")
