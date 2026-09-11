"""Descubrimiento de juegos instalados sin ficha.

Recorre `games/juegos/<sistema>/` y devuelve lo que hay suelto ahí: archivos de
ROM y carpetas sin `game.json`. Solo lee — no mueve, no copia, no escribe nada.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from backend.api.schemas import RomCandidate
from backend.config import Settings
from backend.lib.domain.descubrimiento import EXTENSIONES_IGNORADAS, titulo_propuesto
from backend.store.archivo import safe_id
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore


class DescubrimientoService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.games = GamesStore(settings.games_dir)
        self.systems = SystemsStore(settings.systems_path)

    def candidatos(self, system_id: str = "") -> list[RomCandidate]:
        root = self.settings.games_dir
        if not root.exists():
            return []

        existentes = self._ocupadas()
        # Las carpetas se llaman `safe_id(systemId)`; el formulario necesita el id
        # real ("MS-DOS", no "ms-dos") para seleccionar el sistema.
        nombres = {safe_id(system.id): system.id for system in self.systems.list()}
        filtro = safe_id(system_id) if system_id else ""

        salida: list[RomCandidate] = []
        for system_dir in sorted(root.iterdir()):
            if not system_dir.is_dir() or system_dir.name.startswith("."):
                continue
            if filtro and system_dir.name != filtro:
                continue
            real = nombres.get(system_dir.name, system_dir.name)
            salida.extend(self._del_sistema(system_dir, real, existentes))
        return sorted(salida, key=lambda item: (item.title.lower(), item.systemId))

    def _ocupadas(self) -> set[tuple[str, str]]:
        """Entradas `(carpeta de sistema, nombre)` que ya tienen ficha.

        Se pregunta por el `romRef` de cada ficha y no por su id, porque el id sale
        del título —que limpia `(1992)` y demás— y el nombre en disco no: comparar
        ids dejaba el candidato original a la vista después de darlo de alta.

        Se compara solo el último segmento, normalizado con `safe_id`, para que el
        mismo juego se reconozca lo escriba quien lo escriba: el backend corriendo
        en WSL guarda `/mnt/d/...` y el mismo backend en Windows lee `D:\\...`.
        """
        ocupadas: set[tuple[str, str]] = set()
        for game in self.games.list():
            system_dir = safe_id(game.systemId)
            # Su propia carpeta bajo `juegos/`, la que contiene el `game.json`.
            ocupadas.add((system_dir, safe_id(game.id)))
            ultimo = _ultimo_segmento(game.romRef)
            if not ultimo:
                continue
            # Con extensión (`sf2.zip`) y sin ella: un candidato archivo se
            # identifica por su stem, uno carpeta por su nombre entero.
            ocupadas.add((system_dir, safe_id(ultimo)))
            ocupadas.add((system_dir, safe_id(Path(ultimo).stem)))
        return ocupadas

    def _del_sistema(
        self,
        system_dir: Path,
        system_id: str,
        existentes: set[tuple[str, str]],
    ) -> list[RomCandidate]:
        salida: list[RomCandidate] = []
        for entry in sorted(system_dir.iterdir()):
            if entry.name.startswith("."):
                continue
            leido = self._leer(entry)
            if leido is None:
                continue
            base, kind, file_format, tratamiento, size = leido
            candidato_id = safe_id(base)
            if (system_dir.name, candidato_id) in existentes:
                continue
            if (system_dir.name, safe_id(entry.name)) in existentes:
                continue
            salida.append(
                RomCandidate(
                    id=candidato_id,
                    systemId=system_id,
                    name=entry.name,
                    title=titulo_propuesto(base),
                    path=str(entry.resolve()),
                    kind=kind,
                    file_format=file_format,
                    tratamiento=tratamiento,
                    sizeBytes=size,
                )
            )
        return salida

    def _leer(self, entry: Path) -> tuple[str, str, str, str, int] | None:
        """`(base, kind, file_format, tratamiento, size)`, o None si no es candidato."""
        try:
            if entry.is_dir():
                if (entry / "game.json").exists():
                    return None
                return (entry.name, "dir", "", "descomprimir", _tamano_dir(entry))
            if entry.is_file():
                suffix = entry.suffix.lower()
                if suffix in EXTENSIONES_IGNORADAS:
                    return None
                return (entry.stem, "file", suffix.lstrip("."), "copiar", entry.stat().st_size)
        except OSError:
            # Un enlace roto o un permiso denegado no puede tumbar el listado entero.
            return None
        return None


def _ultimo_segmento(rom_ref: str) -> str:
    """Último tramo de una ruta, venga con `/` o con `\\` y con o sin barra final."""
    limpio = rom_ref.strip().rstrip("/\\")
    if not limpio:
        return ""
    return re.split(r"[\\/]+", limpio)[-1]


def _tamano_dir(path: Path) -> int:
    total = 0
    for base, _dirs, files in os.walk(path, onerror=lambda _exc: None):
        for name in files:
            try:
                total += (Path(base) / name).stat().st_size
            except OSError:
                continue
    return total
