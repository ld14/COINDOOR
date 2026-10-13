# PROGRESS · Rediseño Flyer

Feature: [`spec/features/019-rediseno-flyer/`](../../spec/features/019-rediseno-flyer/spec.md) ·
ADR: [`0023`](../../spec/decisions/0023-estetica-flyer-reemplaza-dos.md)

## Fase 0 · Preparación — hecha (2026-10-08)

### Decisiones de trabajo

- Se trabaja en `master`, sin rama. El paquete queda en `docs/coindoor-rediseno/`.
- Se aprueban `@fontsource/bungee`, `rubik` e `ibm-plex-mono`.
- Los bugs de backend se corrigen en backend si no cambian contrato; si lo cambian,
  `TODO(backend)` y aviso.
- Ante choque, mandan los deltas D1–D5 sobre el rediseño (reseña 0–100, revistas sin
  descarga, export con "Siempre incluido" bloqueado).
- **No se pierde ninguna funcionalidad existente.**

### Decisión 1 · Guardado: autosave con debounce

- `frontend/src/hooks/useGameMutations.ts` expone una mutación por campo
  (`setTextField`, `setReview`, `setCheats`, `patchGame`, `uploadMedia`, …), y el backend
  escribe de forma atómica el `game.json` del juego
  ([`ADR-0008`](../../spec/decisions/0008-persistencia-en-archivos.md)): tolera escrituras
  parciales frecuentes. Plan B del spec §4 (un solo "Guardar") descartado.
- Cada mutación invalida **cuatro** queries (`games`, `systems`, `rom-candidates`,
  `game`). Con autosave eso recargaría la ficha mientras se escribe: hay que invalidar solo
  `game` (y `games` al terminar) y no pisar el estado local de un campo con foco.
- Hoy `FichaJuego.tsx` (1376 líneas) tiene `saveAll` (línea ~129) y `onSaveAll`; son lo que
  desaparece. El botón Exportar ya llama `saveAll()` antes de navegar: ese paso queda
  cubierto por "esperar a que termine el guardado pendiente".

### Decisión 2 · Origen: conservar `source` al aceptar

- `backend/store/juegos.py`: las sugerencias entran como
  `{"status": "suggested", ..., "source": provenance.source}` (líneas ~192 y ~209), pero
  el guardado manual escribe `{"status": "manual"}` **sin `source`** (líneas ~137, 150,
  158 y 219). Hoy un valor aceptado y uno escrito a mano son indistinguibles, y aceptar
  pierde la fuente.
- Cambio: aceptar = `manual` conservando `source`; editar a mano = `manual` + `source:
  "manual"`. Sin campos nuevos. El `source` es procedencia interna y no viaja al export
  ([`ADR-0002`](../../spec/decisions/0002-procedencia-interna.md)). Verificar en el export
  y en `lib/domain/guia.py:114` (lee `status == "manual"`) que nada depende de la ausencia
  de `source`.

## Bugs: causa hallada en el relevamiento

| # | Causa probable (verificar al corregir) |
|---|---|
| 1 | `frontend/src/components/dos/MenuBar.tsx:21` — el texto "0 juegos cargados" está **fijo** en el JSX. |
| 2 | `backend/store/sistemas.py:54` arma `gameCount=0` **fijo**; hay que contar fichas por sistema. |
| 3 | `FichaJuego.tsx:224` ya navega a `/exportar/${game.id}`. Reproducir antes de tocar: puede estar corregido o fallar en otro camino. |
| 4 | Pendiente: `NuevoJuego.tsx`, usar `fielddefs.json`. |
| 5 | Pendiente: `backend/api/roms.py:28` (`list_rom_candidates`) compara contra `romRef` de las fichas. |
| 6 | Pendiente: tamaño de Trucos en `ExportPage.tsx` / `backend/bundle/seleccion.py`. |
| 7 | Pendiente: estado inicial de la selección en `ExportPage.tsx`. |
| 8 | Pendiente: confirmar si perder `?precarga=` es intencional. |

## Relevado del código

- Primitivas en `frontend/src/components/dos/` (Banner, DosButton, DosFileInput, DosInput,
  DosSelect, DosTextarea, FieldTag, MenuBar, Modal, Panel, ProgressBar, SectionHeader,
  Spinner, StatusBadge, StatusBar, SunkenBox), con CSS Modules y tests propios.
- Páginas: `Configuracion`, `ExportPage`, `FichaJuego`, `Juegos`, `NuevoJuego`,
  `Sistemas`, `_Catalogo`, `EmptyPage`.
- Hooks: `useConfig`, `useDominantColors`, `useGame`, `useGameMutations`, `useGames`,
  `useModalFoco`, `useRomCandidates`, `useSuggestionsJob`, `useSystems`.
- Capa de API en `frontend/src/lib/api/` con un módulo por recurso.
- El backend ya soporta `/configuracion` (feature 013), por lo que Configuración (Fase 3)
  puede tener [Probar] sin endpoint nuevo si la validación de ruta ya existe; confirmar.

## Pendientes antes de la Fase 1

- Confirmar que el árbol de `frontend/` está limpio y que las features 015–018 (en curso)
  no tienen cambios sin commitear sobre `FichaJuego.tsx`.
- Correr `npx tsc --noEmit`, lint y tests para fijar la línea base.

## Qué se hizo, por unidad

| Fase | Unidad (commit `rediseno: <unidad>`) | Resultado |
|---|---|---|
| 0 | fase 0 | Feature 019, ADR 0023, decisiones de autosave y de origen. |
| 0 | backend-bugs, backend-source | `gameCount` real, candidatos de ROM sin ficha, cheats/review vacíos; edición manual escribe `source: manual` y existe el endpoint `accept`. |
| 1 | fundacion | Tokens Flyer, fuentes offline y shell (Topbar, Rail con contadores, StatusBar). |
| 2 | prim-base, prim-entrada, prim-nav | Primitivas nuevas y demos en `/_catalogo`. |
| 3 | juegos, sistemas-config | Juegos con pestañas, chips y banda "Seguís con…"; Sistemas con validación de ruta; Configuración con [Probar]. |
| 5 | nuevo-juego | Asistente de cuatro pasos, etiquetas de `fielddefs.json`. |
| 6 | exportar | Grupos en Card, selección por defecto corregida, total en vivo, cola en `/exportar`. |
| 4 | ficha-split, ficha-andamiaje y secciones | Ficha dividida en `pages/ficha/*`, autosave, hero, StepNav, ActionBar. |
| 7 | limpieza-qa (Ola 5) | Ver abajo. |

### Fase 7 · limpieza-qa

- **Funcionalidad restaurada.** Subida de varios PDF de manuales juntos (`Dropzone` con
  `multiple` + `onFiles`, `onFile` intacto). `ManualSection` acepta `onUploadAsync` para subirlos de a uno; **falta cablearlo en `FichaJuego.tsx`** (`onUploadAsync={(f) => mutations.uploadManual.mutateAsync(f)}`): sin eso suben en paralelo y pueden pisarse en el `game.json`. La alternancia primario/secundario al tomar
  color de la carátula usa un único contador (`pages/ficha/acentoSlot.ts`) que leen el Hero
  y Presentación: ya no se desfasan. `FichaJuego.tsx` conserva su `proximoAcento`, ahora
  sin efecto (se puede borrar cuando se destrabe ese archivo).
- **Migración de CSS.** `SuggestionsModal`, `DosFileInput`, `StatusBar`, `ContractBadge` y
  `/_catalogo` pasaron a tokens nuevos; `ImageModal`, `GalleryPanel` y `YoutubeDownload`
  ya los usaban. Lint sin errores (`SuggestionTrace` y `EmptyPage` sin uso eliminados).
- **Limpieza.** Fuera los alias `--dos-*` de `tokens.css`, `pages/ReadPages.module.css` y
  `EmptyPage`. Se conservan `SectionHeader` (lo usan `/_catalogo` y el demo) y
  `DosFileInput` (lo usa el paso Archivo de Nuevo juego). Un test impide reintroducir
  `--dos-*`.
- **Accesibilidad (DESIGN_SPEC §6).** Test de contrato: transiciones de 150 ms o menos,
  `prefers-reduced-motion` global en `reset.css`, y todo CSS que quita el outline repone
  `--focus-ring`. `aria-live` en la subida del `Dropzone`; motivo del botón deshabilitado
  (`disabledReason`) en Galería (Guardar) y Trucos (Separar).

## Diferencias contra los mockups

- **[Usar] en resultados de búsqueda de manuales:** queda [Abrir]. La API actual
  (`lib/api/manuals.ts`) solo sube un archivo o lista resultados; no hay endpoint para
  adjuntar un resultado por URL y descargarlo desde el navegador chocaría con CORS.
- **Juegos:** sin orden por última modificación ni "Exportado 02/10".
- **Configuración:** sin estado de servicios ni defaults.
- **Sistemas:** sin "Editar sistema".
- **Nuevo juego:** sin [Examinar…] (un navegador no entrega rutas del disco).
- **Trucos y Galería:** sin "va en el paquete" por truco ni tilde por miniatura.
- **Exportar:** sin descarga real del `.zip` desde la pantalla.

## Ajustes tras la revisión visual (2026-10-13)

Pedidos puntuales hechos mirando la app corriendo; no figuran en `DESIGN_SPEC.md`, que en
estos puntos quedó desactualizado.

- **Orden de la ficha:** Identidad, Presentación, Imágenes, Galería, Video, Textos, Reseña,
  Cómo se juega, Trucos, Manual y revistas (antes Presentación era la 7.ª).
- **Identidad:** el input y «Sugerir» van en una línea; Formato es una fila compacta.
- **Presentación:** carátula a la izquierda y los dos selectores de color a la derecha, con la
  leyenda de la carátula debajo de ellos; paleta de 17 colores en una línea; sin chips de
  origen (el primario se marca «obligatorio»).
- **Imágenes:** una imagen cargada cuenta como aceptada (sin «Sugerido», «Aceptar» ni
  «Cambiar»; fuera de los pendientes y del banner de precarga). ↻ y borrar (ícono) en una fila,
  y la zona de carga mínima al pie. En `game.json` siguen con `status: suggested`: el cambio es
  solo de presentación y de conteo.
- **Cómo se juega:** sección propia con Objetivo, Primeros pasos, Reglas, Modo multijugador y
  Acciones de los botones (editables). Se quitaron Cantidad de jugadores y Periféricos. El
  checklist pasó a la columna lateral, solo lectura. Backend: `PATCH` acepta `cabinetButtons`
  (escribe `cabinet.button_list`, ya exportado como `guia.acciones`).
- **Juegos:** el listado muestra la carátula cargada (el backend la toma de
  `images.caratula.url`) y toda la tarjeta abre la ficha, también si está lista o exportada.
- **Dependencias:** `npm audit fix` (brace-expansion, source-map-js); solo lockfiles.

Sin verificar en navegador. Sin correr: `test_patch_cargar_acciones_de_los_botones` (falta
`pydantic` en el entorno de desarrollo de Windows). Siguen fallando 3 tests por falta de
Python/Zod (`arcade`, `parity`, `validation`).

## PENDIENTES

1. Backend: `exportedAt` y fecha de modificación en el listado (Juegos no puede ordenar
   por última modificación ni mostrar "Exportado 02/10").
2. Editar sistema.
3. [Examinar…] en Nuevo juego (¿selector nativo vía el backend local?).
4. [Probar] real de ATTRACT (hoy valida la ruta; no ejecuta `attract doctor`).
5. Estado de servicios y defaults en Configuración.
6. "Va en el paquete" por truco y tilde por miniatura de galería: requieren cambio de
   modelo y un ADR.
7. Descarga real del `.zip`.
8. Propuesta de trucos persistida como `suggested`.
9. Adjuntar un resultado de búsqueda de manual ([Usar]): endpoint nuevo.
10. **Verificación visual (e2e) contra los mockups a 1280 px: no se hizo, no hubo navegador.**
    Hasta entonces la feature no se marca "Hecha" en el roadmap.
11. `tsc` falla en `src/pages/FichaJuego.tsx` (línea 365: `markReady.mutateAsync()` sin
    argumentos); es del cableado de la ficha, no de esta unidad.
12. En este entorno: `npm test` con el pool por defecto se cae (usar `--pool=threads`
    con 2 hilos) y fallan 3 tests por falta de Python/Zod (`arcade`, `parity`,
    `validation`).
