from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COINDOOR_", env_file=".env", extra="ignore")

    data_dir: Path = Field(default_factory=lambda: Path.home() / ".coindoor")
    host: str = "127.0.0.1"
    port: int = 8765
    ai_primary_base_url: str = ""
    ai_primary_api_key: str = ""
    ai_primary_model: str = ""
    ai_backup_base_url: str = ""
    ai_backup_api_key: str = ""
    ai_backup_model: str = ""

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"

    @property
    def tmp_dir(self) -> Path:
        return self.data_dir / "tmp"

    @property
    def games_dir(self) -> Path:
        return self.data_dir / "juegos"

    @property
    def systems_path(self) -> Path:
        return self.data_dir / "sistemas.json"

    @property
    def quotas_path(self) -> Path:
        return self.data_dir / "cuotas.json"


def ensure_data_dirs(settings: Settings) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    settings.games_dir.mkdir(parents=True, exist_ok=True)
    settings.tmp_dir.mkdir(parents=True, exist_ok=True)
    for child in settings.tmp_dir.iterdir():
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            import shutil

            shutil.rmtree(child)


_override: Settings | None = None


def set_settings(settings: Settings | None) -> None:
    global _override
    _override = settings
    get_settings.cache_clear()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return _override or Settings()
