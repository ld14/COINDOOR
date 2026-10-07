from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from time import sleep

import pytest
from fastapi.testclient import TestClient

from backend.bundle.pack import pack_staging
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


def test_export_status_edicion_reexport_y_borrado(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    assert api.get("/api/games").json()["items"][0]["exportStatus"] == "pending"

    result = _export_sync(api, game_id)
    assert result is not None
    assert api.get("/api/games").json()["items"][0]["exportStatus"] == "exported"
    # La clasificacion sobrevive al reinicio, sin estado en memoria.
    api = client(tmp_path)
    assert api.get("/api/games").json()["items"][0]["exportStatus"] == "exported"
    api.patch(f"/api/games/{game_id}", json={"identity": {"year": "1990"}})
    item = api.get("/api/games").json()["items"][0]
    assert item["exportStatus"] == "pending"
    assert item["status"] == "ready"
    assert _export_sync(api, game_id) is not None
    assert api.get("/api/games").json()["items"][0]["exportStatus"] == "exported"
    Path(result["file"]).unlink()
    assert api.get("/api/games").json()["items"][0]["exportStatus"] == "pending"


def test_export_status_legacy_filtra_antes_de_paginar(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    for title in ("Otro A", "Otro B"):
        api.post("/api/games", json={
            "systemId": "arcade", "romSource": "upload", "romRef": "",
            "identity": {"title": title},
        })
    bundle = tmp_path / "data" / "exports" / f"{game_id}.coindoor.zip"
    bundle.parent.mkdir(parents=True)
    bundle.write_bytes(b"zip incompleto")
    assert api.get("/api/games?exportStatus=exported").json()["total"] == 0
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("game.json", "{}")
    exported = api.get("/api/games?exportStatus=exported&q=Golden&systemId=arcade&status=incomplete").json()  # noqa: E501
    assert exported["total"] == 1
    assert exported["items"][0]["id"] == game_id
    pending = api.get("/api/games?exportStatus=pending&perPage=1&page=2").json()
    assert pending["total"] == 2
    assert len(pending["items"]) == 1
    assert pending["items"][0]["id"] != game_id
    assert api.get("/api/games?exportStatus=invalid").status_code == 422


@pytest.mark.parametrize("existing", [False, True])
def test_pack_fallido_no_publica_zip_parcial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: bool,
) -> None:
    root = tmp_path / "staging"
    root.mkdir()
    (root / "game.json").write_text("{}")
    output = tmp_path / "exports" / "juego.zip"
    output.parent.mkdir()
    if existing:
        output.write_bytes(b"anterior")

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("disco lleno")

    monkeypatch.setattr(zipfile.ZipFile, "write", fail)
    with pytest.raises(OSError, match="disco lleno"):
        pack_staging(root, output)
    assert not root.exists()
    if existing:
        assert output.read_bytes() == b"anterior"
    else:
        assert not output.exists()
    assert not list(output.parent.glob("*.tmp"))


def test_edicion_durante_export_queda_pendiente(tmp_path: Path) -> None:
    from backend.store.exports import export_status

    root = tmp_path / "staging"
    root.mkdir()
    (root / "game.json").write_text("{}")
    game_file = tmp_path / "game.json"
    game_file.write_text("{}")
    started_ns = game_file.stat().st_mtime_ns
    os.utime(game_file, ns=(started_ns + 1_000_000_000, started_ns + 1_000_000_000))
    output = tmp_path / "juego.zip"
    pack_staging(root, output, started_ns=started_ns)
    assert export_status(output, game_file) == "pending"


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


def test_games_create_rejects_unregistered_system(tmp_path: Path) -> None:
    # Una ficha con sistema inexistente rompía después, en la IA y el export.
    api = client(tmp_path)
    response = api.post(
        "/api/games",
        json={
            "systemId": "mame",
            "romSource": "upload",
            "romRef": "/roms/pacman.zip",
            "identity": {
                "title": "Pac-Man", "year": "", "developer": "", "publisher": "",
                "genre": "", "players": "", "format": ""
            },
        },
    )
    assert response.status_code == 404
    assert "Sistema no encontrado: mame" in response.text
    assert api.get("/api/games").json()["items"] == []


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


def test_cheats_parse_text_without_ia_configured_returns_422(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)

    response = api.post(f"/api/games/{game_id}/fields/cheats/parse-text", json={"text": "30 vidas: arriba arriba"})  # noqa: E501

    assert response.status_code == 422
    assert "No se pudo interpretar el texto" in response.json()["error"]


def test_cheats_parse_text_empty_text_returns_empty_groups(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)

    response = api.post(f"/api/games/{game_id}/fields/cheats/parse-text", json={"text": "   "})

    assert response.status_code == 200
    assert response.json()["groups"] == []


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


def _export_sync(api: TestClient, game_id: str) -> dict:
    created = api.post("/api/export", json={"gameId": game_id, "incluir": []})
    run_id = created.json()["runId"]
    result = api.get(f"/api/export/{run_id}")
    for _ in range(20):
        if result.json()["status"] == "succeeded":
            break
        sleep(0.05)
        result = api.get(f"/api/export/{run_id}")
    return result.json()["result"]


def _fake_installer(attract_dir: Path, body: str) -> None:
    attract_dir.mkdir(parents=True, exist_ok=True)
    script = attract_dir / "install-coindoor-wsl.sh"
    script.write_text(f"#!/usr/bin/env bash\n{body}\n")
    script.chmod(script.stat().st_mode | 0o111)


def test_install_attract_sin_export_previo_falla(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.patch("/api/config", json={"attractDir": str(tmp_path / "attract")})
    game_id = _create_arcade_game(api)

    response = api.post(f"/api/games/{game_id}/install-attract")

    assert response.status_code == 409
    assert "Exportá el juego primero" in response.json()["error"]


def test_install_attract_sin_configurar_falla(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    _export_sync(api, game_id)

    response = api.post(f"/api/games/{game_id}/install-attract")

    assert response.status_code == 422
    assert "Configuración" in response.json()["error"]


def test_install_attract_ok(tmp_path: Path) -> None:
    attract_dir = tmp_path / "attract"
    _fake_installer(attract_dir, 'echo "instalado: $1"; exit 0')
    api = client(tmp_path)
    api.patch("/api/config", json={"attractDir": str(attract_dir)})
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    _export_sync(api, game_id)

    response = api.post(f"/api/games/{game_id}/install-attract")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert "instalado:" in payload["salida"]


def test_install_attract_falla_muestra_salida_del_script(tmp_path: Path) -> None:
    attract_dir = tmp_path / "attract"
    _fake_installer(attract_dir, 'echo "error: falta wslpath" >&2; exit 1')
    api = client(tmp_path)
    api.patch("/api/config", json={"attractDir": str(attract_dir)})
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    _export_sync(api, game_id)

    response = api.post(f"/api/games/{game_id}/install-attract")

    assert response.status_code == 409
    assert "falta wslpath" in response.json()["error"]


def test_config_get_sin_archivo_no_falla(tmp_path: Path) -> None:
    api = client(tmp_path)

    response = api.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {"attractDir": None}


def test_config_patch_ruta_relativa_falla(tmp_path: Path) -> None:
    api = client(tmp_path)

    response = api.patch("/api/config", json={"attractDir": "relativo/attract"})

    assert response.status_code == 422
    assert "La ruta debe ser absoluta" in response.json()["error"]


def test_config_patch_vacio_limpia_el_valor(tmp_path: Path) -> None:
    api = client(tmp_path)
    api.patch("/api/config", json={"attractDir": str(tmp_path / "attract")})

    response = api.patch("/api/config", json={"attractDir": ""})

    assert response.status_code == 200
    assert response.json() == {"attractDir": None}


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


def _export_run(api: TestClient, game_id: str, incluir: list[str]) -> dict:
    created = api.post("/api/export", json={"gameId": game_id, "incluir": incluir})
    run_id = created.json()["runId"]
    result = api.get(f"/api/export/{run_id}")
    for _ in range(20):
        if result.json()["status"] in ("succeeded", "failed"):
            break
        sleep(0.05)
        result = api.get(f"/api/export/{run_id}")
    return result.json()


def _guia_exportada(payload: dict) -> dict | None:
    with zipfile.ZipFile(payload["file"]) as archive:
        return json.loads(archive.read("data.json")).get("guia")


def _opciones(api: TestClient, game_id: str) -> dict[str, dict]:
    opciones = api.get(f"/api/games/{game_id}/export-options").json()
    return {item["key"]: item for item in opciones["obligatorio"] + opciones["opcional"]}


def test_un_texto_de_ejemplo_no_se_ofrece_ni_se_exporta(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    api.put(f"/api/games/{game_id}/fields/objetivo", json={"value": "Vencer a todos los rivales."})
    api.put(f"/api/games/{game_id}/fields/primerosPasos", json={"value": "EJEMPLO: Mover"})

    opciones = _opciones(api, game_id)
    assert opciones["objetivo"]["disponible"] is True
    assert opciones["primerosPasos"]["disponible"] is False
    assert "EJEMPLO" in opciones["primerosPasos"]["motivo"]

    # Pedirlo igual por la API se rechaza con el motivo, sin generar paquete.
    rechazado = _export_run(api, game_id, ["objetivo", "primerosPasos"])
    assert rechazado["status"] == "failed"
    assert "primerosPasos" in rechazado["error"]
    assert "EJEMPLO" in rechazado["error"]

    # Sin ese texto, el resto de la guía viaja y el ejemplo nunca aparece.
    exportado = _export_run(api, game_id, ["objetivo"])["result"]
    guia = _guia_exportada(exportado)
    assert guia["objetivo"] == "Vencer a todos los rivales."
    assert "primerosPasos" not in guia
    assert "EJEMPLO" not in json.dumps(guia)


def test_objetivo_de_ejemplo_deja_el_paquete_sin_guia(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    api.put(f"/api/games/{game_id}/fields/objetivo", json={"value": "ejemplo: texto de prueba"})

    assert _opciones(api, game_id)["objetivo"]["disponible"] is False
    assert _export_run(api, game_id, ["objetivo"])["status"] == "failed"
    assert _guia_exportada(_export_run(api, game_id, [])["result"]) is None


def test_objetivo_con_el_nombre_interno_del_juego_no_se_exporta(tmp_path: Path) -> None:
    api = client(tmp_path)
    game_id = _create_arcade_game(api)
    _make_exportable(api, game_id)
    api.patch(f"/api/games/{game_id}", json={"identity": {"title": "Golden Axe"}})
    # El romset es `goldnaxe` (goldnaxe.zip); el título comercial es otro.
    api.put(f"/api/games/{game_id}/fields/objetivo", json={"value": "En GOLDNAXE hay que avanzar."})

    objetivo = _opciones(api, game_id)["objetivo"]
    assert objetivo["disponible"] is False
    assert "goldnaxe" in objetivo["motivo"]
    rechazado = _export_run(api, game_id, ["objetivo"])
    assert rechazado["status"] == "failed"
    assert "goldnaxe" in rechazado["error"]

    api.put(f"/api/games/{game_id}/fields/objetivo", json={"value": "En Golden Axe hay que avanzar."})
    assert _opciones(api, game_id)["objetivo"]["disponible"] is True
