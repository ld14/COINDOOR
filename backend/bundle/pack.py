from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from backend.store.archivo import mover_binario

# Archivos internos de COINDOOR que NUNCA deben ir en el zip exportado.
# El contrato solo permite: game.json, data.json, media/*
_EXCLUDE_FROM_ZIP = frozenset({"_synopsis.json", "bundle.json"})


def pack_staging(root: Path, output: Path, *, started_ns: int | None = None) -> Path:
    temporary: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
        os.close(fd)
        temporary = Path(name)
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_STORED) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.name not in _EXCLUDE_FROM_ZIP:
                    archive.write(path, path.relative_to(root).as_posix())
        if started_ns is not None:
            # Una ficha editada durante el export debe seguir pendiente de exportar.
            os.utime(temporary, ns=(started_ns, started_ns))
        mover_binario(temporary, output)
        return output
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        shutil.rmtree(root, ignore_errors=True)
