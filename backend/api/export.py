from __future__ import annotations

from fastapi import APIRouter

from backend.api.errors import NotFound
from backend.api.schemas import ExportJob, ExportRequest, JobOut
from backend.config import get_settings
from backend.lib.jobs.ejecutor import submit
from backend.lib.jobs.registro import JobState, registry
from backend.services.export import ExportService

router = APIRouter(prefix="/api", tags=["export"])


def _service() -> ExportService:
    return ExportService(get_settings())


def _out(job: JobState) -> JobOut:
    return JobOut(
        jobId=job.job_id,
        status=job.status,
        progress=job.progress,
        result=job.result,
        error=job.error,
    )


@router.get("/games/{game_id}/export-options")
def export_options(game_id: str) -> dict[str, list[dict[str, object]]]:
    return _service().options(game_id)


@router.post("/export")
def create_export(payload: ExportRequest) -> ExportJob:
    job = submit(_service().export_job(payload.gameId, payload.incluir))
    return ExportJob(runId=job.job_id)


@router.get("/export/{run_id}")
def get_export(run_id: str) -> JobOut:
    job = registry.get(run_id)
    if job is None:
        raise NotFound(f"Export no encontrado: {run_id}")
    return _out(job)
