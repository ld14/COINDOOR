# Design system

> **Los tokens, la tipografía y los componentes están en
> [`docs/claude_diseño/design-system.md`](../../docs/claude_diseño/design-system.md)**, que es
> la fuente de consulta. Acá solo lo constitucional: lo que ninguna pantalla puede romper.

## La estética es una restricción, no una decoración

La interfaz imita un programa de DOS de principios de los 90 (Norton Commander, MS
Anti-Virus, QBasic). Eso fija bordes, colores y densidad, y descarta el vocabulario visual
moderno por completo.

## Prohibido

- `border-radius` distinto de 0 — única excepción, el spinner circular.
- Sombras difusas, degradados, `backdrop-filter`.
- Transiciones y animaciones — única excepción, el spinner.
- Tipografías proporcionales. Una sola familia monoespaciada en toda la app.
- Más de un color de marca: el cian `#00AAAA` es el único.
- Emojis decorativos. Los indicadores son ASCII o caracteres de caja
  (`● ◔ ○ ✓ ~ X [R] 📎`; el clip y `[R]` son las dos excepciones aceptadas).
- Librerías de componentes. Todo control se escribe a mano.

## Los dos bordes

Todo el vocabulario visual se construye con dos:

- **outset** — lo que sobresale: paneles, tarjetas, botones en reposo, filas de lista.
- **inset** — lo que está hundido: inputs, áreas de scroll, previews, barras de progreso.

Un botón presionado pasa a `inset`. No se mueve ni se oscurece.

## Dos capas de color semántico

Los mismos cuatro significados (ok / advertencia / error / info) tienen **dos juegos** y
nunca se mezclan:

| Sobre | Ok | Aviso | Error | Info |
|---|---|---|---|---|
| gris o blanco | `#006600` | `#8A6D00` | `#AA0000` | `#005555` |
| negro (terminal) | `#55FF55` | `#FFFF55` | `#FF5555` | `#00AAAA` |

`#55FF55` sobre blanco es ilegible. La capa la decide el fondo, no el significado.

## Los tres estados de campo, siempre visibles

| Estado | Etiqueta | Color |
|---|---|---|
| `manual` | `● MANUAL` | `#006600` |
| `suggested` | `◔ SUGERIDO` | `#005555` |
| `empty` | `○ VACÍO` | `#888888` |

Es la procedencia de [`ADR-0002`](../decisions/0002-procedencia-interna.md) hecha interfaz.
No es adorno: gobierna si reemplazar un campo pide confirmación.

## Los textos de la UI son literales

Los textos de `screens-spec.md` están escritos para explicar estados intermedios del
sistema —"Adjuntado, sin procesar todavía: estado intermedio, no es 'sin manual'"—.
Parafrasearlos pierde el punto y devuelve al usuario a la ambigüedad que el diseño resuelve.

## Referencia visual

[`docs/claude_diseño/COINDOOR.dc.html`](../../docs/claude_diseño/COINDOOR.dc.html) es el
prototipo funcional de una sola pieza. **Ante ambigüedad visual, gana el prototipo**; ante
ambigüedad de arquitectura, ganan los documentos.

Los deltas de [`frontend-architecture.md`](frontend-architecture.md) mandan sobre los dos:
son correcciones donde el contrato de ATTRACT no admite lo que el diseño propone.
