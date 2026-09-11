from __future__ import annotations

from fastapi import APIRouter, UploadFile

from backend.api.schemas import GameOut, SuggestionJob, YoutubeDownload
from backend.config import get_settings
from backend.lib.jobs.ejecutor import submit
from backend.services.media import MediaService
from backend.services.youtube import YoutubeVideoService

router = APIRouter(prefix="/api/games/{game_id}/media", tags=["media"])


def _service() -> MediaService:
    return MediaService(get_settings())


@router.put("/{key}")
def put_media(game_id: str, key: str, file: UploadFile) -> GameOut:
    data = file.file.read()
    return _service().upload(game_id, key, file.filename or "", data)


@router.post("/video/youtube")
def download_youtube_video(game_id: str, payload: YoutubeDownload) -> SuggestionJob:
    """Descarga el video del juego desde YouTube como un job (ADR-0020)."""
    service = YoutubeVideoService(get_settings())
    job = submit(service.run(game_id, payload.url))
    return SuggestionJob(jobId=job.job_id)
