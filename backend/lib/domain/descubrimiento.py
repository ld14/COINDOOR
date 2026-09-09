"""Lectura del nombre en disco de un juego instalado.

Puro: no toca el filesystem. Convierte un nombre de archivo o carpeta en el
título que se propone en el alta. Nunca es identidad — eso lo pone la precarga
(ADR-0004: la IA y los catálogos producen identidad, un nombre de archivo no).
"""

from __future__ import annotations

import re

# Archivos que están en la carpeta del sistema pero no son juegos: temporales de la
# escritura atómica de `store/archivo.py`, descargas a medio bajar, y JSON del store.
EXTENSIONES_IGNORADAS = frozenset({".tmp", ".part", ".crdownload", ".bak", ".json"})

_GRUPOS = re.compile(r"[(\[][^)\]]*[)\]]")
_SEPARADORES = re.compile(r"[._\-]+")
_ESPACIOS = re.compile(r"\s+")


def titulo_propuesto(nombre: str) -> str:
    """Título legible a partir de `sf2`, `out-of-this-world` o `Contra (USA) [!]`.

    Solo capitaliza cuando el nombre viene todo en minúsculas: si el usuario ya
    escribió `Street Fighter II`, pisarlo con `Street Fighter Ii` sería peor que
    no tocarlo.
    """
    limpio = _GRUPOS.sub(" ", nombre)
    limpio = _SEPARADORES.sub(" ", limpio)
    limpio = _ESPACIOS.sub(" ", limpio).strip()
    if not limpio:
        return nombre.strip()
    if limpio.lower() == limpio:
        return " ".join(parte.capitalize() for parte in limpio.split(" "))
    return limpio
