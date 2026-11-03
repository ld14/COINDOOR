"""Busca un juego en MobyGames y devuelve su ficha para una plataforma.

La búsqueda general (``/search/?q=…&type=game``) trae 12 filas por página y su orden
compara palabras sueltas, no la frase: el juego buscado puede estar en cualquier fila. Por
eso la elección no mira la posición sino los datos de cada fila (ver ``elegir``).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

from backend.lib.providers import coincidencia
from backend.lib.providers.coincidencia import normalizar
from backend.lib.providers.mobygames.parser import (
    Ficha,
    Fila,
    Specs,
    parse_busqueda,
    parse_capturas,
    parse_ficha,
    parse_portada_grande,
    parse_portadas,
    parse_specs,
)

if TYPE_CHECKING:
    from backend.lib.providers.scraping import ScrapingClient

__all__ = [
    "BASE",
    "FichaCompleta",
    "Imagen",
    "buscar_ficha",
    "buscar_imagenes",
    "elegir",
    "normalizar",
    "olvidar",
]

BASE = "https://www.mobygames.com"
# Cada portada pide una página más para la imagen grande, a 3 s: tres alcanzan para elegir
# entre ediciones (la original, la española…).


@dataclass(frozen=True)
class FichaCompleta:
    ficha: Ficha
    specs: Specs


@dataclass(frozen=True)
class Imagen:
    media_url: str
    preview_url: str
    etiqueta: str
    origen_url: str


def elegir(
    filas: tuple[Fila, ...],
    titulo: str,
    anio: str | None,
    plataforma: str,
) -> Fila | None:
    """La fila de la ficha, o ``None`` si no hay una que lo sea sin ambigüedad.

    Solo cuentan las filas con esa plataforma; entre ellas elige la regla común de
    ``coincidencia`` con el título, los "AKA:" y el año de esa plataforma.
    """
    clave = plataforma.lower()
    con_plataforma = [f for f in filas if clave in f.plataformas]
    return coincidencia.elegir(
        con_plataforma,
        titulo,
        anio,
        titulos_de=lambda f: (f.title, *f.alias),
        principal_de=lambda f: f.title,
        anio_de=lambda f: coincidencia.anio_entero(f.plataformas.get(clave)),
    )


# Dos memorias mientras corre el proceso: qué ficha eligió cada búsqueda (o ninguna) y cada
# ficha por su URL. La precarga busca por título y "Sugerir" llega después con la URL que
# quedó en la procedencia: los dos caminos terminan en la misma ficha ya bajada.
_busquedas: dict[tuple[str, str, str], str | None] = {}
_fichas: dict[tuple[str, str], FichaCompleta] = {}
_imagenes: dict[tuple[str, str], tuple[Imagen, ...]] = {}
_memo_lock = threading.Lock()


def olvidar() -> None:
    with _memo_lock:
        _busquedas.clear()
        _fichas.clear()
        _imagenes.clear()


def _base(url: str) -> str:
    return url if url.endswith("/") else url + "/"


def buscar_ficha(
    client: ScrapingClient,
    titulo: str,
    anio: str | None,
    plataforma: str,
    *,
    ficha_url: str | None = None,
) -> FichaCompleta | None:
    """Busca el juego y baja su ficha y sus specs; ``None`` si no hay un resultado claro.

    ``ficha_url`` salta la búsqueda (la procedencia ya trae el enlace de MobyGames). La
    búsqueda y la ficha quedan en memoria mientras corre el proceso: las sugerencias de
    distintos campos y la precarga las reusan sin volver a bajar las páginas.
    """
    url = ficha_url
    if url is None:
        busqueda = (normalizar(titulo), anio or "", plataforma.lower())
        with _memo_lock:
            conocida = busqueda in _busquedas
            url = _busquedas.get(busqueda)
        if not conocida:
            pagina = client.get_page(f"{BASE}/search/?q={quote_plus(titulo.strip())}&type=game")
            fila = elegir(parse_busqueda(pagina), titulo, anio, plataforma)
            url = fila.url if fila else None
            with _memo_lock:
                _busquedas[busqueda] = url
    if not url:
        return None

    base = _base(url)
    clave = (base, plataforma.lower())
    with _memo_lock:
        guardada = _fichas.get(clave)
    if guardada is not None:
        return guardada
    ficha = parse_ficha(client.get_page(base), plataforma)
    specs = parse_specs(client.get_page(base + "specs/"), plataforma)
    resultado = FichaCompleta(ficha, specs)
    with _memo_lock:
        _fichas[clave] = resultado
    return resultado


def buscar_imagenes(
    client: ScrapingClient,
    titulo: str,
    anio: str | None,
    plataforma: str,
    clave: str,
    *,
    ficha_url: str | None = None,
    cuantas: int | None = None,
) -> tuple[Imagen, ...]:
    """Carátulas (``caratula``) o capturas (``captura``) de la plataforma, de la misma ficha
    que eligió ``buscar_ficha``: la edición correcta, no cualquier juego con ese nombre.

    Todas, salvo que se pida ``cuantas``: cada portada es una página más por el navegador. Una
    respuesta recortada no queda en memoria.
    """
    if clave not in ("caratula", "captura"):
        return ()
    completa = buscar_ficha(client, titulo, anio, plataforma, ficha_url=ficha_url)
    if completa is None or not completa.ficha.plataforma_slug:
        return ()
    base = _base(completa.ficha.url)
    memo = (base, clave)
    with _memo_lock:
        guardadas = _imagenes.get(memo)
    if guardadas is not None:
        return guardadas[:cuantas]

    slug = completa.ficha.plataforma_slug
    imagenes: list[Imagen] = []
    if clave == "caratula":
        portadas = parse_portadas(client.get_page(f"{base}covers/{slug}/"))[:cuantas]
        for portada in portadas:
            grande = parse_portada_grande(client.get_page(portada.enlace)) or portada.miniatura
            pais = f" ({portada.pais})" if portada.pais else ""
            imagenes.append(
                Imagen(grande, portada.miniatura, f"Portada frontal{pais}", portada.enlace)
            )
    else:
        capturas = parse_capturas(client.get_page(f"{base}screenshots/{slug}/"))[:cuantas]
        for captura in capturas:
            imagenes.append(
                Imagen(
                    captura.miniatura,
                    captura.miniatura,
                    captura.leyenda or "Captura",
                    captura.url,
                )
            )
    resultado = tuple(imagenes)
    if cuantas is None:
        with _memo_lock:
            _imagenes[memo] = resultado
    return resultado
