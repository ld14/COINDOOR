from __future__ import annotations

import json
import zipfile
from pathlib import Path
from time import sleep

from fastapi.testclient import TestClient

from backend.config import Settings, set_settings
from backend.main import create_app


def client(tmp_path: Path) -> TestClient:
    settings = Settings(
        data_dir=tmp_path / "data",
        ai_primary_base_url="",
        ai_primary_api_key="",
        ai_primary_model="",
        ai_backup_base_url="",
        ai_backup_api_key="",
        ai_backup_model="",
    )
    set_settings(settings)
    return TestClient(create_app(settings), headers={"host": "127.0.0.1:8765"})


def test_host_invalido_rechazado(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path / "data"))
    response = TestClient(app, headers={"host": "evil.com"}).get("/api/systems")
    assert response.status_code == 403


def test_systems_create_rejects_relative_launch(tmp_path: Path) -> None:
    response = client(tmp_path).post(
        "/api/systems",
        json={"name": "SNES", "shortName": "snes", "launchCmd": "emulators/snes9x"},
    )
    assert response.status_code == 422
    assert "La ruta debe ser absoluta" in response.json()["error"]


def test_games_mark_ready_incomplete_returns_missing(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post("/api/systems", json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/local/bin/mame"})  # noqa: E501
    created = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "upload",
            "romRef": "/roms/mslug.zip",
            "identity": {
                "title": "Metal Slug", "year": "", "developer": "", "publisher": "",
                "genre": "", "players": "", "format": ""
            },
        },
    ).json()
    response = api.post(f"/api/games/{created['id']}/mark-ready")
    assert response.status_code == 409
    assert "Identidad: Año" in response.json()["detail"]["missing"]


def test_games_list_filters_and_paginates(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post("/api/systems", json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/local/bin/mame"})  # noqa: E501
    api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "upload",
            "romRef": "/roms/goldnaxe.zip",
            "identity": {
                "title": "Golden Axe", "year": "1989", "developer": "Sega",
                "publisher": "Sega", "genre": "Beat em up", "players": "1-2",
                "format": "Arcade",
            },
        },
    )
    response = api.get("/api/games", params={"q": "golden", "systemId": "arcade", "page": 1, "perPage": 10})  # noqa: E501
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_jobs_create_get_cancel(tmp_path: Path) -> None:
    api = client(tmp_path)
    created = api.post("/api/jobs/test-sleep")
    assert created.status_code == 200
    job_id = created.json()["jobId"]
    assert api.get(f"/api/jobs/{job_id}").status_code == 200
    cancelled = api.delete(f"/api/jobs/{job_id}")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_docs_and_openapi_exist(tmp_path: Path) -> None:
    api = client(tmp_path)
    assert api.get("/api/docs").status_code == 200
    assert api.get("/api/openapi.json").status_code == 200


def _create_arcade_game(api: TestClient) -> str:
    api.post("/api/systems", json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/local/bin/mame"})  # noqa: E501
    created = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "upload",
            "romRef": "/roms/goldnaxe.zip",
            "identity": {
                "title": "Golden Axe", "year": "1989", "developer": "Sega",
                "publisher": "Sega", "genre": "Beat em up", "players": "2",
                "format": "Arcade",
            },
        },
    ).json()
    return str(created["id"])


def test_media_upload_sets_field_and_serves_file(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)

    response = api.put(
        f"/api/games/{game_id}/media/caratula",
        files={"file": ("boxfront.jpg", b"\xff\xd8\xff\xe0fake-jpeg-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["images"]["caratula"]["status"] == "manual"
    url = body["images"]["caratula"]["url"]
    assert url.endswith("/media/arcade/golden-axe/boxFront.jpg")

    served = api.get(url)
    assert served.status_code == 200
    assert served.content == b"\xff\xd8\xff\xe0fake-jpeg-bytes"


def test_media_upload_rejects_unknown_key(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    response = api.put(
        f"/api/games/{game_id}/media/sinopsis",
        files={"file": ("x.jpg", b"data", "image/jpeg")},
    )
    assert response.status_code == 422


def test_media_upload_rejects_empty_file(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    response = api.put(
        f"/api/games/{game_id}/media/caratula",
        files={"file": ("x.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 422


def test_suggestions_endpoint_creates_job_without_credentials(tmp_path: Path) -> None:
    api = client(tmp_path)
    # Usar sistema no-arcade para evitar que ArcadeDB sea consultado.
    api.post("/api/systems", json={"name": "nes", "shortName": "nes", "launchCmd": "/usr/local/bin/fceux"})
    created = api.post(
        "/api/games",
        json={
            "systemId": "nes",
            "romSource": "upload",
            "romRef": "/roms/supermario.zip",
            "identity": {"title": "Super Mario Bros", "year": "1985"},
        },
    ).json()
    game_id = str(created["id"])

    created = api.post(f"/api/games/{game_id}/fields/sinopsis/suggestions")
    assert created.status_code == 200
    job_id = created.json()["jobId"]

    result = api.get(f"/api/jobs/{job_id}")
    for _ in range(20):
        if result.json()["status"] == "succeeded":
            break
        sleep(0.05)
        result = api.get(f"/api/jobs/{job_id}")
    assert result.status_code == 200
    assert result.json()["status"] == "succeeded"
    payload = result.json()["result"]
    # ArcadeDB siempre se consulta (gate por sistema dentro de buscar), IA se salta.
    assert payload["consultados"] == 1
    assert payload["candidatos"] == []


def _make_exportable(api: TestClient, game_id: str) -> None:
    api.put(
        f"/api/games/{game_id}/media/caratula",
        files={"file": ("caratula.jpg", b"caratula", "image/jpeg")},
    )
    api.put(
        f"/api/games/{game_id}/media/poster",
        files={"file": ("poster.jpg", b"poster", "image/jpeg")},
    )
    api.put(
        f"/api/games/{game_id}/fields/sinopsis",
        json={"value": "Un arcade de fantasía."},
    )
    api.patch(f"/api/games/{game_id}", json={"accent": "manual", "accentValue": "#d4a017"})
    api.post(f"/api/games/{game_id}/rom", files={"file": ("goldnaxe.zip", b"rom-bytes", "application/zip")})  # noqa: E501


def test_export_options_and_job_without_attract(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)

    options = api.get(f"/api/games/{game_id}/export-options")
    assert options.status_code == 200
    assert {item["key"] for item in options.json()["obligatorio"]} == {
        "identidad", "caratula", "poster", "sinopsis", "accent", "juego",
    }

    created = api.post("/api/export", json={"gameId": game_id, "incluir": []})
    assert created.status_code == 200
    run_id = created.json()["runId"]

    result = api.get(f"/api/export/{run_id}")
    for _ in range(20):
        if result.json()["status"] == "succeeded":
            break
        sleep(0.05)
        result = api.get(f"/api/export/{run_id}")

    assert result.status_code == 200
    payload = result.json()["result"]
    assert payload["verificado"]["estado"] == "no_verificado"
    with zipfile.ZipFile(payload["file"]) as archive:
        names = archive.namelist()
        assert "game.json" in names
        assert "data.json" in names
        assert "_synopsis.json" not in names
        assert "bundle.json" not in names
        assert "juego/goldnaxe.zip" in names
        assert json.loads(archive.read("game.json"))["file"] == "goldnaxe.zip"


def test_export_rejects_optional_empty_field(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)

    created = api.post("/api/export", json={"gameId": game_id, "incluir": ["video"]})
    run_id = created.json()["runId"]
    result = api.get(f"/api/export/{run_id}")
    for _ in range(20):
        if result.json()["status"] == "failed":
            break
        sleep(0.05)
        result = api.get(f"/api/export/{run_id}")

    assert result.json()["error"] == "Campo no disponible para exportar: video"


def test_system_create_rejects_uppercase_name(tmp_path: Path) -> None:
    response = client(tmp_path).post(
        "/api/systems",
        json={"name": "MAME", "shortName": "mame", "launchCmd": "/usr/local/bin/mame"},
    )
    assert response.status_code == 422
    assert "minusculas" in response.json()["error"]


def test_export_rejects_uppercase_system_name(tmp_path: Path) -> None:
    api = client(tmp_path)

    systems_path = tmp_path / "data" / "sistemas.json"
    systems_data = {
        "version": 1,
        "items": [
            {
                "id": "arcade",
                "name": "Arcade",
                "shortName": "arcade",
                "launchCmd": "/usr/local/bin/mame",
                "valid": True,
                "errorMsg": None,
                "gameCount": 0,
            }
        ],
    }
    systems_path.write_text(json.dumps(systems_data), encoding="utf-8")

    created = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "upload",
            "romRef": "/roms/goldnaxe.zip",
            "identity": {
                "title": "Golden Axe", "year": "1989", "developer": "Sega",
                "publisher": "Sega", "genre": "Beat em up", "players": "2",
                "format": "Arcade",
            },
        },
    ).json()
    game_id = str(created["id"])
    _make_exportable(api, game_id)

    export_created = api.post("/api/export", json={"gameId": game_id, "incluir": []})
    run_id = export_created.json()["runId"]
    result = api.get(f"/api/export/{run_id}")
    for _ in range(20):
        if result.json()["status"] == "failed":
            break
        sleep(0.05)
        result = api.get(f"/api/export/{run_id}")

    assert "minusculas" in result.json()["error"]


def test_patch_systemId_moves_game_to_new_directory(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post("/api/systems", json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/bin/mame"})
    api.post("/api/systems", json={"name": "mame", "shortName": "mame", "launchCmd": "/usr/bin/mame"})
    created = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "upload",
            "romRef": "/roms/goldnaxe.zip",
            "identity": {
                "title": "Golden Axe", "year": "1989", "developer": "Sega",
                "publisher": "Sega", "genre": "Beat em up", "players": "2",
                "format": "Arcade",
            },
        },
    ).json()
    game_id = created["id"]

    old_path = tmp_path / "data" / "juegos" / "arcade" / game_id / "game.json"
    assert old_path.exists()

    response = api.patch(f"/api/games/{game_id}", json={"systemId": "mame"})
    assert response.status_code == 200
    assert response.json()["systemId"] == "mame"

    new_path = tmp_path / "data" / "juegos" / "mame" / game_id / "game.json"
    assert new_path.exists()
    assert not old_path.exists()


def test_patch_systemId_rejects_nonexistent_system(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post("/api/systems", json={"name": "arcade", "shortName": "arcade", "launchCmd": "/usr/bin/mame"})
    created = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "upload",
            "romRef": "/roms/goldnaxe.zip",
            "identity": {
                "title": "Golden Axe", "year": "1989", "developer": "Sega",
                "publisher": "Sega", "genre": "Beat em up", "players": "2",
                "format": "Arcade",
            },
        },
    ).json()
    game_id = created["id"]

    response = api.patch(f"/api/games/{game_id}", json={"systemId": "noexiste"})
    assert response.status_code == 404


def test_cambio_de_sistema_conserva_la_rom_subida(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post("/api/systems", json={"name": "mame", "shortName": "mame", "launchCmd": "/usr/local/bin/mame"})  # noqa: E501
    game_id = _create_arcade_game(api)
    api.post(f"/api/games/{game_id}/rom", files={"file": ("ssriders.zip", b"rom-bytes", "application/zip")})  # noqa: E501

    movido = api.patch(f"/api/games/{game_id}", json={"systemId": "mame"})
    assert movido.status_code == 200

    rom = Path(movido.json()["romRef"])
    assert rom.parent.name == game_id
    assert rom.parent.parent.name == "mame"
    assert rom.read_bytes() == b"rom-bytes"


def test_export_falla_si_la_rom_no_existe(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    # La rom se subio bien y despues desaparecio del disco: el export tiene que
    # frenar en vez de armar un paquete sin ``juego/``.
    Path(api.get(f"/api/games/{game_id}").json()["romRef"]).unlink()

    created = api.post("/api/export", json={"gameId": game_id, "incluir": []})
    run_id = created.json()["runId"]
    result = api.get(f"/api/export/{run_id}")
    for _ in range(20):
        if result.json()["status"] == "failed":
            break
        sleep(0.05)
        result = api.get(f"/api/export/{run_id}")

    assert result.json()["error"] == "El archivo del juego no se pudo incluir en el paquete"


def _identidad_minima() -> dict[str, str]:
    return {
        "title": "Dino", "year": "1990", "developer": "Softie", "publisher": "Softie",
        "genre": "platformer", "players": "1", "format": "Diskette",
    }


def test_alta_por_path_acepta_una_carpeta_de_archivos_sueltos(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post("/api/systems", json={"name": "msdos", "shortName": "msdos", "launchCmd": "/usr/local/bin/dosbox"})  # noqa: E501
    carpeta = tmp_path / "roms" / "dino"
    carpeta.mkdir(parents=True)
    (carpeta / "FRED.EXE").write_bytes(b"exe")

    response = api.post(
        "/api/games",
        json={
            "systemId": "msdos", "romSource": "path", "romRef": str(carpeta),
            "tratamiento": "descomprimir", "identity": _identidad_minima(),
        },
    )
    assert response.status_code == 200
    assert response.json()["romRef"] == str(carpeta)


def test_alta_por_path_rechaza_una_ruta_que_no_existe(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.post("/api/systems", json={"name": "msdos", "shortName": "msdos", "launchCmd": "/usr/local/bin/dosbox"})  # noqa: E501

    response = api.post(
        "/api/games",
        json={
            "systemId": "msdos", "romSource": "path", "romRef": "/msdos/dino-fantasma",
            "identity": _identidad_minima(),
        },
    )
    assert response.status_code == 422
    assert "No existe nada en '/msdos/dino-fantasma'" in response.json()["error"]
    assert api.get("/api/games").json()["total"] == 0


def test_patch_de_romref_rechaza_una_ruta_que_no_existe(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)

    response = api.patch(f"/api/games/{game_id}", json={"romRef": "roms/relativo.zip"})
    assert response.status_code == 422
    assert "debe ser absoluta" in response.json()["error"]

    response = api.patch(f"/api/games/{game_id}", json={"romRef": "/roms/no-existe.zip"})
    assert response.status_code == 422
