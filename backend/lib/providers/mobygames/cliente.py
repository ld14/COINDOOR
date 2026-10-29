"""Busca un juego en MobyGames y devuelve su ficha para una plataforma.

La búsqueda general (``/search/?q=…&type=game``) trae 12 filas por página y su orden
compara palabras sueltas, no la frase: el juego buscado puede estar en cualquier fila. Por
eso la elección no mira la posición sino los datos de cada fila (ver ``elegir``).
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

from backend.lib.providers.mobygames.parser import (
    Ficha,
    Fila,
    Specs,
    parse_busqueda,
    parse_ficha,
    parse_specs,
)

if TYPE_CHECKING:
    from backend.lib.providers.scraping import ScrapingClient

BASE = "https://www.mobygames.com"
# Diferencia máxima de años entre la ficha de COINDOOR y la de MobyGames. Las fechas varían
# por región y por plataforma. Con el título exacto alcanza ±1; con "contiene" el título ya
# es menos seguro, pero MobyGames suele listar otra edición de DOS (Monkey Island: 1990 en
# la ficha, DOS 1992 allá) y hay que mirar más lejos; ahí también se exige la plataforma y
# que quede una sola fila.
TOLERANCIA_EXACTO = 1
TOLERANCIA_CONTIENE = 2


@dataclass(frozen=True)
class FichaCompleta:
    ficha: Ficha
    specs: Specs


def normalizar(texto: str) -> str:
    """Minúsculas, sin puntuación y sin espacios de más."""
    limpio = re.sub(r"[^\w\s]", " ", texto.casefold())
    return " ".join(limpio.split())


def _anio(valor: str | None) -> int | None:
    return int(valor) if valor and valor.isdigit() else None


def _por_anio(
    filas: list[Fila],
    plataforma: str,
    anio: int | None,
    tolerancia: int,
) -> list[Fila]:
    """Si el año separa los candidatos, los que quedan; si no, todos.

    Primero gana el mismo año de esa plataforma; si no hay, el más cercano dentro de
    ``tolerancia``.
    """
    if anio is None:
        return filas
    clave = plataforma.lower()
    for margen in range(tolerancia + 1):
        cerca = [
            f
            for f in filas
            if (a := _anio(f.plataformas.get(clave))) is not None and abs(a - anio) == margen
        ]
        if cerca:
            return cerca
    return []


def elegir(
    filas: tuple[Fila, ...],
    titulo: str,
    anio: str | None,
    plataforma: str,
) -> Fila | None:
    """La fila de la ficha, o ``None`` si no hay una que lo sea sin ambigüedad.

    Solo cuentan las filas con esa plataforma. Dos niveles:

    1. Título exacto: el título o algún "AKA:" es igual al de la ficha. Con una fila, esa;
       con varias, desempata el año de la plataforma.
    2. Solo si el nivel 1 no dio ninguna: el título tiene todas las palabras del de la
       ficha. Acá el año es obligatorio aunque quede una sola fila.
    """
    clave = plataforma.lower()
    con_plataforma = [f for f in filas if clave in f.plataformas]
    buscado = normalizar(titulo)
    if not buscado:
        return None
    ano = _anio(anio)

    exactas = [
        f for f in con_plataforma if buscado in {normalizar(f.title), *map(normalizar, f.alias)}
    ]
    if exactas:
        if len(exactas) == 1:
            return exactas[0]
        elegidas = _por_anio(exactas, plataforma, ano, TOLERANCIA_EXACTO)
        return elegidas[0] if len(elegidas) == 1 else None

    if ano is None:
        return None
    palabras = set(buscado.split())
    contienen = [f for f in con_plataforma if palabras <= set(normalizar(f.title).split())]
    elegidas = _por_anio(contienen, plataforma, ano, TOLERANCIA_CONTIENE)
    return elegidas[0] if len(elegidas) == 1 else None


_memo: dict[tuple[str, str, str], FichaCompleta | None] = {}
_memo_lock = threading.Lock()


def olvidar() -> None:
    with _memo_lock:
        _memo.clear()


def buscar_ficha(
    client: ScrapingClient,
    titulo: str,
    anio: str | None,
    plataforma: str,
    *,
    ficha_url: str | None = None,
) -> FichaCompleta | None:
    """Busca el juego y baja su ficha y sus specs; ``None`` si no hay un resultado claro.

    ``ficha_url`` salta la búsqueda (la procedencia ya trae el enlace de MobyGames). El
    resultado queda en memoria mientras corre el proceso: las sugerencias de distintos
    campos y la precarga lo reusan sin volver a bajar las páginas.
    """
    clave = (ficha_url or normalizar(titulo), anio or "", plataforma.lower())
    with _memo_lock:
        if clave in _memo:
            return _memo[clave]

    url = ficha_url
    if url is None:
        pagina = client.get_page(f"{BASE}/search/?q={quote_plus(titulo.strip())}&type=game")
        fila = elegir(parse_busqueda(pagina), titulo, anio, plataforma)
        url = fila.url if fila else None

    resultado: FichaCompleta | None = None
    if url:
        base = url if url.endswith("/") else url + "/"
        ficha = parse_ficha(client.get_page(base), plataforma)
        specs = parse_specs(client.get_page(base + "specs/"), plataforma)
        resultado = FichaCompleta(ficha, specs)

    with _memo_lock:
        _memo[clave] = resultado
    return resultado
