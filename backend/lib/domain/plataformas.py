"""Catálogo de plataformas: cómo se llama cada sistema de COINDOOR en cada sitio.

El dato vive en ``plataformas.json`` y lo comparten todos los proveedores, como
``fielddefs.json``. Un sitio sin equivalencia se declara ``null``; un sitio ausente de la
fila es un error de carga, para que agregar un sitio obligue a revisar todas las filas.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PLATAFORMAS_PATH = Path(__file__).with_name("plataformas.json")


@dataclass(frozen=True)
class Plataforma:
    name: str
    alias: tuple[str, ...]
    sitios: Mapping[str, str | None]


def _normalizar(system: str) -> str:
    return " ".join(system.lower().split())


@lru_cache(maxsize=1)
def _cargar() -> tuple[tuple[str, ...], Mapping[str, Plataforma]]:
    with PLATAFORMAS_PATH.open(encoding="utf-8") as file:
        datos = json.load(file)
    sitios = tuple(str(sitio) for sitio in datos["sitios"])
    indice: dict[str, Plataforma] = {}
    for fila in datos["plataformas"]:
        faltan = [sitio for sitio in sitios if sitio not in fila]
        if faltan:
            raise ValueError(f"plataformas.json: '{fila['name']}' omite {faltan}")
        plataforma = Plataforma(
            name=str(fila["name"]),
            alias=tuple(str(a) for a in fila["alias"]),
            sitios={sitio: fila[sitio] for sitio in sitios},
        )
        for nombre in (plataforma.name, *plataforma.alias):
            clave = _normalizar(nombre)
            if clave in indice:
                raise ValueError(f"plataformas.json: '{nombre}' está repetido")
            indice[clave] = plataforma
    return sitios, indice


def sitios() -> tuple[str, ...]:
    return _cargar()[0]


def plataforma(system: str) -> Plataforma | None:
    """La fila del catálogo para ese sistema (por nombre o alias), o ``None`` si no está."""
    return _cargar()[1].get(_normalizar(system))


def nombre_en(system: str, sitio: str) -> str | None:
    """Cómo se llama el sistema en ese sitio, o ``None`` si el sitio no lo tiene o el
    sistema no está en el catálogo."""
    fila = plataforma(system)
    if fila is None:
        return None
    return fila.sitios[sitio]
