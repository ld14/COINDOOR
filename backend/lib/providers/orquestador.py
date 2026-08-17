from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict

from backend.config import Settings
from backend.lib.domain.fielddefs import identity_keys
from backend.lib.providers.base import Candidato, Consulta, ProviderTrace
from backend.lib.providers.cortocircuito import breaker
from backend.lib.providers.http import ProviderHttpError
from backend.lib.providers.ia.generador import IaGenerador
from backend.lib.providers.registro import providers_for
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

log = logging.getLogger(__name__)

_IDENTITY_KEYS = identity_keys()
_BATCH_CACHE_KEY = "__identity_batch__"
_SUGGESTABLE_IDENTITY_KEYS = _IDENTITY_KEYS - frozenset({"title", "year"})

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
    ) -> dict[str, object]:
        cache_key = (str(self.settings.data_dir), game_id, key)
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


def cached_candidate(
    settings: Settings,
    game_id: str,
    key: str,
    candidate_id: str,
) -> dict[str, object] | None:
    with _cache_lock:
        payload = _cache.get((str(settings.data_dir), game_id, key))
    if payload is None:
        return None
    candidates = payload.get("candidatos", [])
    if not isinstance(candidates, list):
        return None
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
