from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.lib.domain import plataformas
from backend.lib.domain.plataformas import nombre_en, plataforma, sitios


def test_msdos_resuelve_su_nombre_en_mobygames_y_launchbox() -> None:
    assert nombre_en("msdos", "mobygames") == "DOS"
    assert nombre_en("msdos", "launchbox") == "MS-DOS"


def test_arcade_no_tiene_equivalencia_en_mobygames() -> None:
    assert plataforma("arcade") is not None
    assert nombre_en("arcade", "mobygames") is None
    assert nombre_en("arcade", "launchbox") == "Arcade"


def test_busca_por_alias_sin_distinguir_mayusculas() -> None:
    assert nombre_en("MS-DOS", "mobygames") == "DOS"
    assert nombre_en("  MAME ", "launchbox") == "Arcade"
    assert nombre_en("Arcade", "launchbox") == "Arcade"


def test_un_sistema_fuera_del_catalogo_no_tiene_fila() -> None:
    assert plataforma("atari 2600") is None
    assert nombre_en("atari 2600", "mobygames") is None


def test_toda_fila_declara_todos_los_sitios() -> None:
    for sitio in sitios():
        for nombre in ("msdos", "arcade", "nes", "mega drive", "game boy color"):
            fila = plataforma(nombre)
            assert fila is not None
            assert sitio in fila.sitios


def test_una_fila_que_omite_un_sitio_falla_la_carga(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roto = tmp_path / "plataformas.json"
    roto.write_text(
        json.dumps(
            {
                "sitios": ["mobygames", "launchbox"],
                "plataformas": [{"name": "msdos", "alias": [], "mobygames": "DOS"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(plataformas, "PLATAFORMAS_PATH", roto)
    plataformas._cargar.cache_clear()
    try:
        with pytest.raises(ValueError, match="launchbox"):
            plataformas.sitios()
    finally:
        monkeypatch.undo()
        plataformas._cargar.cache_clear()


def test_un_nombre_repetido_falla_la_carga(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roto = tmp_path / "plataformas.json"
    roto.write_text(
        json.dumps(
            {
                "sitios": ["mobygames"],
                "plataformas": [
                    {"name": "msdos", "alias": ["dos"], "mobygames": "DOS"},
                    {"name": "dos", "alias": [], "mobygames": "DOS"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(plataformas, "PLATAFORMAS_PATH", roto)
    plataformas._cargar.cache_clear()
    try:
        with pytest.raises(ValueError, match="repetido"):
            plataformas.sitios()
    finally:
        monkeypatch.undo()
        plataformas._cargar.cache_clear()
