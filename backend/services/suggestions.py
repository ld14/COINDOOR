from __future__ import annotations

import logging
from collections.abc import Callable

from backend.config import Settings
from backend.lib.jobs.registro import JobState
from backend.lib.providers.orquestador import SuggestionsService

log = logging.getLogger(__name__)


class SuggestionJobsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        game_id: str,
        key: str,
        *,
        reintentar: bool = False,
        source: str | None = None,
    ) -> Callable[[JobState], dict[str, object]]:
        def job_fn(job: JobState) -> dict[str, object]:
            return SuggestionsService(self.settings).suggest(
                game_id,
                key,
                job.cancel_event,
                reintentar=reintentar,
                source=source,
            )

        return job_fn

    def run_identity_batch(
        self,
        game_id: str,
        *,
        reintentar: bool = False,
    ) -> Callable[[JobState], dict[str, object]]:
        def job_fn(job: JobState) -> dict[str, object]:
            log.info("identity batch job starting for game=%s reintentar=%s", game_id, reintentar)
            try:
                result = SuggestionsService(self.settings).suggest_identity_batch(
                    game_id,
                    job.cancel_event,
                    reintentar=reintentar,
                )
                log.info(
                    "identity batch job done: %d candidates",
                    len(result.get("candidatos", [])),
                )
                return result
            except Exception:
                log.exception("identity batch job FAILED for game=%s", game_id)
                raise

        return job_fn
