# Problemas comunes

<!-- GUÍA: una entrada por síntoma real observado. Empieza por el mensaje de error
literal: es lo que el usuario va a buscar. -->

## `YouTube pidió verificación anti-bot. Probá más tarde o actualizá yt-dlp.`

**Causa.** Al pedir el video, YouTube respondió *"Sign in to confirm you're not a bot"*. Pasa
por la reputación de la IP —VPN, proxy, muchas descargas seguidas— o porque YouTube cambió
algo y la versión instalada de yt-dlp quedó vieja
([`ADR-0020`](../spec/decisions/0020-descarga-de-video-youtube.md)).

**Solución.** Actualizar yt-dlp y su componente de JavaScript, y reintentar sin VPN:

```bash
uv lock --upgrade-package yt-dlp --upgrade-package yt-dlp-ejs && uv sync
```

## `Falta ffmpeg en el equipo: instalalo para descargar video de YouTube.`

**Causa.** YouTube sirve el video y el audio por separado, y yt-dlp necesita ffmpeg para
unirlos en el `video.mp4`. `./dev.sh` avisa al arrancar si no lo encuentra.

**Solución.**

```bash
brew install ffmpeg        # macOS
sudo apt install ffmpeg    # WSL / Linux
ffmpeg -version
```

## `No supported JavaScript runtime could be found`

**Causa.** Aparece en el log del proceso cuando Deno no está instalado o no está en el `PATH`.
Hoy yt-dlp igual descarga, pero YouTube puede ocultar formatos —el job falla entonces con
`Este video no tiene versión H.264 de 720p o menos.`— y yt-dlp ya marca como deprecada la
extracción sin runtime. `./dev.sh` avisa al arrancar si no lo encuentra.

**Solución.**

```bash
brew install deno                                  # macOS
curl -fsSL https://deno.land/install.sh | sh       # WSL / Linux
deno --version
```
