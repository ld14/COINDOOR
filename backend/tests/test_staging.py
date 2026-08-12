from __future__ import annotations

import filecmp
import json
import zipfile
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
    resultado = build_staging(settings, _game(settings), incluir=set())
    assert (resultado.root / "media" / "boxFront.jpg").exists()
    assert (resultado.root / "media" / "poster.jpg").exists()


def test_opcional_no_incluido_no_se_copia(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    resultado = build_staging(settings, _game(settings), incluir=set())
    assert not (resultado.root / "media" / "marquee.png").exists()


def test_opcional_incluido_se_copia_con_nombre_de_contrato(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    resultado = build_staging(settings, _game(settings), incluir={"marquesina"})
    assert (resultado.root / "media" / "marquee.png").exists()


def test_captura_se_traduce_a_screenshot(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    game = _game(settings)
    game["images"]["captura"] = {"status": "manual", "url": _write_media(settings, "captura.jpg", b"cap" * 10)}  # noqa: E501
    resultado = build_staging(settings, game, incluir={"captura"})
    assert (resultado.root / "media" / "screenshot.jpg").exists()


def test_data_json_escrito_en_media(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    resultado = build_staging(settings, _game(settings), incluir=set())
    data = json.loads((resultado.root / "media" / "data.json").read_text(encoding="utf-8"))
    assert data["accent"] == "#d4a017"
    assert "mags" not in data


def test_synopsis_json_con_summary(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    resultado = build_staging(settings, _game(settings), incluir=set())
    synopsis = json.loads((resultado.root / "_synopsis.json").read_text(encoding="utf-8"))
    assert synopsis == {"summary": "Un juego de hachas."}


def test_manual_nunca_se_incluye_sin_pipeline_real(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    game = _game(settings)
    game["manuals"] = [{"id": "m1", "fileName": "manual.pdf", "status": "processed", "pages": 6}]
    resultado = build_staging(settings, game, incluir={"manual"})
    assert not (resultado.root / "media" / "_manual").exists()
    data = json.loads((resultado.root / "media" / "data.json").read_text(encoding="utf-8"))
    assert "manual" not in data
    assert "manual" not in resultado.incluye


def test_juego_se_copia_solo_si_incluido_y_romref_existe(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    rom = tmp_path / "roms" / "goldnaxe.zip"
    rom.parent.mkdir(parents=True, exist_ok=True)
    rom.write_bytes(b"rom-bytes")

    game = _game(settings)
    game["romRef"] = str(rom)

    sin_incluir = build_staging(settings, game, incluir=set())
    assert not (sin_incluir.root / "juego").exists()
    assert sin_incluir.rom_archivo is None

    con_incluir = build_staging(settings, game, incluir={"juego"})
    assert (con_incluir.root / "juego" / "goldnaxe.zip").read_bytes() == b"rom-bytes"
    assert con_incluir.rom_archivo == "juego/goldnaxe.zip"
    assert con_incluir.rom_tratamiento == "copiar"


def test_juego_carpeta_ms_dos_se_comprime_y_tratamiento_es_descomprimir(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    carpeta = tmp_path / "roms" / "dot"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "DOT.EXE").write_bytes(b"exe-bytes")
    (carpeta / "DATA.DAT").write_bytes(b"data-bytes")

    game = _game(settings)
    game["romRef"] = str(carpeta)

    resultado = build_staging(settings, game, incluir={"juego"})
    assert resultado.rom_tratamiento == "descomprimir"
    assert resultado.rom_archivo == "juego/dot.zip"

    archivo_zip = resultado.root / "juego" / "dot.zip"
    assert archivo_zip.exists()
    with zipfile.ZipFile(archivo_zip) as archivo:
        assert set(archivo.namelist()) == {"DOT.EXE", "DATA.DAT"}


def test_juego_pedido_pero_romref_inexistente_se_descarta_de_incluye(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    game = _game(settings)
    game["romRef"] = "no-existe.zip"
    resultado = build_staging(settings, game, incluir={"juego"})
    assert "juego" not in resultado.incluye
    assert resultado.rom_archivo is None


def test_dos_corridas_producen_arboles_equivalentes(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    game = _game(settings)
    incluir = {"marquesina"}

    primero = build_staging(settings, game, incluir)
    segundo = build_staging(settings, game, incluir)

    comparacion = filecmp.dircmp(primero.root, segundo.root)
    assert not comparacion.left_only
    assert not comparacion.right_only
    assert not comparacion.diff_files
