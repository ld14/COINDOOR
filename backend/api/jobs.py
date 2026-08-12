from __future__ import annotations

from fastapi import APIRouter

from backend.api.errors import NotFound
from backend.api.schemas import JobOut
from backend.lib.jobs.ejecutor import submit, test_sleep_job
from backend.lib.jobs.registro import JobState, registry

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _out(job: JobState) -> JobOut:
    return JobOut(
        jobId=job.job_id,
        status=job.status,
        progress=job.progress,
        result=job.result,
        error=job.error,
    )


@router.post("/test-sleep")
def create_test_sleep_job() -> JobOut:
    return _out(submit(test_sleep_job))


@router.get("/{job_id}")
def get_job(job_id: str) -> JobOut:
    job = registry.get(job_id)
    if job is None:
        raise NotFound(f"Job no encontrado: {job_id}")
    return _out(job)


@router.delete("/{job_id}")
def cancel_job(job_id: str) -> JobOut:
    job = registry.cancel(job_id)
    if job is None:
        raise NotFound(f"Job no encontrado: {job_id}")
    return _out(job)
