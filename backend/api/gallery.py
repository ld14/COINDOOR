from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.schemas import GameOut, SuggestionJob
from backend.config import get_settings
from backend.lib.jobs.ejecutor import submit
from backend.services.gallery import GalleryService, GuardarGaleriaItem
from backend.store.juegos import to_out

router = APIRouter(prefix="/api/games/{game_id}/gallery", tags=["gallery"])


class GuardarGaleria(BaseModel):
    items: list[GuardarGaleriaItem]


def _service() -> GalleryService:
    return GalleryService(get_settings())


@router.get("/candidates")
def list_candidates(
    game_id: str,
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Imágenes disponibles de ArcadeDB, ImageSearch y Launchbox.

    Si se pasa ``source``, solo consulta esa fuente (para reintentos individuales).
    """
    return _service().candidatos(game_id, source=source)


@router.post("")
def save_gallery(game_id: str, payload: GuardarGaleria) -> SuggestionJob:
    """Descarga las imágenes elegidas. Job porque son varias descargas."""
    service = _service()
    job = submit(service.guardar_job(game_id, payload.items))
    return SuggestionJob(jobId=job.job_id)


@router.post("/{image_id}/use-as/{campo}")
def use_as(game_id: str, image_id: str, campo: str) -> GameOut:
    """Apunta un campo del contrato a una imagen del banco."""
    return to_out(_service().usar_como(game_id, image_id, campo))


@router.delete("/{image_id}")
def delete_gallery_image(game_id: str, image_id: str) -> GameOut:
    return to_out(_service().eliminar(game_id, image_id))
