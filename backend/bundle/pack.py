from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


def pack_staging(root: Path, output: Path) -> Path:
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root).as_posix())
        return output
    finally:
        shutil.rmtree(root, ignore_errors=True)
