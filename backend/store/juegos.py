from __future__ import annotations

import threading
from pathlib import Path

from backend.api.errors import NotFound
from backend.api.schemas import (
    CreateGame,
    FieldProvenance,
    GameManual,
    GameOut,
    MagazineAppearance,
    PatchGame,
    StoredGame,
)
from backend.lib.domain.fielddefs import identity_keys, image_keys, text_keys, video_keys
from backend.store.archivo import escribir_json, leer_json, safe_id


class GamesStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.Lock] = {}
        self._index: dict[str, StoredGame] = {}
        self.rebuild_index()

    def rebuild_index(self) -> None:
        self._index = {}
        for path in self.root.glob("*/*/game.json"):
            game = leer_json(path, StoredGame)
            self._index[game.id] = game

    def list(self) -> list[StoredGame]:
        return list(self._index.values())

    def get(self, game_id: str) -> StoredGame:
        game = self._index.get(game_id)
        if game is None:
            raise NotFound(f"Juego no encontrado: {game_id}")
        return game

    def create(self, payload: CreateGame) -> StoredGame:
        game = StoredGame(
            id=safe_id(payload.identity.title),
            systemId=payload.systemId,
            identity=payload.identity,
            romSource=payload.romSource,
            romRef=payload.romRef,
        )
        self.save(game)
        return game

    def patch(self, game_id: str, payload: PatchGame) -> StoredGame:
        current = self.get(game_id)
        data = current.model_dump()
        patch = payload.model_dump(exclude_unset=True)
        for key, value in patch.items():
            if value is None:
                continue
            if key == "identity" and isinstance(value, dict) and isinstance(data.get(key), dict):
                data[key].update(value)
            else:
                data[key] = value
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def save(self, game: StoredGame) -> None:
        lock = self._lock(game.systemId)
        with lock:
            path = self._path(game)
            escribir_json(path, game)
            self._index[game.id] = game

    def delete_field(self, game_id: str, key: str) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        if key in image_keys():
            data["images"][key] = {"status": "empty"}
        elif key in video_keys():
            data["video"][key] = {"status": "empty"}
        elif key in text_keys():
            data["texts"][key] = {"status": "empty", "value": ""}
        elif key == "accent":
            data["accent"] = "empty"
            data["accentValue"] = ""
        elif key == "accent2":
            data["accent2Value"] = ""
        else:
            raise NotFound(f"Campo no encontrado: {key}")
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def set_text_field(self, game_id: str, key: str, value: str) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        if key not in text_keys():
            raise NotFound(f"Campo no encontrado: {key}")
        data["texts"][key] = {"status": "manual", "value": value}
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def set_review_field(
        self,
        game_id: str,
        score: int | None,
        cats: dict[str, int],
    ) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        data["review"] = {"status": "manual", "score": score, "cats": cats}
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def set_cheats_field(self, game_id: str, groups: list[dict[str, object]]) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        data["cheats"] = {"status": "manual", "groups": groups}
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def apply_identity_suggestion(
        self,
        game_id: str,
        key: str,
        value: str,
        provenance: FieldProvenance,
    ) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        if key not in identity_keys():
            raise NotFound(f"Campo no encontrado: {key}")
        data["identity"][key] = value
        data["identitySource"] = _identity_source(provenance.source)
        data["provenance"][key] = provenance.model_dump(mode="json")
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def apply_text_suggestion(
        self,
        game_id: str,
        key: str,
        value: str,
        provenance: FieldProvenance,
    ) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        if key not in text_keys():
            raise NotFound(f"Campo no encontrado: {key}")
        data["texts"][key] = {"status": "suggested", "value": value, "source": provenance.source}
        data["provenance"][key] = provenance.model_dump(mode="json")
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def apply_rich_suggestion(
        self,
        game_id: str,
        key: str,
        payload: dict[str, object],
        provenance: FieldProvenance,
    ) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        if key not in {"review", "cheats"}:
            raise NotFound(f"Campo no encontrado: {key}")
        data[key] = {"status": "suggested", "source": provenance.source, **payload}
        data["provenance"][key] = provenance.model_dump(mode="json")
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def set_media_field(self, game_id: str, key: str, url: str) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        if key in image_keys():
            data["images"][key] = {"status": "manual", "url": url}
        elif key in video_keys():
            data["video"][key] = {"status": "manual", "url": url}
        else:
            raise NotFound(f"Campo no encontrado: {key}")
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def set_rom_ref(self, game_id: str, rom_ref: str) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        data["romRef"] = rom_ref
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def add_manual(self, game_id: str, manual: GameManual) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        data["manuals"].append(manual.model_dump(mode="json"))
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def remove_manual(self, game_id: str, manual_id: str) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        data["manuals"] = [m for m in data["manuals"] if m.get("id") != manual_id]
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def set_magazine(self, game_id: str, magazine: str, magazine_name: str) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        data["magazine"] = magazine
        data["magazineName"] = magazine_name
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def add_magazine_appearance(self, game_id: str, appearance: MagazineAppearance) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        data["magazineAppearances"].append(appearance.model_dump(mode="json"))
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def remove_magazine_appearance(self, game_id: str, appearance_id: str) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        data["magazineAppearances"] = [
            a for a in data["magazineAppearances"] if a.get("id") != appearance_id
        ]
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def apply_media_suggestion(
        self,
        game_id: str,
        key: str,
        url: str,
        provenance: FieldProvenance | None,
    ) -> StoredGame:
        game = self.get(game_id)
        data = game.model_dump()
        media = {
            "status": "suggested",
            "url": url,
            "source": provenance.source if provenance else None,
        }
        if key in image_keys():
            data["images"][key] = media
        elif key in video_keys():
            data["video"][key] = media
        else:
            raise NotFound(f"Campo no encontrado: {key}")
        if provenance:
            data["provenance"][key] = provenance.model_dump(mode="json")
        updated = StoredGame.model_validate(data)
        self.save(updated)
        return updated

    def _lock(self, system_id: str) -> threading.Lock:
        lock = self._locks.get(system_id)
        if lock is None:
            lock = threading.Lock()
            self._locks[system_id] = lock
        return lock

    def _path(self, game: StoredGame) -> Path:
        return self.root / safe_id(game.systemId) / safe_id(game.id) / "game.json"


def _identity_source(source: str) -> str:
    if source == "MAME":
        return "mame"
    if source == "ScreenScraper":
        return "screenscraper"
    return "manual"


def to_out(game: StoredGame) -> GameOut:
    data = game.model_dump()
    data.setdefault("images", {})
    data.setdefault("video", {})
    data.setdefault("texts", {})
    for key in image_keys():
        data["images"].setdefault(key, {"status": "empty"})
    for key in video_keys():
        data["video"].setdefault(key, {"status": "empty"})
    for key in text_keys():
        data["texts"].setdefault(key, {"status": "empty", "value": ""})
    return GameOut.from_stored(StoredGame.model_validate(data))
