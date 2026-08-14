from __future__ import annotations

import threading
from dataclasses import asdict

from backend.config import Settings
from backend.lib.providers.base import Candidato, Consulta, ProviderTrace
from backend.lib.providers.cortocircuito import breaker
from backend.lib.providers.http import ProviderHttpError
from backend.lib.providers.registro import providers_for
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

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
