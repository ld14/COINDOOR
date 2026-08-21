# Contrato del paquete COINDOOR → ATTRACT

Este documento es autocontenido: podés pegarlo entero en una sesión de
Claude Code dentro del repo COINDOOR sin necesitar acceso al repo ATTRACT.
Especifica el **único** entregable que COINDOOR necesita producir: un zip
que el comando `attract import <paquete.zip>` decodifica e instala.

Origen: ATTRACT es la fábrica de metadata de un frontend Pegasus de máquina
recreativa. Hoy un humano completa `metadata.pegasus.txt` y `data.json` a
mano; COINDOOR reemplaza esa edición manual con un formulario, y exporta
este zip como resultado. La decisión de arquitectura completa, con
alternativas descartadas, vive en `spec/decisions/0027-contrato-paquete-import-coindoor.md`
del repo ATTRACT — este documento es la versión "qué construir", sin la
narrativa de por qué.

## Regla de oro

**Un juego por zip.** Nada de lotes multi-juego, nada de revistas completas
adentro (ver más abajo). Cada exportación de COINDOOR es la ficha de un solo
juego.

## Estructura del zip

```
game.json
data.json
media/
  boxFront.png          ← opcional, cualquiera de estos, tantos como haya
  marquee.png
  poster.png
  video.mp4
  screenshot.png
  _manual/
    manual.pdf           ← opcional, uno o más, nombres ÚNICOS
    servicio.pdf
```

Todos los archivos son opcionales excepto `game.json` (con sus 4 campos
obligatorios, ver abajo). Un paquete mínimo válido es solo `game.json` con
`schema_version`/`system`/`set`/`title` — el resto se completa después o
nunca (ATTRACT trata "sin datos" como un estado válido, no un error).

## `game.json`

```json
{
  "schema_version": "1",
  "system": "arcade",
  "set": "sf2ce",
  "file": "sf2ce.zip",
  "title": "Street Fighter II: Champion Edition",
  "developer": "Capcom",
  "publisher": "Capcom",
  "genre": "Fighting",
  "players": 2,
  "release": "1992-04-10",
  "summary": "Ryu y Ken vuelven al torneo mundial...",
  "format": "PCB"
}
```

| Campo | Obligatorio | Tipo | Notas |
|---|---|---|---|
| `schema_version` | **Sí** | string | Hoy siempre `"1"`. |
| `system` | **Sí** | string | Nombre de la colección, minúsculas (`arcade`, `nes`, `pc`). |
| `set` | **Sí** | string | Identificador físico del juego — ver §Cómo elegir `set`. |
| `title` | **Sí** | string | Título tal como se muestra en pantalla. |
| `file` | No | string | Nombre del archivo de ROM (`sf2ce.zip`). Si se omite, ATTRACT usa `<set>.zip`. |
| `developer` | No | string | |
| `publisher` | No | string | |
| `genre` | No | string | |
| `players` | No | número entero | |
| `release` | No | string | Fecha o solo año. |
| `summary` | No | string | Texto libre, puede tener saltos de línea. |
| `format` | No | string | `PCB`, `GD-ROM`, `Cartucho`, etc — lo que corresponda al soporte físico real. |

### Cómo elegir `set`

`set` es el nombre de carpeta bajo el que va a vivir todo lo del juego
(`media/<set>/`). No es el título de presentación — es el identificador
físico:

- Si el juego es un solo archivo (ROM, disco, cassette): el nombre de
  archivo sin extensión. `tmnt.zip` → `set: "tmnt"`.
- Si es un romset de MAME (arcade): el nombre exacto del set tal como lo
  reconoce MAME (`sf2ce`, `mok`, `goldnaxe`) — abreviaturas históricas de
  hasta 8 caracteres, casi nunca el título completo.
- Si son varios archivos sueltos sin MAME de por medio (ej. un juego de
  MS-DOS con `.exe` + `.cfg` + assets propios): el nombre de la carpeta que
  los contiene.

Reglas de nombre válidas en Windows (ATTRACT las valida, mejor no generar un
paquete que ya vaya a fallar):
- Sin estos caracteres: `< > : " / \ | ? *`
- Sin nombres reservados: `CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`
- Sin terminar en espacio o punto
- Todo en NFC (forma de normalización Unicode estándar — evitar NFD, que es
  lo que producen algunas herramientas en macOS por defecto)

### Sobre la identidad sin verificar

ATTRACT normalmente verifica la identidad de un juego arcade contra
`mame -listxml` antes de crear su ficha. Un paquete COINDOOR **se acepta sin
esa verificación** — la identidad es la que declaró la persona que llenó el
formulario. ATTRACT lo marca internamente como `x-procedencia: declarada`.
Esto significa: **si `set`/`file` no corresponden a un romset real, el juego
no va a arrancar en el gabinete**, y nada en el import lo va a detectar de
antemano. Vale la pena que COINDOOR muestre esta advertencia en su propio
formulario cuando el sistema es arcade.

## `data.json`

Mismo contrato completo que usa la librería de ATTRACT — no es un formato
simplificado. Todos los campos son opcionales.

```json
{
  "accent": "#ff5a3c",
  "accent2": "#4d150b",

  "mags": [
    { "ref": "hobby-consolas-01" }
  ],

  "manual": [
    { "label": "Manual de uso", "file": "manual.pdf" },
    { "label": "Manual de servicio", "file": "servicio.pdf" }
  ],

  "cheats": {
    "combos": [
      { "name": "Hadouken", "input": "↓↘→ + P" }
    ],
    "secretos": {
      "label": "Secretos del juego",
      "items": [
        { "name": "Pelea contra M. Bison", "input": "Termina el juego sin continuar" }
      ]
    }
  },

  "review": {
    "score": 88,
    "verdict": "Un clásico que envejeció bien.",
    "cats": {
      "originalidad": 70,
      "graficos": 90,
      "adiccion": 95,
      "sonido": 85,
      "dificultad": 75,
      "animacion": 88
    }
  }
}
```

Notas por campo:

- **`accent`/`accent2`** — hex `#rrggbb`, exactamente 6 dígitos (no 3).
- **`mags`** — cada entrada necesita `ref` (el nombre de carpeta de una
  revista que **ya existe** en la librería de ATTRACT). COINDOOR no genera
  revistas ni sabe si el `ref` existe — eso lo valida ATTRACT del otro lado,
  y degrada sin romper si no existe. **No** incluyas `article`: ese campo lo
  escribe únicamente la herramienta interna de ATTRACT que linkea revistas
  con juegos.
- **`manual`** — lista de documentos, nunca un objeto suelto. Con un solo
  documento, `label` es opcional. Con **más de uno**, `label` es
  **obligatorio** en cada elemento y no puede repetirse. `file` es el nombre
  del PDF tal como va a estar en `media/_manual/` (ver más abajo) —
  **nunca** incluyas `pages`: eso lo genera ATTRACT a partir del PDF, con una
  herramienta aparte.
- **`cheats`** — el nombre de cada grupo (`combos`, `secretos`, o cualquier
  otro) es libre. Cada grupo es una lista directa de `{name, input}`, o un
  objeto `{label, items: [{name, input}]}` cuando el título del grupo no
  puede derivarse bien de la clave (ej. `secretos` → "SECRETOS" queda bien
  solo; `dos_jugadores` → "DOS JUGADORES" queda tosco, mejor con `label`
  explícito: `"Modo Cooperativo"`).
- **`review`** — `score` 0-100. `cats` es un objeto con exactamente estas
  seis claves, todas opcionales entre sí (una reseña puede tener solo
  algunas evaluadas): `originalidad`, `graficos`, `adiccion`, `sonido`,
  `dificultad`, `animacion`. Todas en minúsculas, sin tildes, valores 0-100.

## `media/`

Carpeta plana (sin subcarpetas por tipo, excepto `_manual/`). El **nombre de
archivo sin extensión** es la clave que Pegasus usa para mostrarlo:

| Archivo | Se muestra como |
|---|---|
| `boxFront.png` / `.jpg` | Carátula frontal |
| `boxBack.png` | Carátula trasera |
| `marquee.png` | Cartel luminoso del gabinete (arcade) |
| `poster.png` | Póster/promocional — fallback de carátula |
| `logo.png` | Logo del juego |
| `cartridge.png` | Imagen del cartucho/cinta/disco |
| `panel.png` | Panel de control (arcade) |
| `screenshot.png` | Captura de pantalla |
| `background.png` | Fondo |
| `video.mp4` | Video de demostración |

No es una lista cerrada — un nombre que Pegasus no reconozca simplemente no
se muestra en ningún lado, no rompe nada. Usa el nombre que corresponda al
contenido real; si dudás, usa `boxFront` para la imagen principal del juego.

### `media/_manual/`

Uno o más PDF, **nombres únicos** dentro de la carpeta (`manual.pdf`,
`servicio.pdf` — nunca dos archivos con el mismo nombre). Cada nombre acá
tiene que coincidir exactamente con el `file` que declaraste en
`data.json → manual[].file`.

**Nunca incluyas páginas rasterizadas (`p001.png`, etc.) — solo el PDF
original.** ATTRACT las genera con su propia herramienta cuando hace falta.

## Lo que COINDOOR NUNCA debe incluir en el paquete

- **Revistas completas** (`_magazines/`, `magazine.json`, páginas
  escaneadas) — son un subsistema aparte de ATTRACT. COINDOOR solo referencia
  una revista existente por `ref` en `data.json → mags[]`.
- **Páginas de manual ya rasterizadas** — solo el PDF crudo.
- **Más de un juego por zip.**
- **La ROM en sí** (`sf2ce.zip` con el contenido del juego) — ATTRACT no
  distribuye ROMs; el paquete es solo metadata y assets.

## Ejemplo de paquete mínimo válido

```
game.json    → {"schema_version":"1","system":"arcade","set":"mok","title":"The Maze of the Kings"}
data.json    → (ausente, o {})
media/       → (vacía)
```

Este paquete es válido: crea el juego "desnudo", sin datos enriquecidos.
ATTRACT trata eso como un estado normal (la mayoría de los juegos de una
colección real quedan así para siempre).

## Preguntas frecuentes al implementar el exportador

**¿Qué pasa si reexporto/reimporto el mismo juego?** Todo se pisa. La
versión más reciente del paquete gana siempre, sin excepción — no hay
merge campo por campo ni preservación de ediciones hechas del lado de
ATTRACT, con una sola excepción: si el paquete nuevo no trae `mags`, se
conserva lo que ya hubiera (para no borrar vínculos con revistas que
ATTRACT haya agregado después).

**¿Puedo mandar caracteres con tildes/eñes?** Sí, todo el contrato es
UTF-8. Asegurate de que tu generador de zip normalice a NFC (no NFD) — es
la forma de normalización Unicode que usa el resto del proyecto.

**¿Qué codificación de línea usar en los JSON?** No importa dentro del zip
(son archivos JSON, no `metadata.pegasus.txt`); ATTRACT los relee y
re-serializa.
