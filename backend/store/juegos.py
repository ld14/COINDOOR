from __future__ import annotations

import threading
from pathlib import Path

from backend.api.errors import NotFound
from backend.api.schemas import CreateGame, GameOut, PatchGame, StoredGame
from backend.store.archivo import escribir_json, leer_json


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
            id=_safe_id(payload.identity.title),
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
        data.update({key: value for key, value in patch.items() if value is not None})
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
        if key in data["images"]:
            data["images"][key] = {"status": "empty"}
        elif key in data["video"]:
            data["video"][key] = {"status": "empty"}
        elif key in data["texts"]:
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
        if key not in data["texts"]:
            raise NotFound(f"Campo no encontrado: {key}")
        data["texts"][key] = {"status": "manual", "value": value}
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
        return self.root / _safe_id(game.systemId) / _safe_id(game.id) / "game.json"


def _safe_id(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "juego"


def to_out(game: StoredGame) -> GameOut:
    return GameOut.from_stored(game)
