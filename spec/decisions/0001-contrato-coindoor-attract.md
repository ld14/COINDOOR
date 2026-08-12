---
id: 0001
title: Publicar el contrato de ATTRACT como dato versionado y validar dos veces
status: accepted
date: 2026-08-10
supersedes: null
superseded-by: null
tags: [data, proceso]
---

# 0001 — Publicar el contrato de ATTRACT como dato versionado y validar dos veces

## Contexto

COINDOOR prepara la metadata de juegos; ATTRACT ensambla y valida la librería que
Pegasus consume en el gabinete. Son dos aplicaciones separadas, con repositorios
separados, y COINDOOR tiene **almacenamiento propio**: los datos viven en su modelo
interno y recién al exportar viajan a la librería de ATTRACT. No comparten proceso ni
—necesariamente— máquina.

Eso obliga a decidir **quién sabe qué necesita ATTRACT y cómo**, porque el
conocimiento hace falta en dos momentos muy distintos:

1. **Mientras se carga**, campo por campo: el formulario tiene que decir "falta la
   marquesina" en el momento, sin red y sin librería materializada.
2. **Al exportar**: hay que verificar que lo producido es válido y completo de verdad.

ATTRACT resuelve **parcialmente** el segundo momento. `attract doctor` valida el eje
VÁLIDA leyendo el disco y ya cubre bastante (encoding, NFC, CRLF, nombres legales en
Windows, JSON bien formado, `assets.*` que resuelven, contrato de `magazine.json`).
El eje COMPLETA **no lo mide nada**: `attract carga` está especificado en
[`ATTRAC-015`](../../docs/attract/ATTRAC-015-carga-guiada/) pero **no existe** — los
comandos reales son `doctor`, `synopsis`, `ingest`, `rasterize`, `mags` y `mcp`.

Ninguno de los dos sirve para el primer momento: todos leen disco.

Restricciones heredadas de ATTRACT que acotan las opciones: el gabinete es **offline**,
ATTRACT es una CLI de **stdlib con cero dependencias nuevas** (dos excepciones acotadas:
ADR-0012 `mcp`, ADR-0022 `pymupdf`), y su contrato de datos vive en prosa
(`docs/CONVENCION.md`) más veinticinco ADRs.

## Decisión

**ATTRACT publica su contrato como un archivo de datos versionado**, generado desde
las mismas definiciones que usan `doctor` y `carga`. COINDOOR lo consume para validar
el formulario en vivo.

**La CLI de ATTRACT sigue siendo la autoridad final.** Tras el export, COINDOOR invoca
`attract doctor` sobre la librería materializada. Si contradice al formulario, **manda
la CLI** y es un bug del contrato publicado.

`doctor` cubre hoy solo el eje VÁLIDA. Mientras `attract carga` no exista, el eje
COMPLETA lo evalúa COINDOOR contra el contrato publicado, sin segunda opinión.

Cada export estampa la versión de contrato con la que se generó.

### Qué implica de cada lado

**ATTRACT debe:**
- Emitir el contrato como dato: por cada sistema, qué campos existen, cuáles son
  obligatorios para COMPLETO, los nombres exactos de asset con su capitalización, y
  las extensiones aceptadas.
- Derivarlo de la misma fuente que alimenta a `doctor` y `carga`. Un archivo escrito
  a mano en paralelo reintroduce justo la divergencia que este ADR evita.
- Versionar el contrato y no romperlo en silencio.
- Implementar `attract carga` ([`ATTRAC-015`](../../docs/attract/ATTRAC-015-carga-guiada/))
  o ceder el eje COMPLETA a COINDOOR de manera explícita. Hoy no lo mide nadie.

**COINDOOR debe:**
- Guardar el contrato con su versión y validar el formulario contra él, sin red.
- No hardcodear ninguna regla del contrato fuera de ese archivo.
- Avisar cuando su contrato guardado quedó viejo respecto del de ATTRACT.

> **La procedencia de cada campo no viaja.** `CONVENCION` §3.1 decide no distinguir
> origen y §3.3 que todo reproceso pisa. COINDOOR la guarda para su propio uso; el
> export no la incluye. Ver [`ADR-0002`](0002-procedencia-interna.md).

## Alternativas consideradas

### A. COINDOOR reimplementa el contrato en su propio código

- A favor: independencia total, cero coordinación entre repos, arranca más rápido.
- En contra: la regla queda escrita dos veces, en dos lenguajes de expresión distintos.
- **Descartada porque:** las dos definiciones de COMPLETO divergen en silencio y el
  síntoma aparece en el gabinete, que es el peor lugar para enterarse. Es el mismo
  riesgo que `ATTRAC-015 plan.md` §Riesgos ya identifica entre `doctor` y `carga`, y lo
  resuelve con la misma regla: ninguna regla se escribe dos veces.

### B. COINDOOR invoca la CLI para todo, incluida la validación en vivo

- A favor: una sola fuente de verdad, sin artefacto intermedio que mantener.
- En contra: exige materializar la librería en disco para responder "¿falta la
  marquesina?".
- **Descartada porque:** COINDOOR tiene almacenamiento propio y los datos recién viajan
  al exportar; no hay librería que mirar mientras se carga. Además ataría el formulario
  a que ATTRACT esté instalado y accesible en la misma máquina, que es justamente lo que
  el modelo de datos separado evita.

### C. COINDOOR habla con ATTRACT por MCP en vez de por CLI

- A favor: `attract mcp` ya existe y expone `doctor` y `synopsis` con salida
  estructurada — nada de parsear texto de terminal.
- En contra: el SDK `mcp` es dependencia opcional de ATTRACT (ADR-0012) y el servidor
  bloquea sirviendo por stdio; hay que gestionarle el ciclo de vida.
- **Descartada porque:** resuelve la invocación, no el problema de este ADR. El
  formulario necesita saber qué falta **antes** de que exista la librería en disco, y
  las tools de MCP también leen disco. Sigue en pie como forma de invocar `doctor` al
  exportar — es una decisión de implementación, no de contrato.

### D. ATTRACT expone un servicio HTTP que COINDOOR consulta

- A favor: contrato siempre fresco, sin versión que sincronizar.
- En contra: convierte una CLI en un servicio, con su ciclo de vida y su despliegue.
- **Descartada porque:** contradice el límite duro de cero dependencias nuevas de
  ATTRACT y el diseño offline del gabinete. Monta infraestructura permanente para
  entregar un archivo que cambia unas pocas veces por año.

### E. El contrato vive solo en `docs/CONVENCION.md` y alguien lo copia

- A favor: cero trabajo inmediato; el documento ya existe.
- En contra: la sincronización depende de que una persona se acuerde.
- **Descartada porque:** es el estado actual y ya falla — `ATTRAC-015 spec.md` §Por qué
  documenta tres reglas del contrato que hoy nadie valida (`collection:` ausente,
  `launch:` relativo, `x-formato` faltante), violables en silencio.

## Consecuencias

**Positivas**

- Una sola definición de COMPLETO, consumida de dos maneras.
- El formulario valida sin red y sin ATTRACT instalado.
- Un export viejo es detectable por su versión de contrato en vez de fallar raro.
- Agregar un campo a la librería es una entrada en el contrato, no un cambio de código
  en dos repos.

**Coste asumido**

- ATTRACT tiene que generar un artefacto que hoy no genera.
- COINDOOR puede quedar desactualizado entre versiones; se mitiga con el aviso, no se
  elimina.
- La doble validación puede contradecirse. Es deliberado: la contradicción es la señal
  de que el contrato publicado quedó mal, y es preferible detectarla al exportar que en
  el gabinete.

**Qué habría que revisar si esto se replantea**

- Si COINDOOR y ATTRACT terminan siempre en la misma máquina y el mismo proceso, la
  alternativa B se vuelve viable y este ADR sobra.
- Si el contrato cambia tan seguido que el aviso de versión molesta más de lo que
  ayuda, conviene revisar C.

## Referencias

- [`docs/attract/ATTRAC-015-carga-guiada/`](../../docs/attract/ATTRAC-015-carga-guiada/) — requisitos de carga escritos desde ATTRACT, **sin implementar**.
- [`docs/ux/requerimiento-funcional.md`](../../docs/ux/requerimiento-funcional.md) §3 (ejes VÁLIDO/COMPLETO), §5.8 (export).
- ATTRACT `docs/CONVENCION.md` — leído: §1 estructura, §2 campos y fallbacks, §3 procedencia, §4 validación.
- ATTRACT `src/attract/cli.py` — comandos reales: `doctor`, `synopsis`, `ingest`, `rasterize`, `mags`, `mcp`.
- ATTRACT ADR-0012 (`mcp` opcional), ADR-0015 (contrato `data.json`), ADR-0018 (`launch:` absoluto).
