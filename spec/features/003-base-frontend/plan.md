# 003 · Base del frontend — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

De abajo hacia arriba: **tokens → primitivas → catálogo → layout → rutas**. Ese orden no es
estético, es la única forma de que las primitivas no se escriban tres veces: si el layout
se hace primero, sus botones nacen ad-hoc y después nadie los reemplaza.

Las primitivas de `components/dos/` **no conocen el dominio**. No saben qué es un juego ni
qué es un campo: reciben props y pintan. Toda la lógica de negocio vive más arriba, en
`features/`. Es lo que permite que la página de catálogo las renderice sin datos.

El look sale del paquete de diseño, que se consulta y no se edita. Ante ambigüedad entre
los documentos y el prototipo `COINDOOR.dc.html`, **gana el prototipo para lo visual**.

## Implementación

1. `vite.config.ts` — React, alias `@/` a `src/`, y proxy de `/api` a
   `http://127.0.0.1:8765` para cuando exista el backend
   ([`ADR-0009`](../../decisions/0009-proceso-local-en-loopback.md)).
2. `src/styles/tokens.css` — las variables de `design-system.md` §1, literales. Es el único
   archivo del proyecto donde aparece un hex.
3. `src/styles/reset.css` — reset mínimo. Sin normalizaciones que redondeen ni suavicen.
4. `src/components/dos/` — quince primitivas, una por archivo, con CSS Module propio:
   `Panel`, `SunkenBox`, `DosButton`, `DosInput`, `DosSelect`, `DosTextarea`,
   `SectionHeader`, `StatusBadge`, `FieldTag`, `Modal`, `ProgressBar`, `Spinner`,
   `MenuBar`, `StatusBar`, `Banner`.
5. `src/pages/_Catalogo.tsx` — página interna en `/_catalogo`, fuera del `MenuBar`, que
   renderiza cada primitiva con todas sus variantes y estados.
6. `src/App.tsx` — el layout de tres zonas, el `<Routes>` con las cinco rutas, y el
   `useEffect` global que registra `F2`/`F3`/`F4`/`Esc`.
7. `src/hooks/useModalFoco.ts` — trampa de foco y cierre con `Esc`, compartido por todos
   los modales.
8. `src/main.tsx` — `BrowserRouter` + `QueryClientProvider`. El cliente de TanStack Query
   se instala acá aunque todavía no haya query que hacer: instalarlo después obliga a
   tocar el árbol entero.

## Decisiones

- **Tokens primero, y ningún literal fuera de `tokens.css`** — un hex suelto en un
  componente es lo que hace imposible ajustar la paleta después.
- **Las primitivas no conocen el dominio** — es lo que hace posible el catálogo y lo que
  evita que `StatusBadge` importe el tipo `Game`.
- **La página de catálogo vive en el árbol de rutas, no en Storybook** — Storybook es una
  dependencia, una configuración y un segundo build para mostrar quince componentes en un
  proyecto que ya tiene dev server. Una ruta interna alcanza.
- **`QueryClientProvider` desde el primer commit**, aunque no haya datos.
- **CSS Modules, sin Tailwind** — límite duro de `tech-stack.md`.
- **Sin librerías de componentes** — límite duro. Ver
  `frontend-architecture.md` §Stack.

## Riesgos

- **El look se degrada de a poco.** Un `border-radius` acá, una transición allá, y a las
  diez pantallas ya no es un programa DOS. Se mitiga con la página de catálogo, que hace
  visible la inconsistencia, y con la regla de que ningún literal sale de `tokens.css`.
- **Las primitivas se quedan cortas y las pantallas improvisan.** Si una pantalla necesita
  un control que no existe, la tentación es escribirlo inline. La regla: si aparece dos
  veces, es una primitiva y va al catálogo.
- **La accesibilidad se pierde persiguiendo el look.** El outline punteado y el foco
  visible son parte del diseño DOS, no una concesión: `outline: none` está prohibido.
