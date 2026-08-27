from __future__ import annotations

import threading
from collections.abc import Sequence

from backend.config import Settings
from backend.lib.domain.fielddefs import identity_keys, image_keys
from backend.lib.providers.arcadedb.proveedor import ArcadeDbProvider
from backend.lib.providers.base import Proveedor
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.launchbox.proveedor import LaunchboxImageProvider
from backend.lib.providers.referencia.images import ImageSearchProvider
from backend.lib.providers.referencia.youtube import YoutubeReferenceProvider
from backend.store.cuotas import QuotasStore

# Tabla campo → proveedores, en orden. Sumar una fuente es una fila; ver ADR-0013.
_ARCADEDB_IDENTITY = ("arcadedb", "ia_primary", "ia_backup")
_ARCADEDB_TEXT = ("arcadedb", "ia_primary", "ia_backup")
_ARCADEDB_IMAGE = ("arcadedb", "image_search", "launchbox")
_ARCADEDB_VIDEO = ("arcadedb", "youtube_referencia")

_TABLE: dict[str, tuple[str, ...]] = {
    **{key: _ARCADEDB_IDENTITY for key in identity_keys()},
    **{key: _ARCADEDB_IMAGE for key in image_keys()},
    "sinopsis": _ARCADEDB_TEXT,
    "review": ("ia_primary", "ia_backup"),
    "cheats": _ARCADEDB_TEXT,
    "video": _ARCADEDB_VIDEO,
}


def providers_for(
    key: str,
    settings: Settings,
    cancel_event: threading.Event | None = None,
) -> Sequence[Proveedor]:
    quotas = QuotasStore(settings.quotas_path)
    providers: list[Proveedor] = []
    for name in _TABLE.get(key, ()):
        provider = _build(name, settings, quotas, cancel_event)
        if provider is not None:
            providers.append(provider)
    return tuple(providers)


def _build(
    name: str,
    settings: Settings,
    quotas: QuotasStore,
    cancel_event: threading.Event | None,
) -> Proveedor | None:
    if name == "ia_primary":
        config = AiModelConfig(
            settings.ai_primary_base_url,
            settings.ai_primary_api_key,
            settings.ai_primary_model,
        )
        return _ia_provider(config, quotas, cancel_event)
    if name == "ia_backup":
        config = AiModelConfig(
            settings.ai_backup_base_url,
            settings.ai_backup_api_key,
            settings.ai_backup_model,
        )
        return _ia_provider(config, quotas, cancel_event)
    if name == "youtube_referencia":
        return YoutubeReferenceProvider()
    if name == "image_search":
        return ImageSearchProvider()
    if name == "launchbox":
        return LaunchboxImageProvider()
    if name == "arcadedb":
        return _arcadedb_provider(settings, quotas, cancel_event)
    raise ValueError(f"Proveedor desconocido: {name}")


def _ia_provider(
    config: AiModelConfig,
    quotas: QuotasStore,
    cancel_event: threading.Event | None,
) -> IaGenerador | None:
    if not config.base_url or not config.api_key or not config.model:
        return None
    http = ProviderHttpClient(
        f"ia:{config.model}",
        IaGenerador.limite,
        quotas,
        timeout=IaGenerador.timeout,
        cancel_event=cancel_event,
    )
    return IaGenerador(config, http)


def _arcadedb_provider(
    settings: Settings,
    quotas: QuotasStore,
    cancel_event: threading.Event | None,
) -> ArcadeDbProvider:
    http = ProviderHttpClient(
        "arcadedb",
        ArcadeDbProvider.limite,
        quotas,
        timeout=ArcadeDbProvider.timeout,
        cancel_event=cancel_event,
    )
    return ArcadeDbProvider(settings, http)
