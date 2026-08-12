from __future__ import annotations

import filecmp
import json
from pathlib import Path
from typing import Any

from backend.bundle.staging import build_staging
from backend.config import Settings


def _settings(tmp_path: Path) -> Settings:
    settings = Settings(data_dir=tmp_path / "data")
    settings.tmp_dir.mkdir(parents=True, exist_ok=True)
    return settings


def _write_media(settings: Settings, name: str, content: bytes) -> str:
    path = settings.media_dir / "arcade" / "goldnaxe" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return f"/media/arcade/goldnaxe/{name}"


def _game(settings: Settings) -> dict[str, Any]:
    return {
        "id": "goldnaxe",
        "systemId": "arcade",
        "identity": {
            "title": "Golden Axe", "year": "1989", "developer": "Sega",
            "publisher": "Sega", "genre": "Beat em up", "players": "2", "format": "Arcade",
        },
        "images": {
            "caratula": {"status": "manual", "url": _write_media(settings, "caratula.jpg", b"box" * 10)},  # noqa: E501
            "poster": {"status": "manual", "url": _write_media(settings, "poster.jpg", b"pos" * 10)},  # noqa: E501
            "marquesina": {"status": "manual", "url": _write_media(settings, "marquesina.png", b"mq" * 5)},  # noqa: E501
            "logo": {"status": "empty"},
            "captura": {"status": "empty"},
        },
        "video": {"video": {"status": "empty"}},
        "texts": {"sinopsis": {"status": "manual", "value": "Un juego de hachas."}},
        "review": {"status": "empty"},
        "cheats": {"status": "empty"},
        "accent": "manual",
        "accentValue": "#d4a017",
        "accent2Value": "",
        "manuals": [],
        "romSource": "path",
        "romRef": "",
    }


def test_obligatorios_se_copian_con_nombre_de_contrato(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    root = build_staging(settings, _game(settings), incluir=set())
    assert (root / "media" / "boxFront.jpg").exists()
    assert (root / "media" / "poster.jpg").exists()


def test_opcional_no_incluido_no_se_copia(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    root = build_staging(settings, _game(settings), incluir=set())
    assert not (root / "media" / "marquee.png").exists()


def test_opcional_incluido_se_copia_con_nombre_de_contrato(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    root = build_staging(settings, _game(settings), incluir={"marquesina"})
    assert (root / "media" / "marquee.png").exists()


def test_captura_se_traduce_a_screenshot(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    game = _game(settings)
    game["images"]["captura"] = {"status": "manual", "url": _write_media(settings, "captura.jpg", b"cap" * 10)}  # noqa: E501
    root = build_staging(settings, game, incluir={"captura"})
    assert (root / "media" / "screenshot.jpg").exists()


def test_data_json_escrito_en_media(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    root = build_staging(settings, _game(settings), incluir=set())
    data = json.loads((root / "media" / "data.json").read_text(encoding="utf-8"))
    assert data["accent"] == "#d4a017"
    assert "mags" not in data


def test_synopsis_json_con_summary(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    root = build_staging(settings, _game(settings), incluir=set())
    synopsis = json.loads((root / "_synopsis.json").read_text(encoding="utf-8"))
    assert synopsis == {"summary": "Un juego de hachas."}


def test_manual_nunca_se_incluye_sin_pipeline_real(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    game = _game(settings)
    game["manuals"] = [{"id": "m1", "fileName": "manual.pdf", "status": "processed", "pages": 6}]
    root = build_staging(settings, game, incluir={"manual"})
    assert not (root / "media" / "_manual").exists()
    data = json.loads((root / "media" / "data.json").read_text(encoding="utf-8"))
    assert "manual" not in data


def test_juego_se_copia_solo_si_incluido_y_romref_existe(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    rom = tmp_path / "roms" / "goldnaxe.zip"
    rom.parent.mkdir(parents=True, exist_ok=True)
    rom.write_bytes(b"rom-bytes")

    game = _game(settings)
    game["romRef"] = str(rom)

    sin_incluir = build_staging(settings, game, incluir=set())
    assert not (sin_incluir / "juego").exists()

    con_incluir = build_staging(settings, game, incluir={"juego"})
    assert (con_incluir / "juego" / "goldnaxe.zip").read_bytes() == b"rom-bytes"


def test_dos_corridas_producen_arboles_equivalentes(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    game = _game(settings)
    incluir = {"marquesina"}

    primero = build_staging(settings, game, incluir)
    segundo = build_staging(settings, game, incluir)

    comparacion = filecmp.dircmp(primero, segundo)
    assert not comparacion.left_only
    assert not comparacion.right_only
    assert not comparacion.diff_files
