# 007 · Edición — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Construir sobre la ficha readonly de la feature [006](../006-pantallas-lectura/spec.md), sin wizard
nuevo grande de entrada. Primero se habilitan mutaciones pequeñas y explícitas: crear juego, editar
identidad/acento, setear/borrar sinopsis, subir/borrar media y marcar listo. Reseña y trucos quedan
como editores estructurados simples, sin sugerencias ni IA.

El estado servidor sigue en TanStack Query. Las mutaciones invalidan `game` y `games`; no hay store
paralelo. La confirmación para reemplazar `manual` se aplica donde pueda entrar un valor no escrito
directamente por el usuario; las sugerencias reales siguen siendo feature 002.

## Implementación

1. `backend/store/juegos.py` — agregar setters mínimos para `review` y `cheats` si no existen.
2. `backend/services/fields.py` y `backend/api/fields.py` — aceptar payload estructurado para
   `review` y `cheats` sin convertirlos a texto.
3. `frontend/src/lib/api/games.ts` — `createGame`, `patchGame`, `markReady`.
4. `frontend/src/lib/api/fields.ts` — `setTextField`, `deleteField`, `setReview`, `setCheats`.
5. `frontend/src/lib/api/media.ts` — `uploadMedia`.
6. `frontend/src/hooks/useGameMutations.ts` — mutaciones TanStack Query e invalidaciones.
7. `frontend/src/pages/NuevoJuego.tsx` — alta mínima en dos pasos: origen e identidad.
8. `frontend/src/pages/FichaJuego.tsx` — modo edición sobre secciones existentes: identidad,
   sinopsis, media, acentos, reseña/trucos estructurados simples y `mark-ready`.
9. `frontend/src/App.tsx` — reemplazar `EmptyPage` de `/juegos/nuevo`.

## Decisiones

- **Editar sobre ficha existente en vez de wizard completo** — menor diff y menos duplicación de UI.
- **Mutaciones pequeñas por recurso** — evita endpoint genérico de campo que mezcle texto, media y
  estructuras.
- **Sin optimismo salvo campos simples** — coherente con reglas frontend; media y alta esperan
  respuesta.
- **Manual PDF queda fuera** — backend aún no tiene job de procesamiento real.

## Riesgos

- **`review` y `cheats` como texto por accidente** — se mitiga con endpoints/payloads
  estructurados y tests.
- **Sobrescribir manual sin confirmación** — se mitiga mostrando confirmación antes de acciones no
  directas; sugerencias reales lo refuerzan en feature 002.
- **Formulario grande y frágil** — se mitiga con secciones pequeñas y guardar explícito por bloque.
