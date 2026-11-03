# 025 · Launchbox reconoce los títulos largos — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Quitar el tope no alcanza: *Wing Commander* tiene tres tarjetas de 1990 y el año no las separa.
Tampoco hace falta inventar una heurística, porque la página de cada juego ya dice cómo se lo
conoce y si es un DLC. Lo que cambia es cuándo se abren las páginas: antes de elegir, y no
después de fallar, porque si no una tarjeta con año gana a la correcta que no lo trae.

## Implementación

1. `backend/lib/providers/launchbox/cliente.py`:
   - `LaunchboxFicha` suma `alternos` y `tipo`; `_parse_details` lee `Alternate Names`, que
     viene en una lista sin enlaces, y `Game Type`.
   - `LaunchboxSearchResult` suma `alternos`, y `_elegir` los compara como título exacto si
     el año de la tarjeta está a ±1 del buscado, o si no hay año buscado.
   - `_con_su_pagina`: si no hay tarjeta exacta, abre todas las que contienen las palabras,
     completa año y alternos y descarta las DLC.
2. `backend/lib/providers/coincidencia.py` — el nivel 2 no acepta una opción con un número de
   secuela entre las palabras que sobran.

## Decisiones

- **Sin tope de páginas** — el tope es lo que escondía la tarjeta correcta. Quedan en memoria y
  la latencia no es un problema de este producto; el cuidado con el sitio es una por vez, con
  pausa de 0,5 s, y parar en la primera falla.
- **El nombre alternativo pide el año** — un remake declara el nombre del original y, sin esa
  condición, una sola opción gana sin mirar el año.
- **Solo se descarta `DLC`** — es el único tipo visto que no es el juego. Otro valor no decide.
- **El filtro de secuelas va en la regla común** — sirve igual para MobyGames y solo puede
  dejar de elegir, que es el lado seguro.

## Riesgos

- **Búsquedas con muchas tarjetas** — "Ultima" abre 21 páginas, unos 15 s la primera vez.
- **Más casos sin elegir** — *Leisure Suit Larry* tiene tres tarjetas de 1987 y antes acertaba
  por ser la única con año en la lista; ahora queda sin elegir. Medido sobre 24 títulos: 17
  elegidos y 7 sin elegir. De los elegidos, solo *Elvira: The Fantasy Adventure* queda en duda:
  Launchbox tiene también *Elvira: Mistress of the Dark*, de 1989.
- **Un número que no es secuela** — "Fleet 2" o "Rambo III" buscados sin el número quedan sin
  elegir, y el dato sale de la fuente siguiente.
- **Launchbox cambia la página** — `alternos` y `tipo` quedan vacíos y se vuelve a la regla de
  título y año.
