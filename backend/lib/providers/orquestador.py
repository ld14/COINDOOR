from __future__ import annotations

import json
import logging
import threading
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from backend.api.errors import BadRequest
from backend.api.schemas import StoredGame
from backend.config import Settings
from backend.lib.domain.fielddefs import identity_keys
from backend.lib.providers.base import Candidato, Consulta, Limite, Proveedor, ProviderTrace
from backend.lib.providers.cortocircuito import breaker
from backend.lib.providers.http import ProviderHttpClient, ProviderHttpError
from backend.lib.providers.ia.client import ModelResponseError, OpenAiCompatibleClient
from backend.lib.providers.ia.generador import AiModelConfig
from backend.lib.providers.registro import ULTIMO_RECURSO, proveedores_ia, providers_for
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

# Clave: (data_dir, game_id, clave, fuente) para las sugerencias y (data_dir, game_id,
# __identity_batch__) para el bloque de identidad.
_cache: dict[tuple[str, ...], dict[str, object]] = {}
_cache_lock = threading.Lock()


# Campos que la IA puede proponer como último recurso, cuando ninguna fuente factual tuvo
# el dato (ADR-0026). Los mismos que completa la precarga de MS-DOS: título, año y formato
# nunca salen de una IA.
_IA_RESPALDO = frozenset({"developer", "publisher", "genre", "players"})
_ETIQUETAS_IA = {
    "developer": "Desarrollador",
    "publisher": "Editor",
    "genre": "Género",
    "players": "Jugadores",
}
# La identidad que respondió la IA, por juego: una sola consulta cubre todos los campos.
_identidad_ia: dict[tuple[str, str], tuple[dict[str, str], ProviderTrace, str]] = {}
# La traza de una fuente de último recurso que no se consultó porque el campo ya tenía
# candidato (ADR-0027). El modal la ofrece para consultarla igual.
NO_HIZO_FALTA = "no hizo falta"

_GUIA_KEYS = frozenset({"objetivo", "primerosPasos", "reglasEsenciales", "modo"})
_MODO_JUGADORES = {"alt": "por turnos", "sim": "a la vez"}


def _contexto_guia(game: StoredGame) -> str:
    """Datos de la ficha para que el modelo reconozca el juego de la guia.

    El titulo guardado suele ser el nombre del romset de MAME (`Arkanoidu`, la `u` es la
    version US) y un modelo no conoce ese nombre: sin esto responde DESCONOCIDO.
    """
    identity = game.identity
    datos = [
        f"desarrollador: {identity.developer}" if identity.developer else "",
        f"género: {identity.genre}" if identity.genre else "",
    ]
    jugadores = f"jugadores: {identity.players}" if identity.players else ""
    nplayers = game.cabinet.nplayers.lower()
    cuando = next((texto for clave, texto in _MODO_JUGADORES.items() if clave in nplayers), "")
    if jugadores:
        datos.append(f"{jugadores} ({cuando})" if cuando else jugadores)
    romset = Path(game.romRef).stem if game.romRef else ""
    if romset:
        datos.append(f"nombre del romset de MAME: {romset}")
    datos = [dato for dato in datos if dato]
    if not datos:
        return ""
    return (
        "Datos de la ficha: " + "; ".join(datos) + ". El título puede ser el nombre del "
        "romset y no el nombre comercial: usá estos datos para identificar el juego."
    )


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
        sin_memo: bool = False,
    ) -> dict[str, object]:
        """``sin_memo`` vuelve a consultar sin reiniciar el cortocircuito, que es lo que hace
        ``reintentar``: lo usa el completado, que no es un pedido puntual del usuario."""
        cache_key = (str(self.settings.data_dir), game_id, key, source or "")
        if not (reintentar or sin_memo):
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
            _contexto_guia(game) if key in _GUIA_KEYS else "",
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
        consultados = 0

        def consultar(provider: Proveedor) -> None:
            nonlocal responded, consultados
            consultados += 1
            try:
                result = provider.buscar(consulta)
            except ProviderHttpError as exc:
                if exc.retry_exhausted:
                    breaker.strike(provider.nombre)
                traces.append(ProviderTrace(provider.nombre, provider.tipo, str(exc)))
                return
            except Exception:
                log.exception("Provider %s failed unexpectedly", provider.nombre)
                traces.append(ProviderTrace(provider.nombre, provider.tipo, "excepción inesperada"))
                return
            candidates.extend(result.candidatos)
            traces.append(result.trace)
            if result.trace.estado == "ok":
                responded += 1

        corte = _primer_ultimo_recurso(providers)
        for provider in providers[:corte]:
            if cancel_event and cancel_event.is_set():
                break
            consultar(provider)
        # Sin ningún candidato factual para el campo, la IA (ADR-0026), antes que las fuentes
        # de último recurso (ADR-0027). No corre cuando el usuario reintenta una fuente puntual.
        if (
            source is None
            and key in _IA_RESPALDO
            and not _tiene_candidato(candidates, key)
            and not (cancel_event and cancel_event.is_set())
        ):
            de_ia, traza = self._respaldo_ia(game, system.name, (key,), cancel_event)
            if traza is not None:
                consultados += 1
                traces.append(traza)
                if de_ia:
                    responded += 1
            candidates.extend(de_ia)
        # Una fuente de último recurso solo si el campo sigue sin candidato; las que van después
        # (el buscador de imágenes), siempre.
        for provider in providers[corte:]:
            if cancel_event and cancel_event.is_set():
                break
            if provider.nombre in ULTIMO_RECURSO and _tiene_candidato(candidates, key):
                traces.append(ProviderTrace(provider.nombre, provider.tipo, NO_HIZO_FALTA))
                continue
            consultar(provider)
        payload: dict[str, object] = {
            "candidatos": [_candidate_out(candidate) for candidate in candidates],
            "respondieron": responded,
            "consultados": consultados,
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
        # Cada clave de identidad se pide a su propia cadena, que no tiene IA; el memo de la
        # ficha evita bajarla una vez por clave. Tres pasos: las fuentes de cada campo hasta la
        # primera de último recurso; la IA, con una sola consulta, para lo que ninguna tuvo
        # (ADR-0026); y el último recurso solo para lo que siga faltando (ADR-0027).
        cadenas = {
            key: providers_for(key, self.settings, cancel_event)
            for key in sorted(_SUGGESTABLE_IDENTITY_KEYS)
        }
        if reintentar:
            for providers in cadenas.values():
                for p in providers:
                    breaker.reset(p.nombre)
        candidates: list[Candidato] = []
        traces: dict[str, ProviderTrace] = {}
        consultados: set[str] = set()
        respondieron: set[str] = set()

        def consultar(key: str, providers: Sequence[Proveedor]) -> None:
            consulta = Consulta(
                game.id,
                key,
                game.identity.title,
                system.name,
                game.identity.year or None,
            )
            for provider in providers:
                if cancel_event and cancel_event.is_set():
                    break
                if breaker.is_open(provider.nombre):
                    continue
                if provider.nombre in ULTIMO_RECURSO and _tiene_candidato(candidates, key):
                    continue
                consultados.add(provider.nombre)
                try:
                    result = provider.buscar(consulta)
                except ProviderHttpError as exc:
                    if exc.retry_exhausted:
                        breaker.strike(provider.nombre)
                    traces[provider.nombre] = ProviderTrace(
                        provider.nombre, provider.tipo, str(exc)
                    )
                    log.warning("identity batch: provider %s failed: %s", provider.nombre, exc)
                    continue
                except Exception:
                    log.exception("Provider %s failed unexpectedly", provider.nombre)
                    traces[provider.nombre] = ProviderTrace(
                        provider.nombre, provider.tipo, "excepción inesperada"
                    )
                    continue
                candidates.extend(result.candidatos)
                traces.setdefault(provider.nombre, result.trace)
                if result.candidatos or result.trace.estado == "ok":
                    respondieron.add(provider.nombre)

        for key, providers in cadenas.items():
            consultar(key, providers[: _primer_ultimo_recurso(providers)])
        faltan = [
            key
            for key in sorted(_IA_RESPALDO & _SUGGESTABLE_IDENTITY_KEYS)
            if not _tiene_candidato(candidates, key)
        ]
        if faltan and not (cancel_event and cancel_event.is_set()):
            de_ia, traza = self._respaldo_ia(game, system.name, faltan, cancel_event)
            if traza is not None:
                consultados.add(traza.nombre)
                traces[traza.nombre] = traza
                if de_ia:
                    respondieron.add(traza.nombre)
            candidates.extend(de_ia)
        for key, providers in cadenas.items():
            consultar(key, providers[_primer_ultimo_recurso(providers) :])
        responded = len(respondieron)
        log.info("identity batch: %d candidates, %d responded", len(candidates), responded)
        payload: dict[str, object] = {
            "candidatos": [_candidate_out(c) for c in candidates],
            "respondieron": responded,
            "consultados": len(consultados),
            "fuentes": [_trace_out(t) for t in traces.values()],
        }
        with _cache_lock:
            _cache[cache_key] = payload
        return payload

    def _respaldo_ia(
        self,
        game: StoredGame,
        sistema: str,
        claves: Sequence[str],
        cancel_event: threading.Event | None,
    ) -> tuple[list[Candidato], ProviderTrace | None]:
        """Candidatos de la IA para las claves sin candidato factual; ``None`` si no hay IA
        configurada. La respuesta queda en memoria por juego: una consulta, todos los campos."""
        respuesta = self._identidad_ia(game, sistema, cancel_event)
        if respuesta is None:
            return [], None
        datos, traza, fuente = respuesta
        candidatos = [
            Candidato(
                id=f"ia-respaldo:{fuente}:{key}",
                key=key,
                kind="identity",
                nombre=f"{_ETIQUETAS_IA[key]} (IA)",
                fuente=fuente,
                clase="aplicable",
                value=valor,
                generado_por_ia=True,
                meta={"respaldo": "sin fuente factual"},
                trace=traza,
            )
            for key in claves
            if key in _IA_RESPALDO and (valor := str(datos.get(key) or "").strip())
        ]
        return candidatos, traza

    def _identidad_ia(
        self,
        game: StoredGame,
        sistema: str,
        cancel_event: threading.Event | None,
    ) -> tuple[dict[str, str], ProviderTrace, str] | None:
        memo = (str(self.settings.data_dir), game.id)
        with _cache_lock:
            guardada = _identidad_ia.get(memo)
        if guardada is not None:
            return guardada
        consulta = Consulta(
            game.id, "identidad", game.identity.title, sistema, game.identity.year or None
        )
        ultima: ProviderTrace | None = None
        for modelo in proveedores_ia(self.settings, cancel_event):
            if breaker.is_open(modelo.nombre) or (cancel_event and cancel_event.is_set()):
                continue
            try:
                result = modelo.buscar(consulta)
            except ProviderHttpError as exc:
                if exc.retry_exhausted:
                    breaker.strike(modelo.nombre)
                ultima = ProviderTrace(modelo.nombre, modelo.tipo, str(exc))
                continue
            except Exception:
                log.exception("Provider %s failed unexpectedly", modelo.nombre)
                ultima = ProviderTrace(modelo.nombre, modelo.tipo, "excepción inesperada")
                continue
            ultima = result.trace
            datos = _json_identidad(result.candidatos[0].value if result.candidatos else None)
            if datos:
                respuesta = (datos, result.trace, modelo.nombre)
                with _cache_lock:
                    _identidad_ia[memo] = respuesta
                return respuesta
        if ultima is None:
            return None
        return {}, ultima, ultima.nombre

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


def _tiene_candidato(candidatos: Sequence[Candidato], key: str) -> bool:
    return any(c.key == key and c.clase == "aplicable" for c in candidatos)


def _primer_ultimo_recurso(providers: Sequence[Proveedor]) -> int:
    """Dónde empieza el último recurso en la cadena (ADR-0027); sin ninguno, al final."""
    return next(
        (i for i, provider in enumerate(providers) if provider.nombre in ULTIMO_RECURSO),
        len(providers),
    )


def _json_identidad(valor: str | None) -> dict[str, str]:
    if not valor:
        return {}
    try:
        datos = json.loads(valor)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(datos, dict):
        return {}
    return {str(k): str(v) for k, v in datos.items() if v is not None}


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
