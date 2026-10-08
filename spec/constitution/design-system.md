# Design system

> **Vigente: tema "Flyer 80s"** ([`ADR-0023`](../decisions/0023-estetica-flyer-reemplaza-dos.md)).
> Tokens, primitivas, estados de campo y pantallas están en
> [`docs/coindoor-rediseno/`](../../docs/coindoor-rediseno/README.md)
> (`DESIGN_SPEC.md`, `tokens/flyer-tokens.css`, `mockups/`). Acá solo lo constitucional: lo
> que ninguna pantalla puede romper.
>
> La estética DOS anterior (`border-radius: 0`, una sola familia monoespaciada, cian
> `#00AAAA`, sin animaciones, bordes outset/inset) quedó reemplazada. `docs/claude_diseño/`
> conserva su descripción, solo como historia.

## Qué es una restricción

- **Los tokens son la única fuente de color, tipografía, espaciado, radios y sombras.**
  Ningún componente escribe un color, un tamaño o una fuente a mano. Los alias `--dos-*`
  son transitorios y se borran al terminar la feature
  [`019`](../features/019-rediseno-flyer/spec.md).
- **Tres familias, cada una con su uso:** Bungee para títulos de página, de juego y de
  tarjeta; Rubik para todo lo que se lee y se carga; IBM Plex Mono para rutas, HEX,
  tamaños, romsets y atajos. Empaquetadas con `@fontsource`: **cero fuentes por red**.
- **Sin librerías de componentes.** Todo control se escribe a mano en `components/dos/`.
- **Un acento por significado**, nunca como único indicador: rojo = acción primaria y
  origen Manual; amarillo = sugerido o pendiente (solo relleno, nunca texto sobre claro);
  azul = origen externo y Exportado. El estado siempre lleva texto o ícono.
- **Contraste:** texto ≥ 4.5:1 y bordes de control ≥ 3:1.
- **Foco visible** (`--focus-ring`) en todo accionable, y todo accionable alcanzable con
  teclado.
- **Movimiento mínimo:** transiciones de hasta 150 ms y respetando
  `prefers-reduced-motion`.

## Los tres estados de campo, siempre visibles

| Dato | Chip |
|---|---|
| `empty` | `○ Vacío` (más `OBLIGATORIO` si bloquea la exportación) |
| `suggested` | `● Sugerido · sin revisar` |
| `manual` con fuente externa | `● <Fuente>` (ArcadeDB, MAME…) |
| `manual` sin fuente | `● Manual` |

Es la procedencia de [`ADR-0002`](../decisions/0002-procedencia-interna.md) hecha
interfaz. Gobierna si reemplazar un campo pide confirmación. Todo lo que propone el
sistema entra como `suggested`; nunca escribe un valor final directo.

## Los textos de la UI

En castellano rioplatense (voseo). Los textos que explican un estado intermedio del
sistema —"Adjuntado, sin procesar todavía: estado intermedio, no es 'sin manual'"— se
conservan literales: parafrasearlos devuelve la ambigüedad que resuelven. El resto
sigue el `DESIGN_SPEC.md`.

## Referencia visual

Las maquetas de [`docs/coindoor-rediseno/mockups/`](../../docs/coindoor-rediseno/mockups/)
son la guía visual; el comportamiento lo manda `DESIGN_SPEC.md`. **Ante ambigüedad visual,
gana la maqueta; ante ambigüedad de comportamiento, gana el spec.**

Los deltas D1–D5 de [`frontend-architecture.md`](frontend-architecture.md) mandan sobre el
rediseño cuando discrepan: cambian el dato, no el look.
