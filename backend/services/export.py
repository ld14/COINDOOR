from __future__ import annotations

import shutil
from collections.abc import Sequence
from dataclasses import asdict
from typing import Any

from backend.api.errors import BadRequest, Conflict
from backend.bundle.manifest import build_manifest
from backend.bundle.pack import pack_staging
from backend.bundle.seleccion import SeleccionItem, compute_seleccion
from backend.bundle.staging import build_staging
from backend.bundle.verify import verify_staging
from backend.config import Settings
from backend.lib.domain.completeness import compute_game_status, missing_required
from backend.lib.jobs.registro import JobState
from backend.store.archivo import safe_id
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore


class ExportService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.games = GamesStore(settings.games_dir)
        self.systems = SystemsStore(settings.systems_path)

    def options(self, game_id: str) -> dict[str, list[dict[str, object]]]:
        game = self.games.get(game_id)
        items = compute_seleccion(self.settings, game.model_dump(mode="json"))
        return {
            "obligatorio": [_item_out(item) for item in items if item.required],
            "opcional": [_item_out(item) for item in items if not item.required],
        }

    def export_job(self, game_id: str, incluir: Sequence[str]) -> Any:
        def job_fn(job: JobState) -> dict[str, object]:
            return self.run(game_id, incluir, job)

        return job_fn

    def run(
        self,
        game_id: str,
        incluir: Sequence[str],
        job: JobState | None = None,
    ) -> dict[str, object]:
        game = self.games.get(game_id)
        game_data = game.model_dump(mode="json")
        if compute_game_status(game_data) != "ready":
            raise Conflict(
                "El juego esta incompleto",
                detail={"missing": missing_required(game_data)},
            )

        system = self.systems.get(game.systemId)
        if system.name != system.name.lower():
            raise BadRequest(
                f"El nombre del sistema '{system.name}' debe ser minusculas. "
                f"Corregilo en Configuracion > Sistemas antes de exportar. "
                f"(contrato ATTRACT: system == system.lower())"
            )

        items = compute_seleccion(self.settings, game_data)
        _validate_incluir(set(incluir), items)
        required = {item.key for item in items if item.required}
        selected = required | set(incluir)

        if job is not None:
            job.progress = 20
        staging = build_staging(self.settings, game_data, selected, system.name)
        try:
            if job is not None:
                job.progress = 50
            verificado = verify_staging(staging.root)
            if verificado.get("ok") is False:
                raise Conflict(
                    "ATTRACT doctor rechazo el bundle",
                    detail={"verificado": verificado},
                )

            manifest = build_manifest(
                game_data,
                system.name,
                staging.incluye - required,
                staging.rom_archivo,
                staging.rom_tratamiento,
                verificado,
            )

            if job is not None:
                job.progress = 80
            output = self.settings.data_dir / "exports" / f"{safe_id(game.id)}.coindoor.zip"
            pack_staging(staging.root, output)
            return {
                "file": str(output),
                "bytes": output.stat().st_size,
                "incluye": manifest["incluye"],
                "verificado": verificado,
            }
        except Exception:
            shutil.rmtree(staging.root, ignore_errors=True)
            raise


def _item_out(item: SeleccionItem) -> dict[str, object]:
    return asdict(item)


def _validate_incluir(incluir: set[str], items: list[SeleccionItem]) -> None:
    by_key = {item.key: item for item in items}
    unknown = incluir - set(by_key)
    if unknown:
        raise BadRequest(f"Campo de export desconocido: {sorted(unknown)[0]}")
    for key in incluir:
        item = by_key[key]
        if not item.disponible:
            raise BadRequest(f"Campo no disponible para exportar: {key}")
