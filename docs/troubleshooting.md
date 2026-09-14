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
unirlos en el `video.mp4`. `./dev.sh` corre `scripts/install-deps.sh` al arrancar, que lo
instala solo si no lo encuentra (brew en macOS, apt en WSL/Linux, winget o choco en Windows
nativo con Git Bash).

**Solución.** Si el instalador no pudo (falta el gestor de paquetes, o falló la red),
instalalo a mano:

```bash
brew install ffmpeg                      # macOS
sudo apt install ffmpeg                  # WSL / Linux
winget install --id Gyan.FFmpeg -e       # Windows nativo (Git Bash / MSYS)
ffmpeg -version
```

## `Error: either unzip or 7z is required to install Deno`

**Causa.** El instalador de Deno necesita `unzip` o `7z` para descomprimir el ejecutable.
Si no encuentra ninguno, falla la instalación de Deno; `dev.sh` avisa y continúa con
el arranque. Los mensajes de npm `up to date` y `packages are looking for funding`
son informativos, no errores.

**Solución.** En Debian/Ubuntu (incluido WSL), ejecutá en la misma terminal donde
corrés `dev.sh`:

```bash
sudo apt-get update
sudo apt-get install unzip
./dev.sh
```

En otras distribuciones, instalá `unzip` o `7z` con su gestor de paquetes y volvé
a ejecutar `./dev.sh`.

## `No supported JavaScript runtime could be found`

**Causa.** Aparece en el log del proceso cuando Deno no está instalado o no está en el `PATH`.
Hoy yt-dlp igual descarga, pero YouTube puede ocultar formatos —el job falla entonces con
`Este video no tiene versión H.264 de 720p o menos.`— y yt-dlp ya marca como deprecada la
extracción sin runtime. `./dev.sh` corre `scripts/install-deps.sh` al arrancar, que lo instala
solo si no lo encuentra.

**Solución.** Si el instalador no pudo, instalalo a mano:

```bash
brew install deno                                  # macOS
curl -fsSL https://deno.land/install.sh | sh       # WSL / Linux
winget install --id DenoLand.Deno -e               # Windows nativo (Git Bash / MSYS)
deno --version
```
