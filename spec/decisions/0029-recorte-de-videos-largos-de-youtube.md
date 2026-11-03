---
id: 0029
title: Recortar a sus primeros 3 minutos los videos de YouTube de más de 10, en vez de rechazarlos
status: accepted
date: 2026-10-31
supersedes: null
superseded-by: null
tags: [backend, data]
---

# 0029 — Recortar los videos largos de YouTube a sus primeros 3 minutos

## Contexto

[`ADR-0020`](0020-descarga-de-video-youtube.md) rechaza los videos de más de 10 minutos y dice
"Sin recorte": el video entra entero al bundle. Para muchos juegos de MS-DOS lo único que hay en
YouTube es un *longplay* de media hora o más, y entonces hay que buscar otro video o cortarlo a
mano con otra herramienta.

El dueño del producto pidió el 2026-10-31 que esos videos, en vez de fallar, se recorten a sus
primeros 3 minutos. Ninguna otra entrada de video se toca.

Prueba real del mismo día con un *longplay* de 39 minutos: bajar solo el comienzo da 180,0 s en
H.264 + AAC y 19 MB, contra casi 200 MB del video entero, y se decodifica sin errores.

## Decisión

**Un video de YouTube de más de 600 s se guarda con sus primeros 180 s, sin bajar el resto.**
Este ADR cambia solo esa parte de ADR-0020; el resto sigue igual:

1. **Solo YouTube.** Un archivo subido a mano o el video de ArcadeDB no se recortan.
2. **De 600 s o menos, el video entra entero.** También uno de 8 minutos.
3. **El tramo es siempre el comienzo.** No hay elección del tramo.
4. **El tramo lo baja un `ffmpeg` propio,** con las URL que resolvió yt-dlp: copia los flujos,
   sin recodificar, con el mismo formato H.264 + AAC de ADR-0020. Da progreso real y se corta en
   cuanto se cancela.
5. **`RECORTE_S` y `MAX_DURACION_S` están en `lib/youtube.py`,** como los demás límites de la
   descarga.

## Alternativas consideradas

### A. `download_ranges` de yt-dlp

- A favor: una opción de yt-dlp, sin código propio de ffmpeg.
- En contra: **comprobado:** yt-dlp llama a ffmpeg sin avisar nada hasta el final. La barra queda
  en 0% durante los 2 minutos que tarda y cancelar demora esos mismos 2 minutos: parece colgado.
- **Descartada porque:** un job largo sin progreso ni cancelación rompe lo que ADR-0020 prometía.

### B. Bajar el video entero y recortarlo después

- A favor: pasa por el camino de siempre.
- En contra: un *longplay* de 3 horas es casi 1 GB para tirar casi todo, y `max_filesize` lo
  descartaría sin error.
- **Descartada porque:** el costo crece con lo que se descarta.

### C. Elegir el tramo o la duración

- A favor: los videos suelen abrir con una presentación, y el comienzo no siempre es lo mejor.
- En contra: agrega interfaz a un flujo que hoy es pegar un link.
- **Descartada porque:** el dueño del producto pidió los primeros 3 minutos. Se puede sumar con
  otro ADR.

## Consecuencias

**Positivas**

- Un *longplay* sirve como fuente de video con solo pegar el link.
- El bundle no crece con videos largos: el recorte ronda los 20 MB.

**Coste asumido**

- El video puede arrancar con una introducción o la voz del autor. El usuario lo ve en la ficha
  y puede cambiarlo.
- Un video de 9 minutos queda más largo que uno de una hora: es la regla pedida.
- La ficha no avisa que el video está recortado. La procedencia conserva la URL original.
- Hay un segundo camino de descarga, con su propio comando de ffmpeg, que depende de que las URL
  de yt-dlp se puedan leer directamente.

**Qué habría que revisar si esto se replantea**

- Si YouTube deja de servir URL que ffmpeg pueda leer, volver a la alternativa A y resolver el
  progreso de otra forma.

## Referencias

- Feature [011-video-youtube](../features/011-video-youtube/spec.md)
- [`ADR-0020`](0020-descarga-de-video-youtube.md) — la decisión que este ADR ajusta
