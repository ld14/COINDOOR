# Roadmap

_Orden y estado de las features. Cada entrada apunta a su carpeta en `../features/`._

## Hecho ✅

- [`003 · base`](../features/003-base-frontend/spec.md) — Vite + React + Router, tokens, primitivas DOS, layout y catálogo interno.
- [`004 · dominio y contrato`](../features/004-dominio-y-contrato/spec.md) — contrato ATTRACT derivado, política de completitud, dominio TS/Python y seed/mock server.
- [`005 · esqueleto de backend`](../features/005-esqueleto-backend/spec.md) — FastAPI local, persistencia atómica, seguridad por loopback + `Host`, patrón de jobs y comando `coindoor`.

Cerrado como trabajo previo:

- Misión, límites duros y modelo de datos verificado contra `goldnaxe`.
- **Doce ADRs** ([índice](../decisions/README.md)), todos `accepted`.
- El paquete de diseño de front-end (`docs/claude_diseño/`), con sus cinco deltas.
- **El stack completo**, front y back, con su análisis en
  [`docs/arquitectura/`](../../docs/arquitectura/README.md).
- Cinco features especificadas: [`001 · export`](../features/001-export-bundle/spec.md),
  [`002 · sugerencias`](../features/002-sugerencias-multiproveedor/spec.md),
  [`003 · base`](../features/003-base-frontend/spec.md),
  [`004 · dominio y contrato`](../features/004-dominio-y-contrato/spec.md) y
  [`005 · esqueleto de backend`](../features/005-esqueleto-backend/spec.md).

001 y 002 son las **dos de mayor riesgo técnico**, especificadas primero a propósito: si
el formato del bundle o el contrato del proveedor están mal pensados, arrastran a todo lo
demás.

## Qué cerró cada cosa

| Qué estaba abierto | Lo cerró |
|---|---|
| Qué significa COMPLETO | Paquete de diseño: 7 campos de identidad + carátula + póster + sinopsis + acento |
| Stack de frontend | Paquete de diseño: Vite + React + TS + TanStack Query, sin librerías de componentes |
| Contrato de API | `data-model.md` §6 más los deltas |
| `review`/`cheats` como texto plano | Delta D1: se estructuran según el contrato |
| Falta `accent2` | Delta D2 |
| Alcance de revistas | Delta D3: solo búsqueda y sugerencia. No se descargan ni se exportan |
| El export no contemplaba el bundle | Delta D4 + feature 001 |
| El modal asumía una sola fuente | Delta D5 + feature 002 |
| `fieldDefs.ts` contra `ADR-0001` | [`ADR-0005`](../decisions/0005-contrato-vendoreado-vs-politica-propia.md): dos archivos y un test que los ata |
| Qué fuentes externas usar | [`ADR-0006`](../decisions/0006-fuentes-externas-multiproveedor.md) |
| Identidad fuera de arcade | [`ADR-0004`](../decisions/0004-coindoor-fuente-identidad-no-mame.md): ScreenScraper por hash cubre consolas; solo PC/DOS queda sin catálogo |
| Stack de backend | ADRs [`0007`](../decisions/0007-fastapi-como-framework-backend.md) a [`0012`](../decisions/0012-verificacion-attract-por-subproceso.md): FastAPI, sin base de datos, loopback, jobs en proceso |
| Dónde corre COINDOOR | [`ADR-0009`](../decisions/0009-proceso-local-en-loopback.md): un proceso local, y ese bind reemplaza a la autenticación |
| El backend no estaba en las seis fases | Feature [005](../features/005-esqueleto-backend/spec.md), que es su propio carril |

## Bloqueado 🚧

1. **Credenciales y cuotas de ScreenScraper y MobyGames**, verificadas contra su
   documentación actual. Bloquea la feature 002, no el arranque.
2. **Elegir el modelo de IA** y escribir `sinopsis.v1.md`. Bloquea la feature 002.

**Ya no bloquea:** el stack. **Ni los dos huecos del contrato** que bloqueaban la
feature 001 (mapeo de `identitySource` a `identidad.origen`, y `players` no entero) —
resueltos, ver [`001/spec.md`](../features/001-export-bundle/spec.md#decisiones-resueltas-antes-de-implementar).
La feature 001 puede arrancar.

## Siguiente 🔜

Las seis fases de `docs/claude_diseño/README.md` son **el carril del frontend**. El
backend no estaba contemplado ahí y va en paralelo, porque las fases 1 a 4 se desarrollan
contra un mock server y no lo necesitan.

| Fase | Qué | Feature | Estado |
|---|---|---|---|
| 1 | **Base** — Vite + React + Router, `tokens.css`, primitivas de `components/dos/`, layout de `App.tsx` | [`003`](../features/003-base-frontend/spec.md) | Hecha |
| 2 | **Dominio y datos mock** — `types.ts`, `contract.json`, `fielddefs.json`, `completeness`, `validation`, mock server con el seed | [`004`](../features/004-dominio-y-contrato/spec.md) | Hecha |
| — | **Esqueleto de backend** — app FastAPI, `store/` con escritura atómica, patrón de job, configuración | [`005`](../features/005-esqueleto-backend/spec.md) | Hecha |
| 3 | **Pantallas de lectura** — Sistemas, lista de Juegos, ficha en solo lectura | — | Falta carpeta |
| 4 | **Edición** — alta en dos pasos, carga y borrado de campos, textos, presentación, marcar como listo | — | Falta carpeta |
| 5 | **Asíncrono** — manuales con job y cancelación, modal de sugerencias | [`002`](../features/002-sugerencias-multiproveedor/spec.md) | Especificada |
| 6 | **Exportación** — lista de exportables, "qué incluir", generación del `.zip` | [`001`](../features/001-export-bundle/spec.md) | Especificada |

**Orden de arranque:** 003 → 004 → 005. Las tres primeras son independientes entre sí
salvo que 004 necesita `contract.json`, y 005 consume el `fielddefs.json` que produce 004.

Los diez juegos del seed son deliberados: cada uno ejercita un caso de borde distinto (año
`197X`, manual sin procesar, sistema con cabecera inválida, rechazo al exportar). Sirven de
checklist de aceptación, no solo de datos de relleno.

## Dependencias fuera de este repo ⚠️

No son features de COINDOOR y este roadmap no las controla:

- **`attract install <bundle>.zip`** — el comando que instala el bundle no existe. Sin él
  el export produce un archivo que nadie abre. Decidido posponerlo hasta cerrar el
  funcionamiento de COINDOOR.
- **El contrato publicado como dato versionado** — ATTRACT tiene que emitirlo
  ([`ADR-0001`](../decisions/0001-contrato-coindoor-attract.md)). Bloquea el punto 3 de
  arriba.

## Backlog / ideas 💡

_Sin comprometer ni ordenar._

- **Reimportar desde una librería existente** hacia COINDOOR. Hoy el flujo es de un solo
  sentido y el bundle pierde la procedencia
  ([`ADR-0002`](../decisions/0002-procedencia-interna.md)).
- **Más proveedores de sugerencias.** La tabla de
  [`ADR-0006`](../decisions/0006-fuentes-externas-multiproveedor.md) es una lista ordenada:
  sumar una fuente es una fila, no un cambio de arquitectura.
- **Paleta de flechas** para escribir los `input` de trucos (`←`, `↘`, `[ATAQUE]`) sobre un
  campo que sigue siendo texto libre.
- **Un juego de MS-DOS en el seed** — cubriría de una sola vez el `tratamiento:
  descomprimir`, la identidad declarada, un sistema sin catálogo y un juego de varios
  archivos. Hoy nada de eso se ejercita.

> Cada feature nueva se crea como `features/NNN-nombre/` con `spec.md`, `plan.md` y
> `tasks.md` **antes** de tocar código.
