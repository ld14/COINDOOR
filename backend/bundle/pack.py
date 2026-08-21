from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

# Archivos internos de COINDOOR que NUNCA deben ir en el zip exportado.
# El contrato solo permite: game.json, data.json, media/*
_EXCLUDE_FROM_ZIP = frozenset({"_synopsis.json", "bundle.json"})


def pack_staging(root: Path, output: Path) -> Path:
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.name not in _EXCLUDE_FROM_ZIP:
                    archive.write(path, path.relative_to(root).as_posix())
        return output
    finally:
        shutil.rmtree(root, ignore_errors=True)
