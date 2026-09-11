# COINDOOR — Brief técnico: incorporar descarga de video de YouTube

**Para:** Claude Code (sesión sobre el repo de COINDOOR)
**De:** Luis David Lopez
**Fecha:** 2026-09-10
**Estado:** evaluación de factibilidad — no hay decisión tomada

---

## 1. Qué te pido

Analizar la factibilidad de incorporar a COINDOOR la capacidad de **descargar video (o su audio) a partir de una URL de YouTube**, y devolver:

1. Un **ADR** (architecture decision record) con la opción recomendada y sus trade-offs.
2. Un **plan de implementación** por fases, con los archivos concretos del repo que se tocan.
3. Un **spike mínimo** funcionando (una ruta / comando / job que baje un video y lo deje donde corresponda), si la factibilidad da verde.

No implementes la solución completa antes de que revisemos el ADR.

---

## 2. Contexto que tenés que relevar vos

No asumas nada del proyecto: arrancá leyendo el repo y completá esta sección antes de opinar.

- Stack, runtime y versiones (`package.json`, `pyproject.toml`, `go.mod`, Dockerfile, etc.).
- Dónde corre: local, VPS, contenedores, serverless, PaaS. Esto **condiciona todo** (ver §4).
- Si ya existe alguna noción de trabajo asíncrono: cola, workers, cron, jobs.
- Cómo y dónde se persiste hoy cualquier archivo binario: disco local, volumen, S3/GCS/R2.
- Si hay autenticación de usuarios y quién podría disparar una descarga.
- Si ya hay algún consumo de contenido de YouTube (API de Data, embeds, transcripciones) para no duplicar.
- Límites operativos existentes: timeouts de request, tamaño máximo de payload, cuotas de storage, egress.

Dejá esa lectura documentada al principio del ADR: si algo no lo podés determinar, listalo como pregunta abierta en lugar de inventarlo.

---

## 3. La pieza técnica base

El estándar de facto es **yt-dlp** (https://github.com/yt-dlp/yt-dlp) — fork activo de youtube-dl, escrito en Python, licencia Unlicense (dominio público, sin fricción de licenciamiento). Es el motor sobre el que están construidas casi todas las alternativas (GUIs, servicios, servidores MCP).

Puntos duros a tener presentes:

- **ffmpeg es una dependencia real, no opcional.** YouTube sirve video y audio en streams separados para las calidades altas; sin ffmpeg quedás limitado a los formatos combinados de baja resolución, y no podés extraer audio ni remuxear.
- **yt-dlp se rompe seguido y se arregla seguido.** YouTube cambia sus mecanismos y yt-dlp publica correcciones con mucha frecuencia. Una versión pineada de hace tres meses puede fallar. Cualquier diseño tiene que contemplar cómo se actualiza esa dependencia sin redeploy completo, y qué pasa cuando falla.
- **Detección de bots.** Descargas desde IPs de datacenter (o sea: cualquier cloud) tienen bastante más probabilidad de recibir desafíos que requieren cookies o cliente alternativo que las hechas desde una IP residencial. Verificá el estado actual de esto — es el punto que más cambió en el último tiempo y el que más probablemente decida la viabilidad.

---

## 4. Opciones a evaluar

Evaluá al menos estas cuatro y descartá explícitamente las que no apliquen:

### A. Binario `yt-dlp` invocado como subproceso desde el backend
Lo más simple y lo más portable entre lenguajes. Requiere que el binario y ffmpeg estén en la imagen/host.
Riesgo principal: **inyección de comandos**. La URL viene del usuario. Nunca armar el comando con un shell string; usar la API de argumentos (`execFile`/`spawn` sin `shell:true`, `subprocess.run` con lista). Validar que la URL sea de un host permitido antes de pasarla.

### B. Librería nativa (solo si COINDOOR es Python)
`import yt_dlp` y usar `YoutubeDL` con `params`. Mejor control de errores y progreso, sin parsear stdout. Ata la versión de yt-dlp al ciclo de dependencias del proyecto — ver el punto de actualizaciones frecuentes.

### C. Worker / servicio separado con cola
Una descarga puede tardar minutos y consumir CPU (el remux con ffmpeg) y disco. Meterla en el ciclo request/response de una API web es un antipatrón: timeouts, workers HTTP bloqueados, imposibilidad de reintentar.
Si COINDOOR es una app web con usuarios, **esta es probablemente la respuesta correcta**: endpoint que encola → worker que baja → notificación / polling de estado → URL firmada al artefacto final.
Costo: sumás infraestructura (broker, worker, storage) que quizás hoy no exista.

### D. Servidor MCP (`@kevinwatt/yt-dlp-mcp` o similar)
**Probablemente no aplica.** Un MCP le da la capacidad a *un asistente* de bajar videos; no le da una feature a *tu producto*. Solo tiene sentido si el objetivo real es que vos, desde Claude, puedas traer material al proyecto durante el desarrollo — o si COINDOOR mismo es un host de agentes. Aclará en el ADR cuál de los dos casos es.

---

## 5. Riesgos y restricciones a documentar

**Legales / ToS.** La descarga de videos está en tensión con los Términos de Servicio de YouTube, y el análisis cambia mucho según el caso de uso (contenido propio, contenido con licencia, uso personal, redistribución) y la jurisdicción. No soy abogado y esto no es asesoramiento legal: el ADR tiene que marcarlo como riesgo abierto y escalarlo, no resolverlo. Si el caso de uso es contenido propio del titular o material con licencia explícita, decilo, porque cambia el panorama por completo. Si el producto va a redistribuir contenido de terceros, eso es un bloqueante de negocio antes que un problema técnico.

**Operativos.**
- Storage: un video de 1080p de 10 minutos ronda los cientos de MB. ¿Se guarda? ¿Cuánto tiempo? ¿Política de retención y limpieza?
- Egress y ancho de banda si después se sirve al usuario.
- Límite de tamaño y duración: definir un tope duro (`--max-filesize`, chequeo previo de duración) para no comerse el disco con un stream de 8 horas.
- Aislamiento: la descarga escribe archivos arbitrarios; correr en un directorio temporal dedicado, con nombres de archivo saneados (`--restrict-filenames` o plantilla propia por ID interno, nunca el título del video crudo).
- Concurrencia y rate limiting por usuario.
- Observabilidad: la tasa de fallos va a ser distinta de cero y va a variar en el tiempo. Métrica de éxito/fallo y alerta si cae.

**Seguridad.**
- Command injection (§4.A).
- SSRF: si aceptás cualquier URL, validá el dominio contra una allowlist antes de tocarla.
- Nunca ejecutar como root en el contenedor.

---

## 6. Alternativa a considerar antes de decidir

Si lo que COINDOOR necesita en realidad es el **contenido** del video (transcripción, metadata, thumbnail) y no el archivo, hay caminos mucho más baratos y sin la fricción legal ni operativa: la API oficial de YouTube Data para metadata, y la descarga de subtítulos/transcripciones (`--write-auto-subs --skip-download`), que es órdenes de magnitud más liviana. Preguntame cuál es el caso de uso real si el repo no lo deja claro — no lo asumas.

---

## 7. Entregable esperado

1. `docs/adr/XXXX-descarga-de-video-youtube.md` con: contexto relevado, opciones, decisión recomendada, consecuencias, riesgos abiertos.
2. Plan por fases con estimación gruesa y archivos afectados.
3. Lista explícita de preguntas abiertas que necesitan mi respuesta.
4. Recién después, y si lo apruebo: el spike.

**Criterio de éxito del análisis:** que yo pueda decidir con esto si esto entra al roadmap o no, sin tener que investigar nada más por mi cuenta.

---

## 8. Prompt sugerido para arrancar

> Leé este brief (`coindoor-yt-download-brief.md`) y después explorá el repo para completar la sección 2. No escribas código todavía. Devolveme primero el relevamiento del contexto y las preguntas abiertas que te queden, y esperá mi respuesta antes de redactar el ADR.
