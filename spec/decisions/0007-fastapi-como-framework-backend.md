---
id: 0007
title: Construir el backend con FastAPI en vez de Django o Flask
status: accepted
date: 2026-08-11
supersedes: null
superseded-by: null
tags: [backend]
---

# 0007 — Construir el backend con FastAPI en vez de Django o Flask

## Contexto

`tech-stack.md` confirma Python y deja el framework abierto. Es el punto 2 de
§Pendientes que bloquean y lo único que impide arrancar la Fase 1.

La elección es libre pero **acotada**, porque el contrato de API ya está escrito:
`docs/claude_diseño/data-model.md` §6 define ~25 endpoints con sus verbos, sus códigos
de error y sus cuerpos, y las features [001](../features/001-export-bundle/plan.md) y
[002](../features/002-sugerencias-multiproveedor/plan.md) agregan los suyos. El paquete
de diseño también escribió los tipos del cliente en TypeScript.

Restricciones que acotan la decisión, todas de `tech-stack.md` §Límites duros:

- **Sin autenticación, usuarios, roles ni permisos.** Un solo usuario, su máquina.
- **Sin carga masiva.** Un juego por vez.
- **Sin colas ni workers.**
- El backend tiene que **leer rutas absolutas del disco** (`romSource: 'path'`),
  **ejecutar subprocesos** (`mame -listxml`, `attract doctor`) y **recibir archivos de
  decenas de MB** (un video de 53 MB, manuales en PDF).

## Decisión

**El backend se construye con FastAPI sobre Uvicorn, con Pydantic v2 en el borde.**

Los DTO de Pydantic son la traducción directa de los tipos TypeScript que el paquete de
diseño ya definió. El esquema OpenAPI se genera solo y se sirve en `/api/docs`; no se
escribe documentación de API a mano.

Los routers son sincrónicos (`def`, no `async def`) salvo donde haya fan-out real de red.
El trabajo del backend es subprocesos, lectura de archivos y PDF, y los tres son
sincrónicos: un `async def` que los llame bloquea el event loop sin avisar.

## Alternativas consideradas

### A. Django + Django REST Framework

- A favor: ORM, migraciones, admin y autenticación listos. El ecosistema más grande de
  Python. Convenciones fuertes que evitan discutir estructura.
- En contra: la mayor parte de lo que aporta está **prohibido** en este proyecto. Su ORM
  asume un servidor de base de datos, y acá no hay base de datos
  ([`ADR-0008`](0008-persistencia-en-archivos.md)).
- **Descartada porque:** auth, sesiones, permisos, admin y middleware de usuario son
  exactamente lo que `tech-stack.md` §Límites duros prohíbe. Quedaría un Django al que
  hay que apagarle la mitad, y con una tabla de usuarios tentadora «por si acaso» que
  rompería el límite duro el día que alguien la use. Un framework que se pelea con su
  propio uso previsto es peor que uno más chico.

### B. Flask

- A favor: mínimo. Solo entra lo que se agregue. Curva casi nula.
- En contra: validación, serialización y OpenAPI hay que traerlos aparte
  (marshmallow, apispec) o escribirlos a mano.
- **Descartada porque:** el resultado sería reimplementar lo que FastAPI ya trae, con
  menos rigor y más código propio que mantener. El ahorro de dependencias es aparente:
  se pagan igual, solo que elegidas de a una.

### C. Node + TypeScript en el backend

- A favor: un solo lenguaje en todo el repo. Los tipos del dominio se escribirían una vez
  en lugar de dos.
- En contra: rasterizar PDF en Node es peor terreno que `pymupdf`, que es justamente la
  librería que ya usa `attract rasterize` (ADR-0022 de ATTRACT). Y se pierde la afinidad
  con ATTRACT, que es el sistema con el que hay que hablar.
- **Descartada porque:** el argumento de «un solo lenguaje» resuelve un riesgo —la
  duplicación del dominio— que se mitiga mejor compartiendo **datos**
  ([`ADR-0011`](0011-fielddefs-json-compartido.md)). A cambio introduce un riesgo peor:
  divergir del comportamiento real de ATTRACT, que es Python y cuyo código hay que poder
  leer para saber qué valida. Ese error se descubre en el gabinete.

### D. Sin framework: `http.server` de stdlib

- A favor: cero dependencias, coherente con la cultura stdlib-only de ATTRACT.
- En contra: no hay multipart, ni validación, ni enrutado, ni códigos de error, ni
  servido de estáticos. Todo eso son ~25 endpoints de trabajo manual.
- **Descartada porque:** ATTRACT es stdlib-only porque corre junto al gabinete offline y
  esa restricción tiene una razón (ADR-0012 y ADR-0022 de ATTRACT documentan las dos
  únicas excepciones). COINDOOR es explícitamente **la mitad conectada** y ya necesita
  httpx, pymupdf y Pillow. Copiar la restricción sin copiar su motivo es cargo cult.

## Consecuencias

**Positivas**

- El contrato de API deja de ser prosa y pasa a ser código verificable: un DTO que no
  coincide con el diseño falla al arrancar, no en producción.
- La documentación de API se genera y no se desincroniza.
- `docs/api-reference.md` se rellena desde OpenAPI en vez de escribirse a mano.
- Los mismos modelos Pydantic que validan la request sirven para validar un `game.json`
  al leerlo del disco ([`ADR-0008`](0008-persistencia-en-archivos.md)).

**Coste asumido**

- Hay que ensamblar a mano lo que Django trae junto: estructura de carpetas,
  configuración, manejo de errores.
- El dominio se escribe dos veces, en TypeScript y en Python. Se mitiga compartiendo
  `fielddefs.json` ([`ADR-0011`](0011-fielddefs-json-compartido.md)); no se elimina.
- Tentación de usar `async def` en todo el backend. La regla es al revés: sincrónico por
  defecto, `async` solo donde haya fan-out de red.

**Qué habría que revisar si esto se replantea**

- Si aparecieran usuarios, roles o colaboración, la misión cambió y Django vuelve a la
  mesa junto con todo lo demás.
- Si el backend terminara siendo un envoltorio fino sobre ATTRACT sin lógica propia,
  convendría revisar si hace falta un framework.

## Referencias

- `docs/claude_diseño/data-model.md` §6 — el contrato de API que hay que implementar.
- `spec/constitution/tech-stack.md` §Límites duros, §Pendientes que bloquean.
- ATTRACT `src/attract/cli.py` — la política stdlib-only y sus dos excepciones acotadas.
- [`ADR-0008`](0008-persistencia-en-archivos.md) — por qué no hay base de datos.
- [`ADR-0011`](0011-fielddefs-json-compartido.md) — cómo se evita duplicar el dominio.
