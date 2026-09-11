# 010 · Video desde YouTube

**Estado:** implementada   <!-- borrador | aprobada | en curso | implementada -->

Decisión en [`ADR-0017`](../../decisions/0017-descarga-de-video-youtube.md).

## Qué hace

**Recibe** una URL de YouTube que el usuario pega en la sección VIDEO de la ficha.
**Descarga** ese video como MP4 H.264 + AAC de hasta 720p y **lo escribe** como el campo
`video` del juego, con `source: YouTube` y la URL en la procedencia. Corre como job, con
progreso y cancelación.

**No cubre** encontrar el video: el modal Sugerir sigue ofreciendo YouTube como `referencia`
([002](../002-sugerencias-multiproveedor/spec.md)). Tampoco recorta: el video entra entero.

## Por qué

8 de los 13 videos cargados hoy se subieron a mano: buscar en YouTube, bajarlo con otra
herramienta y subirlo con `Cargar`. ArcadeDB solo resuelve arcade
([008](../008-arcadedb/spec.md)). Esto reduce ese recorrido a pegar un link.

## Criterios de aceptación

- [x] Dado un juego sin video y `https://youtu.be/<id>` de 10 min o menos, cuando termina el job, entonces existe `media/<sistema>/<juego>/video.mp4` con H.264 + AAC y alto ≤720, y `video.video` es `{status: suggested, source: YouTube}` con `provenance.video.originUrl` igual a `https://www.youtube.com/watch?v=<id>`.
- [x] Dada una URL que no es de un video de YouTube —otro host, una lista, un canal, `file://`, `ytsearch:`—, el endpoint responde 422 sin crear job ni salir a la red; dado un `game_id` inexistente, responde 404.
- [x] Dado un video de más de 600 s o en vivo, el job termina `failed` con el mensaje correspondiente, sin descargar y sin tocar `game.json`.
- [x] Dado un video sin variante H.264 de 720p o menos, el job termina `failed` con su mensaje.
- [x] Dado que YouTube responde con el muro anti-bot, el job termina `failed` con el mensaje que lo nombra.
- [x] Dado un job en curso, cuando se cancela, termina `cancelled` y el campo `video` no cambia.
- [x] Dado cualquier fallo o cancelación, no queda archivo parcial ni en `media/` ni en `tmp/`.
- [x] Dado un video actual `manual`, cuando se pide descargar, la interfaz pide confirmación antes de reemplazarlo.
- [x] Dada una URL que no es de YouTube, la interfaz muestra el error sin llamar a la API.
- [x] Dada una descarga exitosa, el reproductor de la sección muestra el video nuevo sin recargar la página.

## Textos de la interfaz

No están en `docs/claude_diseño/`. Estos son los literales:

- Campo `URL de YouTube` · botones `Descargar` y `Cancelar` · en curso `Descargando de YouTube… {n}%`
- URL inválida: `La URL tiene que ser de un video de youtube.com o youtu.be.`
- Reemplazo: `El video actual fue cargado a mano. ¿Reemplazarlo con el de YouTube?`
- Job fallido: `El video dura más de 10 minutos.` · `No se pueden descargar transmisiones en vivo.` · `Este video no tiene versión H.264 de 720p o menos.` · `YouTube pidió verificación anti-bot. Probá más tarde o actualizá yt-dlp.` · `La descarga terminó sin archivo.`

## Fuera de alcance

- **Buscar el video** o volver aplicable el candidato de YouTube del modal Sugerir: sigue siendo [002](../002-sugerencias-multiproveedor/spec.md), y buscar dentro de YouTube roza el "sin scraping" de ADR-0013.
- **Recortar un tramo.** El video entra entero, hasta 10 min.
- **Cookies del navegador** para sortear el muro anti-bot.
- **Otros sitios de video**, como archive.org o Vimeo.
- **Videos en la galería:** eso es [009](../009-galeria/spec.md).
- **Re-encodear** videos sin variante H.264: fallan de forma explícita.
- **Verificar la licencia del contenido:** es un riesgo abierto en ADR-0017.
