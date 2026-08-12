# COINDOOR — Design System (MS-DOS)

La interfaz imita un programa de DOS de principios de los 90 (Norton Commander, MS Anti-Virus,
QBasic). No es una decoración: define bordes, colores y densidad. Cualquier elemento con
`border-radius`, sombra suave, degradado o transición de color está fuera de estilo.

---

## 1. Paleta

```css
/* tokens.css */
:root {
  /* Superficies */
  --dos-desktop:      #0000AA;  /* Fondo azul del escritorio */
  --dos-panel:        #C0C0C0;  /* Gris de paneles y botones */
  --dos-panel-light:  #FFFFFF;  /* Interior de tarjetas y campos */
  --dos-titlebar:     #00007A;  /* Azul oscuro: barras de título y cabeceras de sección */
  --dos-accent:       #00AAAA;  /* Cian: barra superior, botones primarios, selección */
  --dos-terminal:     #000000;  /* Fondo de consola / previews */

  /* Texto */
  --dos-ink:          #000000;
  --dos-ink-soft:     #333333;
  --dos-ink-muted:    #555555;
  --dos-ink-invert:   #FFFFFF;

  /* Semántica (sobre gris/blanco) */
  --dos-ok:           #006600;
  --dos-warn:         #8A6D00;
  --dos-error:        #AA0000;
  --dos-info:         #005555;

  /* Semántica (sobre negro: colores de terminal) */
  --dos-ok-crt:       #55FF55;
  --dos-warn-crt:     #FFFF55;
  --dos-error-crt:    #FF5555;
  --dos-info-crt:     #00AAAA;

  /* Aviso */
  --dos-banner:       #FFFF55;

  /* Bordes 3D */
  --dos-edge-light:   #FFFFFF;
  --dos-edge-dark:    #808080;
}
```

**Regla de dos capas de color semántico.** Los mismos cuatro significados (ok / advertencia /
error / info) tienen dos juegos: los apagados van sobre gris o blanco; los saturados de
terminal solo sobre fondo negro. Nunca mezclar (`#55FF55` sobre blanco es ilegible).

---

## 2. Tipografía

Una sola familia monoespaciada en toda la aplicación:

```css
font-family: 'Consolas', 'Courier New', monospace;
```

Sin fuentes web. La escala es corta y las diferencias de tamaño son pequeñas — la jerarquía la
dan el peso, el color y las barras azules, no el tamaño.

| Uso | Tamaño | Peso |
|---|---|---|
| Título de pantalla (`h1`) | 17px | 700, color `--dos-titlebar` |
| Barra de título de ventana / modal | 13.5px | 700, blanco sobre `--dos-titlebar` |
| Cabecera de sección | 12.5px | 700, blanco sobre `--dos-titlebar` |
| Cuerpo | 13px | 400 |
| Etiqueta de campo | 12.5px | 700 |
| Texto auxiliar / ayuda | 12.5px | 400, color `--dos-ink-soft` |
| Meta / secundario | 11px–11.5px | 400, color `--dos-ink-muted` |
| Etiqueta de estado de campo | 10.5px | 400 |

Mínimo absoluto: 10.5px, y solo para las etiquetas `○ VACÍO`.

---

## 3. Bordes 3D

El vocabulario entero se construye con dos bordes:

```css
.outset { border: 2px outset var(--dos-panel); }  /* Elemento que sobresale: panel, botón, tarjeta */
.inset  { border: 2px inset  var(--dos-panel); }  /* Elemento hundido: input, área de scroll, preview */
```

- **outset**: paneles, tarjetas, botones en reposo, filas de lista.
- **inset**: inputs, selects, textareas, el contenedor scrolleable de contenido, las previews de
  media, las barras de progreso.
- Un botón presionado cambia a `border-style: inset` (no se mueve ni se oscurece).
- Divisores internos: `1px solid var(--dos-panel)` sobre blanco, o
  `1px solid #AAAAAA` entre filas de una lista.

Nunca `border-radius`. Nunca `box-shadow` difusa; si hace falta profundidad extra en un modal,
una sombra dura: `box-shadow: 4px 4px 0 rgba(0,0,0,0.4)`.

---

## 4. Botones

| Variante | Fondo | Texto | Uso |
|---|---|---|---|
| `primary` | `--dos-accent` | negro, 700, 13px, padding 6/14 | Acción principal de la pantalla |
| `primary-small` | `--dos-accent` | negro, 700, 12.5px, padding 5/10 | Acción principal dentro de una tarjeta |
| `ghost` | `--dos-panel` | negro, 12.5px, padding 6/14 | Acción secundaria |
| `ghost-small` | `--dos-panel` | negro, 11.5px, padding 4/8 | Acciones por campo (Cargar, Sugerir) |
| `danger-small` | `--dos-panel` | `--dos-error`, 11.5px, padding 4/8 | Borrar |

Todos: `border: 2px outset var(--dos-panel)`, `cursor: pointer`, sin transición.
Estado deshabilitado: texto `--dos-edge-dark` y `cursor: default`, sin cambio de borde.

---

## 5. Cabeceras de sección

Dentro de la ficha del juego, cada sección abre con una barra azul que ocupa el **100% del ancho
disponible de la columna de contenido**:

```css
.sectionHeader {
  background: var(--dos-titlebar);
  color: var(--dos-ink-invert);
  font-weight: 700;
  font-size: 12.5px;
  padding: 3px 8px;
  margin-bottom: 8px;
}
```

El panel blanco que sigue a la barra también ocupa el 100% del ancho. Ninguna sección lleva
`max-width` propio: el ancho lo fija la columna de la ficha (920px), no la sección.

---

## 6. Ventanas y modales

```
┌─────────────────────────────────────────┐  ← border: 2px outset #C0C0C0
│ Título de la ventana                  X │  ← barra #00007A, texto blanco 700 13.5px
├─────────────────────────────────────────┤
│  padding: 16px–18px                     │  ← fondo #C0C0C0
│  contenido                              │
│                                         │
│  [ Aceptar ]  [ Cancelar ]              │  ← primary + ghost, gap 8px
└─────────────────────────────────────────┘
```

Backdrop: `rgba(0,0,0,0.55)`. La X de la barra de título cierra. `Esc` también.
Anchos: 420px (formulario corto), 460–480px (lista), 620px (grilla de sugerencias).

---

## 7. Insignias de estado

**Estado del juego** — texto de terminal sobre negro:

```css
.statusBadge {
  background: #000000;
  padding: 3px 9px;
  font-size: 11.5px;
  font-weight: 700;
  white-space: nowrap;
}
```

| Estado | Texto | Color | Borde |
|---|---|---|---|
| ready | `LISTO` | `#55FF55` | `1px solid #006600` |
| incomplete | `INCOMPLETO` | `#FFFF55` | `1px solid #8A6D00` |
| error | `CON ERRORES` | `#FF5555` | `1px solid #AA0000` |

**Estado de campo** — texto suelto, sin caja, 10.5px:

| Estado | Texto | Color |
|---|---|---|
| manual | `● MANUAL` | `#006600` |
| suggested | `◔ SUGERIDO` | `#005555` |
| empty | `○ VACÍO` | `#888888` |

**Origen de la identidad** — sobre negro, 11px, padding 3/9:

| Origen | Texto | Color | Borde |
|---|---|---|---|
| catalog | `✓ CATÁLOGO` | `#55FF55` | `1px solid #006600` |
| manual | `~ DECLARADA A MANO` | `#00AAAA` | `1px solid #005555` |

---

## 8. Previews de media

Las previews son "pantallas": fondo negro, borde inset, texto verde de terminal.

```css
.preview {
  aspect-ratio: 1.3;
  background: #000000;
  border: 1px inset var(--dos-panel);
  display: flex; align-items: center; justify-content: center;
  text-align: center; padding: 8px;
  color: #55FF55; font-size: 10.5px;
}
```

Cuando el campo está vacío, el texto es `<etiqueta> · <ratio>` (ej: `carátula · 3:4`).
Cuando tiene contenido, se muestra la imagen real en `object-fit: contain` sobre el negro.

Las miniaturas de la lista de juegos son de 40×40px, fondo `--dos-panel`, borde
`1px solid #808080`; si no hay portada muestran las iniciales del título en 9px.

---

## 9. Barra de progreso

```css
.progressTrack { height: 14px; background: #000000; border: 2px inset var(--dos-panel); overflow: hidden; }
.progressFill  { height: 100%; background: var(--dos-accent); }
```

Sin transición en el ancho: el salto discreto es correcto para el estilo.

---

## 10. Densidad y espaciado

Escala en múltiplos de 2 desde 4px: `4 · 6 · 8 · 10 · 14 · 18 · 20`.

- Padding de panel: 14px (tarjetas), 18px (formularios en modal), 18px/22px (área de contenido).
- Gap entre tarjetas de una grilla: 12–14px.
- Gap entre filas de lista: 0 (las separa un borde de 1px).
- Gap entre secciones de la ficha: 20px.
- Gap entre botones de un grupo: 5–8px.

Siempre `display: flex` o `grid` con `gap`. Nunca márgenes por elemento para separar hermanos.

---

## 11. Fuera de estilo — no hacer

- `border-radius` en cualquier valor distinto de 0 (excepto el spinner circular).
- Sombras difusas, degradados, `backdrop-filter`.
- Transiciones y animaciones, salvo el spinner de carga.
- Emojis decorativos. Los indicadores son caracteres ASCII o de caja: `●  ◔  ○  ✓  ~  X  [R]  📎`
  (el clip del adjunto y `[R]` de revista son las dos únicas excepciones aceptadas).
- Tipografías proporcionales.
- Más de un color de acento: el cian `#00AAAA` es el único color de marca.
