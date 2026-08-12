from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.api.errors import install_error_handlers
from backend.api.fields import router as fields_router
from backend.api.games import router as games_router
from backend.api.jobs import router as jobs_router
from backend.api.systems import router as systems_router
from backend.config import Settings, ensure_data_dirs, get_settings
from backend.store.cuotas import QuotasStore
from backend.store.sistemas import SystemsStore

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "127.0.0.1:8765", "localhost:8765"}
ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = ROOT / "frontend" / "dist"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    ensure_data_dirs(settings)
    SystemsStore(settings.systems_path)
    QuotasStore(settings.quotas_path)

    app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")
    install_error_handlers(app)
    app.include_router(systems_router)
    app.include_router(games_router)
    app.include_router(fields_router)
    app.include_router(jobs_router)
    app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

    class ValidateHostMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
            if request.headers.get("host", "") not in ALLOWED_HOSTS:
                return Response("Host inválido", status_code=403)
            return await call_next(request)

    app.add_middleware(ValidateHostMiddleware)

    @app.get("/{path:path}", response_model=None)
    def serve_frontend(path: str) -> FileResponse | Response:
        if not FRONTEND_DIST.exists():
            return Response("Frontend build no encontrado", status_code=404)
        requested = (FRONTEND_DIST / path).resolve()
        if requested.is_file() and FRONTEND_DIST.resolve() in requested.parents:
            return FileResponse(requested)
        return FileResponse(FRONTEND_DIST / "index.html")

    return app


app = create_app()
