# Roadmap

_Orden y estado de las features. Cada entrada apunta a su carpeta en `../features/`._

## Estado al 2026-11-07

**La aplicación está en uso.** Funcionan el alta con precarga, la ficha con autoguardado,
«Sugerir» con varias fuentes, la galería, el video de YouTube, el export a `.zip` con
`attract doctor` y la instalación en ATTRACT. Hay 25 features y 29 ADRs
([índice](../decisions/README.md)).

Lo que queda abierto es poco y concreto:

- **Una feature sin implementar:** [021](../features/021-imagenes-steamgriddb-screenscraper/spec.md)
  (SteamGridDB y ScreenScraper), aprobada.
- **Cinco features implementadas con una verificación pendiente:** de 015 a 019. Ver la
  columna «Estado».
- **Tres features que funcionan pero tienen `tasks.md` sin cerrar** (001, 002 y 008): el
  código y sus tests están, pero no se tildaron los casos de aceptación.

**Nada bloquea hoy.** El modelo de IA, que bloqueaba la 002, se configura por `.env` con
una IA principal y una de respaldo, y los prompts están en
`backend/lib/providers/ia/prompts/`.

## Features

| # | Qué | Estado |
| --- | --- | --- |
| [`001`](../features/001-export-bundle/spec.md) | **Export a bundle**: qué incluir, generación del `.zip`, verificación con `attract doctor` | Funciona · `tasks.md` sin cerrar |
| [`002`](../features/002-sugerencias-multiproveedor/spec.md) | **Sugerencias**: el orquestador de fuentes y el modal con candidatos | Funciona · `tasks.md` sin cerrar |
| [`003`](../features/003-base-frontend/spec.md) | **Base del frontend**: Vite + React + Router, tokens y primitivas | Hecha |
| [`004`](../features/004-dominio-y-contrato/spec.md) | **Dominio y contrato**: `contract.json`, `fielddefs.json`, completitud | Hecha |
| [`005`](../features/005-esqueleto-backend/spec.md) | **Esqueleto del backend**: FastAPI, escritura atómica, jobs, `Host` | Hecha |
| [`006`](../features/006-pantallas-lectura/spec.md) | **Pantallas de lectura**: sistemas, juegos, ficha | Hecha |
| [`007`](../features/007-edicion/spec.md) | **Edición**: alta, campos, textos, presentación, reseña y trucos | Hecha |
| [`008`](../features/008-arcadedb/spec.md) | **ArcadeDB**: precarga al alta y candidatos para arcade | Hecha · `tasks.md` sin cerrar · [`ADR-0014`](../decisions/0014-arcadedb-fuente-arcade.md) |
| [`009`](../features/009-galeria/spec.md) | **Galería**: banco de imágenes de todas las fuentes, con selección múltiple | Funciona · la spec sigue en «aprobada» · [`ADR-0016`](../decisions/0016-galeria-en-subcarpeta-gallery.md) |
| [`010`](../features/010-descubrimiento-roms/spec.md) | **ROMs sin ficha**: el alta ofrece lo instalado que no tiene `game.json` | Funciona · la spec sigue en «aprobada» |
| [`011`](../features/011-video-youtube/spec.md) | **Video desde YouTube**: pegar una URL y descargar, con recorte de los largos | Hecha · [`ADR-0020`](../decisions/0020-descarga-de-video-youtube.md) · [`ADR-0029`](../decisions/0029-recorte-de-videos-largos-de-youtube.md) |
| [`012`](../features/012-instalar-en-attract/spec.md) | **Instalar en ATTRACT**: botón en el resultado del export | Hecha · [`ADR-0021`](../decisions/0021-instalar-bundle-por-subproceso.md) |
| [`013`](../features/013-configuracion/spec.md) | **Configuración**: la ruta de ATTRACT | Hecha · [`ADR-0022`](../decisions/0022-configuracion-no-sensible-en-archivo-propio.md) |
| [`014`](../features/014-listado-exportados/spec.md) | **Listado por exportación**: exportados y pendientes, etiquetas y paginación | Hecha |
| [`015`](../features/015-set-romset-real/spec.md) | **`set` con romset real**: `game.json` lleva el romset de MAME | Implementada · falta `attract doctor` sobre un arcade real exportado |
| [`016`](../features/016-guia-en-export/spec.md) | **Bloque `guia` en el export** | Implementada · falta `attract doctor` sobre un zip real con `guia` |
| [`017`](../features/017-objetivo-guia-ia/spec.md) | **Objetivo de la guía**, editable y sugerido por IA | Implementada · falta revisar un candidato de un modelo real |
| [`018`](../features/018-guia-completa/spec.md) | **Guía completa**: periféricos, primeros pasos, reglas y multijugador | Implementada · falta la prueba de extremo a extremo con ATTRACT |
| [`019`](../features/019-rediseno-flyer/spec.md) | **Rediseño Flyer 80s**: tokens, primitivas, shell, ficha, alta, export y autosave | Implementada · falta compararla con los mockups a 1280 px · [`ADR-0023`](../decisions/0023-estetica-flyer-reemplaza-dos.md) |
| [`020`](../features/020-scrapling-mobygames/spec.md) | **Scrapling y MobyGames**: scraping con navegador, fuente de PC/DOS | Hecha · [`ADR-0024`](../decisions/0024-scrapling-y-mobygames-para-pc-dos.md) · [`ADR-0025`](../decisions/0025-precalentar-mobygames-al-arrancar.md) |
| [`021`](../features/021-imagenes-steamgriddb-screenscraper/spec.md) | **SteamGridDB y ScreenScraper**: dos proveedores más de imágenes y video | Aprobada · sin implementar |
| [`022`](../features/022-edicion-correcta-en-las-fuentes/spec.md) | **Edición correcta en todas las fuentes**: Launchbox como 2ª fuente, IA de respaldo en «Sugerir» | Hecha · [`ADR-0026`](../decisions/0026-ia-ultimo-recurso-en-sugerir-identidad.md) |
| [`023`](../features/023-myabandonware-primera-fuente/spec.md) | **MyAbandonware primera fuente de PC/DOS**; MobyGames solo si falta el dato | Hecha · [`ADR-0027`](../decisions/0027-myabandonware-primera-fuente-de-pc-dos.md) |
| [`024`](../features/024-ficha-completa-al-cargar/spec.md) | **Ficha completa al cargar**: el alta llena casi todo y elige qué imagen va en cada casillero | Hecha · [`ADR-0028`](../decisions/0028-la-precarga-completa-toda-la-ficha.md) |
| [`025`](../features/025-launchbox-nombres-alternativos/spec.md) | **Launchbox reconoce los títulos largos** por año, nombres alternativos y tipo | Hecha |

«Funciona» quiere decir que el código y sus tests están y se usan, pero el documento de la
feature no se cerró. Cerrarlo es revisar sus casos de aceptación, no escribir código.

## Siguiente 🔜

1. **Cerrar las verificaciones de 015 a 018** con un export real y `attract doctor`. Un
   solo juego arcade con guía cubre las cuatro.
2. **Comparar la 019 con los mockups.**
3. **Cerrar los `tasks.md` de 001, 002 y 008**, y pasar a «implementada» las specs de 009
   y 010.
4. **Implementar la 021.**

## Dependencias fuera de este repo ⚠️

No son features de COINDOOR y este roadmap no las controla:

- **El instalador.** ATTRACT ya tiene `attract import`, pero COINDOOR sigue usando el
  instalador provisional `install-coindoor-wsl.sh`
  ([`ADR-0021`](../decisions/0021-instalar-bundle-por-subproceso.md)). Pasarse al
  comando nuevo es una decisión propia, con su ADR.
- **El contrato como dato versionado.** ATTRACT ya lo publica con `attract contrato`
  ([`ADR-0001`](../decisions/0001-contrato-coindoor-attract.md)). COINDOOR todavía usa
  su copia vendoreada, `frontend/src/lib/domain/contract.json`.

## Punto de partida (agosto de 2026)

Lo que estaba cerrado antes de la primera línea de código, como referencia histórica:

- Misión, límites duros y modelo de datos verificado contra `goldnaxe`.
- Los doce primeros ADRs, el paquete de diseño (`docs/claude_diseño/`) con sus cinco deltas
  y el stack, con su análisis en [`docs/arquitectura/`](../../docs/arquitectura/README.md).
- Cinco features especificadas: 001, 002, 003, 004 y 005. El orden de arranque fue
  003 → 004 → 005.

| Qué estaba abierto | Lo cerró |
| --- | --- |
| Qué significa COMPLETO | Paquete de diseño: 7 campos de identidad + carátula + póster + sinopsis + acento |
| Stack de frontend | Paquete de diseño: Vite + React + TS + TanStack Query, sin librerías de componentes |
| Contrato de API | `data-model.md` §6 más los deltas |
| `review`/`cheats` como texto plano | Delta D1: se estructuran según el contrato |
| Falta `accent2` | Delta D2 |
| Alcance de revistas | Delta D3: solo búsqueda y sugerencia. No se descargan ni se exportan |
| El export no contemplaba el bundle | Delta D4 + feature 001 |
| El modal asumía una sola fuente | Delta D5 + feature 002 |
| `fieldDefs.ts` contra `ADR-0001` | [`ADR-0005`](../decisions/0005-contrato-vendoreado-vs-politica-propia.md): dos archivos y un test que los ata |
| Qué fuentes externas usar | [`ADR-0006`](../decisions/0006-fuentes-externas-multiproveedor.md), reemplazado después por la cadena de ADR-0013, 0014, 0024 y 0027 |
| Identidad fuera de arcade | [`ADR-0004`](../decisions/0004-coindoor-fuente-identidad-no-mame.md) |
| Stack de backend | ADRs [`0007`](../decisions/0007-fastapi-como-framework-backend.md) a [`0012`](../decisions/0012-verificacion-attract-por-subproceso.md): FastAPI, sin base de datos, loopback, jobs en proceso |

Los diez juegos del seed son deliberados: cada uno ejercita un caso de borde distinto (año
`197X`, manual sin procesar, sistema con cabecera inválida, rechazo al exportar). Sirven de
checklist de aceptación, no solo de datos de relleno.

## Backlog / ideas 💡

_Sin comprometer ni ordenar._

- **Reimportar desde una librería existente** hacia COINDOOR. Hoy el flujo es de un solo
  sentido y el bundle pierde la procedencia
  ([`ADR-0002`](../decisions/0002-procedencia-interna.md)).
- **Más proveedores.** Sumar una fuente es una fila en la cadena de cada campo
  (`backend/lib/providers/registro.py`), no un cambio de arquitectura. La 021 es el
  siguiente caso.
- **Paleta de flechas** para escribir los `input` de trucos (`←`, `↘`, `[ATAQUE]`) sobre un
  campo que sigue siendo texto libre.
- **Un juego de MS-DOS en el seed**: cubriría de una sola vez el `tratamiento:
  descomprimir`, la identidad declarada, un sistema sin catálogo y un juego de varios
  archivos.
- **Un truco a medias no debería exportarse.** ATTRACT exige `name` e `input` en cada
  entrada, y la ficha deja guardar una con un solo campo.

> Cada feature nueva se crea como `features/NNN-nombre/` con `spec.md`, `plan.md` y
> `tasks.md` **antes** de tocar código.
