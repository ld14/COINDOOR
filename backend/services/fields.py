from __future__ import annotations

import json
from pathlib import Path

import httpx

from backend.api.errors import BadRequest, NotFound
from backend.api.schemas import CheatsValue, FieldProvenance, GameOut, ReviewValue
from backend.config import Settings
from backend.lib.domain.fielddefs import identity_keys, image_keys, rich_keys, text_keys, video_keys
from backend.lib.providers.orquestador import cached_candidate, cached_identity_candidate
from backend.store.archivo import escribir_binario, safe_id
from backend.store.juegos import GamesStore, to_out

RICH_SUGGESTION_KEYS = frozenset({"review", "cheats"})


class FieldsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = GamesStore(settings.games_dir)
        self.valid_keys = identity_keys() | image_keys() | video_keys() | text_keys() | rich_keys()

    def set_value(self, game_id: str, key: str, value: str) -> GameOut:
        self._validate_key(key)
        return to_out(self.store.set_text_field(game_id, key, value))

    def delete(self, game_id: str, key: str) -> GameOut:
        self._validate_key(key)
        return to_out(self.store.delete_field(game_id, key))

    def set_review(self, game_id: str, payload: ReviewValue) -> GameOut:
        return to_out(self.store.set_review_field(game_id, payload.score, payload.cats))

    def set_cheats(self, game_id: str, payload: CheatsValue) -> GameOut:
        groups = [group.model_dump(mode="json") for group in payload.groups]
        return to_out(self.store.set_cheats_field(game_id, groups))

    def set_magazine(self, game_id: str, magazine: str, magazine_name: str) -> GameOut:
        return to_out(self.store.set_magazine(game_id, magazine, magazine_name))

    def apply_suggestion(self, game_id: str, key: str, candidate_id: str) -> GameOut:
        self._validate_key(key)
        candidate = cached_candidate(self.settings, game_id, key, candidate_id)
        if candidate is None and key in identity_keys():
            candidate = cached_identity_candidate(self.settings, game_id, candidate_id)
        if candidate is None:
            raise NotFound(f"Candidato no encontrado: {candidate_id}")
        if candidate.get("clase") != "aplicable":
            raise BadRequest("El candidato es referencia y no se puede aplicar")
        provenance = self._provenance(candidate)
        if candidate.get("kind") == "identity":
            value = str(candidate.get("value") or "")
            if not value:
                raise BadRequest("Candidato sin valor")
            return to_out(self.store.apply_identity_suggestion(game_id, key, value, provenance))
        if candidate.get("kind") == "media":
            media_url = str(candidate.get("mediaUrl") or "")
            preview_url = str(candidate.get("previewUrl") or "")
            if not media_url.startswith(("https://", "http://")):
                raise BadRequest("URL de media inválida")
            try:
                url = self._download_candidate_media(game_id, key, media_url)
            except BadRequest:
                if preview_url.startswith(("https://", "http://")) and preview_url != media_url:
                    url = self._download_candidate_media(game_id, key, preview_url)
                else:
                    raise
            return to_out(self.store.apply_media_suggestion(game_id, key, url, provenance))
        if candidate.get("kind") == "text":
            value = str(candidate.get("value") or "")
            if not value:
                raise BadRequest("Candidato sin valor")
            if key in RICH_SUGGESTION_KEYS:
                payload = self._parse_rich_payload(value)
                return to_out(self.store.apply_rich_suggestion(game_id, key, payload, provenance))
            return to_out(self.store.apply_text_suggestion(game_id, key, value, provenance))
        raise BadRequest("Tipo de candidato no soportado")

    def _parse_rich_payload(self, value: str) -> dict[str, object]:
        try:
            payload = json.loads(value)
        except json.JSONDecodeError as exc:
            raise BadRequest("Candidato con JSON inválido") from exc
        if not isinstance(payload, dict):
            raise BadRequest("Candidato con forma inválida")
        return payload

    def _download_candidate_media(self, game_id: str, key: str, media_url: str) -> str:
        game = self.store.get(game_id)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/*,*/*",
            "Referer": "https://duckduckgo.com/",
        }
        response = httpx.get(media_url, timeout=30.0, follow_redirects=True, headers=headers)
        if response.status_code >= 400:
            raise BadRequest(f"El sitio devolvió {response.status_code}")
        suffix = Path(httpx.URL(media_url).path).suffix.lower() or ".jpg"
        system_dir = safe_id(game.systemId)
        game_dir = safe_id(game.id)
        path = self.settings.media_dir / system_dir / game_dir / f"{key}{suffix}"
        escribir_binario(path, response.content)
        return f"/media/{system_dir}/{game_dir}/{key}{suffix}"

    def _provenance(self, candidate: dict[str, object]) -> FieldProvenance:
        trace = candidate.get("trace") if isinstance(candidate.get("trace"), dict) else {}
        urls = trace.get("urlsProcesadas", []) if isinstance(trace, dict) else []
        processed = [
            str(item.get("url"))
            for item in urls
            if isinstance(item, dict) and item.get("url")
        ]
        raw_meta = candidate.get("meta")
        meta = raw_meta if isinstance(raw_meta, dict) else {}
        return FieldProvenance(
            source=str(candidate.get("fuente") or ""),
            originUrl=str(candidate.get("origenUrl") or "") or None,
            sourceId=str(meta.get("source_id") or "") or None,
            sourceType=str(trace.get("tipo") or "api") if isinstance(trace, dict) else "api",
            processedUrls=processed,
        )

    def _validate_key(self, key: str) -> None:
        if key not in self.valid_keys:
            raise BadRequest(f"Campo inválido: {key}")
