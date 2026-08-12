# 003 · Base del frontend

**Estado:** hecho

## Qué hace

**Recibe** el paquete de diseño (`docs/claude_diseño/design-system.md` y
`frontend-architecture.md`). **Produce** un proyecto Vite + React + TypeScript que arranca,
navega entre las cinco rutas vacías, y expone las primitivas visuales de `components/dos/`
en una página de catálogo interna donde se ven todas juntas.

**No** trae datos, ni dominio, ni formularios: las pantallas quedan vacías. Los tipos, la
completitud y el mock server son la feature
[004](../004-dominio-y-contrato/spec.md).

## Por qué

Es la Fase 1 del roadmap y el cimiento de todo el frontend. Las primitivas DOS se escriben
a mano porque **ninguna librería de componentes puede usarse** —los bordes 3D
`outset`/`inset` los rompe cualquiera de ellas—, así que hay que construirlas antes de que
exista una pantalla que las consuma.

La página de catálogo no es un lujo: sin ver los quince controles juntos, las
inconsistencias de borde, densidad y color aparecen de a una, tarde, y ya copiadas en
cinco pantallas.

## Criterios de aceptación

- [x] `npm run dev` levanta la aplicación y `npm run build` produce un build estático.
- [x] Las cinco rutas existen y navegan: `/sistemas`, `/juegos` (default), `/juegos/nuevo`,
      `/juegos/:gameId`, `/exportar`.
- [x] Las teclas `F2`, `F3` y `F4` navegan a Sistemas, Juegos y Exportar. `Esc` cierra el
      modal abierto.
- [x] El layout tiene sus tres zonas fijas: barra de título cian, cuerpo con `MenuBar` de
      190 px y área hundida, y barra de estado negra con las F-keys en amarillo.
- [x] Existe una página de catálogo interna que renderiza **todas** las primitivas de
      `components/dos/` con sus variantes.
- [x] **Cero `border-radius`, cero sombras difusas, cero transiciones** salvo el spinner.
      Una sola familia monoespaciada.
- [x] Ningún color ni tamaño literal en un componente: todo sale de `tokens.css`.
- [x] Todo control interactivo es un elemento real (`button`, `input`, `select`, `a`), y
      el foco se ve con outline punteado negro de 1 px. Nunca `outline: none`.
- [x] Un modal atrapa el foco y se cierra con `Esc` y con la `X` de su barra de título.
- [x] `tsc --noEmit` y el lint pasan limpios en modo `strict`.

## Fuera de alcance

- **Tipos de dominio, completitud, validación y el seed** — eso es la feature
  [004](../004-dominio-y-contrato/spec.md).
- **El contenido real de las cinco pantallas** — Fases 3 y 4 del roadmap.
- **Cualquier llamada a la API.** No hay backend todavía: eso es la feature
  [005](../005-esqueleto-backend/spec.md).
- **La página de catálogo como producto.** Es una herramienta interna de desarrollo, no una
  pantalla del sistema, y no aparece en el `MenuBar`.
