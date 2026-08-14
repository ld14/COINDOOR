from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.schemas import ApplySuggestion, CheatsValue, GameOut, ReviewValue, SuggestionJob
from backend.config import get_settings
from backend.lib.jobs.ejecutor import submit
from backend.services.fields import FieldsService
from backend.services.suggestions import SuggestionJobsService

router = APIRouter(prefix="/api/games/{game_id}/fields", tags=["fields"])


class FieldValue(BaseModel):
    value: str = ""


def _service() -> FieldsService:
    return FieldsService(get_settings())


@router.post("/{key}/suggestions")
def create_suggestion_job(game_id: str, key: str, reintentar: bool = False) -> SuggestionJob:
    fn = SuggestionJobsService(get_settings()).run(game_id, key, reintentar=reintentar)
    job = submit(fn)
    return SuggestionJob(jobId=job.job_id)


@router.post("/{key}/apply-suggestion")
def apply_suggestion(game_id: str, key: str, payload: ApplySuggestion) -> GameOut:
    return _service().apply_suggestion(game_id, key, payload.candidateId)


@router.put("/{key}")
def put_field(game_id: str, key: str, payload: dict[str, Any]) -> GameOut:
    if key == "review":
        return _service().set_review(game_id, ReviewValue.model_validate(payload))
    if key == "cheats":
        return _service().set_cheats(game_id, CheatsValue.model_validate(payload))
    return _service().set_value(game_id, key, FieldValue.model_validate(payload).value)


@router.delete("/{key}")
def delete_field(game_id: str, key: str) -> GameOut:
    return _service().delete(game_id, key)
