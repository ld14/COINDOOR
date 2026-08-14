# 007 · Edición — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas;
marca `[x]` al completarlas._

## Implementación

- [x] Backend: agregar escritura estructurada de `review` y `cheats`. Hecho cuando:
      `PUT /api/games/:id/fields/review|cheats` guarda estructuras válidas.
- [x] Frontend API: agregar mutaciones en `lib/api/games.ts`, `fields.ts` y `media.ts`.
- [x] Hooks: `useGameMutations` invalida `game`, `games` y `systems` donde corresponda.
- [x] `/juegos/nuevo`: alta mínima en dos pasos con sistema, origen de ROM e identidad.
- [x] `/juegos/:gameId`: editar identidad, sinopsis, acentos y media desde la ficha.
- [x] `/juegos/:gameId`: editar `review` como estructura (`score`, `cats`).
- [x] `/juegos/:gameId`: editar `cheats` como grupos y entradas.
- [x] `mark-ready`: mostrar faltantes exactos si backend devuelve 409.
- [x] Confirmación: al borrar un campo `manual` con contenido (sinopsis, media) se pide
      confirmación antes de vaciarlo. El reemplazo por sugerencias (feature 002) queda como
      punto de montaje pendiente, documentado en `spec.md`.

## Tests

- [x] Crear juego desde `/juegos/nuevo` navega a la ficha.
- [x] Ruta relativa en `romRef` muestra error y no crea ficha.
- [x] Editar sinopsis actualiza la ficha y su estado (`FieldTag`); completitud se recalcula
      vía `computeGameStatus`/`missingRequired` sobre el `game` fresco.
- [x] Borrar campo pide confirmación si es `manual`, cancelar no borra, confirmar sí — y la
      sección sigue visible (no se oculta).
- [x] `review` y `cheats` se envían como estructuras (`score`/`cats`, `groups[]`), no texto.
- [x] `mark-ready` incompleto muestra faltantes exactos.
- [x] Upload de media actualiza tarjeta y el backend decide el nombre, no el archivo del
      cliente.

## Cierre

- [x] Validar contra todos los criterios de aceptación de `spec.md`.
- [x] `npm test` limpio (39 passed).
- [x] `npm run build` limpio.
- [x] `uv run pytest` limpio si se toca backend (75 passed).
- [x] No se creó ADR: sin alternativas descartadas, solo se corrigió redacción de un criterio
      de `spec.md` mientras seguía en `borrador`.
- [x] Mover feature 007 a "Hecho" en `../../constitution/roadmap.md`.
