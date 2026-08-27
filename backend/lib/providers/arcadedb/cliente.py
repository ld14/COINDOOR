"""Cliente de ArcadeDB (adb.arcadeitalia.net), por nombre de romset de MAME.

Hacen falta dos endpoints: ``query_mame`` trae identidad, texto y video;
``query_mame_media`` trae el resto de las imagenes y el manual. Se consultan
juntos y se fusionan, con memo para que N campos no cuesten 2N peticiones.

Atribucion exigida por los terminos del servicio: Arcade Database by motoschifo
(https://adb.arcadeitalia.net). El campo ``history`` es (C) arcade-history.com.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from backend.lib.providers.arcadedb.parser import (
    CabinetButtonData,
    HistoryParts,
    parse_buttons,
    parse_history,
)
from backend.lib.providers.http import ProviderHttpClient, ProviderHttpError

BASE_URL = "https://adb.arcadeitalia.net/service_scraper.php"
JUEGO_URL = "https://adb.arcadeitalia.net/?mame={romset}"
YOUTUBE_URL = "https://www.youtube.com/watch?v={video_id}"

ATRIBUCION = (
    "Datos de Arcade Database (motoschifo) — adb.arcadeitalia.net · "
    "Historia (C) arcade-history.com"
)

# ponytail: memo sin TTL, vive lo que el proceso. Es una app de escritorio que se
# reinicia; poner un lru_cache con tope si algun dia importa.
_memo: dict[str, ArcadeGame | None] = {}
_memo_lock = threading.Lock()


@dataclass(frozen=True)
class ArcadeGame:
    romset: str
    title: str = ""
    short_title: str = ""
    manufacturer: str = ""
    year: str = ""
    genre: str = ""
    players: str = ""
    nplayers: str = ""
    serie: str = ""
    cloneof: str = ""
    emulator: str = ""
    screen_orientation: str = ""
    screen_resolution: str = ""
    input_controls: str = ""
    input_buttons: int = 0
    buttons: tuple[CabinetButtonData, ...] = ()
    youtube_video_id: str = ""
    video_url: str = ""
    manual_url: str = ""
    images: dict[str, str] = field(default_factory=dict)
    history: HistoryParts = field(default_factory=HistoryParts)
    urls_consultadas: tuple[str, ...] = ()

    @property
    def origen_url(self) -> str:
        return JUEGO_URL.format(romset=self.romset)

    @property
    def youtube_url(self) -> str:
        if not self.youtube_video_id:
            return ""
        return YOUTUBE_URL.format(video_id=self.youtube_video_id)

    def image(self, *tipos: str) -> str:
        """Primera imagen no vacia entre ``tipos``. ArcadeDB devuelve "" cuando falta."""
        for tipo in tipos:
            url = self.images.get(tipo, "")
            if url:
                return url
        return ""


def fetch(
    romset: str,
    http: ProviderHttpClient,
    *,
    max_length: int | None = None,
) -> ArcadeGame | None:
    """Devuelve el juego, o ``None`` si ArcadeDB no conoce el romset.

    Un romset desconocido responde ``{"release":6,"result":[]}`` con HTTP 200: no
    es un error del proveedor y no debe contar como caida. Por eso devuelve
    ``None`` en vez de levantar, y el cortocircuito no se entera.
    """
    clave = romset.strip().lower()
    if not clave:
        return None
    with _memo_lock:
        if clave in _memo:
            return _memo[clave]

    juego = _fetch_sin_memo(clave, http, max_length)
    with _memo_lock:
        _memo[clave] = juego
    return juego


def olvidar(romset: str) -> None:
    """Saca un romset del memo, para que un reintento explicito vuelva a la red."""
    with _memo_lock:
        _memo.pop(romset.strip().lower(), None)


def fetch_con_padre(
    romset: str,
    http_factory: Callable[[], ProviderHttpClient],
    *,
    max_length: int | None = None,
) -> tuple[ArcadeGame | None, frozenset[str]]:
    """Como ``fetch``, pero completa las imagenes con las del romset padre.

    Un clon publica menos tipos que su padre: ``ffightub`` trae 8 y ``ffight`` 14,
    incluidos ``flyer``, ``marquee`` y ``cabinet``, que son justo los que dejan la
    caratula y la marquesina vacias.

    **Solo se fusionan las imagenes.** La identidad del padre no se toca: puede ser
    otra region o version y pisaria el titulo y el año del juego que se cargo.

    Recibe una fabrica y no un cliente porque son dos peticiones y
    ``ProviderHttpClient`` cierra su httpx.Client al salir del ``with``.

    Devuelve el juego y que tipos aporto el padre, para que la galeria pueda
    marcarlos.
    """
    juego = fetch(romset, http_factory(), max_length=max_length)
    if juego is None or not juego.cloneof:
        return juego, frozenset()

    padre = fetch(juego.cloneof, http_factory(), max_length=max_length)
    if padre is None:
        return juego, frozenset()

    # El clon manda donde publica algo propio; el padre solo rellena huecos.
    del_padre = frozenset(padre.images) - frozenset(juego.images)
    if not del_padre:
        return juego, frozenset()
    return replace(juego, images={**padre.images, **juego.images}), del_padre


def _fetch_sin_memo(
    romset: str,
    http: ProviderHttpClient,
    max_length: int | None,
) -> ArcadeGame | None:
    with http:
        datos = _consultar(http, "query_mame", romset)
        if datos is None:
            return None
        media = _consultar(http, "query_mame_media", romset) or {}
    urls = tuple(
        url
        for url in (datos.get("_url_consultada"), media.get("_url_consultada"))
        if isinstance(url, str) and url
    )
    return _armar(romset, datos, media, urls, max_length)


def _consultar(
    http: ProviderHttpClient,
    ajax: str,
    romset: str,
) -> dict[str, Any] | None:
    """Una peticion. ``None`` si el romset no existe o la respuesta no sirve."""
    try:
        respuesta = http.get_json(BASE_URL, params={"ajax": ajax, "game_name": romset})
    except ProviderHttpError:
        if ajax == "query_mame":
            raise
        return None  # el endpoint de media es opcional: sin el, se pierde el manual
    cuerpo = respuesta.json
    if not isinstance(cuerpo, dict):
        return None
    resultados = cuerpo.get("result")
    if not isinstance(resultados, list) or not resultados:
        return None
    primero = resultados[0]
    if not isinstance(primero, dict):
        return None
    return {**primero, "_url_consultada": respuesta.url}


def _armar(
    romset: str,
    datos: dict[str, Any],
    media: dict[str, Any],
    urls: tuple[str, ...],
    max_length: int | None,
) -> ArcadeGame:
    crudo = {**datos, **{k: v for k, v in media.items() if v}}
    return ArcadeGame(
        romset=romset,
        title=_texto(crudo, "title"),
        short_title=_texto(crudo, "short_title"),
        manufacturer=_texto(crudo, "manufacturer"),
        year=_texto(crudo, "year"),
        genre=_texto(crudo, "genre"),
        players=_texto(crudo, "players"),
        nplayers=_texto(crudo, "nplayers"),
        serie=_texto(crudo, "serie"),
        cloneof=_texto(crudo, "cloneof"),
        emulator=_texto(crudo, "emulator_name"),
        screen_orientation=_texto(crudo, "screen_orientation"),
        screen_resolution=_texto(crudo, "screen_resolution"),
        input_controls=_texto(crudo, "input_controls"),
        input_buttons=_entero(crudo, "input_buttons"),
        buttons=parse_buttons(_texto(crudo, "buttons_colors")),
        youtube_video_id=_texto(crudo, "youtube_video_id"),
        video_url=_texto(crudo, "url_video_shortplay_hd") or _texto(crudo, "url_video_shortplay"),
        manual_url=_texto(crudo, "url_manual"),
        images=_imagenes(crudo),
        history=parse_history(_texto(crudo, "history"), max_length=max_length),
        urls_consultadas=urls,
    )


def _imagenes(crudo: dict[str, Any]) -> dict[str, str]:
    """``url_image_marquee`` -> ``{"marquee": "https://..."}``, sin las vacias."""
    imagenes = {}
    for clave, valor in crudo.items():
        if not clave.startswith("url_image_"):
            continue
        url = str(valor).strip() if valor else ""
        if url:
            imagenes[clave.removeprefix("url_image_")] = url
    return imagenes


def _texto(crudo: dict[str, Any], clave: str) -> str:
    valor = crudo.get(clave)
    return "" if valor is None else str(valor).strip()


def _entero(crudo: dict[str, Any], clave: str) -> int:
    try:
        return int(crudo.get(clave) or 0)
    except (TypeError, ValueError):
        return 0
