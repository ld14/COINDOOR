from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COINDOOR_", env_file=".env", extra="ignore")

    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "games")
    host: str = "127.0.0.1"
    port: int = 8765
    ai_primary_base_url: str = ""
    ai_primary_api_key: str = ""
    ai_primary_model: str = ""
    ai_backup_base_url: str = ""
    ai_backup_api_key: str = ""
    ai_backup_model: str = ""
    # Buscador web, hoy solo para trucos (ADR-0019): lo que encuentra se lo
    # estructura ai_primary/ai_backup. Sin api_key el campo `cheats` se queda sin
    # sugerencia, y es deliberado: un modelo sin evidencia inventa códigos.
    search_base_url: str = "https://api.tavily.com"
    search_api_key: str = ""
    # Scraping con navegador (ADR-0024). El timeout es por página y Scrapling lo usa además
    # como tope de sus esperas mientras resuelve Cloudflare: más alto no ayuda, solo alarga
    # el peor caso. Su documentación pide al menos 60 s con `solve_cloudflare`. El ritmo es la
    # espera entre pedidos al mismo sitio.
    scraping_timeout: float = 60.0
    scraping_pace: float = 3.0
    # Precalentar MobyGames al arrancar (ADR-0025): resuelve el desafío de Cloudflare antes
    # de que el usuario pida algo. `false` lo apaga.
    scraping_warmup: bool = True

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

    @property
    def browser_profile_dir(self) -> Path:
        """Perfil del navegador de scraping: guarda la cookie de Cloudflare entre consultas."""
        return self.data_dir / "navegador"

    @property
    def config_path(self) -> Path:
        return self.data_dir / "configuracion.json"


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
