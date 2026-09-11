# 010 · Video desde YouTube — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Un endpoint valida la URL y el juego, y encola un job con el patrón de `lib/jobs/`
([`ADR-0010`](../../decisions/0010-jobs-en-proceso.md)). El job usa yt-dlp como librería
para leer la duración, bajar la variante H.264 + AAC ≤720p a `tmp/` y moverla a `media/`
como `video.mp4`; recién entonces escribe el campo con `apply_media_suggestion`.
`lib/youtube.py` no conoce HTTP ni el store; `services/youtube.py` no conoce los detalles de
yt-dlp. El modal Sugerir no se toca.

## Implementación

1. `pyproject.toml` — `yt-dlp[default]>=2026.8.19` y override de mypy: yt-dlp no trae `py.typed`.
2. `backend/lib/youtube.py` — `validar_url` (URL canónica `watch?v=<id>` o `ValueError`),
   `descargar` (duración, formato, progreso, cancelación) y `YoutubeError`, con mensajes
   escritos para el usuario.
3. `backend/store/archivo.py` — `mover_binario`: fsync y `os.replace`, sin cargar el video
   en memoria.
4. `backend/services/youtube.py` — `YoutubeVideoService.run`: valida antes de encolar y
   devuelve la función del job.
5. `backend/api/schemas.py` y `backend/api/media.py` — `YoutubeDownload` y
   `POST /api/games/{id}/media/video/youtube` → `{jobId}`.
6. `frontend/src/lib/api/media.ts` y `jobs.ts` — `startYoutubeDownload` y `cancelJob`.
7. `frontend/src/components/YoutubeDownload.tsx` — campo, botón, progreso por polling dentro
   de un `useMutation` (como `useSuggestionsJob`), cancelar y confirmación si el video es
   `manual`. Se monta en el panel VIDEO de `FichaJuego.tsx`, que agrega `?v=` al `src` del
   reproductor: un reemplazo escribe el mismo `video.mp4` y el navegador mostraría el viejo.

## Decisiones

- **yt-dlp como librería, Deno, H.264 ≤720p, tope de 10 min** — ver
  [`ADR-0017`](../../decisions/0017-descarga-de-video-youtube.md).
- **URL canónica en vez de la que pega el usuario** — reconstruir `watch?v=<id>` deja afuera
  listas, canales y parámetros de seguimiento: yt-dlp nunca recibe otra cosa.
- **Descarga en `tmp/<job>` y `os.replace` a `media/`** — un fallo o una cancelación nunca
  dejan un archivo parcial donde el export lo levantaría.
- **Store nuevo al escribir** — la descarga dura minutos, y el índice del store creado en el
  request pisaría lo que el usuario editó mientras tanto.
- **Sin transcode** — sin variante H.264 ≤720p el job falla explícito;
  `_transcode_yuv420p` (`services/arcadedb.py`) queda para cuando pase seguido.

## Riesgos

- **Muro anti-bot o cambio de YouTube** — el job falla con mensaje; se arregla con
  `uv lock --upgrade-package yt-dlp --upgrade-package yt-dlp-ejs && uv sync`. Si persiste
  desde la IP de la casa, ver ADR-0017 §Qué habría que revisar.
- **Deno ausente** — yt-dlp no resuelve los desafíos de YouTube y el job falla; el requisito
  queda en `README.md` y `docs/troubleshooting.md`.
- **Cancelar durante el merge** — corta al terminar ffmpeg (segundos); el campo no cambia
  porque la escritura ocurre después.
