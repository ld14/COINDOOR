# 005 · Esqueleto del backend — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

**El `store/` primero, y antes que cualquier endpoint.** Si la escritura atómica llega
después, los servicios ya escriben con `open(..., 'w')` y nadie los corrige. Es el mismo
criterio que la feature 002 aplica a `providers/http.py`: la política va antes que sus
consumidores.

El resto es una capa fina. `api/` valida y serializa, `services/` decide, `store/` guarda,
y `lib/` no conoce ni HTTP ni el almacenamiento. Los routers son sincrónicos (`def`):
subprocesos, lectura de archivos y pymupdf lo son, y un `async def` que los llame bloquea
el event loop sin avisar.

**Un solo patrón de job** para las cuatro operaciones largas del sistema
([`ADR-0010`](../../decisions/0010-jobs-en-proceso.md)). Se construye acá con un job de
prueba y después lo consumen manuales, sugerencias, revistas y export sin inventar un
mecanismo nuevo cada vez.

## Implementación

Reutiliza el dominio existente de feature004: `backend/lib/domain/completeness.py`,
`backend/lib/domain/validation.py`, `frontend/src/lib/domain/contract.json` y
`frontend/src/lib/domain/fielddefs.json`. No se copian ni se reimplementan esas reglas.


1. `pyproject.toml` — ampliar el archivo existente con `fastapi`, `uvicorn`,
   `pydantic-settings`, `python-multipart` y el script `coindoor = "backend.cli:main"`.
2. `config.py` — `pydantic-settings`: directorio de datos (`~/.coindoor/` por default,
   `COINDOOR_DATA_DIR` para cambiarlo), puerto, credenciales opcionales. Sin credenciales,
   los proveedores se saltean y la app arranca igual.
3. `store/archivo.py` — `leer_json()` y `escribir_json()`. Escribir es: serializar a
   `<nombre>.tmp`, `fsync`, `os.replace()`. Leer es: parsear, migrar por `version`,
   validar con el modelo Pydantic, y fallar **nombrando el archivo**.
   Ver [`ADR-0008`](../../decisions/0008-persistencia-en-archivos.md).
4. `store/migracion.py` — tabla `version → función`. Se agregan, nunca se editan.
5. `store/juegos.py` — CRUD sobre `juegos/<systemId>/<gameId>/game.json` + el índice en
   memoria, con un `threading.Lock` por `systemId`. El índice se actualiza **después** del
   `replace` exitoso.
6. `store/sistemas.py`, `store/cuotas.py` — sobre `sistemas.json` y `cuotas.json`.
7. `lib/jobs/registro.py` y `lib/jobs/ejecutor.py` — `ThreadPoolExecutor`, `dict` de jobs,
   un `threading.Event` por job. **Cancelar interrumpe cualquier espera**, incluido un
   backoff.
8. `api/errors.py` — `CoindoorError` y sus subclases, con un `exception_handler` que las
   mapea a los códigos que el diseño exige (409 con faltantes, 422 con el motivo).
9. `api/schemas.py` — DTOs Pydantic, espejo de `types.ts` con los deltas aplicados.
10. `api/systems.py`, `api/games.py`, `api/fields.py`, `api/jobs.py` — los endpoints del
    alcance, siempre bajo `/api`.
11. `main.py` — la app, el middleware de `Host`, `/api/docs`, el montaje de `/media` y del
    build del frontend con fallback a `index.html`, y la limpieza de `tmp/` al arrancar.
12. `cli.py` — entrypoint `uv run coindoor`, con Uvicorn fijado a `127.0.0.1:8765`.

## Decisiones

- **`store/` antes que los endpoints** — si llega después, nadie reescribe los `open()`.
- **El índice en memoria se actualiza después del `replace`, nunca antes** — si se
  actualiza primero y la escritura falla, la lista miente hasta reiniciar.
- **Un `Lock` por `set`, no uno global** — hay un solo proceso, pero dos hilos (el usuario
  y un job) pueden tocar juegos distintos a la vez.
- **Routers `def`, no `async def`** — ver `tech-stack.md` §Convenciones del backend.
- **El bind a loopback más la validación de `Host` reemplazan a la autenticación** — las
  dos cosas, no una. Ver
  [`ADR-0009`](../../decisions/0009-proceso-local-en-loopback.md).
- **Sin base de datos** — ver
  [`ADR-0008`](../../decisions/0008-persistencia-en-archivos.md).
- **Los nombres de archivo los genera el servidor**, nunca el cliente, y toda ruta se
  resuelve y se comprueba que caiga dentro del directorio esperado.

## Riesgos

- **La escritura atómica se implementa mal y nadie se entera.** Un `open(..., 'w')` sobre
  el archivo final funciona el 99,9 % de las veces. El test que mata el proceso a mitad de
  guardado es la única forma de saberlo, y va desde el primer día.
- **Path traversal por `romRef` o por el `key` de un campo.** El backend acepta rutas
  absolutas por diseño. `key` se valida contra `fielddefs.json`, y toda ruta derivada se
  resuelve y se comprueba contra su directorio.
- **Falta la validación del header `Host`.** Es la mitigación menos obvia de las tres y
  la que parece redundante — es justamente la que para el DNS rebinding, que sortea el
  bind a loopback.
- **El índice en memoria crece con la colección.** A 200 juegos es gratis; el límite de
  esta decisión está escrito en
  [`ADR-0008`](../../decisions/0008-persistencia-en-archivos.md) §Qué habría que revisar.
- **Un job huérfano si el proceso muere.** El staging del export se limpia al arrancar,
  no solo al terminar.
