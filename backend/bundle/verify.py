from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def verify_staging(root: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["attract", "doctor", str(root)],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        return {"por": "attract doctor", "estado": "no_verificado", "ok": None}
    except subprocess.TimeoutExpired:
        return {"por": "attract doctor", "estado": "error", "ok": False}

    if completed.returncode == 0:
        return {"por": "attract doctor", "estado": "verificado", "ok": True}
    return {"por": "attract doctor", "estado": "error", "ok": False}
