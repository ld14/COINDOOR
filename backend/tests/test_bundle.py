from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.bundle.seleccion import SeleccionItem, compute_seleccion
from backend.config import Settings


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "data")


def _base_game() -> dict[str, Any]:
    return {
        "id": "goldnaxe",
        "systemId": "arcade",
        "identity": {
            "title": "Golden Axe", "year": "1989", "developer": "Sega",
            "publisher": "Sega", "genre": "Beat em up", "players": "2", "format": "Arcade",
        },
        "images": {},
        "video": {},
        "texts": {},
        "review": {"status": "empty"},
        "cheats": {"status": "empty"},
        "accent": "empty",
        "accentValue": "",
        "accent2Value": "",
        "manuals": [],
        "romSource": "path",
        "romRef": "",
    }


def _by_key(items: list[SeleccionItem], key: str) -> SeleccionItem:
    return next(item for item in items if item.key == key)


def test_identidad_siempre_disponible_y_obligatoria(tmp_path: Path) -> None:
    items = compute_seleccion(_settings(tmp_path), _base_game())
    identidad = _by_key(items, "identidad")
    assert identidad.required is True
    assert identidad.disponible is True
    assert identidad.bytes > 0


def test_obligatorios_del_contrato(tmp_path: Path) -> None:
    items = compute_seleccion(_settings(tmp_path), _base_game())
    required_keys = {item.key for item in items if item.required}
    assert required_keys == {"identidad", "caratula", "poster", "sinopsis", "accent", "juego"}


def test_imagen_vacia_no_disponible(tmp_path: Path) -> None:
    items = compute_seleccion(_settings(tmp_path), _base_game())
    assert _by_key(items, "marquesina").disponible is False
    assert _by_key(items, "marquesina").bytes == 0


def test_imagen_cargada_pesa_el_archivo_real(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    media_path = settings.media_dir / "arcade" / "goldnaxe" / "caratula.jpg"
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_bytes(b"\xff\xd8\xff" * 100)

    game = _base_game()
    game["images"] = {"caratula": {"status": "manual", "url": "/media/arcade/goldnaxe/caratula.jpg"}}  # noqa: E501

    items = compute_seleccion(settings, game)
    caratula = _by_key(items, "caratula")
    assert caratula.disponible is True
    assert caratula.bytes == 300


def test_sinopsis_pesa_el_texto(tmp_path: Path) -> None:
    game = _base_game()
    game["texts"] = {"sinopsis": {"status": "manual", "value": "Hola mundo"}}
    items = compute_seleccion(_settings(tmp_path), game)
    sinopsis = _by_key(items, "sinopsis")
    assert sinopsis.disponible is True
    assert sinopsis.bytes == len(b"Hola mundo")


def test_review_null_no_disponible_pero_no_falla(tmp_path: Path) -> None:
    items = compute_seleccion(_settings(tmp_path), _base_game())
    review = _by_key(items, "review")
    assert review.required is False
    assert review.disponible is False


def test_manual_disponible_sin_pesar_hasta_que_exista_endpoint(tmp_path: Path) -> None:
    game = _base_game()
    game["manuals"] = [{"id": "m1", "fileName": "manual.pdf", "status": "processed", "pages": 6}]
    items = compute_seleccion(_settings(tmp_path), game)
    manual = _by_key(items, "manual")
    assert manual.disponible is True
    assert manual.bytes == 0


def test_juego_disponible_si_romref_existe_en_disco(tmp_path: Path) -> None:
    rom = tmp_path / "roms" / "goldnaxe.zip"
    rom.parent.mkdir(parents=True, exist_ok=True)
    rom.write_bytes(b"0" * 1024)

    game = _base_game()
    game["romRef"] = str(rom)
    items = compute_seleccion(_settings(tmp_path), game)
    juego = _by_key(items, "juego")
    assert juego.disponible is True
    assert juego.bytes == 1024


def test_juego_no_disponible_si_romref_no_existe(tmp_path: Path) -> None:
    game = _base_game()
    game["romRef"] = "sf2.zip"
    items = compute_seleccion(_settings(tmp_path), game)
    assert _by_key(items, "juego").disponible is False


def test_accent2_vacio_no_disponible(tmp_path: Path) -> None:
    items = compute_seleccion(_settings(tmp_path), _base_game())
    assert _by_key(items, "accent2").disponible is False
    assert _by_key(items, "accent2").required is False
