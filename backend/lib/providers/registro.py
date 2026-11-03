from __future__ import annotations

import threading
from collections.abc import Sequence

from backend.config import Settings
from backend.lib.domain.fielddefs import identity_keys, image_keys
from backend.lib.providers.arcadedb.proveedor import ArcadeDbProvider
from backend.lib.providers.base import Limite, Proveedor
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.client import OpenAiCompatibleClient
from backend.lib.providers.ia.generador import AiModelConfig, IaGenerador
from backend.lib.providers.ia.trucos_web import TavilyClient, TrucosWebGenerador
from backend.lib.providers.launchbox.proveedor import LaunchboxImageProvider
from backend.lib.providers.mobygames.proveedor import MobyGamesProvider
from backend.lib.providers.myabandonware.proveedor import MyAbandonwareProvider
from backend.lib.providers.referencia.images import ImageSearchProvider
from backend.lib.providers.referencia.youtube import YoutubeReferenceProvider
from backend.lib.providers.scraping import ScrapingClient, navegador_disponible
from backend.store.cuotas import QuotasStore
from backend.store.juegos import GamesStore

# Tabla campo → proveedores, en orden. Sumar una fuente es una fila; ver ADR-0013.
# El orden de PC/DOS es el de ADR-0027: myabandonware, Launchbox, la IA y, al final, MobyGames.
# Ninguna cadena de identidad tiene IA: si ninguna fuente tiene el dato, el orquestador la
# consulta como último recurso (ADR-0026), antes de las fuentes de ULTIMO_RECURSO.
_IDENTIDAD = ("arcadedb", "myabandonware", "launchbox", "mobygames")
_TITULO = ("arcadedb", "myabandonware", "mobygames")
# myabandonware no da jugadores (su `playMode` dice "SinglePlayer" en todos los juegos) y solo
# MobyGames da el formato.
_JUGADORES = ("arcadedb", "launchbox", "mobygames")
_FORMATO = ("arcadedb", "mobygames")
_SINOPSIS = ("arcadedb", "myabandonware", "ia_primary", "ia_backup", "mobygames")
# Trucos NO caen a los modelos a secas: sin evidencia devuelven vacíos falsos y
# códigos inventados, que es peor que no sugerir nada (ADR-0019).
_ARCADEDB_CHEATS = ("arcadedb", "trucos_web")
# Imágenes: primero las de la edición y al final el buscador, que no sabe de ediciones
# (feature 022). myabandonware no tiene carátulas.
_CARATULA = ("arcadedb", "launchbox", "mobygames", "image_search")
_CAPTURA = ("arcadedb", "myabandonware", "launchbox", "mobygames", "image_search")
_ARCADEDB_IMAGE = ("arcadedb", "launchbox", "image_search")
_ARCADEDB_VIDEO = ("arcadedb", "youtube_referencia")

_TABLE: dict[str, tuple[str, ...]] = {
    **{key: _IDENTIDAD for key in identity_keys()},
    "title": _TITULO,
    "players": _JUGADORES,
    "format": _FORMATO,
    **{key: _ARCADEDB_IMAGE for key in image_keys()},
    "caratula": _CARATULA,
    "captura": _CAPTURA,
    "sinopsis": _SINOPSIS,
    # ArcadeDB no tiene un "objetivo": solo la IA, y siempre como candidato a revisar.
    **{key: ("ia_primary", "ia_backup") for key in ("objetivo", "primerosPasos", "reglasEsenciales", "modo")},  # noqa: E501
    "review": ("ia_primary", "ia_backup"),
    "cheats": _ARCADEDB_CHEATS,
    "video": _ARCADEDB_VIDEO,
}

# Fuentes de último recurso (ADR-0027): se consultan solo si ninguna fuente anterior de la
# cadena dio un candidato para el campo, y la IA de respaldo va antes que ellas.
ULTIMO_RECURSO = frozenset({MobyGamesProvider.nombre})


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


def proveedor_mobygames(settings: Settings) -> MobyGamesProvider | None:
    """MobyGames fuera de una cadena: la galería suma todas las fuentes, no las recorre en orden."""
    return _mobygames_provider(settings, QuotasStore(settings.quotas_path), None)


def proveedores_ia(
    settings: Settings,
    cancel_event: threading.Event | None = None,
) -> Sequence[Proveedor]:
    """Los modelos configurados, primario y respaldo: el último recurso de la identidad
    (ADR-0026), que el orquestador consulta solo si ninguna fuente factual tuvo el dato."""
    quotas = QuotasStore(settings.quotas_path)
    modelos = (_build(name, settings, quotas, cancel_event) for name in ("ia_primary", "ia_backup"))
    return tuple(modelo for modelo in modelos if modelo is not None)


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
    if name == "trucos_web":
        return _trucos_web_provider(settings, quotas, cancel_event)
    if name == "youtube_referencia":
        return YoutubeReferenceProvider()
    if name == "image_search":
        return ImageSearchProvider()
    if name == "launchbox":
        return LaunchboxImageProvider()
    if name == "arcadedb":
        return _arcadedb_provider(settings, quotas, cancel_event)
    if name == "myabandonware":
        return _myabandonware_provider(settings, quotas, cancel_event)
    if name == "mobygames":
        return _mobygames_provider(settings, quotas, cancel_event)
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


def _trucos_web_provider(
    settings: Settings,
    quotas: QuotasStore,
    cancel_event: threading.Event | None,
) -> TrucosWebGenerador | None:
    """Buscador + los modelos ya configurados (ADR-0019). Sin buscador no hay
    proveedor: pasarle el prompt a un modelo sin evidencia es lo que se descartó."""
    if not settings.search_base_url or not settings.search_api_key:
        return None
    buscador = TavilyClient(
        settings.search_base_url,
        settings.search_api_key,
        ProviderHttpClient(
            "tavily",
            TrucosWebGenerador.limite,
            quotas,
            timeout=TrucosWebGenerador.timeout,
            cancel_event=cancel_event,
        ),
    )
    modelos = []
    for config in (
        AiModelConfig(
            settings.ai_primary_base_url,
            settings.ai_primary_api_key,
            settings.ai_primary_model,
        ),
        AiModelConfig(
            settings.ai_backup_base_url,
            settings.ai_backup_api_key,
            settings.ai_backup_model,
        ),
    ):
        if not (config.base_url and config.api_key and config.model):
            continue
        http = ProviderHttpClient(
            f"ia:{config.model}",
            IaGenerador.limite,
            quotas,
            timeout=IaGenerador.timeout,
            cancel_event=cancel_event,
        )
        modelos.append(
            OpenAiCompatibleClient(config.base_url, config.api_key, config.model, http),
        )
    if not modelos:
        return None
    return TrucosWebGenerador(buscador, modelos)


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


def _mobygames_provider(
    settings: Settings,
    quotas: QuotasStore,
    cancel_event: threading.Event | None,
) -> MobyGamesProvider | None:
    """Sin Chromium no hay proveedor: la app arranca igual y las cadenas siguen de largo."""
    if not navegador_disponible():
        return None

    def cliente() -> ScrapingClient:
        return ScrapingClient(
            "mobygames",
            Limite(espera_min=settings.scraping_pace),
            quotas,
            timeout=settings.scraping_timeout,
            cancel_event=cancel_event,
            perfil=settings.browser_profile_dir,
        )

    # myabandonware enlaza la ficha de MobyGames del juego: con ella no hace falta buscar.
    myabandonware = _myabandonware_provider(settings, quotas, cancel_event)
    return MobyGamesProvider(
        GamesStore(settings.games_dir),
        cliente,
        timeout=settings.scraping_timeout,
        pace=settings.scraping_pace,
        enlace=myabandonware.enlace_mobygames,
    )


def _myabandonware_provider(
    settings: Settings,
    quotas: QuotasStore,
    cancel_event: threading.Event | None,
) -> MyAbandonwareProvider:
    """HTTP común, sin navegador: el sitio no tiene Cloudflare (ADR-0027)."""

    def http() -> ProviderHttpClient:
        return ProviderHttpClient(
            "myabandonware",
            MyAbandonwareProvider.limite,
            quotas,
            timeout=MyAbandonwareProvider.timeout,
            cancel_event=cancel_event,
        )

    return MyAbandonwareProvider(http, settings.myabandonware_dir)
