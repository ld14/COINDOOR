from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Nombre de romset de MAME: minusculas, digitos y guion bajo.
_ROMSET = re.compile(r"^[a-z0-9_]+$")
# Sistemas cuyo ROM se identifica por romset de MAME ("arcade" y "mame" son lo mismo).
_SISTEMAS_ROMSET = frozenset({"arcade", "mame"})
_EXT_ROM =frozenset({".zip", ".7z", ".chd"})


def set_exportado(game: Mapping[str, Any]) -> str:
    """Valor del campo ``set`` que viaja al bundle.

    ``set`` es la identidad del juego para ATTRACT: si cambia entre dos exports,
    ``attract import`` crea un bloque nuevo en vez de actualizar el existente. Por eso
    no depende de ``identitySource``, que se sobrescribe con la fuente del ultimo campo
    de identidad editado.

    En un sistema arcade/mame con un ``romRef`` cuyo nombre es un romset valido, es ese
    romset (lo que ATTRACT necesita para consultar ``-listxml``). En cualquier otro caso
    es el ``id`` interno: el slug del titulo. Otros sistemas (p. ej. MS-DOS) tambien
    tienen ``romRef``, pero ahi es una carpeta o un zip que no nombra un romset.
    """
    slug = str(game.get("id", ""))
    if str(game.get("systemId") or "").strip().lower() not in _SISTEMAS_ROMSET:
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
