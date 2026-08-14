# 006 · Pantallas de lectura — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Conectar primero lectura real, sin inventar estado local ni duplicar dominio. La UI consume `/api`
con TanStack Query y conserva filtros en query string. Las páginas reutilizan primitivas DOS y las
funciones de `lib/domain/`; los componentes nuevos solo formatean datos y estados.

La ficha queda estrictamente readonly: ningún botón que escriba, ningún upload y ningún cambio de
campo. Donde el backend no tenga dato, la pantalla muestra vacío explícito en vez de ocultar la
sección.

## Implementación

1. `frontend/src/lib/api/client.ts` — wrapper mínimo de `fetch` relativo a `/api`, con error
   explícito si HTTP falla.
2. `frontend/src/lib/api/systems.ts` — `listSystems()` con tipos del dominio.
3. `frontend/src/lib/api/games.ts` — `listGames(params)` y `getGame(id)` con los DTOs actuales.
4. `frontend/src/hooks/useSystems.ts`, `useGames.ts`, `useGame.ts` — hooks TanStack Query con keys
   estables.
5. `frontend/src/pages/Sistemas.tsx` — tarjetas de sistemas y cabecera inválida.
6. `frontend/src/pages/Juegos.tsx` — filtros en query string, lista, estados, placeholders y
   paginación si el backend devuelve varias páginas.
7. `frontend/src/pages/FichaJuego.tsx` — ficha readonly con identidad, media, textos, presentación,
   manuales, revista, errores y faltantes.
8. `frontend/src/App.tsx` — reemplazar páginas vacías de `/sistemas`, `/juegos` y
   `/juegos/:gameId`.

## Decisiones

- **API real en vez de mock server** — la feature 005 ya existe y esta fase valida integración real.
- **TanStack Query en vez de `useEffect` + `fetch`** — regla del frontend y evita estado servidor
  duplicado.
- **Sin componente genérico de “campo universal”** — tres pantallas chicas; abstracción ahora agrega
  más lectura que ahorro.
- **Secciones vacías visibles** — regla de diseño: campo sin dato nunca desaparece.

## Riesgos

- **Divergencia con dominio** — se mitiga usando `computeGameStatus` y `missingRequired` existentes.
- **Tipos API/backend no idénticos a `Game`** — se mitiga con funciones de API pequeñas y tests de
  render; si aparece transformación real, queda localizada en `lib/api`.
- **Fichas grandes con muchos campos** — se mitiga con componentes por sección, no con formulario
  único.
