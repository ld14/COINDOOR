# COINDOOR · Especificación de diseño (tema Flyer 80s)

Referencia visual: `mockups/*.html` (abrir en el navegador) y `mockups/png/`.
Tokens: `tokens/flyer-tokens.css` (CSS) y `tokens/tokens.json` (fuente, incluye las otras 2 opciones descartadas: usar solo el tema `flyer`).

> Las maquetas son estáticas y usan imágenes de relleno. Lo que manda es el comportamiento descripto acá; la maqueta es la guía visual.

---

## 1. Fundamentos

### Color (tema `flyer`)

| Token | Valor | Uso |
|---|---|---|
| `--surface-0` | `#F3E6CC` | Fondo de la app |
| `--surface-1` | `#FFF8EA` | Tarjetas |
| `--surface-2` | `#FFFFFF` | Campos, slots, filas |
| `--surface-inverse` | `#1B1A2E` | Topbar, statusbar, panel "Siguiente pendiente" |
| `--ink` / `--ink-muted` | `#1B1A2E` / `#57536C` | Texto |
| `--line` / `--line-soft` | `#1B1A2E` / `#E4D4B2` | Bordes / divisores |
| `--accent` | `#C8233A` | Acción primaria, paso activo, origen **Manual** |
| `--accent-2` | `#FFC93C` | **Sugerido / pendiente**. Solo relleno, texto encima en `--ink-on-accent-2` |
| `--accent-3` | `#2B59C3` | Origen **ArcadeDB**, estado **Exportado** |
| `--ok` / `--warn` / `--error` | `#1E7A4A` / `#8A5A00` / `#B3122A` | Estados |

Contraste verificado: texto ≥ 4.5:1, bordes de control ≥ 3:1. El estado nunca depende solo del color: siempre lleva texto o ícono (✓, !, ✕).

### Tipografía

- **Bungee** (display): título de página o juego (40px), encabezado de tarjeta (18px), número de paso. Nunca en párrafos ni en etiquetas.
- **Rubik** (body): todo lo demás. Cuerpo 15/22, etiqueta 13px semibold, meta 12px.
- **IBM Plex Mono**: rutas, nombres de archivo, HEX, tamaños, entradas MAME (`P1_BUTTON1`), atajos de teclado.
- Hoy todo está en Consolas. Pasarlo a Rubik es el cambio de legibilidad más grande.

### Forma

- Tarjeta: borde 3px `--line`, `--radius-lg`, `--shadow-card` (sombra dura desplazada 5px).
- Control (input, select, botón): borde 2px, `--radius-md`. Foco: `--focus-ring`.
- Chips, pasos y barras de progreso: `--radius-pill`.
- Encabezado de tarjeta: **banda de color** de fondo (`--band`), borde inferior 3px, número en círculo + título Bungee + texto de ayuda + acción a la derecha. Rotación de bandas por sección: Identidad `accent-3`, Imágenes `accent-2`, Video `accent-3`, Textos `accent`, Cómo se juega `accent-2`, Trucos `accent-2`, Reseña `accent-3`, Manual `accent`, Presentación `accent`. Sobre `accent-2` el texto va en `--ink-on-accent-2`; sobre las demás bandas, en blanco.

### Layout global (shell)

```
┌ topbar (surface-inverse, borde inferior 6px accent-2) ───────────────────────┐
│ ■■■ COINDOOR  preparador…   [⌕ Buscar juego, sistema o romset…  /]   (Contrato ATTRACT v3) │
├ rail 200px ──┬ main ──────────────────────────────────────────────────────────┤
│ Sistemas   2 │ crumbs                                                           │
│ Juegos    29 │ page-head (h1 Bungee + subtítulo + acciones)                     │
│ Nuevo j.   7 │ contenido: col-main (fluida) + col-side 300px sticky             │
│ Exportar   2 │                                                                  │
│ Config.      │                                                                  │
├──────────────┴─────────────────────────────────────────────────────────────────┤
│ statusbar: F1 Ayuda · F2 Sistemas · F3 Juegos · F4 Exportar · F5 Config · Ctrl+K · Contrato ATTRACT v3 ✓ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

- El **rail** reemplaza al `MenuBar`. Muestra contadores reales: juegos, sistemas, ROMs sin ficha, pendientes de exportar. El ítem activo va relleno en `accent` con `shadow-pop`.
- El **Banner "Contrato ATTRACT cargado…"** deja de estar en todas las páginas. Pasa a un indicador chico en la topbar y la statusbar, y solo vuelve como banner si hay un problema con el contrato.
- `/` enfoca la búsqueda global. `Ctrl+K` queda reservado para una paleta de comandos (opcional, fase final). Esc cierra modales. F1–F5 se mantienen.
- Desaparecen la sombra ASCII `░` de `.content` y el borde de 5px.
- Por debajo de 900px el rail se colapsa a íconos y `col-side` baja debajo de `col-main`.

---

## 2. Primitivas (evolución de `src/components/dos/`)

Mantener los nombres y las APIs actuales donde se pueda y agregar props. Equivalencias:

| Hoy | Nuevo comportamiento |
|---|---|
| `DosButton` variants `primary`, `primary-small`, `ghost`, `ghost-small`, `danger-small`, `pressed` | Agregar `secondary` (fondo `surface-2`, borde 2px `line`) y prop `size: 'md' \| 'sm'`. `primary` = `accent` + `shadow-pop`. `ghost` = sin borde, subrayado. `danger` = ghost en `--error`. `disabled` = `surface-2`, texto muted, sin sombra, con el **motivo** en `title` o al lado ("Exportar (faltan 3)"). |
| `FieldTag status: manual\|suggested\|empty` | Pasa a **OriginChip**. Ver §3. Agregar la prop `source?: string`. |
| `StatusBadge status: ready\|incomplete\|error` | Labels: `incomplete` → "● En carga" (`accent-2`), `ready` → "✓ Listo" (`ok`), `error` → "✕ Con errores" (`error`). Agregar `exported` → "⇪ Exportado" (`accent-3`, fondo `surface-1`). Píldora con borde 2px. |
| `Panel` | **Card**: props `band?: CSS color var`, `number?: number`, `title`, `hint?`, `actions?`. |
| `SectionHeader` | Lo absorbe Card (encabezado con banda). Se puede mantener para encabezados de página. |
| `SunkenBox` | Fondo `surface-2`, borde 2px `line-soft`, radio md. |
| `ProgressBar` | Píldora, borde 1.5–2px `line`, alto 6–10px, relleno según estado. |
| `Modal` | Card con banda; ancho por tamaño; Esc y click afuera cierran (mantener `useModalFoco`). |
| `DosInput` / `DosTextarea` / `DosSelect` | Borde 2px, `radius-md`, 15px Rubik. Placeholder con **ejemplo real** ("Ej.: 1993"). Estado `invalid` → borde `error` + mensaje debajo. |
| `DosFileInput` | Reemplazar por **Dropzone** (abajo). |
| `MenuBar` | **Rail** (§1). |
| `StatusBar` | Fondo `surface-inverse`, `kbd` con borde; sumar el indicador de contrato a la derecha. |
| `Banner` | Solo para problemas: fondo `accent-2`, borde 2px, ícono "!". |
| `Spinner` | Igual, en `accent`. |

### Primitivas nuevas

- **SegmentedControl**: opciones excluyentes cortas (Tratamiento, Modo multijugador, Instalados/Ruta/Subir). La opción activa va en `accent` y una opción imposible queda `disabled` y tachada.
- **ChoiceCards** (`.pk` en la maqueta): opciones con subtítulo (Formato, Sistema, Tratamiento en el alta). La seleccionada va en `accent` + `shadow-pop`; la recomendada tiene borde punteado `accent-3` y el subtítulo "recomendado por…".
- **NumberStepper**: − valor + (Jugadores).
- **ListEditor**: un ítem por fila, reordenable por arrastre (⋮⋮), Enter agrega el siguiente, "+ Agregar paso". Reemplaza a los textareas de "un paso por línea" (Primeros pasos, Reglas). Se serializa igual que hoy (líneas).
- **Dropzone**: arrastrar, pegar con Ctrl+V o hacer clic. Muestra "Soltá una imagen acá o pegala con Ctrl+V", tiene una acción secundaria opcional ("Buscar en ArcadeDB") y un estado de progreso.
- **InlineSuggestion**: caja con borde punteado `accent-2` debajo del campo: "ArcadeDB sugiere: **X** — [Usar] [Ignorar]".
- **StepNav**: píldoras numeradas por sección (sticky). El número indica estado: número normal = en curso, ✓ en `ok` = completa, ! en `error` = bloquea la exportación, fondo `accent-2` = algo para revisar. Al lado lleva el texto corto del pendiente ("Objetivo obligatorio", "5 sugeridos"). Clic hace scroll a la sección.
- **CheckTile**: casilla grande de 22px con label y metadato a la derecha (paquete de exportación, trucos, galería).
- **FilterTabs** con contador y **FilterChips** (sistemas).
- **NextPendingCard**: panel `surface-inverse` en la columna lateral con el próximo pendiente, el botón "Ir → N" y la cola ordenada (primero obligatorios en rojo, después revisiones en ámbar).
- **ActionBar** inferior sticky (solo en la ficha): progreso, atajos, "Guardar borrador y salir", "Exportar" (deshabilitado con el motivo).

Actualizar `/_catalogo` para que muestre todas las primitivas en sus estados. Es la referencia viva.

---

## 3. Origen y estado de un campo

El modelo actual tiene `FieldStatus = 'empty' | 'manual' | 'suggested'` + `source?: string`. Mapeo a la UI sin cambiar el backend:

| Datos | Chip | Visual del control |
|---|---|---|
| `status: 'empty'` | `○ Vacío` (contorno) | Placeholder con ejemplo |
| `empty` + obligatorio que bloquea la exportación | `○ Vacío` + etiqueta `OBLIGATORIO` en rojo | Borde 2px `error` + "✕ Bloquea la exportación" |
| `status: 'suggested'` | `● Sugerido · sin revisar` (relleno `accent-2`) | Borde punteado `accent-2` + botón "✓ Aceptar" (Enter) |
| `status: 'manual'` y `source` externo (`arcadedb`, `mame`, `screenscraper`, …) | `● ArcadeDB` (punto `accent-3`; el texto es el nombre de la fuente) | Normal |
| `status: 'manual'` sin `source` o `source: 'manual'` | `● Manual` (punto `accent`) | Normal |
| Error de formato (`game.errors[field]`) | — | Borde `error` + mensaje inline ("Hex incompleto: 6 dígitos") |
| Subida o descarga en curso | — | Barra de progreso + Cancelar; el resto del form sigue editable |

Reglas:

1. **Aceptar** una sugerencia = `status: 'manual'`, conservando el `source`. El chip pasa de "Sugerido" a "ArcadeDB".
2. **Editar** a mano un valor con `source` externo = `status: 'manual'`, `source: 'manual'`. Si la fuente tiene otro valor, se muestra como InlineSuggestion "ArcadeDB dice: X [Usar]".
3. Todo lo que propone el sistema (ArcadeDB, reglas, IA, "Proponer") entra como `suggested`. Nunca escribe un valor final directo.
4. "Sugerir" deja de ser un botón por campo con texto. Pasa a ser un ícono ↻ (con `title="Sugerir desde ArcadeDB"`) por campo y un "↻ Sugerir todo" por sección.
5. Un obligatorio vacío se pinta en `error` solo si bloquea algo (exportar); antes de eso es "Vacío".

> **Verificar en el código**: si `source` hoy no distingue "aceptado de ArcadeDB" de "escrito a mano", ajustar `useGameMutations` para setear `source` al aceptar o editar. No inventar campos nuevos en el backend sin confirmarlo.

---

## 4. Guardado

- **Objetivo**: sacar los botones "Guardar X" por sección y "Guardar todo". Se guarda **automáticamente** con debounce (~800 ms tras dejar de escribir y al perder el foco), usando las mutaciones existentes.
- La topbar muestra "Guardando…", "Guardado · hace 4 s" o "Error al guardar — Reintentar".
- Si el backend no tolera escrituras parciales frecuentes, plan B: mantener un **único** "Guardar cambios" en la ActionBar, con contador de cambios sin guardar y `beforeunload`. Decidirlo después de leer `useGameMutations.ts` y la API.
- "Marcar como listo" desaparece como acción manual si el estado se calcula (completitud 100% = Listo). Si hoy es una marca explícita del usuario, se mantiene en la cabecera del juego.

---

## 5. Pantallas

### 5.1 Ficha de juego `/juegos/:gameId` (maquetas 01, 02, 03, 04)

Orden vertical: crumbs → **Hero** → **Banner de precarga** (si hay sugerencias pendientes) → **StepNav** sticky → `col-main` + `col-side` sticky → **ActionBar**.

- **Hero**: carátula 112×150 (en Flyer, rotada −3° con `shadow-pop`) sobre fondo `accent-2`. Lleva StatusBadge, sistemas y archivo; título Bungee 40px con sombra de texto `accent`; metadatos en una línea; progreso; y **"Para exportar falta:"** con píldoras ✕ clickeables por cada obligatorio faltante (salen de `missingRequired()` + `guiaChecklist` requeridos).
- **Banner de precarga**: "ArcadeDB trajo N datos · X aplicados · **Y esperan revisión**", barra de proporción y botones [Aceptar todo] [Revisar una por una →]. "Revisar una por una" abre el `SuggestionsModal` existente, o recorre los campos `suggested` haciendo scroll a cada uno.
- **Secciones** (Card numerada, en este orden): 1 Identidad · 2 Imágenes · 3 Video · 4 Textos · 5 Cómo se juega · 6 Trucos · 7 Presentación · 8 Galería · 9 Reseña · 10 Manual y revistas · Gabinete (en la columna lateral).
  - **Identidad**: grilla de 2 columnas. Formato con ChoiceCards (recomendada según el sistema o romset). Jugadores con NumberStepper. Etiquetas desde `fielddefs.json` en castellano.
  - **Imágenes**: 4–5 slots en grilla. Si hay varias candidatas de distintas fuentes, aparece una fila "ArcadeDB encontró 3 opciones — elegí una" con la seleccionada resaltada y un Dropzone "Usar la mía". Cada slot `suggested` lleva borde punteado y [✓ Aceptar] [Cambiar]; los aceptados, "✓ Aceptada". Va un "✓ Aceptar las N" en el encabezado.
  - **Video**: Dropzone .mp4 + URL de YouTube con [Descargar] y progreso (`YoutubeDownload` existente).
  - **Textos**: Sinopsis con contador (`248 / 600`) y "✓ Aceptar como está / o editalo y queda como Manual". **Objetivo** obligatorio con placeholder de ejemplo, error "Sin objetivo la guía no se exporta" y "✦ Proponer un objetivo". Primeros pasos y Reglas con ListEditor + "✦ Proponer 3 pasos".
  - **Cómo se juega**: el checklist (`guiaChecklist`) con acción en la fila: [Escribir ↑] lleva al campo y Modo multijugador se resuelve con un SegmentedControl en la misma fila. Si el juego es simultáneo, *Individual* queda deshabilitado.
  - **Trucos** (`CheatsField.groups[].entries{name,input}`): grupos con nombre editable y "Eliminar grupo". Cada entrada tiene casilla "va en el paquete", **Qué hace** (`name`), **Código / procedimiento** (`input`), ⋮⋮ para reordenar y ✕. Las entradas se colapsan a una línea si son largas. La caja "Pegá una guía o texto suelto → ✦ Separar en trucos" reemplaza a "Interpretar con IA", y el resultado entra como `suggested`.
  - **Presentación**: color primario obligatorio. Si los colores dominantes son casi negros (luminancia < 0.05), avisa y propone colores con buen contraste. Se puede tomar un color de la carátula con un clic (cursor crosshair). Input HEX con validación en vivo. Secundario igual, opcional.
  - **Galería**: miniaturas tildables (viajan en el paquete) + "Traer de ArcadeDB / LaunchBox".
  - **Reseña**: puntaje 0–100 grande con barra y las 6 categorías del modelo (`originalidad, graficos, adiccion, sonido, dificultad, animacion`) con escala de 1 a 5.
  - **Manual y revistas**: Dropzone PDF + resultados de búsqueda (título, páginas, tamaño, [Usar]) y un estado vacío claro para revistas.
- **col-side** (sticky): NextPendingCard · Archivo del juego (nombre, tamaño, ruta en mono, ⇄ cambiar, SegmentedControl de Tratamiento) · Gabinete (specs + tabla del mapa de botones con color) · Precarga ("Hoy 14:02 · 21 datos · ↻ Volver a precargar; no pisa lo editado").
- **ActionBar**: `60% · 3 obligatorios · 6 para revisar` · atajos `Enter` aceptar sugerencia, `N` siguiente pendiente · [Guardar borrador y salir] [⇪ Exportar (faltan 3)].
- **FichaJuego.tsx hoy es enorme**: dividirlo en `src/pages/ficha/` con un componente por sección (`IdentidadSection`, `ImagenesSection`, …), `FichaHero`, `StepNav`, `NextPending` y `ActionBar`. El estado de completitud sale de un hook (`useFichaProgress`) que combina `missingRequired`, `guiaChecklist` y los `suggested`.

### 5.2 Juegos `/juegos` (maqueta 05)

- page-head: "Juegos" + "29 fichas · 2 para exportar · 7 ROMs instalados sin ficha" + [Ver 7 ROMs sin ficha] [+ Nuevo juego].
- FilterTabs con contador: Todos · En carga · Listos sin exportar · Exportados · Con errores. Fila con búsqueda, FilterChips de sistema con contador, orden (última modificación por defecto) y toggle grilla/lista.
- Si hay un juego en carga: banda `accent-2` "Seguís con *X* · 60% · faltan …" con [Continuar →].
- Grilla de 5 columnas de tarjetas: carátula 3:4 (si no hay, iniciales sobre un color derivado del título), badge de estado, título, `SISTEMA · AÑO`, barra de progreso, nota ("Faltan 3 obligatorios" o "Exportado 02/10") y **acción según el estado**: Seguir cargando / Exportar / Abrir. La vista lista mantiene la fila actual mejorada.
- "Cargar más" o paginación al pie.

### 5.3 Nuevo juego `/juegos/nuevo` (maqueta 06)

Asistente de 4 pasos (pasos en píldora): **Archivo → Sistema y tratamiento → Identidad → Abrir la ficha**.

1. **Archivo**: tarjetas seleccionables de los ROMs instalados sin ficha (tipo ZIP/DIR, nombre, `MAME · zip · 21 MB`, ruta en mono) + filtro. SegmentedControl [Instalados | Indicar ruta | Subir ROM].
2. **Sistema y tratamiento**: ChoiceCards. Se **propone por carpeta** (`mame/` → Arcade + Copiar, `ms-dos/` → MS-DOS + Descomprimir) con el chip "Detectado". "+ Nuevo sistema" abre el alta en un modal.
3. **Identidad**: precargada si el catálogo o ArcadeDB lo reconoce. Labels en castellano desde `fielddefs.json` (hoy muestra `title`, `year`…).
4. Columna lateral "Resumen del alta" (`surface-inverse`) con casilla "Precargar ArcadeDB al crear" (tildada) y **[Crear ficha y empezar a cargar →]**, que navega a la ficha con la precarga lista.

### 5.4 Exportar `/exportar/:gameId` y `/exportar` (maqueta 07)

- Grupos en Card: **Siempre incluido** (deshabilitados y tildados) · **Guía "Cómo se juega"** · **Media opcional** · **Extras**, cada uno con "N de M · tamaño" y [Quitar todo].
- CheckTile por ítem con el tamaño en mono. **Lo opcional que tiene datos viene tildado por defecto**; lo que no tiene datos queda deshabilitado con el motivo ("no hay trucos", "sin cargar").
- Columna lateral: total grande (Bungee) + cantidad de elementos; **Destino** con radio [Cargar en ATTRACT (ruta ✓) | Descargar .zip]; [⇪ Exportar a ATTRACT]; "Exportado por última vez el 02/10. Se reemplaza esa versión."
- **`/exportar` sin id** pasa a ser la **cola**: listos sin exportar y en carga, con [Exportar los listos (N)] y un link a cada uno.

### 5.5 Sistemas `/sistemas` (maqueta 08)

- Grilla de 3 tarjetas: ícono con el nombre corto, nombre, `shortName` en mono, **contador real** de juegos y comando de lanzamiento en mono con validación (✓ existe / ✕ no existe, desde `System.valid` y `errorMsg`). Acciones [Ver juegos] (abre `/juegos` filtrado) y [Editar].
- La tarjeta punteada "Nuevo sistema" valida que la ruta sea absoluta mientras escribís, tiene [Examinar…] y deja [Crear sistema] deshabilitado mientras haya errores.

### 5.6 Configuración `/configuracion` (maqueta 09)

- **ATTRACT**: ruta en mono + [Probar] → "✓ encontrado · contrato vN" o error.
- **Servicios** (solo lectura): ArcadeDB, IA, buscador de imágenes. Cada uno muestra un punto de estado y una explicación de qué se desactiva si falta la clave. **Nunca mostrar valores de `.env`.** Si hoy no hay un endpoint de estado, mostrar solo lo que el backend ya expone o dejar la sección para después.
- **Valores por defecto**: precargar ArcadeDB al crear, incluir lo opcional al exportar, tratamiento por defecto. Implementar solo si hay dónde guardarlos; si no, dejarlo anotado como pendiente.

---

## 6. Accesibilidad y calidad

- Todo accionable se alcanza con teclado; el foco visible usa `--focus-ring`.
- Los chips y badges siempre llevan texto.
- Los botones deshabilitados explican el motivo.
- Las regiones con progreso usan `aria-live="polite"`.
- Respetar `prefers-reduced-motion` (sin transiciones de más de 150ms).
- Probar a 1280px y 1440px; nada roto a 900px.
