"""HTML de MobyGames → datos. No baja nada y no conoce a Scrapling: recibe páginas.

La ficha (``/game/{id}/{slug}/``) trae título, año por plataforma, desarrollador, editor por
plataforma, género, nota de críticos y descripción. Los jugadores y el soporte salen de
``/game/{id}/{slug}/specs/``, que lista las specs de todas las plataformas.

El HTML que baja Scrapling es el de la página ya procesada: solo se leen el JSON-LD y listas
HTML, nunca los atributos de los componentes de Vue.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.lib.providers.scraping import Pagina

# Soporte de MobyGames → soporte físico del contrato (``bundle/gamejson.py``). Lo que no
# está acá ("Download", "Cartridge" de más de un tipo…) no tiene equivalente y se omite.
_SOPORTES = (
    ("floppy", "Diskette"),
    ("disk", "Diskette"),
    ("cartridge", "Cartucho"),
    ("dvd", "DVD"),
    ("cd", "CD"),
)
_ETIQUETAS_JUGADORES = ("number of players supported", "number of offline players")


@dataclass(frozen=True)
class Ficha:
    url: str
    title: str
    alias: tuple[str, ...]
    year: str
    developer: str
    publisher: str
    genre: str
    description: str
    score: int | None
    # El nombre de la plataforma en las URL de MobyGames ("dos"): lleva a las carátulas y las
    # capturas de esa plataforma.
    plataforma_slug: str = ""


@dataclass(frozen=True)
class Specs:
    players: str
    formatos: tuple[str, ...]


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
        return [valor] if valor.strip() else []
    if isinstance(valor, list):
        return [str(v).strip() for v in valor if str(v).strip()]
    return []


def _mismo(a: str, b: str) -> bool:
    return a.strip().lower() == b.strip().lower()


def _anio(page: Pagina, plataforma: str) -> str:
    """El año de esa plataforma en 'Releases by Date'; no el del primer lanzamiento."""
    for fila in page.css("#platformLinks li"):
        enlaces = fila.css("a")
        if len(enlaces) < 2:
            continue
        nombre = _texto(enlaces[-1])
        if _mismo(nombre, plataforma):
            return _texto(enlaces[0])
    return ""


def _editor(page: Pagina, plataforma: str) -> str:
    """El primer editor de la lista que publicó en esa plataforma."""
    for enlace in page.css("#publisherLinks li a"):
        try:
            popover = json.loads(enlace.attrib.get("data-popover", "{}"))
        except ValueError:
            continue
        plataformas = popover.get("platforms", [])
        if any(_mismo(str(p), plataforma) for p in plataformas):
            return _texto(enlace)
    return ""


def _nota_criticos(page: Pagina) -> int | None:
    for dt in page.css(".info-scores dt"):
        if _mismo(_texto(dt), "critics"):
            dd = dt.xpath("following-sibling::dd[1]")
            if not dd:
                return None
            encontrado = re.search(r"(\d{1,3})\s*%", _texto(dd[0]))
            return int(encontrado.group(1)) if encontrado else None
    return None


def _slug_plataforma(page: Pagina, plataforma: str) -> str:
    """El slug de la plataforma, del enlace "/platform/{slug}/" de su fila en "Releases"."""
    for fila in page.css("#platformLinks li"):
        enlaces = fila.css("a")
        if enlaces and _mismo(_texto(enlaces[-1]), plataforma):
            encontrado = re.search(r"/platform/([^/]+)/", str(enlaces[-1].attrib.get("href", "")))
            if encontrado:
                return encontrado.group(1)
    return ""


def parse_ficha(page: Pagina, plataforma: str) -> Ficha:
    """Lee la ficha de un juego para una plataforma (el nombre de MobyGames, ej. "DOS")."""
    datos = _json_ld(page)
    encabezado = page.css("h1")
    titulo = str(datos.get("name") or (_texto(encabezado[0]) if encabezado else ""))
    desarrolladores = page.css("#developerLinks li a")
    parrafos = [_texto(p) for p in page.css("#description-text p")]
    canonico = page.css('link[rel="canonical"]::attr(href)').get() or ""
    return Ficha(
        url=str(canonico),
        title=titulo.strip(),
        alias=tuple(_como_lista(datos.get("alternateName"))),
        year=_anio(page, plataforma),
        developer=_texto(desarrolladores[0]) if desarrolladores else "",
        publisher=_editor(page, plataforma),
        genre=", ".join(_como_lista(datos.get("genre"))),
        description="\n\n".join(p for p in parrafos if p),
        score=_nota_criticos(page),
        plataforma_slug=_slug_plataforma(page, plataforma),
    )


def _formato(soporte: str) -> str:
    minusculas = soporte.lower()
    for marca, formato in _SOPORTES:
        if re.search(rf"\b{marca}\b", minusculas):
            return formato
    return ""


def _jugadores(valores: list[str]) -> str:
    cifras = [int(n) for valor in valores for n in re.findall(r"\d+", valor)]
    if not cifras:
        return ""
    menor, mayor = min(cifras), max(cifras)
    return str(menor) if menor == mayor else f"{menor}-{mayor}"


def parse_specs(page: Pagina, plataforma: str) -> Specs:
    """Jugadores y soporte físico de una plataforma, de la página de specs."""
    en_bloque = False
    jugadores: list[str] = []
    formatos: list[str] = []
    for fila in page.css("table tr"):
        encabezado = fila.css("h4")
        if encabezado:
            # El h4 trae además el enlace "+" de contribuir: solo cuenta su propio texto.
            propio = " ".join(str(encabezado[0].css("::text").get() or "").split())
            en_bloque = _mismo(propio, plataforma)
            continue
        if not en_bloque:
            continue
        celdas = fila.css("td")
        if len(celdas) < 2:
            continue
        etiqueta = _texto(celdas[0]).rstrip(":").strip().lower()
        valores = [_texto(a) for a in celdas[1].css("li")]
        if etiqueta in _ETIQUETAS_JUGADORES:
            jugadores.extend(valores)
        elif etiqueta == "media type":
            for valor in valores:
                formato = _formato(valor)
                if formato and formato not in formatos:
                    formatos.append(formato)
    return Specs(players=_jugadores(jugadores), formatos=tuple(formatos))


@dataclass(frozen=True)
class Fila:
    """Una fila de juego de la búsqueda: título, títulos alternativos y año por plataforma."""

    id: str
    title: str
    url: str
    alias: tuple[str, ...]
    plataformas: Mapping[str, str]  # nombre de plataforma en minúsculas → año


def _alias(td: Any) -> tuple[str, ...]:
    for chico in td.css("small.text-muted"):
        texto = _texto(chico)
        if texto.startswith("AKA:"):
            return tuple(a.strip() for a in texto[4:].split(",") if a.strip())
    return ()


def _plataformas(td: Any) -> dict[str, str]:
    """'DOS (1992), Amiga (1992)' → {'dos': '1992', 'amiga': '1992'}."""
    listas = td.xpath("./small[small]")
    if not listas:
        return {}
    encontradas = re.findall(r"([^(),]+?)\s*\((\d{4})\)", _texto(listas[0]))
    return {nombre.strip().lower(): anio for nombre, anio in encontradas}


def parse_busqueda(page: Pagina) -> tuple[Fila, ...]:
    """Las filas de juego de la primera página de resultados.

    Con la búsqueda general se mezclan filas de grupo, persona o empresa: se descartan.
    """
    filas = []
    for tr in page.css("#search-results tr"):
        if tr.attrib.get("data-track-target-type") != "game":
            continue
        celdas = tr.css("td")
        enlaces = celdas[1].css("b a") if len(celdas) > 1 else []
        if not enlaces:
            continue
        filas.append(
            Fila(
                id=str(tr.attrib.get("data-track-target-id", "")),
                title=_texto(enlaces[0]),
                url=str(enlaces[0].attrib.get("href", "")),
                alias=_alias(celdas[1]),
                plataformas=_plataformas(celdas[1]),
            )
        )
    return tuple(filas)


@dataclass(frozen=True)
class Portada:
    """Una portada frontal de la página de carátulas de una plataforma."""

    enlace: str  # la página de esa carátula, donde está la imagen grande
    miniatura: str
    pais: str


@dataclass(frozen=True)
class Captura:
    url: str
    miniatura: str
    leyenda: str


def parse_portadas(page: Pagina) -> tuple[Portada, ...]:
    """Las portadas frontales de la página de carátulas, en el orden de la página.

    Cada edición es una ``<section>`` con una tabla (país, empaque) y una ``<figure>`` por
    imagen, rotulada en ``figcaption`` ("Front Cover", "Back Cover"…).
    """
    portadas: list[Portada] = []
    for seccion in page.css("main section"):
        pais = ""
        for fila in seccion.css("tr"):
            celdas = fila.css("td")
            if len(celdas) >= 2 and _texto(celdas[0]).rstrip(":").lower() == "country":
                pais = ", ".join(_texto(li) for li in celdas[1].css("li") if _texto(li))
        for figura in seccion.css("figure"):
            leyenda = figura.css("figcaption")
            enlace = figura.css("a")
            imagen = figura.css("img")
            if not leyenda or not enlace or not imagen:
                continue
            if _texto(leyenda[0]).lower() != "front cover":
                continue
            portadas.append(
                Portada(
                    enlace=str(enlace[0].attrib.get("href", "")),
                    miniatura=str(imagen[0].attrib.get("src", "")),
                    pais=pais,
                )
            )
    return tuple(portadas)


def parse_portada_grande(page: Pagina) -> str:
    """La imagen grande de la página de una carátula (su ``alt`` empieza con "Front Cover")."""
    for imagen in page.css("main img"):
        if str(imagen.attrib.get("alt", "")).lower().startswith("front cover"):
            return str(imagen.attrib.get("src", ""))
    return ""


def parse_capturas(page: Pagina) -> tuple[Captura, ...]:
    """Las capturas de la página de una plataforma; en DOS (320×200) la miniatura ya es la
    imagen completa."""
    capturas: list[Captura] = []
    for figura in page.css("main figure"):
        enlace = figura.css("a")
        imagen = figura.css("img")
        if not enlace or not imagen:
            continue
        leyenda = figura.css("figcaption")
        capturas.append(
            Captura(
                url=str(enlace[0].attrib.get("href", "")),
                miniatura=str(imagen[0].attrib.get("src", "")),
                leyenda=_texto(leyenda[0]) if leyenda else "",
            )
        )
    return tuple(capturas)
