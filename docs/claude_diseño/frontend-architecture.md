# COINDOOR — Frontend Architecture

Aplicación de escritorio web para carga y curaduría de juegos retro. Estética MS-DOS / Norton
Commander. Este documento define la arquitectura de implementación. Los documentos hermanos
(`design-system.md`, `data-model.md`, `screens-spec.md`) definen el aspecto visual, los datos y
el comportamiento pantalla por pantalla.

---

## 1. Stack

| Capa | Elección | Motivo |
|---|---|---|
| Build | Vite | Arranque rápido, sin configuración |
| Lenguaje | TypeScript (strict) | El modelo de datos tiene muchos estados discriminados |
| UI | React 18 | Componentes de función + hooks |
| Estado servidor | TanStack Query v5 | Cache, invalidación, polling de jobs |
| Estado UI | useState local + un `AppContext` | El estado global real es mínimo |
| Router | React Router v6 | Rutas por pantalla, deep-link a la ficha |
| Formularios | react-hook-form + zod | Validación del contrato ATTRACT |
| Estilos | CSS Modules + `tokens.css` | Sin Tailwind: los bordes 3D outset/inset y el
   look DOS se expresan mejor con CSS plano |
| Tests | Vitest + Testing Library | Reglas de completitud y máquinas de estado |

No usar librerías de componentes (MUI, shadcn, Chakra). El look es deliberadamente el de un
programa DOS y cualquier librería moderna lo rompe. Todos los controles se escriben a mano.

---

## 2. Estructura de carpetas

```
src/
  main.tsx
  App.tsx                      # Router + layout DOS (barra título, menú, barra F-keys)
  styles/
    tokens.css                 # Variables CSS: paleta DOS, bordes, tipografía
    reset.css
  lib/
    api/
      client.ts                # fetch wrapper, manejo de errores
      systems.ts               # endpoints de sistemas
      games.ts                 # endpoints de juegos
      assets.ts                # subida de imágenes/video/texto
      suggestions.ts           # sugerencias externas
      manuals.ts               # adjuntar/procesar manuales
      magazines.ts             # búsqueda IA de revistas
      export.ts                # export + verificación ATTRACT
    domain/
      types.ts                 # Ver data-model.md
      fieldDefs.ts             # IMAGE_DEFS / VIDEO_DEFS / TEXT_DEFS
      completeness.ts          # missingRequired(), computeGameStatus()
      validation.ts            # esquemas zod (ruta absoluta, año 4 dígitos, hex)
  components/
    dos/                       # Primitivas visuales — ver design-system.md
      Panel.tsx                # Caja gris con borde outset
      SunkenBox.tsx            # Borde inset (inputs, previews)
      DosButton.tsx            # variant: primary | ghost | ghost-small | danger-small
      DosInput.tsx
      DosSelect.tsx
      DosTextarea.tsx
      SectionHeader.tsx        # Barra azul #00007A a 100% de ancho
      StatusBadge.tsx          # LISTO / INCOMPLETO / CON ERRORES
      FieldTag.tsx             # ● MANUAL / ◔ SUGERIDO / ○ VACÍO
      Modal.tsx                # Ventana con barra de título azul y botón X
      ProgressBar.tsx
      Spinner.tsx
      MenuBar.tsx              # Panel lateral "Main Menu"
      StatusBar.tsx            # Barra negra F1..Esc
      Banner.tsx               # Aviso amarillo del contrato
  features/
    systems/
      SystemsPage.tsx
      SystemCard.tsx
      NewSystemModal.tsx
    games/
      GamesPage.tsx
      GamesFilters.tsx
      GameRow.tsx              # Fila con miniatura de portada
    newGame/
      NewGamePage.tsx
      RomSourceStep.tsx        # Subir ROM | Indicar ruta
      IdentityStep.tsx
    game/
      GameDetailPage.tsx
      GameDetailHeader.tsx
      IdentitySection.tsx
      MediaSection.tsx         # Imágenes + Video (misma tarjeta de campo)
      FieldCard.tsx
      TextsSection.tsx
      PresentationSection.tsx  # Swatches + HEX + detectar de la carátula
      ManualsSection.tsx       # Lista de N manuales
      MagazineSection.tsx
      SuggestionsModal.tsx
      MagazineSearchModal.tsx
    export/
      ExportPage.tsx
      ExportGameList.tsx       # Buscador + lista paginada
      ExportRunPanel.tsx       # Armando → Verificando → Resultado
  hooks/
    useGames.ts
    useGame.ts
    useSystems.ts
    useSuggestions.ts
    useManualProcessing.ts     # polling del job
    useExportRun.ts
```

---

## 3. Rutas

| Ruta | Pantalla |
|---|---|
| `/sistemas` | Sistemas / plataformas |
| `/juegos` | Lista de juegos (default) |
| `/juegos/nuevo` | Alta de un juego (wizard 2 pasos) |
| `/juegos/:gameId` | Ficha del juego |
| `/exportar` | Exportar |

Los filtros de la lista de juegos y el buscador de exportación viven en la query string
(`?q=&sistema=&estado=`) para que la vista sea compartible y sobreviva al refresh.

---

## 4. Layout de la aplicación (`App.tsx`)

Tres zonas fijas, siempre presentes:

1. **Barra de título** — franja cian `#00AAAA`, texto negro centrado
   `COINDOOR — Carga de juegos retro`, con un cuadradito gris a la izquierda (botón de sistema).
2. **Cuerpo** — flex horizontal, `padding: 10px; gap: 10px`:
   - `MenuBar` fijo de 190px (panel gris con cabecera azul "Main Menu" y contador de
     juegos/sistemas al pie).
   - Zona de contenido: `Banner` opcional del contrato + un panel gris con borde **inset**
     que scrollea. Todo el contenido de cada pantalla vive dentro de ese panel.
3. **Barra de estado** — franja negra con `F1 Ayuda · F2 Sistemas · F3 Juegos · F4 Exportar ·
   Esc Cerrar`; las teclas en amarillo `#FFFF55`.

Los atajos F2/F3/F4/Esc se registran en un `useEffect` global en `App.tsx` y navegan.

---

## 5. Estado y datos

### 5.1 Regla general

Todo dato de dominio (sistemas, juegos, campos, manuales, revistas) viene del servidor vía
TanStack Query. El estado local de React solo guarda cosas efímeras de UI: qué modal está
abierto, el texto del buscador, el paso del wizard, el valor del input HEX.

### 5.2 Query keys

```ts
['systems']
['games', { q, systemId, status, page }]
['game', gameId]
['suggestions', gameId, fieldKey]
['magazine-search', gameId]
['export-run', runId]
```

### 5.3 Mutaciones e invalidación

| Mutación | Invalida |
|---|---|
| `createSystem` | `['systems']` |
| `createGame` | `['games']` |
| `setField(gameId, key, value)` | `['game', gameId]`, `['games']` |
| `clearField` | idem |
| `applySuggestion` | idem |
| `setAccent` | `['game', gameId]` |
| `attachManual` | `['game', gameId]` |
| `processManual` | arranca polling; al terminar invalida `['game', gameId]` |
| `linkMagazine` / `unlinkMagazine` | `['game', gameId]` |
| `markReady` | `['game', gameId]`, `['games']` |

Usar actualización optimista solo en `setField` y `setAccent` (feedback inmediato al tildar un
campo). El resto espera la respuesta.

### 5.4 Jobs asíncronos

Procesar un manual y exportar un juego son trabajos largos del backend. El patrón es el mismo:

1. `POST` devuelve `{ jobId, status: 'running', progress: 0 }`.
2. El hook hace polling de `GET /jobs/:jobId` cada 500 ms.
3. Al llegar a `status: 'done' | 'failed' | 'cancelled'` corta el polling e invalida la query
   del recurso.
4. `DELETE /jobs/:jobId` cancela.

El progreso mostrado en la UI es el `progress` real del job, nunca un timer del cliente.

---

## 6. Reglas de dominio en el cliente

`lib/domain/completeness.ts` es la fuente de verdad del cliente sobre completitud. El servidor
valida lo mismo; el cliente lo replica para dar feedback sin round-trip.

```ts
export function missingRequired(game: Game): string[]
export function computeGameStatus(game: Game): 'ready' | 'incomplete' | 'error'
```

`computeGameStatus` es un orden de prioridad fijo:

1. Si `game.errors.length > 0` → `error` (errores de formato del contrato ATTRACT).
2. Si `missingRequired(game).length > 0` → `incomplete`.
3. Si no → `ready`.

**Campos obligatorios** (y solo estos):

- Los 7 campos de identidad: título, año, desarrollador, editor, género, jugadores, formato.
- Imagen `caratula` (Carátula).
- Imagen `poster` (Póster).
- Texto `sinopsis` (Sinopsis).
- Color de acento (`accent !== 'empty'`).

Marquesina, logo, captura, video, reseña, trucos, manuales y revista son **opcionales**: su
ausencia nunca bloquea "Marcar como listo" ni la exportación.

---

## 7. Estados de campo

Cada campo de media/texto tiene un estado de tres valores que gobierna su etiqueta y sus
acciones:

| Estado | Etiqueta | Significado |
|---|---|---|
| `empty` | `○ VACÍO` | No hay contenido |
| `manual` | `● MANUAL` | Lo cargó el usuario |
| `suggested` | `◔ SUGERIDO` | Vino de una fuente externa |

Regla de reemplazo: si el usuario aplica una sugerencia sobre un campo en `manual`, hay que
pedir confirmación explícita ("Este campo fue cargado a mano. ¿Reemplazarlo?"). Sobre `empty` o
`suggested` se aplica directo.

En el panel de sugerencias, si el campo ya tiene contenido, la **primera** tarjeta candidata es
siempre "Tu archivo actual" — quedarse con lo que hay es la opción por defecto.

---

## 8. Manejo de errores

Tres clases de error, tratadas distinto en la UI:

1. **Error de formato del contrato** (`game.errors[]`) — bloquea el export. Se muestra en un
   recuadro negro con borde rojo en la ficha, nombrando campo y motivo.
2. **Falta un campo requerido** — no es un error, es incompletitud. Se muestra solo al intentar
   "Marcar como listo", listando qué falta.
3. **Falla de una fuente externa** (sugerencias, búsqueda IA de revistas) — es temporal y ajeno
   al juego. Ofrecer "Reintentar" como acción primaria, nunca dejar al usuario en un callejón.

Un vínculo de revista roto es **faltante, no error**: el juego sigue siendo válido y exportable.

---

## 9. Accesibilidad y teclado

- Todo control interactivo es un `<button>`, `<input>`, `<select>` o `<a>` real. Nada de `div`
  con `onClick` salvo filas de lista, que llevan `role="button"` y `tabIndex={0}`.
- Foco visible: outline punteado negro de 1px (coherente con DOS), nunca `outline: none`.
- Los modales atrapan el foco y cierran con `Esc`.
- Contraste mínimo AA: texto negro sobre gris `#C0C0C0` y sobre blanco; en los recuadros negros
  se usan los colores de terminal saturados (`#55FF55`, `#FFFF55`, `#FF5555`).

---

## 10. Rendimiento

- La lista de juegos pagina del lado del servidor (50 por página). No hay scroll infinito: hay
  paginación explícita, coherente con el look DOS.
- Las miniaturas de portada se sirven en un tamaño dedicado (`?thumb=80`) y llevan
  `loading="lazy"`.
- La ficha del juego carga un único `GET /games/:id` con todo embebido; no hace N requests por
  sección.
