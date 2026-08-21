from __future__ import annotations

from pathlib import Path
import json

import httpx
import pytest

from backend.api.errors import BadRequest
from backend.api.schemas import CreateGame, Identity, NewSystem
from backend.config import Settings
from backend.lib.providers.base import Candidato, Consulta, Limite, ProviderResult, ProviderTrace
from backend.lib.providers.cortocircuito import breaker
from backend.lib.providers.http import ProviderHttpClient, ProviderHttpError, ProviderRejected
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.orquestador import SuggestionsService
from backend.lib.providers.referencia.youtube import YoutubeReferenceProvider
from backend.lib.providers.registro import providers_for
from backend.services.fields import FieldsService
from backend.store.cuotas import QuotasStore
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore


def _seeded_settings(tmp_path: Path) -> Settings:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="arcade", shortName="arcade", launchCmd="/bin/echo"),
    )
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="arcade",
            romSource="path",
            romRef="/roms/goldnaxe.zip",
            identity=Identity(
                title="Golden Axe",
                year="1989",
                developer="Sega",
                publisher="Sega",
                genre="Beat em up",
                players="2",
                format="Arcade",
            ),
        )
    )
    return settings


def test_http_rejects_403_without_retry(tmp_path: Path) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(403)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    provider = ProviderHttpClient("Test", Limite(), quotas, timeout=1, client=client)

    with pytest.raises(ProviderRejected), provider:
        provider.get_json("https://example.test/rejected")

    assert calls == 1


def test_suggestions_cache_avoids_second_provider_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _seeded_settings(tmp_path)
    calls = 0

    class FakeProvider:
        nombre = "Fake"
        tipo = "api"
        campos = frozenset({"year"})
        timeout = 1.0
        limite = Limite()

        def buscar(self, consulta: Consulta) -> ProviderResult:
            nonlocal calls
            calls += 1
            trace = ProviderTrace("Fake", "api", "ok")
            candidate = Candidato(
                "fake:year",
                "year",
                "identity",
                "1989",
                "Fake",
                "aplicable",
                value="1989",
                trace=trace,
            )
            return ProviderResult((candidate,), trace)

    monkeypatch.setattr(
        "backend.lib.providers.orquestador.providers_for",
        lambda _key, _settings, _cancel_event=None: (FakeProvider(),),
    )

    service = SuggestionsService(settings)
    first = service.suggest("golden-axe", "year")
    second = service.suggest("golden-axe", "year")

    assert first == second
    assert calls == 1


def test_one_provider_fails_other_responds_no_error_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _seeded_settings(tmp_path)

    class BrokenProvider:
        nombre = "Broken"
        tipo = "api"
        campos = frozenset({"year"})
        timeout = 1.0
        limite = Limite()

        def buscar(self, consulta: Consulta) -> ProviderResult:
            raise ProviderHttpError("caído", retry_exhausted=True)

    class HealthyProvider:
        nombre = "Healthy"
        tipo = "api"
        campos = frozenset({"year"})
        timeout = 1.0
        limite = Limite()

        def buscar(self, consulta: Consulta) -> ProviderResult:
            trace = ProviderTrace("Healthy", "api", "ok")
            candidate = Candidato(
                "healthy:year", "year", "identity", "1989", "Healthy", "aplicable",
                value="1989", trace=trace,
            )
            return ProviderResult((candidate,), trace)

    monkeypatch.setattr(
        "backend.lib.providers.orquestador.providers_for",
        lambda _key, _settings, _cancel_event=None: (BrokenProvider(), HealthyProvider()),
    )

    payload = SuggestionsService(settings).suggest("golden-axe", "year")

    assert payload["respondieron"] == 1
    assert payload["consultados"] == 2
    assert len(payload["candidatos"]) == 1
    assert payload["candidatos"][0]["fuente"] == "Healthy"


def test_circuit_breaker_resets_on_reintentar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _seeded_settings(tmp_path)
    calls = 0

    class FlakyProvider:
        nombre = "Flaky-test-circuit"
        tipo = "api"
        campos = frozenset({"year"})
        timeout = 1.0
        limite = Limite()

        def buscar(self, consulta: Consulta) -> ProviderResult:
            nonlocal calls
            calls += 1
            raise ProviderHttpError("fallo persistente", retry_exhausted=True)

    monkeypatch.setattr(
        "backend.lib.providers.orquestador.providers_for",
        lambda _key, _settings, _cancel_event=None: (FlakyProvider(),),
    )
    breaker.reset("Flaky-test-circuit")
    service = SuggestionsService(settings)

    service.suggest("golden-axe", "year", reintentar=True)
    assert calls == 1

    service.suggest("golden-axe", "year", reintentar=True)
    assert calls == 2

    # reintentar=True resets the circuit breaker, so the provider runs again
    service.suggest("golden-axe", "year", reintentar=True)
    assert calls == 3


def test_ia_generador_returns_sinopsis_candidate(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Un beat 'em up de vikingos."}}]},
        )

    http = ProviderHttpClient(
        "ia:test-model",
        Limite(),
        QuotasStore(tmp_path / "cuotas.json"),
        timeout=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    config = AiModelConfig("https://api.test/v1", "key", "test-model")
    result = IaGenerador(config, http).buscar(
        Consulta("golden-axe", "sinopsis", "Golden Axe", "Arcade", "1989"),
    )

    assert result.trace.estado == "ok"
    assert result.candidatos[0].value == "Un beat 'em up de vikingos."
    assert result.candidatos[0].generado_por_ia is True


def test_ia_generador_cheats_prompt_requires_matching_platform(tmp_path: Path) -> None:
    seen_prompt = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_prompt
        seen_prompt = json.loads(request.content)["messages"][0]["content"]
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"groups": []}'}}]},
        )

    http = ProviderHttpClient(
        "ia:test-model",
        Limite(),
        QuotasStore(tmp_path / "cuotas.json"),
        timeout=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    config = AiModelConfig("https://api.test/v1", "key", "test-model")
    result = IaGenerador(config, http).buscar(
        Consulta("ghost-n-goblins", "cheats", "Ghosts 'n Goblins", "MAME (máquinas arcade)", "1985"),
    )

    assert result.trace.estado == "ok"
    assert "solo para la\nversión de MAME (máquinas arcade)" in seen_prompt
    assert "no mezcles\ntrucos de ports" in seen_prompt
    assert "Si no\npodés asociar el truco con MAME (máquinas arcade), omitilo" in seen_prompt
    assert "usuarios principiantes" in seen_prompt
    assert "DIP\nswitches, explicá que son interruptores/configuración" in seen_prompt
    assert "menú de servicio, explicá cómo se accede" in seen_prompt


def test_ia_generador_invalid_review_json_fails_explicit(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "no es json"}}]})

    http = ProviderHttpClient(
        "ia:test-model",
        Limite(),
        QuotasStore(tmp_path / "cuotas.json"),
        timeout=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    config = AiModelConfig("https://api.test/v1", "key", "test-model")
    result = IaGenerador(config, http).buscar(
        Consulta("golden-axe", "review", "Golden Axe", "Arcade", "1989"),
    )

    assert result.trace.estado != "ok"
    assert result.candidatos == ()


def test_youtube_reference_provider_returns_single_referencia_candidate() -> None:
    result = YoutubeReferenceProvider().buscar(
        Consulta("golden-axe", "video", "Golden Axe", "Arcade", "1989"),
    )

    assert len(result.candidatos) == 1
    candidate = result.candidatos[0]
    assert candidate.clase == "referencia"
    assert candidate.origen_url is not None
    assert "youtube.com" in candidate.origen_url


def test_registro_skips_ia_without_credentials(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        ai_primary_base_url="",
        ai_primary_api_key="",
        ai_primary_model="",
        ai_backup_base_url="",
        ai_backup_api_key="",
        ai_backup_model="",
    )
    settings.data_dir.mkdir(parents=True)

    assert providers_for("sinopsis", settings) == ()
    video_providers = providers_for("video", settings)
    assert len(video_providers) == 1
    assert video_providers[0].nombre == "YouTube"


def test_apply_suggestion_rejects_referencia_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _seeded_settings(tmp_path)
    monkeypatch.setattr(
        "backend.lib.providers.orquestador.providers_for",
        lambda _key, _settings, _cancel_event=None: (YoutubeReferenceProvider(),),
    )
    payload = SuggestionsService(settings).suggest("golden-axe", "video")
    candidate_id = payload["candidatos"][0]["id"]

    with pytest.raises(BadRequest):
        FieldsService(settings).apply_suggestion("golden-axe", "video", candidate_id)


def test_identity_suggestion_uses_current_value_with_ia(tmp_path: Path) -> None:
    settings = _seeded_settings(tmp_path)

    payload = SuggestionsService(settings).suggest("golden-axe", "title")

    assert payload["consultados"] >= 1
    identity_candidates = [c for c in payload["candidatos"] if c["kind"] == "identity"]
    assert len(identity_candidates) >= 1
    actual = identity_candidates[0]
    assert actual["value"] == "Golden Axe"
    assert actual["generadoPorIa"] is False


def test_empty_identity_suggestion_returns_empty_results(tmp_path: Path) -> None:
    settings = _seeded_settings(tmp_path)
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="arcade",
            romSource="path",
            romRef="/roms/empty.zip",
            identity=Identity(title="Empty Year", year=""),
        )
    )

    payload = SuggestionsService(settings).suggest("empty-year", "year")

    assert payload["consultados"] >= 1
    assert payload["candidatos"] == []


def test_apply_identity_suggestion_updates_identity_field(tmp_path: Path) -> None:
    settings = _seeded_settings(tmp_path)
    payload = SuggestionsService(settings).suggest("golden-axe", "publisher")
    candidate_id = payload["candidatos"][0]["id"]

    game = FieldsService(settings).apply_suggestion("golden-axe", "publisher", candidate_id)

    assert game.identity.publisher == "Sega"
    assert game.identitySource == "manual"


def test_apply_identity_suggestion_accepts_ia_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _seeded_settings(tmp_path)

    class FakeIdentityIaProvider:
        nombre = "Fake IA"
        tipo = "api"
        campos = frozenset({"year"})
        timeout = 1.0
        limite = Limite()

        def buscar(self, consulta: Consulta) -> ProviderResult:
            trace = ProviderTrace("Fake IA", "api", "ok")
            candidate = Candidato(
                "fake-ia:year",
                "year",
                "identity",
                "1989",
                "Fake IA",
                "aplicable",
                value="1989",
                trace=trace,
                generado_por_ia=True,
            )
            return ProviderResult((candidate,), trace)

    monkeypatch.setattr(
        "backend.lib.providers.orquestador.providers_for",
        lambda _key, _settings, _cancel_event=None: (FakeIdentityIaProvider(),),
    )

    payload = SuggestionsService(settings).suggest("golden-axe", "year", reintentar=True)

    assert len(payload["candidatos"]) == 1
    assert payload["candidatos"][0]["generadoPorIa"] is True
