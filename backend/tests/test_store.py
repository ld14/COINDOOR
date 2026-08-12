from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from pydantic import BaseModel

from backend.api.errors import StorageError
from backend.store.archivo import escribir_binario, escribir_json, leer_json


class Doc(BaseModel):
    version: int = 1
    name: str


def test_write_and_read_json(tmp_path: Path) -> None:
    path = tmp_path / "doc.json"
    escribir_json(path, Doc(name="ok"))
    assert leer_json(path, Doc).name == "ok"


def test_corrupt_json_names_file(tmp_path: Path) -> None:
    path = tmp_path / "doc.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(StorageError) as exc:
        leer_json(path, Doc)
    assert str(path) in str(exc.value)


def test_status_not_saved(tmp_path: Path) -> None:
    path = tmp_path / "doc.json"
    escribir_json(path, {"version": 1, "name": "ok", "status": "ready"})
    assert "status" not in json.loads(path.read_text(encoding="utf-8"))


def test_replace_failure_keeps_previous_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: E501
    path = tmp_path / "doc.json"
    escribir_json(path, Doc(name="old"))

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("boom")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(StorageError):
        escribir_json(path, Doc(name="new"))
    assert leer_json(path, Doc).name == "old"


def test_write_binary_creates_parents_and_content(tmp_path: Path) -> None:
    path = tmp_path / "media" / "arcade" / "goldnaxe" / "caratula.jpg"
    escribir_binario(path, b"\xff\xd8\xff")
    assert path.read_bytes() == b"\xff\xd8\xff"


def test_write_binary_replace_failure_keeps_previous_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: E501
    path = tmp_path / "caratula.jpg"
    escribir_binario(path, b"old")

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("boom")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(StorageError):
        escribir_binario(path, b"new")
    assert path.read_bytes() == b"old"
