# 011 · Video desde YouTube — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas;
marca `[x]` al completarlas._

## Implementación

- [x] Agregar `yt-dlp[default]` a `pyproject.toml` con override de mypy. Hecho cuando: `uv sync` instala `yt-dlp` y `yt-dlp-ejs`.
- [x] Implementar `backend/lib/youtube.py`. Hecho cuando: pasan los tests de URL, duración, errores y cancelación, sin red.
- [x] Implementar `mover_binario` en `backend/store/archivo.py`. Hecho cuando: el servicio lo usa y `tmp/` queda vacío.
- [x] Implementar `backend/services/youtube.py`. Depende de: las dos anteriores. Hecho cuando: el job deja `video.mp4` y el campo `suggested` con `originUrl`.
- [x] Cablear `POST /api/games/{id}/media/video/youtube`. Hecho cuando: responde `{jobId}`, 422 con URL inválida y 404 sin juego.
- [x] Agregar `startYoutubeDownload` y `cancelJob` en `frontend/src/lib/api/`.
- [x] Implementar `frontend/src/components/YoutubeDownload.tsx` y montarlo en el panel VIDEO. Hecho cuando: descarga, muestra progreso, cancela y refresca el reproductor.

## Tests

- [x] Caso feliz: una descarga simulada escribe `media/arcade/golden-axe/video.mp4` y la procedencia.
- [x] Caso límite: un video de 601 s o en vivo falla sin llegar a descargar.
- [x] Caso de fallo: el muro anti-bot y el formato inexistente llegan como mensajes legibles; nada queda en `media/` ni en `tmp/`.
- [x] Invariante: una URL que no es un video de YouTube nunca llega a yt-dlp (422 en el endpoint, error en la interfaz).
- [x] Interfaz: URL inválida sin llamar a la API; confirmación si el video es `manual`; el éxito actualiza el reproductor; el fallo muestra el mensaje.

## Cierre

- [x] Validar contra todos los criterios de aceptación de `spec.md`, con una descarga real. Hecho el 2026-09-11 sobre datos temporales, por la API y desde la ficha en el navegador: Golden Axe, 10,5 MB en 2,8 s, h264 960×720 yuv420p + aac, cancelación sin restos y reproductor actualizado sin recargar.
- [x] Lint y tipos limpios en lo tocado. Quedan problemas previos, ajenos a la feature y ya presentes en `HEAD`: `missing` y `summary` sin usar en `FichaJuego.tsx`, errores de mypy en `lib/providers/` y dos tests de frontend (`validation.test.ts` y la ficha de `read-pages.test.tsx`).
- [x] Actualizar `../../constitution/tech-stack.md` si cambió el stack,
      el modelo de datos o los límites duros.
- [x] Crear ADR en `../../decisions/` si alguna decisión tuvo alternativas
      descartadas o revirtió una previa.
- [x] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.
- [x] Actualizar `docs/`: `troubleshooting.md` con el muro anti-bot y el runtime de Deno. `api-reference.md` sigue siendo plantilla: el endpoint lo publica FastAPI en `/api/docs`.
