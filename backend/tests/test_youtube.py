from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from time import sleep
from typing import Any

import pytest
from fastapi.testclient import TestClient
from yt_dlp.utils import DownloadError

from backend.api.schemas import CreateGame, Identity, NewSystem
from backend.config import Settings, set_settings
from backend.lib import youtube
from backend.lib.jobs.registro import JobState
from backend.main import create_app
from backend.services.youtube import YoutubeVideoService
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

URL = "https://www.youtube.com/watch?v=earaCnLVL98"
VIDEO = "/media/arcade/golden-axe/video.mp4"


def _simular_yt_dlp(
    monkeypatch: pytest.MonkeyPatch,
    *,
    info: dict[str, Any] | None = None,
    error: str | None = None,
    al_bajar: Callable[[], object] | None = None,
) -> None:
    """Reemplaza a ``YoutubeDL``: ningún test sale a la red."""

    class FakeYoutubeDL:
        def __init__(self, params: dict[str, Any]) -> None:
            self.params = params

        def __enter__(self) -> FakeYoutubeDL:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def extract_info(self, _url: str, download: bool) -> dict[str, Any]:
            if error:
                raise DownloadError(error)
            return {"duration": 69, "requested_formats": [{"filesize": 10}], **(info or {})}

        def process_ie_result(self, _info: dict[str, Any], download: bool) -> None:
            if al_bajar:
                al_bajar()
            estado = {"status": "downloading", "filename": "video.f136.mp4", "downloaded_bytes": 10}
            for hook in self.params["progress_hooks"]:
                hook(estado)
            (Path(self.params["paths"]["home"]) / "video.mp4").write_bytes(b"mp4")

    monkeypatch.setattr(youtube, "YoutubeDL", FakeYoutubeDL)


def _settings(tmp_path: Path) -> Settings:
    settings = Settings(data_dir=tmp_path / "data")
    settings.tmp_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="arcade", shortName="arcade", launchCmd="/bin/echo"),
    )
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="arcade",
            romSource="path",
            romRef="/roms/goldnaxe.zip",
            identity=Identity(title="Golden Axe", format="Arcade"),
        )
    )
    return settings


def _juego(settings: Settings) -> dict[str, Any]:
    return GamesStore(settings.games_dir).get("golden-axe").model_dump(mode="json")


def _sin_video_ni_restos(settings: Settings) -> bool:
    video = _juego(settings)["video"].get("video") or {}
    return (
        video.get("status", "empty") == "empty"
        and not (settings.media_dir / "arcade").exists()
        and list(settings.tmp_dir.iterdir()) == []
    )


def _api(settings: Settings) -> TestClient:
    set_settings(settings)
    return TestClient(create_app(settings), headers={"host": "127.0.0.1:8765"})


@pytest.mark.parametrize(
    "url",
    [
        "https://youtu.be/earaCnLVL98",
        "https://www.youtube.com/watch?v=earaCnLVL98&list=PL123&t=42s",
        "http://m.youtube.com/watch?v=earaCnLVL98",
    ],
)
def test_validar_url_devuelve_la_url_canonica(url: str) -> None:
    assert youtube.validar_url(url) == URL


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://vimeo.com/76979871",
        "https://youtube.com.evil.example/watch?v=earaCnLVL98",
        "file:///etc/passwd",
        "ytsearch:golden axe",
        "https://www.youtube.com/playlist?list=PL123",
        "https://www.youtube.com/@sega",
    ],
)
def test_validar_url_rechaza_lo_que_no_es_un_video_de_youtube(url: str) -> None:
    with pytest.raises(ValueError, match="youtube.com o youtu.be"):
        youtube.validar_url(url)


def test_descarga_escribe_el_video_con_su_procedencia(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _simular_yt_dlp(monkeypatch)
    job = JobState(job_id="yt")

    resultado = YoutubeVideoService(settings).run("golden-axe", "https://youtu.be/earaCnLVL98")(job)

    assert resultado == {"url": VIDEO}
    assert (settings.media_dir / "arcade" / "golden-axe" / "video.mp4").read_bytes() == b"mp4"
    juego = _juego(settings)
    assert juego["video"]["video"] == {"status": "suggested", "url": VIDEO, "source": "YouTube"}
    assert juego["provenance"]["video"]["originUrl"] == URL
    assert job.progress == 95
    assert list(settings.tmp_dir.iterdir()) == []


@pytest.mark.parametrize(
    ("info", "mensaje"),
    [
        ({"duration": 601}, "El video dura más de 10 minutos."),
        ({"duration": None, "is_live": True}, "No se pueden descargar transmisiones en vivo."),
    ],
)
def test_video_largo_o_en_vivo_falla_antes_de_bajar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, info: dict[str, Any], mensaje: str
) -> None:
    settings = _settings(tmp_path)
    _simular_yt_dlp(monkeypatch, info=info, al_bajar=lambda: pytest.fail("no debía descargar"))

    with pytest.raises(youtube.YoutubeError) as fallo:
        YoutubeVideoService(settings).run("golden-axe", URL)(JobState(job_id="yt"))

    assert str(fallo.value) == mensaje
    assert _sin_video_ni_restos(settings)


@pytest.mark.parametrize(
    ("error", "mensaje"),
    [
        (
            "ERROR: [youtube] x: Sign in to confirm you're not a bot. Use --cookies",
            "YouTube pidió verificación anti-bot. Probá más tarde o actualizá yt-dlp.",
        ),
        (
            "ERROR: [youtube] x: Requested format is not available. Use --list-formats",
            "Este video no tiene versión H.264 de 720p o menos.",
        ),
        (
            "ERROR: You have requested merging of multiple formats but ffmpeg is not installed.",
            "Falta ffmpeg en el equipo: instalalo para descargar video de YouTube.",
        ),
        ("ERROR: [youtube] x: Video unavailable", "[youtube] x: Video unavailable"),
    ],
)
def test_errores_de_yt_dlp_llegan_legibles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: str, mensaje: str
) -> None:
    _simular_yt_dlp(monkeypatch, error=error)

    with pytest.raises(youtube.YoutubeError) as fallo:
        youtube.descargar(URL, tmp_path, threading.Event(), lambda _: None)

    assert str(fallo.value) == mensaje


def test_cancelar_no_toca_el_juego_ni_deja_restos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    job = JobState(job_id="yt")
    _simular_yt_dlp(monkeypatch, al_bajar=job.cancel_event.set)

    assert YoutubeVideoService(settings).run("golden-axe", URL)(job) == {}
    assert _sin_video_ni_restos(settings)


def test_un_corte_de_yt_dlp_sin_pedido_del_usuario_es_un_fallo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from yt_dlp.utils import RejectedVideoReached

    settings = _settings(tmp_path)

    def rechazar() -> None:
        raise RejectedVideoReached()

    _simular_yt_dlp(monkeypatch, al_bajar=rechazar)

    # Si se tragara como cancelación, el ejecutor marcaría el job `succeeded` sin video.
    with pytest.raises(RejectedVideoReached):
        YoutubeVideoService(settings).run("golden-axe", URL)(JobState(job_id="yt"))

    assert _sin_video_ni_restos(settings)


def test_endpoint_responde_422_con_url_invalida_y_404_sin_juego(tmp_path: Path) -> None:
    api = _api(_settings(tmp_path))

    invalida = api.post(
        "/api/games/golden-axe/media/video/youtube", json={"url": "https://vimeo.com/1"}
    )
    assert invalida.status_code == 422
    assert invalida.json()["error"] == youtube.URL_INVALIDA

    inexistente = api.post("/api/games/no-existe/media/video/youtube", json={"url": URL})
    assert inexistente.status_code == 404


def test_endpoint_descarga_el_video_como_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _api(_settings(tmp_path))
    _simular_yt_dlp(monkeypatch)

    creado = api.post("/api/games/golden-axe/media/video/youtube", json={"url": URL})
    assert creado.status_code == 200
    job_id = creado.json()["jobId"]
    for _ in range(40):
        job = api.get(f"/api/jobs/{job_id}").json()
        if job["status"] not in {"queued", "running"}:
            break
        sleep(0.05)

    assert job["status"] == "succeeded", job
    assert job["result"] == {"url": VIDEO}
    video = api.get("/api/games/golden-axe").json()["video"]["video"]
    assert video == {"status": "suggested", "url": VIDEO, "source": "YouTube"}
