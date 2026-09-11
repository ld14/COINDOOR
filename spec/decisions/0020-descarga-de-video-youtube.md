---
id: 0020
title: Descargar video de YouTube a pedido con yt-dlp como librería, en vez de tratarlo solo como referencia
status: accepted
date: 2026-09-10
supersedes: null
superseded-by: null
tags: [backend, data]
---

# 0020 — Descargar video de YouTube a pedido con yt-dlp como librería

## Contexto

Desde [`ADR-0006`](0006-fuentes-externas-multiproveedor.md), YouTube es un candidato
`referencia`: el modal abre una búsqueda, el usuario consigue el archivo por fuera y lo sube
con `Cargar`. El motivo quedó escrito en su §Coste asumido: *"COINDOOR no baja el video ni lo
recorta […] Evita el problema de términos de uso y el del recorte de una sola vez, a cambio
de un paso manual"*. [`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md) y
[`ADR-0014`](0014-arcadedb-fuente-arcade.md) conservaron esa fila, y la feature
[002](../features/002-sugerencias-multiproveedor/spec.md) lo deja fuera de alcance.

**Qué cambió:** el paso manual se está cobrando, y el impedimento técnico se verificó resuelto.

- De los 13 juegos con video cargado al 2026-09-10, **8 se subieron a mano** (`status:
  manual`). Los otros 5 vienen de ArcadeDB, que solo cubre arcade. ATTRACT estima "conseguir
  el video" en 5–10 minutos por juego (`../attract/docs/baseline.md`).
- Spike del 2026-09-10 desde la máquina de desarrollo: yt-dlp 2026.08.19 usado como librería
  bajó el gameplay de Golden Axe (69 s) en **5,7 s**, sin cookies, como MP4 **H.264 960×720
  yuv420p + AAC** de 10,5 MB. `allowed_extractors=['youtube']` rechazó una URL de Vimeo sin
  salir a la red.

Restricciones que condicionan la decisión:

- **Un usuario, un proceso en `127.0.0.1`, sin Docker ni colas**
  ([`ADR-0009`](0009-proceso-local-en-loopback.md), [`ADR-0010`](0010-jobs-en-proceso.md)).
  La descarga sale desde una IP residencial, no desde un datacenter.
- **El gabinete es Windows, con Pegasus sobre Qt 5.15 QtMultimedia.** El único códec
  verificado reproduciendo ahí es H.264 (`../attract/docs/plataforma-pegasus.md`
  §QtMultimedia). El contrato acepta `.mp4` y `.webm`, pero no hay evidencia de VP9 ni AV1.
- **Los videos del gabinete son loops cortos:** los 13 actuales duran entre 15 y 135 s.
- **yt-dlp se rompe y se arregla seguido.** Hoy, para YouTube, necesita además `yt-dlp-ejs` y
  un runtime JavaScript externo; Deno es el default.
- **YouTube corta con "Sign in to confirm you're not a bot"** según la reputación de la IP:
  casi siempre desde datacenter, rara vez desde conexiones residenciales.
- **Términos de uso.** Descargar está en tensión con los ToS de YouTube. Este ADR no lo
  resuelve: lo registra como riesgo abierto.

## Decisión

**Pegar una URL de YouTube en la sección VIDEO de la ficha descarga ese video y lo escribe
como el campo `video` del juego.** Acotado así:

1. **A pedido y con endpoint propio:** `POST /api/games/{game_id}/media/video/youtube`. Nada
   se descarga solo. El modal Sugerir no cambia: ahí YouTube sigue siendo `referencia`.
2. **yt-dlp como paquete Python**, `yt-dlp[default]` (incluye `yt-dlp-ejs`), fijado en
   `uv.lock`. Se actualiza con `uv lock --upgrade-package yt-dlp --upgrade-package yt-dlp-ejs`.
3. **Deno como runtime JavaScript**, que es el default de yt-dlp: sin configuración, y el
   código que ejecuta corre sin acceso a disco ni red. Queda como requisito del host junto a
   ffmpeg, que ya se usaba sin estar documentado.
4. **Solo YouTube:** allowlist de hosts antes de encolar, y `allowed_extractors=['youtube']`
   dentro de yt-dlp.
5. **Video completo, hasta 10 min, sin transmisiones en vivo.** La duración se lee con
   `extract_info(download=False)` antes de bajar un byte.
6. **MP4 H.264 + AAC, hasta 720p, por remux sin re-encode.** Si el video no tiene esa
   variante, el job falla con un mensaje explícito.
7. **Job en proceso, con progreso y cancelación** (ADR-0010). Descarga en `tmp/`, se mueve de
   forma atómica a `media/` y queda con `source: YouTube` y la URL de origen en la
   procedencia, que no viaja al bundle ([`ADR-0002`](0002-procedencia-interna.md)).

## Alternativas consideradas

### A. Seguir con YouTube solo como referencia

- A favor: cero dependencias nuevas, y la aplicación no asume el riesgo de ToS. Es la
  decisión vigente.
- En contra: 8 de 13 videos exigieron una herramienta externa y una subida manual.
- **Descartada porque:** el dueño del producto pidió este flujo después de ver el
  relevamiento, el costo es medible, y el único impedimento técnico —obtener un MP4 que el
  gabinete reproduzca— quedó resuelto en el spike.

### B. Invocar el binario `yt-dlp` por subproceso

- A favor: se actualiza con `yt-dlp -U`, fuera del ciclo de dependencias. Cancelar es matar el
  proceso, incluso en medio del merge de ffmpeg.
- En contra: es otro binario del host que `uv sync` no instala. El progreso hay que parsearlo
  de stdout, los errores llegan como texto, y chequear la duración antes de bajar exige una
  segunda invocación.
- **Descartada porque:** la librería da progreso por `progress_hooks`, errores tipados
  (`DownloadError`, `DownloadCancelled`) y metadata antes de descargar, todo verificado en el
  spike, y la instala `uv sync`, que `dev.sh` ya corre. Con el binario habría que parsear la
  salida de otro programa, lo mismo que [`ADR-0012`](0012-verificacion-attract-por-subproceso.md)
  decidió no hacer con `attract doctor`.

### C. Worker o servicio separado con cola

- A favor: aísla CPU y disco de la API, y los reintentos sobreviven a un reinicio.
- En contra: suma broker, worker y un proceso más que supervisar.
- **Descartada porque:** ADR-0010 ya descartó Celery y RQ para esta aplicación y
  `tech-stack.md` §Límites duros lo prohíbe. El único problema real, no bloquear la
  petición, lo cubre el patrón de jobs en hilos, y la descarga medida tardó segundos.

### D. Servidor MCP (`@kevinwatt/yt-dlp-mcp` o similar)

- A favor: cero código en COINDOOR.
- En contra: le da la capacidad a un asistente, no al producto.
- **Descartada porque:** COINDOOR no aloja agentes, y `mission.md` exige que cargar un juego
  completo no obligue a abrir una terminal en ningún momento.

### E. YouTube Data API o descarga de subtítulos

- A favor: la API es oficial, y bajar subtítulos pesa órdenes de magnitud menos.
- En contra: entregan metadata y texto, no el video.
- **Descartada porque:** el campo `video` necesita un `.mp4` o `.webm` (`contract.json`), y
  ninguna de las dos lo provee. La Data API además pide API key y tiene cuota, los mismos
  motivos por los que ADR-0013 sacó otras fuentes.

### F. La mejor calidad disponible (VP9 o AV1 en WebM, 1080p o más)

- A favor: mejor imagen, y el contrato acepta `.webm`.
- En contra: el doble o más de peso por minuto.
- **Descartada porque:** el único códec verificado en el Pegasus del gabinete es H.264, y los
  juegos tienen resolución nativa de 224 a 480 líneas: 1080p no agrega detalle visible.

### G. Node como runtime JavaScript

- A favor: ya está instalado (v26; yt-dlp pide ≥22), así que no hay nada que instalar.
- En contra: requiere configurarlo explícitamente con `js_runtimes`.
- **Descartada porque:** según la wiki EJS de yt-dlp, con Deno el código corre sin acceso a
  disco ni red, mientras que Node solo restringe *algunos* permisos. Y el código que se
  ejecuta viene de YouTube.

## Consecuencias

**Positivas**

- Cargar el video de un juego de cualquier sistema, no solo arcade, pasa a ser pegar un link.
- Sin infraestructura nueva: el mismo patrón de job, el mismo store y los mismos nombres de
  archivo del contrato.
- La URL de origen queda en la procedencia: se puede auditar o volver a bajar.

**Coste asumido**

- **Riesgo legal abierto, no resuelto.** Descargar contradice los ToS de YouTube, y el
  análisis depende del contenido y de la jurisdicción; esto no es asesoramiento legal. El uso
  previsto es personal, con bundles solo hacia máquinas propias, el mismo criterio que
  [`ADR-0003`](0003-bundle-por-juego.md) aplica a los archivos del juego. Compartir bundles
  con video de terceros exige revisarlo antes, no después.
- **Tres dependencias nuevas o formalizadas:** `yt-dlp[default]` en Python, y Deno y ffmpeg en
  el host.
- **Se va a romper.** Cuando YouTube cambie algo, la descarga falla hasta que se actualice
  yt-dlp. El job lo informa; no hay fallback automático.
- **yt-dlp reintenta por su cuenta.** Es una excepción consciente a *"ningún proveedor
  implementa su propio reintento"*: yt-dlp no es un proveedor de `lib/providers/`, y
  reimplementar su política no aporta nada.
- **Cambia la letra de §Límites duros.** *"Solo las sugerencias salen a la red"* tiene que
  nombrar también esta descarga. Cargar, editar y exportar siguen funcionando sin internet.
- **Sin recorte.** El video entra entero al bundle: a razón de ~9 MB por minuto (lo medido en
  el spike), el tope de 10 min ronda los 90 MB.
- **Cancelar durante el merge no es inmediato:** corta recién cuando termina el post-proceso
  de ffmpeg.
- Mientras dura, una descarga ocupa uno de los cuatro hilos del pool de jobs.

**Qué habría que revisar si esto se replantea**

- Si el muro anti-bot aparece en descargas consecutivas desde la IP de la casa, el camino sin
  cookies dejó de servir: decidir entre `cookiesfrombrowser` o volver a la alternativa A.
- Si yt-dlp empieza a exigir componentes remotos (`remote_components`) o credenciales para
  YouTube, la dependencia cambió de naturaleza.
- Si aparece la intención de compartir bundles con terceros, la cuestión legal bloquea antes
  que cualquier tema técnico.
- Si varios videos pedidos no tienen variante H.264 de 720p o menos, conviene agregar
  re-encode: `_transcode_yuv420p` ya existe en `backend/services/arcadedb.py`.
- Si una fuente con loops listos cubre los sistemas que no son arcade, esta descarga pierde
  su motivo.

## Referencias

- Brief: `docs/coindoor-yt-download-brief.md`
- Feature [011-video-youtube](../features/011-video-youtube/spec.md)
- Spike del 2026-09-10, fuera del repo: `youtu.be/earaCnLVL98` (Golden Axe, id tomado de
  ArcadeDB) — 69 s de video, 5,7 s de descarga, 10,5 MB, h264 960×720 yuv420p + aac
- yt-dlp 2026.08.19: https://github.com/yt-dlp/yt-dlp · https://github.com/yt-dlp/yt-dlp/wiki/EJS
- `../attract/docs/plataforma-pegasus.md` §QtMultimedia — H.264 verificado en el gabinete
- `../attract/docs/baseline.md` — el costo manual de conseguir el video
- [`ADR-0006`](0006-fuentes-externas-multiproveedor.md) §Coste asumido — la postura que este
  ADR revisa
