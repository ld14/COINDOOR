# PROGRESS · Rediseño Flyer

Feature: [`spec/features/019-rediseno-flyer/`](../../spec/features/019-rediseno-flyer/spec.md) ·
ADR: [`0023`](../../spec/decisions/0023-estetica-flyer-reemplaza-dos.md)

## Fase 0 · Preparación — hecha (2026-10-08)

### Decisiones de trabajo

- Se trabaja en `master`, sin rama. El paquete queda en `docs/coindoor-rediseno/`.
- Se aprueban `@fontsource/bungee`, `rubik` e `ibm-plex-mono`.
- Los bugs de backend se corrigen en backend si no cambian contrato; si lo cambian,
  `TODO(backend)` y aviso.
- Ante choque, mandan los deltas D1–D5 sobre el rediseño (reseña 0–100, revistas sin
  descarga, export con "Siempre incluido" bloqueado).
- **No se pierde ninguna funcionalidad existente.**

### Decisión 1 · Guardado: autosave con debounce

- `frontend/src/hooks/useGameMutations.ts` expone una mutación por campo
  (`setTextField`, `setReview`, `setCheats`, `patchGame`, `uploadMedia`, …), y el backend
  escribe de forma atómica el `game.json` del juego
  ([`ADR-0008`](../../spec/decisions/0008-persistencia-en-archivos.md)): tolera escrituras
  parciales frecuentes. Plan B del spec §4 (un solo "Guardar") descartado.
- Cada mutación invalida **cuatro** queries (`games`, `systems`, `rom-candidates`,
  `game`). Con autosave eso recargaría la ficha mientras se escribe: hay que invalidar solo
  `game` (y `games` al terminar) y no pisar el estado local de un campo con foco.
- Hoy `FichaJuego.tsx` (1376 líneas) tiene `saveAll` (línea ~129) y `onSaveAll`; son lo que
  desaparece. El botón Exportar ya llama `saveAll()` antes de navegar: ese paso queda
  cubierto por "esperar a que termine el guardado pendiente".

### Decisión 2 · Origen: conservar `source` al aceptar

- `backend/store/juegos.py`: las sugerencias entran como
  `{"status": "suggested", ..., "source": provenance.source}` (líneas ~192 y ~209), pero
  el guardado manual escribe `{"status": "manual"}` **sin `source`** (líneas ~137, 150,
  158 y 219). Hoy un valor aceptado y uno escrito a mano son indistinguibles, y aceptar
  pierde la fuente.
- Cambio: aceptar = `manual` conservando `source`; editar a mano = `manual` + `source:
  "manual"`. Sin campos nuevos. El `source` es procedencia interna y no viaja al export
  ([`ADR-0002`](../../spec/decisions/0002-procedencia-interna.md)). Verificar en el export
  y en `lib/domain/guia.py:114` (lee `status == "manual"`) que nada depende de la ausencia
  de `source`.

## Bugs: causa hallada en el relevamiento

| # | Causa probable (verificar al corregir) |
|---|---|
| 1 | `frontend/src/components/dos/MenuBar.tsx:21` — el texto "0 juegos cargados" está **fijo** en el JSX. |
| 2 | `backend/store/sistemas.py:54` arma `gameCount=0` **fijo**; hay que contar fichas por sistema. |
| 3 | `FichaJuego.tsx:224` ya navega a `/exportar/${game.id}`. Reproducir antes de tocar: puede estar corregido o fallar en otro camino. |
| 4 | Pendiente: `NuevoJuego.tsx`, usar `fielddefs.json`. |
| 5 | Pendiente: `backend/api/roms.py:28` (`list_rom_candidates`) compara contra `romRef` de las fichas. |
| 6 | Pendiente: tamaño de Trucos en `ExportPage.tsx` / `backend/bundle/seleccion.py`. |
| 7 | Pendiente: estado inicial de la selección en `ExportPage.tsx`. |
| 8 | Pendiente: confirmar si perder `?precarga=` es intencional. |

## Relevado del código

- Primitivas en `frontend/src/components/dos/` (Banner, DosButton, DosFileInput, DosInput,
  DosSelect, DosTextarea, FieldTag, MenuBar, Modal, Panel, ProgressBar, SectionHeader,
  Spinner, StatusBadge, StatusBar, SunkenBox), con CSS Modules y tests propios.
- Páginas: `Configuracion`, `ExportPage`, `FichaJuego`, `Juegos`, `NuevoJuego`,
  `Sistemas`, `_Catalogo`, `EmptyPage`.
- Hooks: `useConfig`, `useDominantColors`, `useGame`, `useGameMutations`, `useGames`,
  `useModalFoco`, `useRomCandidates`, `useSuggestionsJob`, `useSystems`.
- Capa de API en `frontend/src/lib/api/` con un módulo por recurso.
- El backend ya soporta `/configuracion` (feature 013), por lo que Configuración (Fase 3)
  puede tener [Probar] sin endpoint nuevo si la validación de ruta ya existe; confirmar.

## Pendientes antes de la Fase 1

- Confirmar que el árbol de `frontend/` está limpio y que las features 015–018 (en curso)
  no tienen cambios sin commitear sobre `FichaJuego.tsx`.
- Correr `npx tsc --noEmit`, lint y tests para fijar la línea base.

## Diferencias contra los mockups

_(se completa al cerrar cada fase)_
