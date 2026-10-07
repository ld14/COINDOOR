# 015 · `set` con el romset real — Tareas

## Implementación

- [x] Crear `backend/bundle/identidad.py::set_exportado`. Hecho cuando: los casos de
      aceptación del spec devuelven el valor esperado.
- [x] Usarla en `bundle/gamejson.py` y `bundle/manifest.py`. Hecho cuando: ninguno
      lee `game["id"]` para el campo `set`.

## Tests

- [x] SFA2, MK2 y Simpsons con `identitySource="mame"` → `sfa2`, `mk2`, `simpsons`.
- [x] Pac-Man y Shufshot sin cambio.
- [x] Sin `romRef` y con `identitySource="manual"` → slug.
- [x] `romRef` carpeta con nombre no válido → slug.
- [x] Coincidencia `game.json` ↔ `manifest`.
- [x] `tests/test_staging.py` y `tests/test_manifest.py` siguen pasando (`set == "goldnaxe"`).
- [x] `romRef` con separadores de Windows (`D:\roms\MK2.zip`) se resuelve en Linux.

## Cierre

- [x] pytest (266 pasan) y ruff limpios, corridos en WSL con `.venv/bin/python`.
- [ ] Exportar un arcade real y correr `attract doctor` sobre el zip.
- [ ] Marcar "implementada" en `spec.md` y mover a "Hecho" en `../../constitution/roadmap.md`.
