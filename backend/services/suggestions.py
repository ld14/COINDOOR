from __future__ import annotations

from collections.abc import Callable

from backend.config import Settings
from backend.lib.jobs.registro import JobState
from backend.lib.providers.orquestador import SuggestionsService


class SuggestionJobsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        game_id: str,
        key: str,
        *,
        reintentar: bool = False,
    ) -> Callable[[JobState], dict[str, object]]:
        def job_fn(job: JobState) -> dict[str, object]:
            return SuggestionsService(self.settings).suggest(
                game_id,
                key,
                job.cancel_event,
                reintentar=reintentar,
            )

        return job_fn
