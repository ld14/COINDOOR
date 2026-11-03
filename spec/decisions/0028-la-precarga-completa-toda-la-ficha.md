---
id: 0028
title: La precarga completa toda la ficha, en todos los sistemas, y juzga qué imagen va en cada casillero
status: accepted
date: 2026-10-31
supersedes: null
superseded-by: null
tags: [backend, proceso]
---

# 0028 — La precarga completa toda la ficha, en todos los sistemas

## Contexto

[`ADR-0015`](0015-precarga-con-red-al-alta.md) permitió salir a la red al dar de alta un juego
y [`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md) lo amplió a MS-DOS. Esa precarga deja
trabajo que el usuario hace campo por campo:

- En arcade y MS-DOS llena identidad, sinopsis y las imágenes que su fuente publica. Reseña,
  "Cómo se juega", trucos, color de acento y el resto de las imágenes quedan vacíos.
- En cualquier otro sistema no hace nada.

El dueño del producto pidió el 2026-10-31 que el sistema llene por defecto la mayoría de las
secciones posibles y que el usuario ajuste sobre eso, y que elija por su cuenta qué imagen va
como logo, marquesina, captura.

Elegir la imagen no se resuelve tomando el primer resultado. Prueba real con *Prince of
Persia* (2026-10-31): la búsqueda `arcade marquee` y la búsqueda `game logo` devuelven sobre
todo cajas, y `cover art` mezcla el manual y portadas de otros juegos de la saga. Con ese
criterio la ficha quedaría con una caja en la marquesina. Un primer filtro, solo por forma y
por contener el título, dejó pasar el logo de *Wing Commander Standoff*, un mod de fans.

## Decisión

**Un job nuevo completa la ficha: corre la precarga de la fuente del sistema, si tiene, y
después pasa por cada campo vacío con la misma cadena de "Sugerir", aplicando el mejor
candidato.** Sigue la misma excepción de `tech-stack.md` §Convenciones, no una nueva:

1. **Un endpoint con nombre propio,** `POST /api/games/{game_id}/completar`. Lo llaman el alta
   y un botón de la ficha.
2. **Un juego por vez, job cancelable, solo campos vacíos.** Los límites 1 a 5 de ADR-0015 no
   cambian. Una fuente caída deja ese campo vacío y el job sigue.
3. **El límite 6 de ADR-0015 se reemplaza:** el gate ya no es el sistema sino que el juego
   tenga título. El gate por sistema queda solo para elegir la precarga de la fuente.
4. **Lo que entra es sugerencia.** Mismo estado y misma procedencia que al elegir el candidato
   a mano en "Sugerir". Nada entra como `manual`.
5. **El orden de las cadenas es el criterio** para identidad y textos: el primer candidato
   aplicable. La IA de identidad sigue siendo el último recurso de
   [`ADR-0026`](0026-ia-ultimo-recurso-en-sugerir-identidad.md).
6. **Las imágenes se juzgan por fuente, forma y texto.** Lo que una fuente publica como tipo
   (ArcadeDB, Launchbox, MobyGames, las capturas de myabandonware) se toma en el orden de la
   cadena. Lo del buscador solo entra si sus proporciones encajan en el casillero, si su título
   nombra al juego y nada más que vocabulario genérico (ni una secuela, ni un mod, ni otra
   plataforma u otro año) y, para logo y póster, si dice serlo. **Si ninguna encaja, el
   casillero queda vacío:** mejor pedirle la imagen al usuario que dejar una incorrecta.
7. **El póster obligatorio toma la carátula** si no hay otro, como ya hace ArcadeDB con el
   `flyer`. El color de acento sale de la carátula, con ffmpeg.

**Queda fuera, a propósito:** el video (ADR-0020 dice "nada se descarga solo" y YouTube sigue
como referencia), los manuales, las revistas y la galería, que es un banco que elige el
usuario.

## Alternativas consideradas

### A. Mantener los botones "Sugerir" campo por campo

- A favor: no toca ninguna regla y cada dato pasa por una persona antes de entrar.
- En contra: son unas veinte aperturas de modal por juego para aceptar casi siempre el primero.
- **Descartada porque:** el dueño del producto pidió lo contrario. El control se conserva: todo
  entra como sugerencia y se revisa con "Revisar una por una".

### B. Que el frontend dispare una sugerencia por cada campo

- A favor: reutiliza los endpoints que ya existen.
- En contra: el trabajo depende de que la pestaña siga abierta, y son veinte jobs sin un
  progreso común ni un cancelar único.
- **Descartada porque:** ADR-0015 ya resolvió que esto es un solo job, con endpoint y progreso.

### C. Que un modelo con visión mire cada imagen

- A favor: es el juicio más cercano al de una persona; distingue una caja de una marquesina.
- En contra: cada imagen es una llamada de pago, con decenas de candidatas por juego, y el
  modelo configurado no tiene por qué soportar visión.
- **Descartada porque:** proporciones y título ya vienen gratis en cada resultado, y el error
  que queda es dejar un casillero vacío, que es el lado seguro.

### D. Descargar el video automáticamente con el primer resultado de YouTube

- A favor: es lo que más tiempo le sigue costando al usuario en muchas fichas.
- En contra: ADR-0020 lo prohíbe, cada video pesa decenas de MB, y el primer resultado de una
  búsqueda puede ser un *review* o un *longplay* de otra versión.
- **Descartada porque:** reabre una decisión aceptada, con su riesgo de ToS, sin que nada haya
  cambiado. Se puede replantear con otro ADR.

### E. Completar al abrir la ficha

- **Descartada por lo mismo que en ADR-0015:** una ficha se abre cien veces y §Convenciones
  prohíbe salir a la red al abrirla.

## Consecuencias

**Positivas**

- Dar de alta un juego deja la ficha casi armada, en cualquier sistema.
- Las fichas ya creadas se completan con el mismo botón.
- "Sugerir" sigue funcionando igual para elegir otra opción.

**Coste asumido**

- El alta gasta cuota de IA y de buscador sin que se apriete nada: hasta siete consultas de IA
  por juego, más la de trucos. Un solo usuario y un juego por vez lo vuelve aceptable; con
  carga masiva, prohibida por §Límites duros, no lo sería.
- Tarda minutos, no segundos. La ficha se puede editar mientras tanto, y un campo que el
  usuario llena durante el job no se pisa porque el vacío se comprueba justo antes de escribir.
- Una imagen elegida por el buscador puede ser de otra edición aunque pase el filtro. La
  interfaz ya muestra la imagen con su fuente; un casillero con imagen cuenta como aceptado,
  así que hay que mirarla antes de exportar.
- `mission.md` §"No decidimos nada automáticamente" se precisa: el sistema puede dejar el campo
  cargado como sugerencia, pero nada queda confirmado sin que lo vea una persona.

**Qué habría que revisar si esto se replantea**

- Si la cuota se vuelve un problema, ofrecer apagar la IA en el alta. Ya hay una casilla para
  no completar.
- Si ATTRACT empieza a medir las proporciones, los rangos de cada casillero tienen que salir de
  `fielddefs.json` en vez de quedar en el código.

## Referencias

- Feature [024-ficha-completa-al-cargar](../features/024-ficha-completa-al-cargar/spec.md)
- [`ADR-0015`](0015-precarga-con-red-al-alta.md) — la excepción que este ADR amplía
- [`ADR-0020`](0020-descarga-de-video-youtube.md) — por qué el video queda afuera
- [`ADR-0026`](0026-ia-ultimo-recurso-en-sugerir-identidad.md) y
  [`ADR-0027`](0027-myabandonware-primera-fuente-de-pc-dos.md) — el orden de las cadenas
