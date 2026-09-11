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

```text
backend/
├── api/             # routers, DTOs Pydantic, errores
│   ├── schemas.py
│   ├── errors.py
│   ├── systems.py
│   ├── games.py
│   ├── fields.py
│   ├── media.py
│   └── jobs.py
├── services/        # lógica de negocio
│   ├── systems.py
│   ├── games.py
│   ├── fields.py
│   ├── media.py
│   └── arcadedb.py  # precarga ArcadeDB al crear juego arcade
├── store/           # archivo.py (atómico) · juegos · sistemas · cuotas · migracion
├── lib/
│   ├── domain/      # completeness.py · validation.py · fielddefs.py
│   ├── providers/
│   │   ├── arcadedb/  # parser.py · cliente.py · proveedor.py
│   │   ├── ia/        # client.py · generador.py · trucos_web.py · traductor.py · prompts/
│   │   └── ...
│   └── jobs/        # registro.py · ejecutor.py
├── config.py
├── main.py
└── cli.py
```

## Variables de entorno

Todas con prefijo `COINDOOR_`, en un `.env` fuera del repo. Sin credenciales el proveedor
correspondiente simplemente no se construye — no hay error, el campo se queda sin sugerencia.

| Variable | Para qué |
|---|---|
| `AI_PRIMARY_BASE_URL` / `_API_KEY` / `_MODEL` | Modelo principal. Sinopsis, reseña, identidad, precarga al alta y parseo de texto pegado |
| `AI_BACKUP_BASE_URL` / `_API_KEY` / `_MODEL` | Respaldo del anterior, mismos campos |
| `SEARCH_BASE_URL` / `SEARCH_API_KEY` | Buscador web (Tavily), hoy **solo trucos** ([ADR-0019](../spec/decisions/0019-buscador-mas-modelo-para-trucos.md)). Lo que encuentra lo estructura `AI_PRIMARY` |
| `DATA_DIR`, `HOST`, `PORT` | Ver `config.py` |

Trucos es el único campo que **no** cae a los modelos a secas: se midió que sin evidencia
devuelven vacíos falsos y códigos inventados, y eso es peor que no sugerir nada. Si falta
`SEARCH_API_KEY`, el campo queda solo con ArcadeDB (arcade) y carga manual.

El presupuesto de evidencia de `trucos_web.py` no es cosmético: `gpt-oss-120b` en el tier
gratuito de Groq tiene 8.000 TPM y cuenta `prompt + max_tokens`, así que pasarle las páginas
enteras devuelve 429.

## Contexto ampliado

- Stack y límites: `spec/constitution/tech-stack.md`
- Decisiones: `spec/decisions/` — sobre todo [0007](../spec/decisions/0007-fastapi-como-framework-backend.md), [0008](../spec/decisions/0008-persistencia-en-archivos.md), [0009](../spec/decisions/0009-proceso-local-en-loopback.md), [0010](../spec/decisions/0010-jobs-en-proceso.md)
- Análisis completo del stack: `docs/arquitectura/`
