# 005 · Esqueleto del backend — Tareas

_Checklist accionable derivada del `plan.md`._

## Antes de tocar código

- [x] Confirmar la ruta del directorio de datos y su variable de entorno. Hecho cuando:
      está escrito el default (`~/.coindoor/`) y cómo se cambia (`COINDOOR_DATA_DIR`).
- [x] Tener `fielddefs.json` de la feature [004](../004-dominio-y-contrato/spec.md). El
      backend lo lee, no lo duplica
      ([`ADR-0011`](../../decisions/0011-fielddefs-json-compartido.md)).
- [x] Tener `pyproject.toml` base y dominio Python de feature004. Hecho cuando existen
      `backend/lib/domain/completeness.py` y `backend/lib/domain/validation.py`.

## Implementación

- [x] `pyproject.toml` ampliado con `fastapi`, `uvicorn`, `pydantic-settings`,
      `python-multipart` y script `coindoor`. Hecho cuando: `uv run coindoor`,
      `uv run pytest`, `uv run ruff check .` y `uv run mypy backend/lib` corren.
- [x] `config.py` con `COINDOOR_DATA_DIR`, default `~/.coindoor/`, host `127.0.0.1` y
      puerto `8765`. Hecho cuando: la app arranca sin `.env` ni credenciales.
- [x] `store/archivo.py` — **primero que nada**. Hecho cuando: escribir es temporal +
      `fsync` + `os.replace()`, y leer valida con Pydantic y falla nombrando el archivo.
- [x] `store/migracion.py` — tabla `version → función`, con la v1 vacía como base.
- [x] `store/juegos.py` — CRUD + índice en memoria + `Lock` por `set`. Hecho cuando: el
      índice se actualiza **después** del `replace`, nunca antes.
- [x] `store/sistemas.py` y `store/cuotas.py`.
- [x] `config.py` con `pydantic-settings`. Hecho cuando: la app arranca sin `.env` y sin
      ninguna credencial.
- [x] `lib/jobs/` — registro, ejecutor y cancelación. Hecho cuando: un job de prueba que
      duerme 30 s se cancela **en el momento**, no al terminar la espera.
- [x] `api/errors.py` — `CoindoorError` y el `exception_handler`.
- [x] `api/schemas.py` — DTOs espejo de `types.ts` con los deltas D1–D3 aplicados.
- [x] `api/systems.py` — `GET /api/systems`, `POST /api/systems`.
- [x] `api/games.py` — `GET /api/games` (filtros + paginación), `GET /api/games/:id`,
      `POST /api/games`, `PATCH /api/games/:id`, `POST /api/games/:id/mark-ready`.
- [x] `api/fields.py` — `PUT` y `DELETE /api/games/:id/fields/:key`, con multipart en
      streaming.
- [x] `api/jobs.py` — `POST /api/jobs/test-sleep`, `GET` y `DELETE /api/jobs/:jobId`.
- [x] `main.py` — middleware de `Host`, `/api/docs`, `/api/openapi.json`, montaje de
      `/media` y del build del frontend con fallback a `index.html`, limpieza de `tmp/` al
      arrancar.
- [x] Comando `coindoor` que levanta Uvicorn en `127.0.0.1:8765` y abre el navegador.

## Tests

### Persistencia — los que no se pueden saltear

- [x] **Matar el proceso a mitad de un guardado deja el `game.json` anterior intacto y
      legible.** Sin este test, la escritura atómica está mal y nadie se entera.
- [x] Un `game.json` corrupto produce un error que **nombra el archivo**, no un `KeyError`.
- [x] Un documento con `version` vieja se migra al leer y se reescribe al guardar.
- [x] `status` no aparece en ningún archivo guardado.
- [x] Dos hilos guardando el mismo juego no se pisan.

### Seguridad

- [x] Una request con `Host: evil.com` se rechaza. **Es la mitigación menos obvia y la que
      para el DNS rebinding.**
- [x] Un `key` de campo que no está en `fielddefs.json` se rechaza.
- [x] Un `romRef` con `../` no escapa del directorio esperado.

### API

- [x] `POST /api/systems` con ruta relativa → 422 con el mensaje del contrato.
- [x] `POST /api/games/:id/mark-ready` sobre un juego incompleto → 409 **con la lista exacta de faltantes**.
- [x] `POST /api/games/:id/mark-ready` sobre un juego `ready` → 200.
- [x] `GET /api/games` filtra por `q`, `systemId` y `status`, y pagina.
- [x] Un juego con error de formato aparece como `error` aunque esté completo.
- [x] Subir un archivo grande no lo carga entero en memoria.

### Jobs

- [x] `POST /api/jobs/test-sleep` devuelve `jobId`; `GET /api/jobs/:jobId` reporta
      progreso real; `DELETE /api/jobs/:jobId` cancela.
- [x] Cancelar durante una espera larga corta **en el momento**.
- [x] Un job que falla queda en `failed` con su motivo, y no tumba el proceso.

### Arranque

- [x] Sin `.env` ni credenciales, la app arranca.
- [x] Al arrancar crea `~/.coindoor/` o `COINDOOR_DATA_DIR` si falta, con
      `sistemas.json`, `cuotas.json`, `juegos/` y `tmp/`, y limpia `tmp/`.

## Cierre

- [x] Validar contra todos los criterios de aceptación de `spec.md`.
- [x] `mypy`, ruff y pytest limpios.
- [x] Verificar a mano que el proceso **no** responde desde otra máquina de la red.
- [x] Rellenar `backend/CLAUDE.md` con las rutas y comandos reales.
- [x] Actualizar `../../constitution/tech-stack.md` §Comandos con lo que de verdad corre.
- [x] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.
