from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.schemas import CreateGame, Identity
from backend.config import Settings, set_settings
from backend.lib.domain.descubrimiento import titulo_propuesto
from backend.main import create_app
from backend.services.descubrimiento import _ultimo_segmento
from backend.store.juegos import GamesStore


def client(tmp_path: Path) -> TestClient:
    settings = Settings(data_dir=tmp_path / "data")
    set_settings(settings)
    return TestClient(create_app(settings), headers={"host": "127.0.0.1:8765"})


def candidatos(api: TestClient, system_id: str = "") -> list[dict[str, object]]:
    suffix = f"?systemId={system_id}" if system_id else ""
    response = api.get(f"/api/roms/candidates{suffix}")
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("sf2", "Sf2"),
        ("out-of-this-world", "Out Of This World"),
        ("super_mario_bros", "Super Mario Bros"),
        ("Street Fighter II (World)", "Street Fighter II"),
        ("Contra (USA) [!]", "Contra"),
        ("(USA)", "(USA)"),
    ],
)
def test_titulo_propuesto(nombre: str, esperado: str) -> None:
    assert titulo_propuesto(nombre) == esperado


def test_candidatos_sin_carpeta_devuelve_lista_vacia(tmp_path: Path) -> None:
    assert candidatos(client(tmp_path)) == []


def test_candidatos_lista_archivos_y_carpetas_sueltas(tmp_path: Path) -> None:
    api = client(tmp_path)
    juegos = tmp_path / "data" / "juegos"
    (juegos / "mame").mkdir(parents=True)
    (juegos / "mame" / "sf2.zip").write_bytes(b"rom")
    (juegos / "nes").mkdir(parents=True)
    (juegos / "nes" / "Super Mario Bros").mkdir()
    (juegos / "nes" / "Super Mario Bros" / "smb.nes").write_bytes(b"rom")

    items = candidatos(api)
    por_id = {item["id"]: item for item in items}
    assert set(por_id) == {"sf2", "super-mario-bros"}

    archivo = por_id["sf2"]
    assert archivo["systemId"] == "mame"
    assert archivo["kind"] == "file"
    assert archivo["file_format"] == "zip"
    assert archivo["tratamiento"] == "copiar"
    assert archivo["title"] == "Sf2"
    assert Path(archivo["path"]) == (juegos / "mame" / "sf2.zip").resolve()
    assert archivo["sizeBytes"] == 3

    carpeta = por_id["super-mario-bros"]
    assert carpeta["kind"] == "dir"
    assert carpeta["file_format"] == ""
    assert carpeta["tratamiento"] == "descomprimir"
    assert carpeta["sizeBytes"] == 3


def crear_ficha(api: TestClient, tmp_path: Path, titulo: str) -> str:
    """Alta real por la API. `romRef` tiene que existir en disco: la valida el servicio."""
    rom = tmp_path / "roms" / f"{titulo}.zip"
    rom.parent.mkdir(parents=True, exist_ok=True)
    rom.write_bytes(b"rom")
    api.post(
        "/api/systems",
        json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/bin/mame"},
    )
    response = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "path",
            "romRef": str(rom.resolve()),
            "identity": {
                "title": titulo, "year": "1991", "developer": "", "publisher": "",
                "genre": "", "players": "", "format": "",
            },
        },
    )
    assert response.status_code == 200, response.text
    return str(response.json()["id"])


def test_candidatos_omite_carpeta_con_ficha(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = crear_ficha(api, tmp_path, "Golden Axe")
    assert (tmp_path / "data" / "juegos" / "arcade" / game_id / "game.json").exists()
    assert candidatos(api) == []


def test_una_ficha_no_tapa_el_mismo_nombre_en_otro_sistema(tmp_path: Path) -> None:
    """La ocupacion es por sistema: `sf2.zip` en `nes/` no es el `sf2` de arcade."""
    api = client(tmp_path)
    crear_ficha(api, tmp_path, "sf2")
    nes = tmp_path / "data" / "juegos" / "nes"
    nes.mkdir(parents=True, exist_ok=True)
    (nes / "sf2.zip").write_bytes(b"rom")

    items = candidatos(api)
    assert [(item["systemId"], item["id"]) for item in items] == [("nes", "sf2")]


def test_alta_tapa_el_candidato_aunque_el_titulo_limpie_el_nombre(tmp_path: Path) -> None:
    """El id de la ficha sale del titulo y el del candidato del nombre en disco.

    `Indiana Jones ... (1992)` da `...-atlantis-1992` como candidato y
    `...-atlantis` como ficha: comparar ids dejaba el candidato a la vista.
    """
    api = client(tmp_path)
    api.post(
        "/api/systems",
        json={"name": "msdos", "shortName": "MS-DOS", "launchCmd": "/opt/dosbox"},
    )
    ms_dos = tmp_path / "data" / "juegos" / "ms-dos"
    carpeta = ms_dos / "Indiana Jones and the Fate of Atlantis (1992)"
    carpeta.mkdir(parents=True)
    (carpeta / "INDY.EXE").write_bytes(b"exe")

    antes = candidatos(api)
    assert [item["id"] for item in antes] == ["indiana-jones-and-the-fate-of-atlantis-1992"]

    creado = api.post(
        "/api/games",
        json={
            "systemId": "MS-DOS",
            "romSource": "path",
            "romRef": str(carpeta.resolve()),
            "tratamiento": "descomprimir",
            "identity": {
                "title": "Indiana Jones and the Fate of Atlantis", "year": "1992",
                "developer": "", "publisher": "", "genre": "", "players": "", "format": "",
            },
        },
    )
    assert creado.status_code == 200, creado.text
    assert creado.json()["id"] == "indiana-jones-and-the-fate-of-atlantis"
    assert candidatos(api) == []


def test_candidato_archivo_desaparece_cuando_una_ficha_apunta_a_el(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post(
        "/api/systems",
        json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/bin/mame"},
    )
    rom = tmp_path / "data" / "juegos" / "arcade" / "sf2.zip"
    rom.parent.mkdir(parents=True)
    rom.write_bytes(b"rom")

    assert [item["id"] for item in candidatos(api)] == ["sf2"]

    creado = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "path",
            "romRef": str(rom.resolve()),
            "identity": {
                "title": "Street Fighter II", "year": "1991", "developer": "",
                "publisher": "", "genre": "", "players": "", "format": "",
            },
        },
    )
    assert creado.status_code == 200, creado.text
    assert candidatos(api) == []


def test_ficha_creada_en_wsl_tapa_el_candidato_leido_desde_windows(tmp_path: Path) -> None:
    r"""`./dev.sh` corre el backend en WSL y guarda `/mnt/d/...`; el mismo repo
    abierto desde Windows lee `D:\...`. Es el mismo juego y no debe reaparecer."""
    api = client(tmp_path)
    juegos = tmp_path / "data" / "juegos"
    (juegos / "ms-dos" / "Doom").mkdir(parents=True)
    (juegos / "ms-dos" / "Doom" / "DOOM.EXE").write_bytes(b"exe")

    assert [item["id"] for item in candidatos(api)] == ["doom"]

    GamesStore(juegos).create(
        CreateGame(
            systemId="ms-dos",
            romSource="path",
            romRef="/mnt/d/Juegos/COINDOOR/games/juegos/ms-dos/Doom",
            tratamiento="descomprimir",
            identity=Identity(title="Doom", year="1993"),
        )
    )

    assert candidatos(api) == []


@pytest.mark.parametrize(
    ("rom_ref", "esperado"),
    [
        ("/mnt/d/games/juegos/ms-dos/Doom", "Doom"),
        (r"D:\Juegos\games\juegos\ms-dos\Doom", "Doom"),
        ("/roms/arcade/sf2.zip", "sf2.zip"),
        ("/roms/msdos/dino/", "dino"),
        ("/", ""),
        ("", ""),
    ],
)
def test_ultimo_segmento(rom_ref: str, esperado: str) -> None:
    assert _ultimo_segmento(rom_ref) == esperado


def test_candidatos_omite_temporales_y_ocultos(tmp_path: Path) -> None:
    api = client(tmp_path)
    mame = tmp_path / "data" / "juegos" / "mame"
    mame.mkdir(parents=True)
    for nombre in (".game.json.abc.tmp", "descarga.part", "game.json", ".oculto.zip"):
        (mame / nombre).write_bytes(b"x")
    (mame / "sf2.zip").write_bytes(b"rom")

    assert [item["id"] for item in candidatos(api)] == ["sf2"]


def test_candidatos_usan_el_id_real_del_sistema(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post(
        "/api/systems",
        json={"name": "msdos", "shortName": "MS-DOS", "launchCmd": "/opt/dosbox"},
    )
    doom = tmp_path / "data" / "juegos" / "ms-dos" / "Doom"
    doom.mkdir(parents=True)
    (doom / "DOOM.EXE").write_bytes(b"exe")

    items = candidatos(api)
    assert [item["systemId"] for item in items] == ["MS-DOS"]
    assert candidatos(api, "MS-DOS") == items
    assert candidatos(api, "nes") == []


def _alta(api: TestClient, system_id: str, rom_ref: str, titulo: str) -> dict[str, object]:
    response = api.post(
        "/api/games",
        json={
            "systemId": system_id,
            "romSource": "path",
            "romRef": rom_ref,
            "identity": {
                "title": titulo, "year": "1991", "developer": "", "publisher": "",
                "genre": "", "players": "", "format": "",
            },
        },
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


def test_alta_desde_carpeta_guarda_la_ficha_adentro_del_juego(tmp_path: Path) -> None:
    """ADR-0017: el `game.json` va adentro de la carpeta del propio juego."""
    api = client(tmp_path)
    api.post(
        "/api/systems",
        json={"name": "msdos", "shortName": "MS-DOS", "launchCmd": "/opt/dosbox"},
    )
    carpeta = tmp_path / "data" / "juegos" / "ms-dos" / "Doom II (1994)"
    carpeta.mkdir(parents=True)
    (carpeta / "DOOM2.EXE").write_bytes(b"exe")

    _alta(api, "MS-DOS", str(carpeta.resolve()), "Doom II")

    assert (carpeta / "game.json").exists()
    assert not (carpeta.parent / "doom-ii").exists()
    assert candidatos(api) == []


def test_renombrar_la_carpeta_no_hace_reaparecer_el_juego(tmp_path: Path) -> None:
    """La ficha viaja con la carpeta: el criterio deja de depender del nombre."""
    api = client(tmp_path)
    api.post(
        "/api/systems",
        json={"name": "msdos", "shortName": "MS-DOS", "launchCmd": "/opt/dosbox"},
    )
    carpeta = tmp_path / "data" / "juegos" / "ms-dos" / "Doom II (1994)"
    carpeta.mkdir(parents=True)
    (carpeta / "DOOM2.EXE").write_bytes(b"exe")
    _alta(api, "MS-DOS", str(carpeta.resolve()), "Doom II")

    carpeta.rename(carpeta.parent / "DOOM 2 [完全版]")

    assert candidatos(api) == []


def test_alta_desde_rom_suelta_la_mueve_a_la_carpeta_de_la_ficha(tmp_path: Path) -> None:
    """Un archivo no puede contener el `game.json`, asi que se adopta."""
    api = client(tmp_path)
    api.post(
        "/api/systems",
        json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/bin/mame"},
    )
    rom = tmp_path / "data" / "juegos" / "arcade" / "sf2.zip"
    rom.parent.mkdir(parents=True)
    rom.write_bytes(b"rom")

    creado = _alta(api, "arcade", str(rom.resolve()), "Street Fighter II")

    destino = rom.parent / "street-fighter-ii" / "sf2.zip"
    assert destino.exists()
    assert not rom.exists()
    assert Path(str(creado["romRef"])) == destino
    assert candidatos(api) == []


def test_alta_con_rom_fuera_de_juegos_no_mueve_nada(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post(
        "/api/systems",
        json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/bin/mame"},
    )
    rom = tmp_path / "roms" / "mslug.zip"
    rom.parent.mkdir(parents=True)
    rom.write_bytes(b"rom")

    creado = _alta(api, "arcade", str(rom.resolve()), "Metal Slug")

    assert rom.exists()
    assert Path(str(creado["romRef"])) == rom.resolve()
    ficha = tmp_path / "data" / "juegos" / "arcade" / "metal-slug" / "game.json"
    assert ficha.exists()
