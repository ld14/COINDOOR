# Dominio COINDOOR

`contract.json` es la copia local del contrato de ATTRACT. No define la política de completitud de COINDOOR: solo registra campos, assets y datos ricos que ATTRACT acepta.

## Procedencia

ATTRACT todavía no publica un `contract.json`, así que esta versión fue derivada a mano el 2026-08-11 desde:

- `../attract/docs/CONVENCION.md`
- `../attract/src/attract/doctor.py`
- `../attract/library/arcade/metadata.pegasus.txt`
- `../attract/library/arcade/media/goldnaxe/`

`goldnaxe` es el único juego completo y funciona como referencia operativa. `logo` y `screenshot` se incluyen porque COINDOOR los expone como campos soportados; no aparecen en `goldnaxe`.

## Actualización

1. Reemplazar `contract.json` por el contrato publicado por ATTRACT o rederivarlo de las fuentes anteriores.
2. No agregar reglas de completitud en `contract.json`.
3. Ajustar `fielddefs.json` solo si COINDOOR necesita mapear nuevos campos o assets.
4. Correr tests de contrato-política y paridad TypeScript/Python.
