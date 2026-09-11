from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict
from pathlib import Path

from backend.api.errors import BadRequest
from backend.config import Settings
from backend.lib.domain.fielddefs import identity_keys
from backend.lib.providers.base import Candidato, Consulta, Limite, ProviderTrace
from backend.lib.providers.cortocircuito import breaker
from backend.lib.providers.http import ProviderHttpClient, ProviderHttpError
from backend.lib.providers.ia.client import ModelResponseError, OpenAiCompatibleClient
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.registro import providers_for
from backend.store.cuotas import QuotasStore
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

log = logging.getLogger(__name__)

_IDENTITY_KEYS = identity_keys()
_BATCH_CACHE_KEY = "__identity_batch__"
_SUGGESTABLE_IDENTITY_KEYS = _IDENTITY_KEYS - frozenset({"title", "year"})
_PARSE_PROMPT_PATH = Path(__file__).parent / "ia" / "prompts" / "cheats-parse.v1.md"
# Una guía completa da decenas de entradas; con el tope por defecto el modelo recorta y
# devuelve menos de lo que hay en el texto.
_PARSE_MAX_TOKENS = 16000

_cache: dict[tuple[str, str, str], dict[str, object]] = {}
_cache_lock = threading.Lock()


class SuggestionsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.games = GamesStore(settings.games_dir)
        self.systems = SystemsStore(settings.systems_path)

    def suggest(
        self,
        game_id: str,
        key: str,
        cancel_event: threading.Event | None = None,
        *,
        reintentar: bool = False,
        source: str | None = None,
    ) -> dict[str, object]:
        cache_key = (str(self.settings.data_dir), game_id, key, source or "")
        if not reintentar:
            with _cache_lock:
                cached = _cache.get(cache_key)
            if cached is not None:
                return cached
        game = self.games.get(game_id)
        system = self.systems.get(game.systemId)
        consulta = Consulta(
            game.id,
            key,
            game.identity.title,
            system.name,
            game.identity.year or None,
        )
        providers = providers_for(key, self.settings, cancel_event)
        if source:
            providers = [p for p in providers if p.nombre == source]
        if reintentar:
            for p in providers:
                breaker.reset(p.nombre)
        providers = [provider for provider in providers if not breaker.is_open(provider.nombre)]
        candidates: list[Candidato] = []
        traces: list[ProviderTrace] = []
        responded = 0
        for provider in providers:
            if cancel_event and cancel_event.is_set():
                break
            try:
                result = provider.buscar(consulta)
            except ProviderHttpError as exc:
                if exc.retry_exhausted:
                    breaker.strike(provider.nombre)
                traces.append(ProviderTrace(provider.nombre, provider.tipo, str(exc)))
                continue
            except Exception:
                log.exception("Provider %s failed unexpectedly", provider.nombre)
                traces.append(ProviderTrace(provider.nombre, provider.tipo, "excepción inesperada"))
                continue
            candidates.extend(result.candidatos)
            traces.append(result.trace)
            if result.trace.estado == "ok":
                responded += 1
        payload: dict[str, object] = {
            "candidatos": [_candidate_out(candidate) for candidate in candidates],
            "respondieron": responded,
            "consultados": len(providers),
            "fuentes": [_trace_out(trace) for trace in traces],
        }
        with _cache_lock:
            _cache[cache_key] = payload
        return payload

    def suggest_identity_batch(
        self,
        game_id: str,
        cancel_event: threading.Event | None = None,
        *,
        reintentar: bool = False,
    ) -> dict[str, object]:
        cache_key = (str(self.settings.data_dir), game_id, _BATCH_CACHE_KEY)
        if not reintentar:
            with _cache_lock:
                cached = _cache.get(cache_key)
            if cached is not None:
                return cached
        game = self.games.get(game_id)
        system = self.systems.get(game.systemId)
        consulta = Consulta(
            game.id,
            "identidad",
            game.identity.title,
            system.name,
            game.identity.year or None,
        )
        providers = providers_for("sinopsis", self.settings, cancel_event)
        if reintentar:
            for p in providers:
                breaker.reset(p.nombre)
        providers = [p for p in providers if not breaker.is_open(p.nombre)]
        log.info("identity batch: %d providers for %s", len(providers), game_id)
        candidates: list[Candidato] = []
        traces: list[ProviderTrace] = []
        responded = 0
        for provider in providers:
            if cancel_event and cancel_event.is_set():
                break
            try:
                result = provider.buscar(consulta)
            except ProviderHttpError as exc:
                if exc.retry_exhausted:
                    breaker.strike(provider.nombre)
                traces.append(ProviderTrace(provider.nombre, provider.tipo, str(exc)))
                log.warning("identity batch: provider %s failed: %s", provider.nombre, exc)
                continue
            except Exception:
                log.exception("Provider %s failed unexpectedly", provider.nombre)
                traces.append(ProviderTrace(provider.nombre, provider.tipo, "excepción inesperada"))
                continue
            traces.append(result.trace)
            if result.trace.estado == "ok":
                responded += 1
            if isinstance(provider, IaGenerador) and result.candidatos:
                raw = result.candidatos[0].value
                if raw:
                    try:
                        data = json.loads(raw) if isinstance(raw, str) else raw
                    except (json.JSONDecodeError, TypeError):
                        data = {}
                    if isinstance(data, dict):
                        for field_key in _SUGGESTABLE_IDENTITY_KEYS:
                            val = str(data.get(field_key, ""))
                            if val:
                                candidates.append(Candidato(
                                    id=f"ia-batch:{provider.config.model}:{field_key}",
                                    key=field_key,
                                    kind="identity",
                                    nombre=f"{field_key} generado por IA",
                                    fuente=provider.nombre,
                                    clase="aplicable",
                                    value=val,
                                    generado_por_ia=True,
                                    meta={"prompt_version": "v1", "modelo": provider.config.model},
                                    trace=result.trace,
                                ))
        log.info("identity batch: %d candidates, %d responded", len(candidates), responded)
        payload: dict[str, object] = {
            "candidatos": [_candidate_out(c) for c in candidates],
            "respondieron": responded,
            "consultados": len(providers),
            "fuentes": [_trace_out(t) for t in traces],
        }
        with _cache_lock:
            _cache[cache_key] = payload
        return payload

    def parse_cheats_text(self, game_id: str, text: str) -> list[dict[str, object]]:
        """Convierte texto pegado a mano (Markdown, prosa, lo que sea) en `groups`."""
        text = text.strip()
        if not text:
            return []
        game = self.games.get(game_id)
        system = self.systems.get(game.systemId)
        prompt = _PARSE_PROMPT_PATH.read_text(encoding="utf-8").format(
            titulo=game.identity.title,
            sistema=system.name,
            texto=text,
        )
        quotas = QuotasStore(self.settings.quotas_path)
        configs = (
            AiModelConfig(
                self.settings.ai_primary_base_url,
                self.settings.ai_primary_api_key,
                self.settings.ai_primary_model,
            ),
            AiModelConfig(
                self.settings.ai_backup_base_url,
                self.settings.ai_backup_api_key,
                self.settings.ai_backup_model,
            ),
        )
        last_error = ""
        for config in configs:
            if not (config.base_url and config.api_key and config.model):
                continue
            http = ProviderHttpClient(
                f"ia-parse:{config.model}",
                Limite(por_segundo=None, por_dia=None, espera_min=1.0),
                quotas,
                timeout=45.0,
            )
            client = OpenAiCompatibleClient(config.base_url, config.api_key, config.model, http)
            try:
                content = client.complete(prompt, max_tokens=_PARSE_MAX_TOKENS)
                data = json.loads(content)
                if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
                    raise ModelResponseError("respuesta sin 'groups'")
                return [_grupo_en_un_renglon(group) for group in data["groups"]]
            except Exception as exc:
                log.warning("parse_cheats_text: %s falló: %s", config.model, exc)
                last_error = str(exc)
                continue
        motivo = last_error or "sin modelo de IA configurado"
        raise BadRequest(f"No se pudo interpretar el texto: {motivo}")


def _un_renglon(valor: object) -> str:
    """Aplasta saltos de línea: el contrato guarda cada truco en un renglón (`goldnaxe`)."""
    return " ".join(str(valor).split())


def _grupo_en_un_renglon(group: object) -> dict[str, object]:
    if not isinstance(group, dict):
        return {"name": "", "entries": []}
    entries = group.get("entries")
    return {
        "name": _un_renglon(group.get("name", "")),
        "entries": [
            {"name": _un_renglon(e.get("name", "")), "input": _un_renglon(e.get("input", ""))}
            for e in (entries if isinstance(entries, list) else [])
            if isinstance(e, dict)
        ],
    }


def cached_candidate(
    settings: Settings,
    game_id: str,
    key: str,
    candidate_id: str,
) -> dict[str, object] | None:
    prefix = (str(settings.data_dir), game_id, key)
    with _cache_lock:
        for cache_key, payload in _cache.items():
            if cache_key[:3] != prefix:
                continue
            candidates = payload.get("candidatos", [])
            if not isinstance(candidates, list):
                continue
            for candidate in candidates:
                if isinstance(candidate, dict) and candidate.get("id") == candidate_id:
                    return candidate
    return None


def cached_identity_candidate(
    settings: Settings,
    game_id: str,
    candidate_id: str,
) -> dict[str, object] | None:
    with _cache_lock:
        payload = _cache.get((str(settings.data_dir), game_id, _BATCH_CACHE_KEY))
    if payload is None:
        return None
    candidates = payload.get("candidatos", [])
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == candidate_id:
            return candidate
    return None


def _candidate_out(candidate: Candidato) -> dict[str, object]:
    return {
        "id": candidate.id,
        "key": candidate.key,
        "kind": candidate.kind,
        "nombre": candidate.nombre,
        "fuente": candidate.fuente,
        "clase": candidate.clase,
        "value": candidate.value,
        "previewUrl": candidate.preview_url,
        "mediaUrl": candidate.media_url,
        "origenUrl": candidate.origen_url,
        "generadoPorIa": candidate.generado_por_ia,
        "meta": candidate.meta,
        "trace": _trace_out(candidate.trace) if candidate.trace else None,
    }


def _trace_out(trace: ProviderTrace) -> dict[str, object]:
    return {
        "nombre": trace.nombre,
        "tipo": trace.tipo,
        "estado": trace.estado,
        "urlsProcesadas": [asdict(url) for url in trace.urls_procesadas],
        "datosObtenidos": list(trace.datos_obtenidos),
    }
