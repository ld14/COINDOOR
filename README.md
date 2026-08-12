# COINDOOR

Herramienta para preparar la metadata de juegos de una colección arcade —video, carátula,
marquesina, sinopsis, reseña, trucos, manual— y entregarla como un `.zip` instalable en
[ATTRACT](../attract), que la ensambla en la librería que Pegasus muestra en el gabinete.

El gabinete es offline por diseño y ATTRACT no descarga nada. COINDOOR es la mitad
conectada del sistema: busca, propone, arma y empaqueta.

> **Estado: diseño cerrado, sin código.** Están la misión, el modelo de datos, doce
> decisiones de arquitectura, la especificación del front-end, el stack completo y cinco
> features listas para implementar. **La Fase 1 puede arrancar.**

## Por dónde empezar

| Si querés… | Leé |
|---|---|
| Entender qué se está construyendo | [`spec/constitution/mission.md`](spec/constitution/mission.md) |
| Diseñar la interfaz | [`docs/ux/requerimiento-funcional.md`](docs/ux/requerimiento-funcional.md) |
| Saber por qué se decidió algo | [`spec/decisions/`](spec/decisions/README.md) |
| Escribir código | [`spec/constitution/tech-stack.md`](spec/constitution/tech-stack.md) |
| Entender el stack y qué se descartó | [`docs/arquitectura/`](docs/arquitectura/README.md) |
| Ver qué sigue | [`spec/constitution/roadmap.md`](spec/constitution/roadmap.md) |
| Entender un término | [`spec/constitution/glosario.md`](spec/constitution/glosario.md) |

## Las decisiones tomadas

Las doce están en `proposed`, con sus alternativas descartadas.

**Del producto y el contrato:**

1. [**0001**](spec/decisions/0001-contrato-coindoor-attract.md) — el contrato de ATTRACT
   se consume como dato versionado; su CLI es la autoridad final.
2. [**0002**](spec/decisions/0002-procedencia-interna.md) — la procedencia de cada campo
   vive solo en COINDOOR y no viaja al export.
3. [**0003**](spec/decisions/0003-bundle-por-juego.md) — cada juego se entrega como un
   `.zip` instalable, no por API. Transporta campos, no sintaxis.
4. [**0004**](spec/decisions/0004-coindoor-fuente-identidad-no-mame.md) — para las
   plataformas que MAME no conoce, COINDOOR es la fuente de identidad.
5. [**0005**](spec/decisions/0005-contrato-vendoreado-vs-politica-propia.md) — el contrato
   vendoreado y la política de completitud son archivos distintos, atados por un test.
6. [**0006**](spec/decisions/0006-fuentes-externas-multiproveedor.md) — varias fuentes por
   campo; una caída no rompe la búsqueda.

**Del stack:**

7. [**0007**](spec/decisions/0007-fastapi-como-framework-backend.md) — FastAPI, no Django
   ni Flask: el contrato de API ya está escrito como tipos.
8. [**0008**](spec/decisions/0008-persistencia-en-archivos.md) — **sin base de datos**: un
   `game.json` por juego, con su media al lado.
9. [**0009**](spec/decisions/0009-proceso-local-en-loopback.md) — un proceso en
   `127.0.0.1`; ese bind reemplaza a la autenticación.
10. [**0010**](spec/decisions/0010-jobs-en-proceso.md) — los cuatro trabajos largos corren
    en hilos del propio proceso. Sin colas, sin workers.
11. [**0011**](spec/decisions/0011-fielddefs-json-compartido.md) — la política de
    completitud es un JSON que leen el front y el back.
12. [**0012**](spec/decisions/0012-verificacion-attract-por-subproceso.md) — `attract
    doctor` se invoca por subproceso y su salida no se parsea.

## Features especificadas

| # | Feature | Qué es |
|---|---|---|
| [003](spec/features/003-base-frontend/spec.md) | **Base del frontend** | Vite + React + las primitivas DOS. **El arranque** |
| [004](spec/features/004-dominio-y-contrato/spec.md) | **Dominio y contrato** | `contract.json`, `fielddefs.json`, completitud y el seed |
| [005](spec/features/005-esqueleto-backend/spec.md) | **Esqueleto del backend** | FastAPI, escritura atómica, patrón de job |
| [002](spec/features/002-sugerencias-multiproveedor/spec.md) | **Sugerencias** | El orquestador de fuentes externas |
| [001](spec/features/001-export-bundle/spec.md) | **Export a bundle** | El `.zip` instalable y su manifiesto |

001 y 002 son las de mayor riesgo técnico y se especificaron primero a propósito. **El
orden de trabajo es 003 → 004 → 005.** Las fases 3 y 4 del roadmap todavía no tienen
carpeta.

## Requisitos

Python 3.12 · [uv](https://docs.astral.sh/uv/) · Node 20+.
Opcionales: los binarios `mame` y `attract` — sin ellos la aplicación funciona con más
trabajo manual.

Detalle en [`spec/constitution/tech-stack.md`](spec/constitution/tech-stack.md).

## Desarrollo

Spec Driven Development: primero la spec, luego el plan, luego las tareas, y solo
entonces el código. Ver [`spec/README.md`](spec/README.md).

La constitución manda: si una feature choca con `spec/constitution/`, se replantea la
feature.

## Licencia

`<PENDIENTE>`
