# Plan de implementación · Rediseño Flyer de COINDOOR

Stack detectado: React + Vite + TypeScript, CSS Modules, TanStack Query y react-router-dom. Hay tokens en `src/styles/tokens.css`, primitivas en `src/components/dos/`, páginas en `src/pages/` y dominio en `src/lib/domain/`.

**Reglas generales**

- Trabajar en la rama `rediseno-flyer`. Cada fase termina con la app andando, `tsc --noEmit` sin errores, lint OK y un commit.
- No cambiar contratos de API ni el modelo de datos sin avisar. Si algo de la spec necesita backend, dejarlo marcado como `TODO(backend)` y seguir.
- Toda la UI en castellano rioplatense (voseo), igual que hoy.
- Después de cada fase, comparar contra `mockups/png/` y anotar en `PROGRESS.md` qué quedó distinto y por qué.
- Las fases 4 y 5 son las más grandes: proponer un sub-plan antes de arrancarlas.

---

## Fase 0 · Preparación (corta)

1. Crear la rama. Copiar esta carpeta a `docs/rediseno/`.
2. Leer `DESIGN_SPEC.md`, abrir los mockups y relevar:
   - `src/styles/tokens.css`, `src/App.tsx`, `src/App.module.css` y `src/components/dos/*`.
   - `src/hooks/useGameMutations.ts`, `src/lib/domain/completeness.ts`, `types.ts` y `fielddefs.json`.
   - Cómo calcula `MenuBar` el texto "N juegos cargados".
3. Escribir `docs/rediseno/PROGRESS.md` con:
   - Lo relevado.
   - La decisión de **guardado** (autosave o un solo guardar; ver spec §4).
   - Cómo se va a distinguir "aceptado de ArcadeDB" de "manual" (spec §3).

**Listo cuando**: PROGRESS.md tiene las dos decisiones justificadas con referencias al código.

## Fase 1 · Tokens, fuentes y shell

1. Instalar `@fontsource/bungee`, `@fontsource/rubik` y `@fontsource/ibm-plex-mono`, e importarlos en `main.tsx`.
2. Reemplazar el `:root` de `src/styles/tokens.css` por `tokens/flyer-tokens.css`, con los alias `--dos-*` incluidos para no romper los CSS modules.
3. Shell (`App.tsx`, `App.module.css`):
   - Topbar con marca, búsqueda global (`/` la enfoca) e indicador de contrato.
   - `MenuBar` → **Rail**: vertical, con contadores reales. **Corregir** "0 juegos cargados".
   - `Banner` solo si el contrato tiene un problema.
   - `StatusBar` con el indicador de contrato a la derecha.
   - Sacar la sombra ASCII `░` y el borde de 5px de `.content`.
4. Comportamiento responsive por debajo de 900px (spec §1).

**Listo cuando**: todas las pantallas cargan con la paleta nueva, Rubik como fuente de cuerpo, rail y topbar nuevos, contador correcto y ninguna regresión funcional.

## Fase 2 · Primitivas

1. Actualizar `src/components/dos/*` según spec §2. Mantener las APIs y agregar props:
   - `DosButton`: variante `secondary` y prop `size`.
   - `StatusBadge`: estado `exported`.
   - `FieldTag` → `OriginChip`: prop `source`; se puede dejar `FieldTag` como alias.
   - `Panel`/`Card`: props `band`, `number`, `title`, `hint`, `actions`.
   - `ProgressBar` en píldora.
   - `Modal` con banda.
   - Inputs con estado `invalid` y mensaje.
2. Crear las nuevas:
   - `SegmentedControl`, `ChoiceCards`, `NumberStepper`, `ListEditor`
   - `Dropzone`: drag, Ctrl+V, clic y progreso; reemplaza `DosFileInput` en la UI.
   - `InlineSuggestion`, `StepNav`, `CheckTile`, `FilterTabs`, `FilterChips`, `NextPendingCard`, `ActionBar`
3. Migrar los CSS modules de las primitivas a tokens nuevos (sin `--dos-*`).
4. Actualizar `/_catalogo` con todas las primitivas y sus estados. Es la referencia viva para comparar contra `mockups/03-estados-de-campo.html`.

**Listo cuando**: `/_catalogo` muestra todo, se puede usar con teclado y las primitivas no usan `--dos-*`.

## Fase 3 · Juegos, Sistemas, Configuración (pantallas simples primero)

1. **Juegos** (spec §5.2, mockup 05): FilterTabs con contadores, FilterChips de sistema, orden, grilla/lista, banda "Seguís con…", tarjetas con la acción según el estado. Mantener la paginación actual.
2. **Sistemas** (spec §5.4, mockup 08): tarjetas con contador real (**corregir** "0 juegos"; revisar `gameCount` en la API/hook), validación de la ruta absoluta en vivo, alta en tarjeta.
3. **Configuración** (spec §5.6, mockup 09): ATTRACT con [Probar] si existe un endpoint, o validación de la ruta. Servicios y valores por defecto solo si el backend ya los expone; si no, `TODO(backend)`.

**Listo cuando**: las 3 pantallas coinciden con su mockup y los contadores muestran datos reales.

## Fase 4 · Ficha de juego (la más grande; proponer sub-plan antes de tocar código)

1. **Partir `src/pages/FichaJuego.tsx`** en `src/pages/ficha/`:
   - `FichaPage` (layout)
   - `FichaHero`, `PrecargaBanner`, `StepNav`, `NextPending`, `ActionBar`
   - Una sección por archivo: Identidad, Imágenes, Video, Textos, CómoSeJuega, Trucos, Presentación, Galería, Reseña, ManualRevistas, Gabinete
   - Hacerlo primero **sin cambiar la UI** (refactor puro) y commitear.
2. Hook `useFichaProgress(game)`: % completo, obligatorios faltantes (con ancla a la sección o campo), sugerencias pendientes y orden de la cola "siguiente pendiente".
3. Aplicar la UI nueva sección por sección (spec §5.1, mockups 01, 02 y 04), con OriginChip, InlineSuggestion, ListEditor, ChoiceCards, etc.
4. **Guardado** según la decisión de la fase 0: sacar los "Guardar X" y "Guardar todo". Indicador en la topbar.
5. **Revisión de sugerencias**: "Aceptar" por campo (Enter), "Aceptar todas" por sección, banner de precarga con [Aceptar todo] [Revisar una por una] (reusar `SuggestionsModal` / `useSuggestionsJob`).
6. **Atajos**: `N` lleva al siguiente pendiente y `Enter` acepta la sugerencia del campo con foco, sin interferir al escribir en textareas.
7. Trucos con casilla de inclusión y "Separar en trucos" (el resultado entra como `suggested`); Presentación con selector de color desde la carátula y validación de HEX; Reseña con las 6 categorías.

**Listo cuando**:

- `/juegos/lethal-enforcers` se ve y se comporta como `mockups/02-ficha-en-carga`.
- `/juegos/arkanoidu` coincide con `01-ficha-completa`.
- No queda ningún botón "Guardar X" por sección.
- Exportar está deshabilitado con el motivo mientras falten obligatorios.

## Fase 5 · Nuevo juego (asistente)

Spec §5.3 y mockup 06. Asistente de 4 pasos, sistema y tratamiento detectados por carpeta, identidad con labels de `fielddefs.json` (**corregir** las claves en inglés), "Crear ficha y empezar a cargar" con precarga. **Revisar** por qué ROMs que ya tienen ficha aparecen en "Instalados sin ficha" (ver `BUGS.md`).

## Fase 6 · Exportar

Spec §5.4 y mockup 07.

1. **Corregir** el botón Exportar de la ficha para que navegue a `/exportar/:gameId`.
2. Paquete agrupado, opcionales con datos tildados por defecto, ítems sin datos deshabilitados con el motivo, total, destino ATTRACT o .zip, fecha de la última exportación.
3. `/exportar` sin id pasa a ser la cola de exportación.

## Fase 7 · Limpieza y QA

1. Borrar los alias `--dos-*` que ya no se usen (`grep -r "var(--dos-" src`) y los componentes muertos.
2. Revisar accesibilidad: contraste, foco, teclado y `aria-live` en el progreso (spec §6).
3. Comparar cada pantalla con su mockup a 1280px y anotar las diferencias en PROGRESS.md.
4. Correr los tests existentes y sumar tests a `useFichaProgress` y al mapeo de origen (spec §3).

---

## Fuera de alcance (no hacer sin pedir)

- Paleta de comandos `Ctrl+K` (dejar el atajo reservado).
- Endpoints nuevos de backend (estado de servicios, preferencias) → `TODO(backend)`.
- Las otras dos opciones de diseño (Refinado y Cabina) que aparecen en `tokens.json`.
