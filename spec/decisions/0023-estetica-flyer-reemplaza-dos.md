---
id: 0023
title: La estética "Flyer 80s" reemplaza a la estética DOS
status: accepted
date: 2026-10-08
supersedes: null
superseded-by: null
tags: [frontend]
---

# 0023 — La estética "Flyer 80s" reemplaza a la estética DOS

## Contexto

`spec/constitution/design-system.md` fijaba la estética DOS como "una restricción, no una
decoración": `border-radius: 0`, una sola familia monoespaciada, un único color de marca
(cian), sin animaciones, bordes outset/inset y textos literales de `screens-spec.md`. No
hay un ADR detrás de esa regla: venía del paquete `docs/claude_diseño/`.

Al recorrer la app con las cinco pantallas funcionando se detectaron problemas que esa
estética provoca o agrava: todo en Consolas (legibilidad), el estado de cada campo difícil
de leer de un vistazo, la ficha de juego como una pared de campos sin jerarquía ni guía de
qué falta, un menú superior que no muestra contadores y un banner del contrato repetido en
todas las páginas. El paquete `docs/coindoor-rediseno/` (tema "Flyer 80s", con maquetas,
tokens y plan por fases) resuelve eso.

Aplicarlo choca con la constitución en tipografía, color, radios, bordes, animaciones y
vocabulario de estados. No se puede hacer con un ajuste: es un reemplazo.

## Decisión

**El rediseño Flyer es la cara definitiva de COINDOOR.** `design-system.md` de la
constitución se actualiza: la restricción pasa a ser el tema Flyer (tokens de
`docs/coindoor-rediseno/tokens/flyer-tokens.css`), y la estética DOS queda como historia.
Se mantiene todo lo que no era estético:

- Sin librerías de componentes: todo control sigue escribiéndose a mano en `components/dos/`.
- Los tres estados de campo siguen siendo `manual`, `suggested` y `empty`
  ([`ADR-0002`](0002-procedencia-interna.md)); cambia cómo se ven, no qué significan.
- Dos capas de color semántico, ahora sobre superficie clara e inversa.

También se asumen estos cambios de producto, que van en la misma feature
([`019`](../features/019-rediseno-flyer/spec.md)):

- El alta de un juego pasa de dos a cuatro pasos (Archivo → Sistema y tratamiento →
  Identidad → Abrir la ficha).
- `/exportar` sin id pasa de "Seleccioná un juego" a ser la cola de exportación.
- La ficha se guarda automáticamente; desaparecen los botones "Guardar X" por sección.
- Aceptar una sugerencia conserva su `source` (hoy el backend lo pierde al pasar a
  `manual`). La procedencia sigue siendo interna y no viaja al export (ADR-0002).

**Donde el paquete de rediseño y los deltas D1–D5 de
[`frontend-architecture.md`](../constitution/frontend-architecture.md) discrepan, mandan
los deltas**: el rediseño cambia cómo se ve un control, no el dato del contrato. En
concreto, las categorías de reseña van de 0 a 100 (D1), las revistas solo se vinculan y no
se exportan (D3) y el export conserva "Siempre incluido" bloqueado (D4).

## Alternativas consideradas

### Mantener la estética DOS y mejorar la usabilidad por dentro

- A favor: cero choque con la constitución; el aire retro es coherente con un gabinete.
- En contra: los problemas de legibilidad y jerarquía vienen de la tipografía única
  monoespaciada, de la ausencia de color de estado y de bordes que no distinguen
  jerarquías; no se resuelven sin tocar esas reglas.
- **Descartada porque:** lo que se pide corregir (leer el estado de un campo de un
  vistazo, distinguir lo obligatorio de lo sugerido, tipografía legible) está prohibido
  por la propia estética DOS.

### Adoptar una de las otras dos opciones de `tokens.json` (Refinado, Cabina)

- A favor: ya están tokenizadas.
- En contra: no tienen maquetas ni plan; el diseño validado es Flyer.
- **Descartada porque:** son opciones no elegidas del paquete; reabrirlas es otro ADR.

### Convivencia: tema DOS y tema Flyer conmutables

- A favor: reversible.
- En contra: dobla el costo de cada primitiva y de cada pantalla; el producto es de un
  solo usuario y no pide temas.
- **Descartada porque:** complejidad sin beneficio para un único usuario.

## Consecuencias

**Positivas**

- Estado de campo, pendientes y progreso legibles de un vistazo; guía de qué falta para
  exportar.
- Un solo sistema de tokens, con las fuentes empaquetadas localmente (offline).

**Coste asumido**

- Tres dependencias nuevas: `@fontsource/bungee`, `@fontsource/rubik`,
  `@fontsource/ibm-plex-mono`. Aprobadas el 2026-10-08.
- Se reescriben CSS modules y primitivas de `components/dos/`; hay un periodo con alias
  `--dos-*` hasta migrar todo.
- `docs/claude_diseño/design-system.md` y `screens-spec.md` quedan desactualizados en
  lo visual; no se editan (se consultan), y este ADR más `019` mandan.

**Qué habría que revisar si esto se replantea**

- Si el gabinete o ATTRACT empiezan a compartir identidad visual con COINDOOR.
- Si las fuentes empaquetadas pesan de más para la distribución.

## Referencias

- [`docs/coindoor-rediseno/`](../../docs/coindoor-rediseno/README.md)
- [`spec/features/019-rediseno-flyer/`](../features/019-rediseno-flyer/spec.md)
- [`spec/constitution/design-system.md`](../constitution/design-system.md)
