"""La regla para elegir un juego entre los resultados de una búsqueda por título.

La comparten todas las fuentes que buscan por nombre (MobyGames, Launchbox): con el mismo
título, la misma plataforma y el mismo año, todas eligen la misma edición. Dos niveles:

1. **Título exacto:** el título o un alias es igual al buscado. Con una opción, esa; con
   varias, desempata el año (el mismo y, si no hay, a ±``TOLERANCIA_EXACTO``).
2. **Título que contiene**, solo si el nivel 1 no dio ninguna: el título tiene todas las
   palabras del buscado, enteras, y lo que sobra no es un número de secuela. El año es
   obligatorio aunque quede una sola opción (el mismo y, si no hay, a ±``TOLERANCIA_CONTIENE``).

Sin una coincidencia clara no elige ninguna: es el lado seguro del error, porque elegir otro
juego contamina la ficha con datos e imágenes ajenos.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence

# Las fechas varían por región y por plataforma. Con el título exacto alcanza ±1; con
# "contiene" hay que mirar más lejos (Monkey Island: 1990 en la ficha, la edición de DOS que
# lista MobyGames es de 1992), y por eso ese nivel exige el año y una sola opción.
TOLERANCIA_EXACTO = 1
TOLERANCIA_CONTIENE = 2

# "Ultima II" contiene "Ultima" y está a un año del original, pero es otro juego. "1" no entra:
# "Commander Keen 1" sí es el primero.
_SECUELA = re.compile(r"[2-9]|ii|iii|iv|v|vi|vii|viii|ix|x")


def normalizar(texto: str) -> str:
    """Minúsculas, sin puntuación y sin espacios de más."""
    limpio = re.sub(r"[^\w\s]", " ", texto.casefold())
    return " ".join(limpio.split())


def anio_entero(valor: str | None) -> int | None:
    return int(valor) if valor and valor.isdigit() else None


def _contiene(titulo: str, palabras: set[str]) -> bool:
    """El título tiene todas las palabras y lo que le sobra no lo vuelve una secuela."""
    propias = set(normalizar(titulo).split())
    return palabras <= propias and not any(_SECUELA.fullmatch(p) for p in propias - palabras)


def _por_anio[T](
    opciones: list[T],
    anio_de: Callable[[T], int | None],
    anio: int | None,
    tolerancia: int,
) -> list[T]:
    """Si el año separa las opciones, las que quedan; sin año buscado, todas."""
    if anio is None:
        return opciones
    for margen in range(tolerancia + 1):
        cerca = [
            o for o in opciones if (a := anio_de(o)) is not None and abs(a - anio) == margen
        ]
        if cerca:
            return cerca
    return []


def elegir[T](
    opciones: Sequence[T],
    titulo: str,
    anio: str | None,
    *,
    titulos_de: Callable[[T], Iterable[str]],
    principal_de: Callable[[T], str],
    anio_de: Callable[[T], int | None],
) -> T | None:
    """La opción que es el juego buscado, o ``None`` si no hay una sin ambigüedad.

    ``titulos_de`` da el título y los alias de una opción (nivel 1); ``principal_de``, el
    título con el que se compara en el nivel 2; ``anio_de``, su año en la plataforma buscada.
    Las opciones ya vienen filtradas por plataforma.
    """
    buscado = normalizar(titulo)
    if not buscado:
        return None
    ano = anio_entero(anio)

    exactas = [o for o in opciones if buscado in {normalizar(t) for t in titulos_de(o)}]
    if exactas:
        if len(exactas) == 1:
            return exactas[0]
        elegidas = _por_anio(exactas, anio_de, ano, TOLERANCIA_EXACTO)
        return elegidas[0] if len(elegidas) == 1 else None

    if ano is None:
        return None
    palabras = set(buscado.split())
    contienen = [o for o in opciones if _contiene(principal_de(o), palabras)]
    elegidas = _por_anio(contienen, anio_de, ano, TOLERANCIA_CONTIENE)
    return elegidas[0] if len(elegidas) == 1 else None
