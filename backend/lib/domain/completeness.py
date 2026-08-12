from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

GameStatus = Literal["ready", "incomplete", "error"]

ROOT = Path(__file__).resolve().parents[3]
FIELDDEFS_PATH = ROOT / "frontend" / "src" / "lib" / "domain" / "fielddefs.json"


def _fielddefs() -> Mapping[str, Any]:
    with FIELDDEFS_PATH.open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, Mapping):
        raise TypeError("fielddefs.json must contain an object")
    return value


def _status(container: Mapping[str, Any], key: str) -> str:
    value = container.get(key)
    if isinstance(value, Mapping):
        status = value.get("status")
        return status if isinstance(status, str) else "empty"
    return "empty"


def missing_required(game: Mapping[str, Any]) -> list[str]:
    fielddefs = _fielddefs()
    missing: list[str] = []
    identity = game.get("identity", {})
    images = game.get("images", {})
    videos = game.get("video", {})
    texts = game.get("texts", {})

    if not isinstance(identity, Mapping):
        identity = {}
    if not isinstance(images, Mapping):
        images = {}
    if not isinstance(videos, Mapping):
        videos = {}
    if not isinstance(texts, Mapping):
        texts = {}

    for field in fielddefs["identity"]:
        if field["required"] and not str(identity.get(field["key"], "")).strip():
            missing.append(f"Identidad: {field['label']}")

    for field in fielddefs["images"]:
        if field["required"] and _status(images, field["key"]) == "empty":
            missing.append(str(field["label"]))

    for field in fielddefs["videos"]:
        if field["required"] and _status(videos, field["key"]) == "empty":
            missing.append(str(field["label"]))

    for field in fielddefs["texts"]:
        if field["required"] and _status(texts, field["key"]) == "empty":
            missing.append(str(field["label"]))

    for field in fielddefs["rich"]:
        if field["key"] == "accent" and field["required"] and game.get("accent") == "empty":
            missing.append(f"Presentación: {field['label']}")

    return missing


def compute_game_status(game: Mapping[str, Any]) -> GameStatus:
    errors = game.get("errors", [])
    if isinstance(errors, list) and errors:
        return "error"
    if missing_required(game):
        return "incomplete"
    return "ready"
