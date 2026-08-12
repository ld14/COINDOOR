from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class CoindoorError(Exception):
    status_code = 400

    def __init__(self, message: str, *, detail: object | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class NotFound(CoindoorError):
    status_code = 404


class Conflict(CoindoorError):
    status_code = 409


class BadRequest(CoindoorError):
    status_code = 422


class StorageError(CoindoorError):
    status_code = 500


async def coindoor_exception_handler(_request: Request, exc: CoindoorError) -> JSONResponse:
    payload: dict[str, object] = {"error": exc.message}
    if exc.detail is not None:
        payload["detail"] = exc.detail
    return JSONResponse(payload, status_code=exc.status_code)


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CoindoorError, coindoor_exception_handler)
