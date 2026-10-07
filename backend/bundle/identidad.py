from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Nombre de romset de MAME: minusculas, digitos y guion bajo.
_ROMSET = re.compile(r"^[a-z0-9_]+$")
_EXT_ROM = frozenset({".zip", ".7z", ".chd"})


def set_exportado(game: Mapping[str, Any]) -> str:
    """Valor del campo ``set`` que viaja al bundle.

    Con ``identitySource == "mame"`` y un ``romRef`` cuyo nombre es un romset valido,
    es ese romset (lo que ATTRACT necesita para consultar ``-listxml``). En cualquier
    otro caso es el ``id`` interno: el slug del titulo, como antes.
    """
    slug = str(game.get("id", ""))
    if game.get("identitySource") != "mame":
        return slug
    rom_ref = str(game.get("romRef") or "").strip()
    if not rom_ref:
        return slug
    # `romRef` puede venir con separadores de Windows aunque el proceso corra en Linux.
    ruta = Path(rom_ref.replace("\\", "/"))
    # Un archivo se nombra sin extension; una carpeta se usa entera, para que un
    # nombre con punto no pierda su tramo final como si fuera una extension.
    nombre = (ruta.stem if ruta.suffix.lower() in _EXT_ROM else ruta.name).lower()
    return nombre if _ROMSET.match(nombre) else slug
