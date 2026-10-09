# 019 · Rediseño "Flyer 80s" — Tareas

_Checklist derivada del `plan.md`. Estado al cierre de la Ola 5: las fases 1 a 6 están implementadas y cubiertas por tests de componente; **nada se verificó visualmente en un navegador**. Cada fase termina con la app andando, `npx tsc --noEmit`
y lint limpios, `PROGRESS.md` actualizado y un commit
`rediseno: fase N – <resumen>`. El detalle de cada tarea está en
[`docs/coindoor-rediseno/PLAN.md`](../../../docs/coindoor-rediseno/PLAN.md)._

## Fase 0 · Preparación

- [x] Crear la feature 019, el ADR 0023 y actualizar la constitución. Hecho cuando: están
      en `spec/` y el índice de ADRs y el roadmap los enlazan.
- [x] Escribir `docs/coindoor-rediseno/PROGRESS.md` con lo relevado y las dos decisiones
      (autosave, origen). Hecho cuando: ambas están justificadas con referencias al código.

## Fase 1 · Tokens, fuentes y shell

- [x] Instalar `@fontsource/bungee`, `rubik`, `ibm-plex-mono` e importarlos en `main.tsx`.
- [x] Reemplazar el `:root` de `frontend/src/styles/tokens.css` por `flyer-tokens.css`
      con los alias `--dos-*`.
- [x] Topbar con marca, búsqueda global (`/`) e indicador de contrato.
- [x] `MenuBar` → Rail con contadores reales. Hecho cuando: ya no dice "0 juegos" (bug 1).
- [x] `Banner` solo ante problema del contrato; `StatusBar` con indicador; quitar la
      sombra `░` y el borde de 5 px; responsive bajo 900 px.

## Fase 2 · Primitivas

- [x] Actualizar `DosButton`, `StatusBadge`, `FieldTag`→`OriginChip`, `Panel`→`Card`,
      `ProgressBar`, `Modal`, inputs con `invalid`.
- [x] Crear `SegmentedControl`, `ChoiceCards`, `NumberStepper`, `ListEditor`, `Dropzone`,
      `InlineSuggestion`, `StepNav`, `CheckTile`, `FilterTabs`, `FilterChips`,
      `NextPendingCard`, `ActionBar`.
- [x] Migrar los CSS modules de las primitivas a tokens nuevos y actualizar `/_catalogo`.

## Fase 3 · Juegos, Sistemas, Configuración

- [x] Juegos: FilterTabs, FilterChips, orden, grilla, banda "Seguís con…". Sin orden por última modificación ni "Exportado dd/mm" (falta `exportedAt`/fecha en el backend).
- [x] Sistemas: contador real (bug 2, backend si corresponde) y validación de ruta en vivo.
- [x] Configuración: ATTRACT con [Probar] (valida la ruta; no corre `attract doctor`: ver PENDIENTES en `PROGRESS.md`). Servicios y defaults NO están: el backend no los expone.

## Fase 4 · Ficha de juego (sub-plan y OK antes)

- [x] Refactor puro de `FichaJuego.tsx` a `src/pages/ficha/` y commit aparte.
- [x] `useFichaProgress(game)` con tests.
- [x] UI nueva por sección, con checklist de funciones existentes verificadas.
- [x] Autosave y `source` al aceptar/editar (backend `store/juegos.py`) con tests.
- [x] Revisión de sugerencias y atajos `Enter` / `N`.

## Fase 5 · Nuevo juego (sub-plan y OK antes)

- [x] Asistente de cuatro pasos, labels de `fielddefs.json` (bug 4), ROMs sin ficha (bug 5).

## Fase 6 · Exportar

- [x] Botón de la ficha a `/exportar/:gameId` (bug 3), paquete agrupado, tildados por
      defecto (bug 7), tamaño de trucos vacío (bug 6), cola en `/exportar`.

## Fase 7 · Limpieza y QA

- [x] Borrar `--dos-*` sin uso y componentes muertos (alias, `ReadPages.module.css`, `EmptyPage`). Se conservan `SectionHeader` y `DosFileInput`: tienen usos.
- [x] Accesibilidad auditada por grep y tests (foco, `aria-live`, motivo del deshabilitado, `prefers-reduced-motion`).
- [ ] Comparar cada pantalla con su mockup a 1280 px. **Sin hacer: no hubo navegador en las olas de implementación.**

## Cierre

- [ ] Validar contra todos los criterios de `spec.md` (falta la verificación visual y los criterios que dependen del backend pendiente).
- [ ] Lint, tipos y tests limpios.
- [ ] Actualizar `docs/` si cambió la superficie pública.
- [ ] Marcar la feature como "Hecha" en `../../constitution/roadmap.md`.
