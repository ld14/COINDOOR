# 016 · Bloque `guia` en el export — Plan

_Cómo se implementa lo descrito en `spec.md`._

## Enfoque

`guia` se arma con el mismo patrón que `cheats` y `manual` en `build_datajson`. Se emite
solo con `objetivo` presente, porque el contrato de ATTRACT lo exige y la sinopsis no es
confiable (2 de 6 juegos del piloto tenían errores de fondo). Por eso `objetivo` es un
campo propio, revisable aparte.

## Fases

- **016a (esta feature)** — backend: exportar `acciones` + `objetivo` + metadatos fijos.
  `objetivo` se carga por la API de campos existente.
- **017** — carga de `objetivo` (a mano y sugerido por IA). `primerosPasos` y
  `reglasEsenciales` quedan para otra feature.

## Implementación

1. **Antes de codificar:** confirmar `guia` contra `../attract/docs/CONVENCION.md` y
   `src/attract/doctor.py` (líneas ~284, 527-535). `frontend/src/lib/domain/contract.json`
   no la contiene hoy: si el contrato se consume como dato versionado (ADR-0001/0005),
   actualizarlo por el mecanismo existente, no a mano en código.
2. `objetivo` se lee de `texts.objetivo`, campo de la feature [`017`](../017-objetivo-guia-ia/spec.md);
   `CabinetButton` se reutiliza tal cual y no hay bloque `guia` propio en `StoredGame`.
3. `backend/bundle/datajson.py` — `_guia(game)`: `objetivo`, `acciones` (de
   `cabinet.button_list`), `multijugador.jugadores` (con `_players_int`), `fuentes`,
   `revision`.
4. La inclusión en «qué incluir» es la fila del texto `objetivo` (017); no hay fila `guia`.
6. Corregir el comentario de `tests/test_arcadedb.py` sobre `cabinet` y ADR-0002.

## Decisiones

- **`objetivo` propio en vez de reusar `texts.sinopsis`** — la sinopsis generada falló en
  el piloto; reusarla repetiría el error dentro del bloque.
- **Solo `button_list`, no `cabinet` entero** — `resolution`/`orientation` son del mueble
  original (ADR-0037 alternativa A, descartada).
- **`revision` deriva del estado de `texts.objetivo`** — `manual` → `revisado`; si no, `borrador`.
- **No emitir `modo` ni `perifericos`** — sin dato real, adivinar por género es lo que el
  contrato quiere evitar; su ausencia es AVISO, no ERROR.

## Cambios respecto del borrador

- `fuentes` **no se emite**: COINDOOR no guarda la fecha de consulta de ArcadeDB y `fecha`
  es obligatoria en ATTRACT. Se sumará cuando exista ese dato.
- `multijugador.jugadores` se emite solo si `identity.players` es un entero limpio ≥ 1;
  `"1-2"` se omite en vez de afirmar un `1` falso (a diferencia de `game.json`).
- `revision` es `revisado` solo si `texts.objetivo` está en `manual`; si no, `borrador`.

## Riesgos

- **`contract.json` ya no es derivado a mano** — ATTRACT lo publica (ADR-0039 de ATTRACT)
  y se vendoreó con su comando. Queda un hueco no bloqueante: `CONTRATO_VERSION = "1"` en
  `bundle/manifest.py` sigue siendo el placeholder frente al `"attract-1"` publicado.
