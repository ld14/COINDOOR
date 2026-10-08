# 019 · Rediseño "Flyer 80s" — Tareas

_Checklist derivada del `plan.md`. Cada fase termina con la app andando, `npx tsc --noEmit`
y lint limpios, `PROGRESS.md` actualizado y un commit
`rediseno: fase N – <resumen>`. El detalle de cada tarea está en
[`docs/coindoor-rediseno/PLAN.md`](../../../docs/coindoor-rediseno/PLAN.md)._

## Fase 0 · Preparación

- [x] Crear la feature 019, el ADR 0023 y actualizar la constitución. Hecho cuando: están
      en `spec/` y el índice de ADRs y el roadmap los enlazan.
- [x] Escribir `docs/coindoor-rediseno/PROGRESS.md` con lo relevado y las dos decisiones
      (autosave, origen). Hecho cuando: ambas están justificadas con referencias al código.

## Fase 1 · Tokens, fuentes y shell

- [ ] Instalar `@fontsource/bungee`, `rubik`, `ibm-plex-mono` e importarlos en `main.tsx`.
- [ ] Reemplazar el `:root` de `frontend/src/styles/tokens.css` por `flyer-tokens.css`
      con los alias `--dos-*`.
- [ ] Topbar con marca, búsqueda global (`/`) e indicador de contrato.
- [ ] `MenuBar` → Rail con contadores reales. Hecho cuando: ya no dice "0 juegos" (bug 1).
- [ ] `Banner` solo ante problema del contrato; `StatusBar` con indicador; quitar la
      sombra `░` y el borde de 5 px; responsive bajo 900 px.

## Fase 2 · Primitivas

- [ ] Actualizar `DosButton`, `StatusBadge`, `FieldTag`→`OriginChip`, `Panel`→`Card`,
      `ProgressBar`, `Modal`, inputs con `invalid`.
- [ ] Crear `SegmentedControl`, `ChoiceCards`, `NumberStepper`, `ListEditor`, `Dropzone`,
      `InlineSuggestion`, `StepNav`, `CheckTile`, `FilterTabs`, `FilterChips`,
      `NextPendingCard`, `ActionBar`.
- [ ] Migrar los CSS modules de las primitivas a tokens nuevos y actualizar `/_catalogo`.

## Fase 3 · Juegos, Sistemas, Configuración

- [ ] Juegos: FilterTabs, FilterChips, orden, grilla/lista, banda "Seguís con…".
- [ ] Sistemas: contador real (bug 2, backend si corresponde) y validación de ruta en vivo.
- [ ] Configuración: ATTRACT con [Probar]; servicios y defaults solo si el backend los expone.

## Fase 4 · Ficha de juego (sub-plan y OK antes)

- [ ] Refactor puro de `FichaJuego.tsx` a `src/pages/ficha/` y commit aparte.
- [ ] `useFichaProgress(game)` con tests.
- [ ] UI nueva por sección, con checklist de funciones existentes verificadas.
- [ ] Autosave y `source` al aceptar/editar (backend `store/juegos.py`) con tests.
- [ ] Revisión de sugerencias y atajos `Enter` / `N`.

## Fase 5 · Nuevo juego (sub-plan y OK antes)

- [ ] Asistente de cuatro pasos, labels de `fielddefs.json` (bug 4), ROMs sin ficha (bug 5).

## Fase 6 · Exportar

- [ ] Botón de la ficha a `/exportar/:gameId` (bug 3), paquete agrupado, tildados por
      defecto (bug 7), tamaño de trucos vacío (bug 6), cola en `/exportar`.

## Fase 7 · Limpieza y QA

- [ ] Borrar `--dos-*` sin uso y componentes muertos.
- [ ] Revisar accesibilidad y comparar cada pantalla con su mockup a 1280 px.

## Cierre

- [ ] Validar contra todos los criterios de `spec.md`.
- [ ] Lint, tipos y tests limpios.
- [ ] Actualizar `docs/` si cambió la superficie pública.
- [ ] Marcar la feature como "Hecha" en `../../constitution/roadmap.md`.
