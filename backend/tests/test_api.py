from __future__ import annotations

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
    api.post("/api/systems", json={"name": "Arcade", "shortName": "arcade", "launchCmd": "/usr/local/bin/mame"})  # noqa: E501
    created = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "path",
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
    api.post("/api/systems", json={"name": "Arcade", "shortName": "arcade", "launchCmd": "/usr/local/bin/mame"})  # noqa: E501
    api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "path",
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
    api.post("/api/systems", json={"name": "Arcade", "shortName": "arcade", "launchCmd": "/usr/local/bin/mame"})  # noqa: E501
    created = api.post(
        "/api/games",
        json={
            "systemId": "arcade",
            "romSource": "path",
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
    assert url.endswith("/media/arcade/golden-axe/caratula.jpg")

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
    game_id = _create_arcade_game(api)

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
    assert payload["consultados"] == 0
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


def test_export_options_and_job_without_attract(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)

    options = api.get(f"/api/games/{game_id}/export-options")
    assert options.status_code == 200
    assert {item["key"] for item in options.json()["obligatorio"]} == {
        "identidad", "caratula", "poster", "sinopsis", "accent",
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
        assert archive.getinfo("bundle.json").compress_type == zipfile.ZIP_STORED
        assert "media/data.json" in archive.namelist()
        assert "_synopsis.json" in archive.namelist()


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
