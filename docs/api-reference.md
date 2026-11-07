# Referencia

<!-- GUÍA: superficie pública. Si es autogenerada, indica el comando que la
regenera y no la edites a mano. -->

La referencia de la API la genera FastAPI a partir del código, así que siempre coincide
con la versión que está corriendo. No se mantiene a mano.

Con la aplicación levantada (`./dev.sh` o `uv run coindoor`):

| Qué | Dónde |
|---|---|
| Referencia navegable, con cada endpoint y sus esquemas | `http://127.0.0.1:8765/api/docs` |
| El esquema OpenAPI en JSON | `http://127.0.0.1:8765/api/openapi.json` |

La API escucha solo en `127.0.0.1` y rechaza los pedidos cuyo header `Host` no sea
`127.0.0.1:8765` o `localhost:8765`. No pide autenticación.

Los trabajos largos (precarga, completar la ficha, descargar video) responden enseguida
con un `jobId`, y el resultado se consulta en `GET /api/jobs/{jobId}` hasta que termina.
El export funciona igual, pero devuelve un `runId` que se consulta en
`GET /api/export/{runId}`. Instalar en ATTRACT
(`POST /api/games/{gameId}/install-attract`) responde cuando termina.
