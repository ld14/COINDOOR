# 017 · Objetivo de la guía, sugerido por IA

**Estado:** en curso

## Qué hace

El juego gana un texto **Objetivo** («qué hay que lograr», 3-4 frases) que se carga igual
que la Sinopsis: se escribe a mano, o se pide **Sugerir** y la IA propone un candidato que
la persona aplica o descarta en el modal de siempre. Ese texto es el `objetivo` obligatorio
del bloque `guia` que exporta [`016`](../016-guia-en-export/spec.md).

Fuera de alcance: `primerosPasos`, `reglasEsenciales`, `multijugador.modo` y
`perifericos` (sin proceso de carga todavía), y cualquier fuente que no sea la IA.

## Por qué

Sin `objetivo`, ATTRACT rechaza la guía y 016 no exporta nada. El piloto de ATTRACT mostró
que un texto generado sin revisar llegó a inventar un botón y a describir otro juego; por
eso la IA **propone** y el candidato nunca se aplica solo (mismo modal, mismo `apply`).

## Criterios de aceptación

- [ ] La ficha muestra un campo «Objetivo» bajo Textos, con Guardar, Sugerir y Borrar.
- [ ] Sugerir devuelve candidatos solo de la IA (sin ArcadeDB), marcados como generados
      por IA; aplicar uno deja el campo en `suggested`, guardarlo a mano lo pasa a `manual`.
- [ ] El prompt prohíbe nombrar botones, teclas o controles; si el modelo no conoce el
      juego, responde `DESCONOCIDO` y no se ofrece candidato.
- [ ] Una respuesta vacía, `DESCONOCIDO` o de más de 600 caracteres no genera candidato.
- [ ] El campo es opcional: no cambia la completitud ni deja un juego en `incomplete`.
- [ ] En «qué incluir» del export aparece «Objetivo (Cómo se juega)»; sin ese texto, `guia`
      no viaja. `guia.revision` es `revisado` solo si el campo está en `manual`.
- [ ] Las fichas anteriores, sin `texts.objetivo`, se leen y se muestran sin error.
