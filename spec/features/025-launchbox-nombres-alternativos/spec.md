# 025 · Launchbox reconoce los títulos largos

**Estado:** implementada

## Qué hace

Cuando la búsqueda de Launchbox no trae una tarjeta con el título exacto, el sistema abre las
páginas de las tarjetas que contienen todas las palabras y usa lo que ahí publica Launchbox: el
año, los nombres alternativos y el tipo de juego. Así "Wing Commander" encuentra *Wing
Commander: The 3-D Space Combat Simulator*, que declara ese nombre alternativo, y no se queda
con *The Secret Missions*, que Launchbox marca como DLC.

## Por qué

La regla de [022](../022-edicion-correcta-en-las-fuentes/spec.md) abría solo las tres primeras
tarjetas sin año y solo si no había elegido ninguna. Prueba real del 2026-10-31 con 24 títulos
de MS-DOS: *Wing Commander* no encuentra su juego, y es peor cuando elige, porque una tarjeta
con año gana a la correcta que no lo trae en la lista. "Space Quest" (1986) se queda con
*Space Quest II*, y "Commander Keen" (1990) con *Commander Keen 6*. Elegir otro juego
contamina la ficha con datos e imágenes ajenos.

## Criterios de aceptación

- [x] Dado un título sin tarjeta exacta, cuando una tarjeta lo declara como nombre alternativo,
      entonces esa tarjeta cuenta como título exacto, con o sin año buscado.
- [x] Dado un nombre alternativo de una tarjeta con otro año, cuando se busca con año, entonces
      no cuenta: "Space Quest" (1986) no elige el remake de 1991, que también se llama así.
- [x] Dado "Wing Commander" (1990) en MS-DOS, cuando se busca, entonces elige *Wing Commander:
      The 3-D Space Combat Simulator*.
- [x] Dada una tarjeta que Launchbox marca como DLC, cuando no hay título exacto, entonces no
      se elige.
- [x] Dada una tarjeta con año y otra sin año en la lista, cuando no hay título exacto, entonces
      las dos compiten con su año: "Space Quest" (1986) no elige *Space Quest II*.
- [x] Dado un título sin tarjeta exacta, cuando la única opción dentro del margen de años es una
      secuela numerada, entonces no elige ninguna: "Ultima" (1981) no elige *Ultima II*.
- [x] Dada una tarjeta con el título exacto, cuando se busca, entonces no se abre ninguna
      página de más.
- [x] Dado que una página falla, cuando se están abriendo las tarjetas, entonces se deja de
      pedir y se elige con lo que ya se sabe.
- [x] Dadas muchas tarjetas, cuando se abren, entonces se hace una por vez, con pausa, y la
      misma búsqueda repetida no vuelve a bajarlas.

## Fuera de alcance

- Cambiar los márgenes de años de la regla común: siguen ±1 y ±2.
- Usar nombres alternativos de MobyGames: ya los usa.
- Corregir las fichas ya guardadas: "Completar lo que falta" solo llena lo vacío.
