from __future__ import annotations

import uvicorn

from backend.config import ensure_data_dirs, get_settings


def main() -> None:
    settings = get_settings()
    ensure_data_dirs(settings)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=settings.port, reload=False)


if __name__ == "__main__":
    main()
