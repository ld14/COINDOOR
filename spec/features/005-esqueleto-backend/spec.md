# 005 · Esqueleto del backend

**Estado:** hecho

## Qué hace

**Recibe** el contrato de API de `data-model.md` §6 con los deltas aplicados, más el
`contract.json`, `fielddefs.json` y dominio Python creados por la feature
[004](../004-dominio-y-contrato/spec.md). **Produce** un proceso FastAPI que arranca en
`127.0.0.1`, sirve el build del frontend desde el mismo origen, persiste sistemas y juegos
como archivos, y expone el patrón de job que después consumen manuales, export,
sugerencias y revistas.

Implementa los endpoints de **sistemas, juegos y campos**. No implementa sugerencias,
manuales, revistas ni export: cada uno tiene su feature.

## Por qué

Las seis fases del roadmap salen de `docs/claude_diseño/` y son todas de frontend: el
backend **no estaba contemplado en ninguna**. Las fases 1 a 4 se desarrollan contra un mock
server y no lo necesitan, pero las fases 5 y 6 —y las features
[001](../001-export-bundle/spec.md) y [002](../002-sugerencias-multiproveedor/spec.md)—
suponen un backend que hoy no existe.

Esta feature es ese carril. Lo que construye no es una pantalla sino **cuatro cimientos que
todo lo demás asume**: la escritura atómica, el patrón de job, la frontera de seguridad y
la configuración sin credenciales.

## Criterios de aceptación

- [x] `uv run coindoor` levanta un proceso que escucha en `127.0.0.1:8765` y sirve
      `/api/*`, `/media/*`, `/api/docs` y el build del frontend desde el mismo origen.
- [x] El proceso **no** escucha en `0.0.0.0`, y una request con un header `Host` que no sea
      `127.0.0.1` ni `localhost` se rechaza.
- [x] La aplicación **arranca sin ninguna credencial configurada**.
- [x] Al arrancar crea el directorio de datos si no existe y limpia `tmp/`. El default es
      `~/.coindoor/`, configurable con `COINDOOR_DATA_DIR`. La forma mínima es:
      `sistemas.json`, `cuotas.json`, `juegos/<systemId>/<gameId>/game.json` y `tmp/`.
- [x] Guardar un juego escribe a un temporal y hace `os.replace()`. **Matar el proceso a
      mitad de un guardado deja el archivo anterior intacto y legible.**
- [x] Leer un `game.json` corrupto o inválido produce un error que **nombra el archivo**,
      no un `KeyError` propagado.
- [x] Un `game.json` con `version` vieja se migra al leerlo y se reescribe al guardar.
- [x] `status` no aparece en ningún archivo guardado: se calcula al leer.
- [x] `GET /api/games` filtra por texto, sistema y estado, y pagina. Los resultados salen
      del índice en memoria, que se actualiza **después** de cada escritura exitosa.
- [x] `POST /api/games/:id/mark-ready` sobre un juego incompleto devuelve **409 con la
      lista exacta de faltantes**.
- [x] `POST /api/systems` con una ruta relativa devuelve **422** con el mensaje del
      contrato.
- [x] Subir un archivo de 53 MB no lo carga entero en memoria.
- [x] El patrón de job funciona de punta a punta con un job de prueba:
      `POST /api/jobs/test-sleep` → `jobId`, `GET /api/jobs/:jobId` con progreso real,
      `DELETE /api/jobs/:jobId` que cancela **en el momento**.
- [x] `/api/docs` sirve Swagger UI y `/api/openapi.json` sirve el OpenAPI generado.

## Fuera de alcance

- **Sugerencias y proveedores** — feature [002](../002-sugerencias-multiproveedor/spec.md).
- **Export y bundle** — feature [001](../001-export-bundle/spec.md).
- **Procesar manuales (PDF → páginas) y buscar revistas.** El patrón de job se construye
  acá; esos dos jobs concretos, no.
- **Detección de acento desde la carátula.** Necesita Pillow y va con la pantalla de
  presentación.
- **Autenticación**, en cualquier forma. Es un límite duro
  ([`ADR-0009`](../../decisions/0009-proceso-local-en-loopback.md)).
