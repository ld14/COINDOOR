# 006 · Pantallas de lectura — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas;
marca `[x]` al completarlas._

## Implementación

- [x] Implementar `frontend/src/lib/api/client.ts` — `fetchJson` relativo a `/api`. Hecho cuando:
      errores HTTP producen mensaje explícito y no se repite `fetch` crudo en páginas.
- [x] Implementar `frontend/src/lib/api/systems.ts` — listar sistemas. Hecho cuando:
      `/sistemas` no importa datos del mock directo.
- [x] Implementar `frontend/src/lib/api/games.ts` — listar juegos con filtros y obtener ficha.
      Hecho cuando: query params coinciden con backend (`q`, `systemId`, `status`, `page`,
      `perPage`).
- [x] Implementar hooks `useSystems`, `useGames`, `useGame`. Hecho cuando: todas las páginas leen
      estado servidor vía TanStack Query.
- [x] Implementar `frontend/src/pages/Sistemas.tsx` — título, bajada, tarjetas y estado inválido.
- [x] Implementar `frontend/src/pages/Juegos.tsx` — filtros en query string, lista, estados,
      placeholders y vacíos.
- [x] Implementar `frontend/src/pages/FichaJuego.tsx` — ficha readonly con secciones siempre
      visibles.
- [x] Cablear rutas en `frontend/src/App.tsx` reemplazando `EmptyPage` para `/sistemas`, `/juegos`
      y `/juegos/:gameId`.

## Tests

- [x] `/sistemas` renderiza sistemas y marca cabecera inválida.
- [x] `/juegos` renderiza lista y conserva filtros en query string tras cambiar controles.
- [x] Lista de juegos muestra placeholder si no hay carátula.
- [x] `/juegos/:gameId` muestra secciones vacías en vez de ocultarlas.
- [x] `gameId` inexistente muestra error explícito y enlace de vuelta.
- [x] Juego con `errors` muestra bloque de errores de formato.

## Cierre

- [x] Validar contra todos los criterios de aceptación de `spec.md`.
- [x] `npm test` limpio.
- [x] `npm run build` limpio.
- [x] No crear ADR: no hay decisión nueva con alternativas reales.
- [ ] Mover feature 006 a "Hecho" en `../../constitution/roadmap.md` solo cuando cumpla aceptación.
