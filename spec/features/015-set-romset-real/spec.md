# 015 · `set` con el romset real

**Estado:** en curso

## Qué hace

El campo `set` de `game.json` —el que ATTRACT usa para nombrar el juego en su librería y
para correr `-listxml`— lleva el **romset real de MAME** cuando COINDOOR ya lo conoce, no el
slug del título. El `id` interno y los nombres de carpeta siguen siendo el slug.

Fuera de alcance: cambiar el `id`, renombrar carpetas o reabrir
[`ADR-0026` de ATTRACT](../../../../attract/spec/decisions/0026-identidad-declarada-sin-mame.md)
(declarar un `set` a mano sigue siendo un riesgo aceptado allá).

## Por qué

Hoy `set = safe_id(title)`. En el piloto de ATTRACT, 3 de 5 arcades quedaron con `set`
equivocado (`street-fighter-alpha-2` en vez de `sfa2`, `mortal-kombat-2` en vez de `mk2`,
`the-simpsons` en vez de `simpsons`) y `attract controles` no pudo consultar `-listxml`.
Origen: pedido de ATTRACT (`docs/pedido-coindoor.md`).

**Corrección al pedido:** `manifest["set"]` no viaja al zip (`bundle.json` se excluye en
`bundle/pack.py`). El valor que ATTRACT lee es `game.json["set"]`, escrito en
`bundle/gamejson.py`. Se corrigen los dos por coherencia.

## Criterios de aceptación

- [ ] Dado un arcade con `identitySource == "mame"` y `romRef` = `.../sfa2.zip`, cuando se
      exporta, entonces `game.json["set"] == "sfa2"` (igual para `mk2`, `simpsons`).
- [ ] Un juego cuyo slug ya coincide con su romset (`pacman`, `shufshot`) exporta igual que hoy.
- [ ] Sin `romRef`, o con `identitySource != "mame"`, `set` cae al slug actual.
- [ ] `romRef` que es una carpeta cuyo nombre no es un romset (p. ej. con puntos) no
      produce un `set` inválido: cae al slug.
- [ ] `game.json["set"]` y `manifest["set"]` coinciden siempre.
- [ ] El `id`, la carpeta y las URLs del juego no cambian.

## Fuera de alcance

- Persistir el romset como campo nuevo de `game.json` — se deriva de `romRef`, ver plan.
- Verificar contra MAME que el `set` exista — es de ATTRACT (`doctor`).
