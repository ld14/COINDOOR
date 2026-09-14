from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def install_bundle(
    script: Path,
    bundle: Path,
    library: Path,
    *,
    timeout: int = 300,
) -> dict[str, Any]:
    """Instala un bundle corriendo el instalador que ya existe en ATTRACT.

    No reinterpreta lo que hace el script (ADR-0001, ADR-0021): el veredicto
    sale solo del código de salida, igual que `bundle/verify.py` con
    `attract doctor`. `stdout`/`stderr` se devuelven crudos, solo para
    mostrarlos como diagnóstico si falla.
    """
    try:
        completed = subprocess.run(
            [str(script), str(bundle), str(library)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError:
        return {"ok": False, "estado": "no_disponible", "salida": ""}
    except subprocess.TimeoutExpired:
        return {"ok": False, "estado": "timeout", "salida": ""}

    salida = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode == 0:
        return {"ok": True, "estado": "instalado", "salida": salida}
    return {"ok": False, "estado": "error", "salida": salida}
