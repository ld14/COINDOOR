---
id: 0010
title: Ejecutar los trabajos largos en hilos del propio proceso, sin cola ni worker
status: accepted
date: 2026-08-11
supersedes: null
superseded-by: null
tags: [backend]
---

# 0010 — Ejecutar los trabajos largos en hilos del propio proceso, sin cola ni worker

## Contexto

Hay una tensión aparente en la documentación que conviene dejar resuelta por escrito.

`tech-stack.md` §Límites duros: **«Sin trabajos en segundo plano, colas ni workers. Se
descartaron al confirmar que no hay carga masiva; reintroducirlos exige un ADR.»**

Y sin embargo **cuatro operaciones** están especificadas como trabajos con `jobId`,
polling y cancelación:

| Operación | Duración típica | Cancelable | Fuente |
|---|---|---|---|
| Procesar un manual (PDF → páginas) | Segundos a minutos | Sí, vuelve a `unprocessed` | UX §5.6 |
| Exportar un juego | Segundos (copiar 63 MB) | — | Feature 001 |
| Buscar sugerencias | Decenas de segundos | Sí, **debe cortar el backoff** | Feature 002 |
| Buscar revistas con IA | Decenas de segundos | Sí | Delta D3 |

La reconciliación ya está escrita en `frontend-architecture.md` §Jobs y repetida en el
plan de la feature 002: *«son tareas acotadas y en proceso, no infraestructura de
procesamiento general»*. Este ADR fija **cómo** se implementan, que es lo que falta.

## Decisión

**Los cuatro trabajos corren en hilos del mismo proceso**, sobre un
`ThreadPoolExecutor`, con un registro de jobs en memoria y un `threading.Event` por job
para cancelar.

```
POST  <recurso>        → { jobId, status: 'running', progress: 0 }
GET   /jobs/:jobId     → { status, progress, … }        polling cada 500 ms
DELETE /jobs/:jobId    → cancela
```

**Un solo patrón de job para las cuatro operaciones**, no cuatro mecanismos.

El trabajo es I/O-bound —red, disco, subprocesos— salvo `pymupdf`, así que el GIL no
estorba. El progreso que se expone es el real del job, nunca un timer.

**Nada del registro de jobs persiste**, y es deliberado: un job en curso no sobrevive a
cerrar la aplicación. El requisito real es sobrevivir a un **refresh del navegador**, y
eso sí se cumple porque el proceso sigue vivo.

**Lo único que sí persiste es el contador de cuota diaria por proveedor**, en
`cuotas.json`. Si viviera en memoria, reiniciar lo pondría en cero y volveríamos a
pegarle a una API que ya nos cortó — riesgo identificado en el plan de la feature 002.

**Cancelar tiene que interrumpir el backoff.** Si el usuario cierra el modal durante una
espera de 16 s, el job termina en ese momento. Un `DELETE` que hay que esperar no cancela
nada.

## Alternativas consideradas

### A. Celery o RQ con Redis

- A favor: durabilidad, reintentos gestionados, jobs que sobreviven al reinicio,
  observabilidad de la cola.
- En contra: un broker, un proceso worker y un proceso más que arrancar y supervisar,
  para una aplicación de escritorio de un usuario.
- **Descartada porque:** es exactamente lo que `tech-stack.md` §Límites duros descartó al
  confirmar que no hay carga masiva. Resuelve durabilidad y escala, y acá no hay ninguna
  de las dos: el usuario está sentado frente a la máquina y son cuatro operaciones que él
  mismo dispara, de a una.

### B. `BackgroundTasks` de FastAPI

- A favor: ya viene con el framework, cero código de infraestructura.
- En contra: **no se pueden consultar ni cancelar**.
- **Descartada porque:** no cumple los requisitos. El diseño exige progreso visible y
  cancelación en las cuatro operaciones, y `BackgroundTasks` no ofrece ninguna de las dos.

### C. `multiprocessing` en vez de hilos

- A favor: esquiva el GIL, y rasterizar un PDF sí es trabajo de CPU.
- En contra: serializar estado entre procesos, y cancelar pasa a ser matar un proceso.
- **Descartada porque:** de los cuatro trabajos, tres son I/O puro. Rasterizar es el
  único CPU-bound y ocurre de a un manual por vez, con el usuario esperando a propósito
  (`tech-stack.md`: *la latencia no es un problema de este producto*). Pagar
  serialización y complejidad de cancelación por el único caso que no la necesita es al
  revés.

### D. Respuesta sincrónica, sin jobs

- A favor: lo más simple posible; ningún registro, ningún polling.
- En contra: una búsqueda de decenas de segundos la cortan navegadores y proxies, no se
  puede cancelar, y un refresh pierde el trabajo.
- **Descartada porque:** el plan de la feature 002 nombra los tres problemas. Además el
  diseño ya especifica polling cada 500 ms para manuales y export: hacerlo distinto en
  sugerencias sería un cuarto mecanismo para el mismo problema.

## Consecuencias

**Positivas**

- Cero infraestructura: no hay broker, ni worker, ni proceso extra que supervisar.
- Un solo patrón que aprender, testear y depurar, para las cuatro operaciones.
- Cancelar es inmediato porque el `Event` lo mira el mismo hilo que hace el trabajo,
  incluido el backoff.

**Coste asumido**

- Un job muere con el proceso. Aceptable porque el usuario está presente.
- **Un export interrumpido puede dejar staging huérfano de decenas de MB.** Se mitiga con
  `try/finally` alrededor del export y limpieza de `tmp/` al arrancar. Riesgo ya
  identificado en el plan de la feature 001.
- El progreso vive en memoria: dos pestañas abiertas ven el mismo job, que es lo correcto,
  pero nada lo persiste si el proceso cae.

**Qué habría que revisar si esto se replantea**

- Si apareciera carga masiva —cargar una carpeta entera, procesar N manuales a la vez—,
  cambia la premisa y la alternativa A vuelve a la mesa. Sería un cambio de misión, no una
  feature.
- Si el rasterizado de manuales grandes bloqueara notablemente la interfaz, conviene
  revisar la alternativa C **solo para ese job**.

## Referencias

- `spec/constitution/tech-stack.md` §Límites duros — sin colas ni workers.
- `spec/constitution/frontend-architecture.md` §Jobs asíncronos — el patrón y su reconciliación.
- [`002-sugerencias-multiproveedor/plan.md`](../features/002-sugerencias-multiproveedor/plan.md) §Las sugerencias son un job — por qué no sincrónico.
- [`001-export-bundle/plan.md`](../features/001-export-bundle/plan.md) §Riesgos — el staging huérfano.
- `docs/ux/requerimiento-funcional.md` §5.6 — progreso visible y cancelable.
