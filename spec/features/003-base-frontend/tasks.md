# 003 · Base del frontend — Tareas

_Checklist accionable derivada del `plan.md`._

## Antes de tocar código

- [x] Confirmar que los ADRs [0007](../../decisions/0007-fastapi-como-framework-backend.md)
      a [0012](../../decisions/0012-verificacion-attract-por-subproceso.md) están
      aceptados. Hecho cuando: su `status` dice `accepted`.
- [x] Tener a mano `COINDOOR.dc.html`, el prototipo. Gana sobre los documentos para lo
      visual. **No está presente en el repo; se validó contra `design-system.md`.**

## Implementación

- [x] Andamiaje `npm create vite@latest -- --template react-ts` en `frontend/`. Hecho
      cuando: `npm run dev` y `npm run build` corren, con `strict: true` en `tsconfig`.
- [x] `vite.config.ts` — alias `@/` y proxy de `/api` a `127.0.0.1:8765`.
- [x] `src/styles/tokens.css` — las variables de `design-system.md` §1. Hecho cuando: es
      el **único** archivo del proyecto con un hex.
- [x] `src/styles/reset.css`.
- [x] `Panel` y `SunkenBox` — los bordes `2px outset` / `2px inset`. Hecho cuando: se ven
      iguales que en el prototipo, sin `border-radius` ni sombra.
- [x] `DosButton` — variantes `primary`, `primary-small`, `ghost`, `ghost-small`,
      `danger-small`, más el estado presionado (`border-style: inset`, sin moverse) y el
      deshabilitado (texto `--dos-edge-dark`, sin cambio de borde).
- [x] `DosInput`, `DosSelect`, `DosTextarea` — borde inset, foco visible.
- [x] `SectionHeader` — barra azul al **100 % del ancho de la columna**. Hecho cuando: el
      panel que la sigue tiene exactamente el mismo ancho.
- [x] `StatusBadge` — `LISTO` / `INCOMPLETO` / `CON ERRORES`, texto de terminal sobre
      negro con su borde. Recibe el estado por prop; **no lo calcula**.
- [x] `FieldTag` — `● MANUAL` / `◔ SUGERIDO` / `○ VACÍO`, 10.5 px, sin caja.
- [x] `Modal` + `useModalFoco` — barra de título azul, `X`, backdrop
      `rgba(0,0,0,0.55)`, sombra dura `4px 4px 0`. Hecho cuando: atrapa el foco, cierra
      con `Esc` y con la `X`, y devuelve el foco al elemento que lo abrió.
- [x] `ProgressBar` — pista negra inset, relleno cian, **sin transición de ancho**.
- [x] `Spinner` — la única animación permitida en todo el proyecto.
- [x] `MenuBar` — panel lateral fijo de 190 px con cabecera azul y contador al pie.
- [x] `StatusBar` — franja negra con `F1 Ayuda · F2 Sistemas · F3 Juegos · F4 Exportar ·
      Esc Cerrar`, teclas en `#FFFF55`.
- [x] `Banner` — aviso amarillo del contrato.
- [x] `src/pages/_Catalogo.tsx` en `/_catalogo`. Hecho cuando: renderiza las quince
      primitivas con **todas** sus variantes y estados, y no aparece en el `MenuBar`.
- [x] `App.tsx` — las tres zonas del layout y las cinco rutas, con las pantallas vacías.
- [x] Atajos globales `F2` / `F3` / `F4` / `Esc` en un `useEffect` de `App.tsx`.
- [x] `main.tsx` — `BrowserRouter` + `QueryClientProvider`.

## Tests

- [x] Cada primitiva renderiza sin props opcionales y no lanza.
- [x] `DosButton` deshabilitado no dispara `onClick`.
- [x] `Modal`: `Esc` lo cierra, el foco queda atrapado adentro, y al cerrarse vuelve al
      disparador.
- [x] `F2` / `F3` / `F4` navegan; con un modal abierto, `Esc` lo cierra **y no navega**.
- [x] Test de estilo: ningún archivo bajo `src/` fuera de `tokens.css` contiene un hex ni
      un `border-radius` distinto de 0. Hecho cuando: falla si alguien agrega uno.

## Cierre

- [x] Validar contra todos los criterios de aceptación de `spec.md`.
- [x] `tsc --noEmit`, lint y tests limpios.
- [x] Comparar la página de catálogo contra `COINDOOR.dc.html` lado a lado. El prototipo
      ya está en el repo (`docs/claude_diseño/COINDOOR.dc.html`). Comparación por código:
      cada valor de `tokens.css` y de los CSS Modules de `components/dos/` (colores,
      `2px outset/inset`, paddings, anchos de modal 420/460/620px, backdrop
      `rgba(0,0,0,.55)`) coincide con los estilos inline del prototipo. Sin discrepancias.
- [x] Actualizar `frontend/CLAUDE.md` con las rutas reales si cambiaron. La estructura
      documentada decía `features/` y `lib/api/`; la real usa `pages/` y todavía no tiene
      `lib/api/`. Corregido.
- [x] Mover la feature a "Hecho" en `../../constitution/roadmap.md`. Ya estaba listada ahí.
