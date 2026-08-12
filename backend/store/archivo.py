from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from backend.api.errors import StorageError
from backend.store.migracion import migrate

ModelT = TypeVar("ModelT", bound=BaseModel)


def leer_json[ModelT: BaseModel](path: Path, model: type[ModelT]) -> ModelT:
    try:
        with path.open(encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as exc:
        raise StorageError(f"JSON inválido en {path}") from exc
    except OSError as exc:
        raise StorageError(f"No se pudo leer {path}") from exc

    if not isinstance(payload, dict):
        raise StorageError(f"JSON inválido en {path}: se esperaba un objeto")

    try:
        migrated = migrate(payload)
        return model.model_validate(migrated)
    except (ValidationError, ValueError) as exc:
        raise StorageError(f"Datos inválidos en {path}") from exc


def safe_id(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "juego"


def media_path(media_dir: Path, url: str) -> Path | None:
    prefix = "/media/"
    if not url.startswith(prefix):
        return None
    return media_dir / Path(url[len(prefix) :])


def escribir_binario(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp_path, path)
        _fsync_dir(path.parent)
    except OSError as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        finally:
            raise StorageError(f"No se pudo escribir {path}") from exc


def escribir_json(path: Path, payload: BaseModel | dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode="json", exclude={"status"}) if isinstance(payload, BaseModel) else dict(payload)  # noqa: E501
    data.pop("status", None)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2, sort_keys=True)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp_path, path)
        _fsync_dir(path.parent)
    except OSError as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        finally:
            raise StorageError(f"No se pudo escribir {path}") from exc


def _fsync_dir(path: Path) -> None:
    if hasattr(os, "O_DIRECTORY"):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
