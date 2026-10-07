# 018 · Guía completa: periféricos, pasos, reglas y modo

**Estado:** en curso (falta la prueba de extremo a extremo con ATTRACT)

## Qué hace

Completa el bloque `guia` de [`016`](../016-guia-en-export/spec.md) y [`017`](../017-objetivo-guia-ia/spec.md)
con lo que pide ATTRACT (`027-como-se-juega/pedido-coindoor.md`):

- **`perifericos`** — derivado de lo que ArcadeDB publica como control del juego
  (`dial`, `joystick`, `trackball`…), sin que nadie lo cargue.
- **`primerosPasos`** y **`reglasEsenciales`** — textos opcionales, una línea por ítem,
  que se escriben a mano o se sugieren con IA igual que el objetivo.
- **`multijugador.modo`** — `individual | cooperativo | versus`. Sale solo cuando es
  seguro (juegos por turnos o de un jugador); si no, se elige a mano o se sugiere.
- **`acciones`** — ya viaja desde `cabinet.button_list` (016). Si ArcadeDB no publica
  botones con acción para el juego, no hay `acciones`: no se inventan.

Fuera de alcance: fuentes por campo (ADR-0002), tecla de salida, botones físicos.

## Por qué

Hoy un juego como Arkanoid exporta solo `objetivo` y `jugadores`. El piloto de ATTRACT
mostró que asumir `modo` por género es justo el error que este campo existe para evitar.

## Criterios de aceptación

- [ ] `perifericos` sale de `cabinet.controls` con el vocabulario de ATTRACT
      (`joy`, `trackball`, `dial`, `paddle`, `lightgun`, `mouse`, `keyboard`); un control
      desconocido se omite. Arkanoid → `["dial"]`.
- [ ] `primerosPasos` y `reglasEsenciales` se editan en la ficha, se sugieren con IA y
      viajan como lista de textos; una sugerencia sin líneas útiles no genera candidato.
- [ ] `modo` es `individual` si ArcadeDB marca el juego por turnos (`alt`) o es de un
      jugador; en juegos simultáneos (`sim`) queda vacío hasta que se elija.
- [ ] `modo` solo admite los tres valores; la IA que responde otra cosa, o `DESCONOCIDO`,
      no genera candidato.
- [ ] Cada texto opcional viaja solo si se tilda en «qué incluir»; `acciones` y
      `perifericos` acompañan a la guía porque son datos, no texto.
- [ ] `revision` es `revisado` solo si todos los textos incluidos están en `manual`.
- [ ] Una ficha anterior, sin estos campos, se lee y exporta igual.
- [ ] La ficha muestra un **checklist de «Cómo se juega»** con cada elemento (objetivo,
      primeros pasos, reglas, jugadores, modo, periféricos, acciones) como listo o faltante,
      el motivo de lo que falta y qué se exige para exportar (el objetivo).
- [ ] **Un placeholder no puede llegar al paquete.** Un texto de la guía con una línea que
      empiece por «EJEMPLO:» (sin distinguir mayúsculas) cuenta como ausente: no se ofrece en
      «qué incluir», el export lo rechaza con el motivo y el bloque lo ignora.
- [ ] **Migración única (versión 2).** Los textos de la guía marcados a mano en una ficha
      anterior pasan a «sugerido, sin revisar»; la guía exportada baja de `revisado` a
      `borrador` hasta que una persona vuelva a guardarlos. Una ficha nueva nace en v2.
- [ ] **Objetivo con el nombre interno.** Si el objetivo contiene tal cual el romset, el id o la
      carpeta del juego (sin distinguir mayúsculas), no se exporta y la ficha lo explica. No
      aplica cuando ese nombre coincide con el título comercial (`xevious`).
- [ ] Cuando **Sugerir** no produce nada, el checklist dice «No se pudo generar» con el
      motivo (p. ej. «el modelo no conoce el juego»), y el modal lo muestra como «sin
      resultados» y no como «error de la fuente externa».
