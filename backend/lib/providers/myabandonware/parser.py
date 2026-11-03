"""HTML de myabandonware.com → datos. No baja nada: recibe páginas y el ``sitemap``.

La página de un juego (``/game/{slug}-{id}``) es de una plataforma. La tabla ``gameInfo`` trae
los nombres alternativos, el año, la plataforma, el género y, no siempre, el desarrollador; el
JSON-LD, los editores en orden de lanzamiento (la tabla los ordena por nombre) y el
desarrollador (``author``). Las capturas van en una pestaña por plataforma.

``playMode`` dice "SinglePlayer" en todos los juegos, también en los de dos jugadores: no se lee.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

if TYPE_CHECKING:
    from backend.lib.providers.scraping import Pagina

BASE = "https://www.myabandonware.com"
_URL_MOBYGAMES = "mobygames.com/game/"
_SLUG_EN_SITEMAP = re.compile(r"<loc>\s*https?://www\.myabandonware\.com/game/([^<\s/]+)/?\s*</loc>")


@dataclass(frozen=True)
class Captura:
    url: str
    miniatura: str


@dataclass(frozen=True)
class Ficha:
    url: str
    title: str
    alias: tuple[str, ...]
    year: str
    plataforma: str
    developer: str
    publisher: str
    genre: str
    description: str
    # Solo las de la plataforma de la página: las otras pestañas son de otras versiones.
    capturas: tuple[Captura, ...]
    # La ficha del mismo juego en MobyGames, de los enlaces externos de la página.
    mobygames_url: str = ""


def _texto(elemento: Any) -> str:
    return " ".join(str(elemento.get_all_text()).split())


def _json_ld(page: Pagina) -> dict[str, Any]:
    for bloque in page.css('script[type="application/ld+json"]::text').getall():
        try:
            datos = json.loads(bloque)
        except ValueError:
            continue
        if isinstance(datos, dict) and datos.get("@type") == "VideoGame":
            return datos
    return {}


def _como_lista(valor: Any) -> list[str]:
    if isinstance(valor, str):
        return [valor.strip()] if valor.strip() else []
    if isinstance(valor, list):
        return [str(v).strip() for v in valor if str(v).strip()]
    return []


def _tabla(page: Pagina) -> dict[str, str]:
    """Las filas de ``table.gameInfo``: el encabezado, en minúsculas, y su texto."""
    filas: dict[str, str] = {}
    for fila in page.css("table.gameInfo tr"):
        encabezado, celda = fila.css("th"), fila.css("td")
        if encabezado and celda:
            filas[_texto(encabezado[0]).lower()] = _texto(celda[0])
    return filas


def _primero(valores: str) -> str:
    """El primero de una lista separada por comas, como la escribe la tabla."""
    return valores.split(",")[0].strip()


def _descripcion(page: Pagina) -> str:
    """Los párrafos hasta la firma ("Review By …"): lo que sigue son notas del sitio."""
    parrafos: list[str] = []
    for parrafo in page.css("div.gameDescription p"):
        if parrafo.css("span.revhotud"):
            break
        texto = _texto(parrafo)
        if texto:
            parrafos.append(texto)
    return "\n\n".join(parrafos)


def _capturas(page: Pagina, plataforma: str) -> tuple[Captura, ...]:
    """Las capturas de la pestaña de esa plataforma ("DOS")."""
    pestana = next(
        (
            str(enlace.attrib.get("data-platform", ""))
            for enlace in page.css('a[onclick*="toggleScreentabs"]')
            if _texto(enlace).lower() == plataforma.lower()
        ),
        "",
    )
    if not pestana:
        return ()
    capturas: list[Captura] = []
    selector = f'div.items.screens[data-platform="{pestana}"] a.itemListScreenshot'
    for enlace in page.css(selector):
        grande = str(enlace.attrib.get("href", ""))
        if not grande:
            continue
        imagenes = enlace.css("img")
        chica = str(imagenes[0].attrib.get("src", "")) if imagenes else ""
        capturas.append(Captura(urljoin(BASE, grande), urljoin(BASE, chica or grande)))
    return tuple(capturas)


def parse_ficha(page: Pagina, url: str) -> Ficha:
    """Lee la página de un juego; la plataforma es la de la página ("DOS")."""
    datos = _json_ld(page)
    tabla = _tabla(page)
    encabezado = page.css("h2")
    titulo = str(datos.get("name") or (_texto(encabezado[0]) if encabezado else ""))
    anio = re.search(r"\b(\d{4})\b", str(datos.get("datePublished") or tabla.get("year", "")))
    plataforma = tabla.get("platform", "")
    mobygames = next(
        (
            str(enlace.attrib.get("href", ""))
            for enlace in page.css("a[href]")
            if _URL_MOBYGAMES in str(enlace.attrib.get("href", ""))
        ),
        "",
    )
    return Ficha(
        url=url,
        title=titulo.strip(),
        alias=tuple(a.strip() for a in tabla.get("alt names", "").split(",") if a.strip()),
        year=anio.group(1) if anio else "",
        plataforma=plataforma,
        developer=next(iter(_como_lista(datos.get("author"))), "")
        or _primero(tabla.get("developer", "")),
        publisher=next(iter(_como_lista(datos.get("publisher"))), "")
        or _primero(tabla.get("publisher", "")),
        genre=", ".join(_como_lista(datos.get("genre"))) or tabla.get("genre", ""),
        description=_descripcion(page),
        capturas=_capturas(page, plataforma) if plataforma else (),
        mobygames_url=mobygames,
    )


def parse_sitemap(xml: str) -> tuple[str, ...]:
    """Los slugs de las páginas de juego del ``sitemap`` (``prince-of-persia-pd``), en orden."""
    return tuple(_SLUG_EN_SITEMAP.findall(xml))
