from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Literal

from backend.api.errors import StorageError

ExportStatus = Literal["pending", "exported"]


def export_status(bundle: Path, game_file: Path) -> ExportStatus:
    try:
        if not bundle.is_file() or not zipfile.is_zipfile(bundle):
            return "pending"
        return (
            "exported" if bundle.stat().st_mtime_ns >= game_file.stat().st_mtime_ns else "pending"
        )
    except FileNotFoundError:
        return "pending"
    except OSError as exc:
        raise StorageError(
            f"No se pudo consultar el export {bundle} o la ficha {game_file}"
        ) from exc
