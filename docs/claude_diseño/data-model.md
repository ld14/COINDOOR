# COINDOOR — Modelo de datos y reglas

Fuente de verdad de los tipos del cliente y de las reglas que gobiernan estados, completitud y
validación. El backend valida lo mismo; el cliente lo replica para dar feedback inmediato.

---

## 1. Tipos

```ts
// lib/domain/types.ts

export type FieldStatus = 'empty' | 'manual' | 'suggested';
export type GameStatus  = 'ready' | 'incomplete' | 'error';
export type IdentitySource = 'catalog' | 'manual';
export type MagazineLink = 'empty' | 'linked' | 'broken';
export type ManualStatus = 'unprocessed' | 'processing' | 'processed' | 'failed';
export type RomSource = 'upload' | 'path';

export interface System {
  id: string;
  name: string;          // Nombre visible: "Nintendo Entertainment System"
  shortName: string;     // Identificador corto: "nes"
  launchCmd: string;     // Comando del emulador; DEBE ser ruta absoluta
  valid: boolean;        // false si el comando no valida
  errorMsg?: string;
  gameCount: number;     // Lo calcula el servidor
}

export interface FormatError {
  field: string;         // Etiqueta visible: "Año"
  message: string;       // "Debe ser un número de 4 dígitos (contrato ATTRACT)."
}

export interface Identity {
  title: string;
  year: string;
  developer: string;
  publisher: string;
  genre: string;
  players: string;
  format: string;
}

export interface MediaField {
  status: FieldStatus;
  url?: string;          // Presente si status !== 'empty'
  source?: string;       // "IGDB", "MobyGames"… si status === 'suggested'
}

export interface TextField {
  status: FieldStatus;
  value: string;
  source?: string;
}

export interface GameManual {
  id: string;
  fileName: string;
  status: ManualStatus;
  pages: number;         // 0 hasta que status === 'processed'
  progress?: number;     // 0..100 mientras status === 'processing'
}

export interface Game {
  id: string;
  systemId: string;
  identity: Identity;
  identitySource: IdentitySource;
  romSource: RomSource;
  romRef: string;                        // Nombre de archivo o ruta absoluta
  errors: FormatError[];                 // Errores de formato del contrato ATTRACT
  images: Record<ImageKey, MediaField>;
  video: Record<VideoKey, MediaField>;
  texts: Record<TextKey, TextField>;
  accent: FieldStatus;                   // 'empty' | 'manual' | 'suggested'
  accentValue: string;                   // "#2F6FED"; "" si accent === 'empty'
  manuals: GameManual[];                 // Puede haber varios
  magazine: MagazineLink;
  magazineName: string;
  coverThumbUrl?: string;                // Miniatura de la portada para la lista
}
```

---

## 2. Definiciones de campos

```ts
// lib/domain/fieldDefs.ts

export type ImageKey = 'caratula' | 'marquesina' | 'poster' | 'logo' | 'captura';
export type VideoKey = 'video';
export type TextKey  = 'sinopsis' | 'resena' | 'trucos';

export const IMAGE_DEFS = [
  { key: 'caratula',   label: 'Carátula',            ratio: '3:4',  required: true  },
  { key: 'marquesina', label: 'Marquesina',          ratio: '4:1',  required: false },
  { key: 'poster',     label: 'Póster',              ratio: '2:3',  required: true  },
  { key: 'logo',       label: 'Logo',                ratio: '16:9', required: false },
  { key: 'captura',    label: 'Captura de pantalla', ratio: '16:9', required: false },
] as const;

export const VIDEO_DEFS = [
  { key: 'video', label: 'Video de gameplay', ratio: '16:9', required: false },
] as const;

export const TEXT_DEFS = [
  { key: 'sinopsis', label: 'Sinopsis', required: true  },
  { key: 'resena',   label: 'Reseña',   required: false },
  { key: 'trucos',   label: 'Trucos',   required: false },
] as const;

export const IDENTITY_FIELDS = [
  { key: 'title',     label: 'Título'        },
  { key: 'year',      label: 'Año'           },
  { key: 'developer', label: 'Desarrollador' },
  { key: 'publisher', label: 'Editor'        },
  { key: 'genre',     label: 'Género'        },
  { key: 'players',   label: 'Jugadores'     },
  { key: 'format',    label: 'Formato'       },
] as const;

export const ACCENT_PRESETS = ['#e0433a', '#ffb703', '#2f6fed', '#7c5cff', '#2dd4a7'];
```

---

## 3. Completitud

```ts
// lib/domain/completeness.ts

export function missingRequired(game: Game): string[] {
  const missing: string[] = [];

  for (const f of IDENTITY_FIELDS) {
    if (!game.identity[f.key]?.trim()) missing.push(`Identidad: ${f.label}`);
  }
  for (const d of IMAGE_DEFS) {
    if (d.required && game.images[d.key].status === 'empty') missing.push(d.label);
  }
  for (const d of VIDEO_DEFS) {
    if (d.required && game.video[d.key].status === 'empty') missing.push(d.label);
  }
  for (const d of TEXT_DEFS) {
    if (d.required && game.texts[d.key].status === 'empty') missing.push(d.label);
  }
  if (game.accent === 'empty') missing.push('Presentación: color de acento');

  return missing;
}

export function computeGameStatus(game: Game): GameStatus {
  if (game.errors.length > 0) return 'error';
  if (missingRequired(game).length > 0) return 'incomplete';
  return 'ready';
}
```

**Obligatorio (exactamente esto):** los 7 campos de identidad, Carátula, Póster, Sinopsis y el
color de acento.

**Opcional (nunca bloquea):** Marquesina, Logo, Captura, Video de gameplay, Reseña, Trucos,
manuales y revista vinculada.

El orden de prioridad importa: un juego con errores de formato es `error` aunque además le
falten campos. El recuadro de errores y el de faltantes pueden coexistir en la ficha.

---

## 4. Validación

```ts
// lib/domain/validation.ts
import { z } from 'zod';

/** El comando del emulador debe ser una ruta absoluta POSIX o Windows. */
export const absolutePath = z.string().refine(
  (v) => /^\//.test(v) || /^[A-Za-z]:\\/.test(v),
  'La ruta debe ser absoluta (ej: /opt/emulador/bin o C:\\Emuladores\\bin.exe). ' +
  'Si no, el juego no arranca en el gabinete sin avisar.'
);

export const hexColor = z.string().regex(
  /^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$/,
  'Formato inválido (ej: #2F6FED)'
);

export const yearField = z.string().regex(/^\d{4}$/, 'Debe ser un número de 4 dígitos (contrato ATTRACT).');

export const newSystemSchema = z.object({
  name: z.string().min(1, 'Requerido'),
  shortName: z.string().min(1, 'Requerido'),
  launchCmd: absolutePath,
});
```

El error del comando se muestra **al escribir** (campo tocado), no solo al enviar: es el punto
donde más se equivoca el flujo hoy y una ruta relativa falla en silencio en el gabinete.

---

## 5. Máquinas de estado

### 5.1 Campo de media/texto

```
empty ──[Cargar]──────────────► manual
empty ──[Sugerir → elegir]────► suggested
suggested ──[Cargar]──────────► manual
suggested ──[Sugerir → elegir]► suggested
manual ──[Sugerir → elegir]───► CONFIRMAR → suggested
manual ──[Borrar]─────────────► empty
suggested ──[Borrar]──────────► empty
```

La confirmación al reemplazar contenido `manual` es obligatoria. En los campos de texto, aplicar
una sugerencia rellena el `<textarea>` con el texto sugerido y deja el campo editable; en cuanto
el usuario lo modifica pasa a `manual`.

### 5.2 Manual (por cada archivo de la lista)

```
(no existe) ──[Adjuntar PDF]──► unprocessed
unprocessed ──[Procesar]──────► processing ──► processed
processing  ──[Cancelar]──────► unprocessed
processing  ──[falla]─────────► failed ──[Reintentar]──► processing
```

`unprocessed` es un estado real e intermedio: hay archivo pero no páginas. La UI nunca lo
presenta como "sin manual". Un juego puede tener N manuales y cada uno avanza por su cuenta.

### 5.3 Revista

```
empty ──[Buscar con IA]──► (búsqueda) ──[Descargar y guardar]──► linked
linked ──[Desvincular]───► empty
broken ──[Buscar otra]───► (búsqueda) ──► linked
```

`broken` significa que la revista referenciada ya no está en el repositorio. Es un **faltante,
no un error**: el juego sigue siendo válido y exportable.

### 5.4 Exportación (de a un juego)

```
idle ──[Exportar juego X]──► armando ──► verificando ──► done
```

`done` trae un veredicto de ATTRACT: `Verificado` o `Rechazado por ATTRACT` con el detalle del
motivo (ej: nombre de archivo con mayúscula inválida — el contrato es case-sensitive). Desde
`done` se vuelve a la lista.

Solo los juegos en estado `ready` son exportables. La exportación es **de a un juego por vez**
por el peso de los archivos.

---

## 6. API

Base: `/api`.

### Sistemas
```
GET    /systems                          → System[]
POST   /systems  { name, shortName, launchCmd }   → System   (422 si la ruta no es absoluta)
```

### Juegos
```
GET    /games?q=&systemId=&status=&page=&perPage=50
       → { items: GameSummary[], page, perPage, total }
GET    /games/:id                        → Game
POST   /games  { systemId, romSource, romRef, identity }  → Game
PATCH  /games/:id  { identity? , accent?, accentValue? }  → Game
POST   /games/:id/mark-ready             → Game   (409 con la lista de faltantes si no aplica)
```

`GameSummary` incluye `id, title, year, systemName, identitySource, status, coverThumbUrl`.

### Detección de identidad
```
POST   /roms/identify  { systemId, romSource, romRef }
       → { recognized: true,  identity: Identity }
       | { recognized: false }
```

### Campos
```
PUT    /games/:id/fields/:key   (multipart o { value })   → Game
DELETE /games/:id/fields/:key                             → Game
GET    /games/:id/suggestions/:key
       → { candidates: [{ id, name, source, previewUrl }] }   (200 con lista vacía = sin resultados)
POST   /games/:id/fields/:key/apply-suggestion  { candidateId }  → Game
```

### Presentación
```
POST   /games/:id/accent/detect     → { color: "#RRGGBB" }   (409 si no hay carátula cargada)
```

### Manuales
```
POST   /games/:id/manuals               (multipart, N archivos)  → GameManual[]
POST   /games/:id/manuals/:manualId/process   → { jobId }
DELETE /jobs/:jobId                            (cancelar)
GET    /jobs/:jobId                            → { status, progress }
DELETE /games/:id/manuals/:manualId
```

### Revistas
```
POST   /games/:id/magazines/search       → { jobId }
GET    /jobs/:jobId                      → { status, results: [{ id, name, issue, reason }] }
POST   /games/:id/magazines/:magazineId/download-and-link   → Game
DELETE /games/:id/magazine                                   → Game
```

### Exportación
```
POST   /export  { gameId }               → { runId }
GET    /export/:runId
       → { stage: 'armando' | 'verificando' | 'done',
           result?: { verdict: 'verified' | 'rejected', detail?: string } }
```

---

## 7. Datos de ejemplo (seed de desarrollo)

Cuatro sistemas, uno de ellos con el comando inválido a propósito:

| id | name | shortName | launchCmd | valid |
|---|---|---|---|---|
| arcade | Arcade / MAME | arcade | `/opt/mame/mame64 %rom%` | sí |
| nes | NES | nes | `/opt/emulators/nestopia/nestopia %rom%` | sí |
| genesis | Genesis / Mega Drive | genesis | `/opt/emulators/genesisplusgx/retroarch %rom%` | sí |
| snes | SNES | snes | `emulators/snes9x/snes9x %rom%` | **no** (relativa) |

Diez juegos que cubren los tres estados y todos los casos de borde:

| Juego | Sistema | Caso que ejercita |
|---|---|---|
| Sonic the Hedgehog | genesis | Completo, manual procesado, revista vinculada |
| Street Fighter II | arcade | Incompleto (falta póster) |
| Metal Slug | arcade | Ficha recién creada, todo vacío |
| Pac-Man | arcade | Completo; ATTRACT lo rechaza al exportar |
| Donkey Kong | arcade | Error de formato: año `197X` |
| Super Mario Bros. | nes | Manual adjuntado sin procesar |
| The Legend of Zelda | nes | Error de formato: formato `Cartucho JP` |
| Contra | nes | Vínculo de revista roto |
| Streets of Rage 2 | genesis | Completo, 10 páginas de manual |
| Super Metroid | snes | Incompleto en un sistema con cabecera inválida |
