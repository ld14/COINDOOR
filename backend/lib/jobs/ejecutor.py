from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from backend.lib.jobs.registro import JobState, registry

executor = ThreadPoolExecutor(max_workers=4)
JobFn = Callable[[JobState], Any]


def submit(fn: JobFn) -> JobState:
    job = registry.create()
    executor.submit(_run, job, fn)
    return job


def _run(job: JobState, fn: JobFn) -> None:
    if job.cancel_event.is_set():
        job.status = "cancelled"
        return
    job.status = "running"
    try:
        result = fn(job)
    except Exception as exc:  # noqa: BLE001
        if job.cancel_event.is_set():
            job.status = "cancelled"
        else:
            job.status = "failed"
            job.error = str(exc)
        return
    if job.cancel_event.is_set():
        job.status = "cancelled"
        return
    job.status = "succeeded"
    job.progress = 100
    job.result = result


def test_sleep_job(job: JobState) -> dict[str, str]:
    for step in range(1, 31):
        if job.cancel_event.wait(0.1):
            job.status = "cancelled"
            return {"cancelled": "true"}
        job.progress = int(step / 30 * 100)
    return {"ok": "true"}
