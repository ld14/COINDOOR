from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


@dataclass
class JobState:
    job_id: str
    status: JobStatus = "queued"
    progress: int = 0
    result: Any = None
    error: str | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create(self) -> JobState:
        job = JobState(job_id=uuid4().hex)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> JobState | None:
        job = self.get(job_id)
        if job is not None:
            job.cancel_event.set()
            if job.status in {"queued", "running"}:
                job.status = "cancelled"
        return job


registry = JobRegistry()
