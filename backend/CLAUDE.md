# Backend

> **Estado actual:** FastAPI mínimo implementado en la feature
> [005](../spec/features/005-esqueleto-backend/spec.md). Sirve API en `/api/*`, estáticos en
> `/media/*`, el build del frontend en `/*` y documentación en `/api/docs`.

Stack: Python 3.12 + FastAPI + Pydantic v2 + Uvicorn. **Sin base de datos**: un
`game.json` por juego.

## Reglas

- Handlers finos: la lógica de negocio va en `services/`, nunca en la ruta.
- Todo input externo se valida en el borde con Pydantic.
- **Toda escritura es atómica**: temporal → `fsync` → `os.replace()`. Nunca escribas sobre
  el archivo en su lugar.
- **Toda lectura valida** y falla nombrando el archivo. Nunca propagues `KeyError` ni
  `JSONDecodeError` hacia arriba.
- **`status` no se guarda nunca.** Se calcula al leer: `error > incomplete > ready`.
- Routers `def`, no `async def`. Subprocesos, pymupdf y archivos son sincrónicos.
- `subprocess` con lista de argumentos. **Jamás `shell=True`.**
- Los nombres de archivo los genera el servidor. El cliente nunca los escribe.
- Ningún proveedor implementa su propio reintento: la política vive en
  `lib/providers/http.py`.
- Las reglas del contrato salen de `contract.json` y `fielddefs.json`. **No las escribas en
  código.**
- El proceso escucha en `127.0.0.1`. Nunca en `0.0.0.0`.
- Middleware valida `Host: 127.0.0.1` / `localhost`.
- `status` no se guarda; se calcula al leer con `compute_game_status()`.
- Jobs en memoria con cancelación por `threading.Event`.
- Todo endpoint nuevo necesita test de integración.

## Estructura actual

```
backend/
├── api/             # routers, DTOs Pydantic, errores
│   ├── schemas.py
│   ├── errors.py
│   ├── systems.py
│   ├── games.py
│   ├── fields.py
│   └── jobs.py
├── services/        # lógica de negocio
│   ├── systems.py
│   ├── games.py
│   └── fields.py
├── store/           # archivo.py (atómico) · juegos · sistemas · cuotas · migracion
├── lib/
│   ├── domain/      # completeness.py · validation.py
│   └── jobs/        # registro.py · ejecutor.py
├── config.py
├── main.py
└── cli.py
```

## Contexto ampliado

- Stack y límites: `spec/constitution/tech-stack.md`
- Decisiones: `spec/decisions/` — sobre todo [0007](../spec/decisions/0007-fastapi-como-framework-backend.md), [0008](../spec/decisions/0008-persistencia-en-archivos.md), [0009](../spec/decisions/0009-proceso-local-en-loopback.md), [0010](../spec/decisions/0010-jobs-en-proceso.md)
- Análisis completo del stack: `docs/arquitectura/`
