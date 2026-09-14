# 012 · Instalar en ATTRACT — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

El backend recalcula la ruta del `.zip` exportado a partir del `game_id` — la misma que
ya escribe `ExportService.run()` — en vez de recibirla del cliente: el nombre de archivo
lo genera el servidor, nunca el cliente (regla de `backend/CLAUDE.md`). Si no existe, es
un `Conflict`: hay que exportar antes de instalar.

Es una llamada síncrona a `subprocess.run`, con el mismo criterio que
`backend/bundle/verify.py` usa para `attract doctor`: código de argumentos en lista,
nunca `shell=True`, veredicto por código de salida. A diferencia de `verify.py`, sí se
conserva `stdout`/`stderr` para mostrarlos si falla — no para interpretarlos, solo como
diagnóstico legible por humanos (`ADR-0021`).

No es un job: copiar unos MB y correr `doctor` remoto no es el tipo de operación que
`ADR-0010` reservó para el patrón de `jobId` + polling, y agregar una quinta operación
asíncrona por esto sería la complejidad que `tech-stack.md` §Convenciones pide no sumar
para ahorrar segundos.

## Implementación

La captura de stdout y stderr usa UTF-8 explícito con `errors="replace"`: la salida
de PowerShell puede contener bytes de otra codificación. Solo se reemplazan los
caracteres inválidos para mostrar el diagnóstico, sin interpretar su contenido ni
alterar el resultado determinado por el código de salida.

1. `backend/bundle/install.py` (nuevo) — `install_bundle(script, bundle, library, *,
   timeout=300) -> dict`. Mismo shape que `verify_staging()`: `try/except
   FileNotFoundError/TimeoutExpired`, arma `{"ok": bool, "estado": str, "salida": str}`
   a partir solo del código de salida, más `stdout`+`stderr` crudos para diagnóstico.
2. `backend/services/export.py` — nuevo método `ExportService.install(game_id) ->
   dict[str, object]`:
   - Recalcula `bundle = data_dir/exports/{safe_id(game.id)}.coindoor.zip`;
     si no existe → `Conflict("No hay un export para instalar. Exportá el juego primero.")`.
   - Lee `attract_dir` de `ConfigStore(settings.config_path).attract_dir()`
     ([013 · Configuración](../013-configuracion/plan.md)); si es `None` → `BadRequest`
     pidiendo configurarlo en Configuración.
   - Si `attract_dir/install-coindoor-wsl.sh` no existe → `BadRequest` nombrando la ruta.
   - Llama a `install_bundle(...)`; si `ok` es `False` → `Conflict` con la `salida` en el
     mensaje (no en `detail`: el cliente de export solo lee `payload.error`, ver
     `frontend/src/lib/api/client.ts`).
3. `backend/api/export.py` — `POST /games/{game_id}/install-attract`, sin body, delega en
   el service y devuelve `InstallOut`.
4. `backend/api/schemas.py` — `InstallOut(BaseModel): ok: bool; estado: str; salida: str`.
5. `frontend/src/lib/api/export.ts` — `InstallResult` + `installAttract(gameId)` que
   postea a `/games/{gameId}/install-attract` con `fetchJson`.
6. `frontend/src/pages/ExportPage.tsx` — en el bloque `if (result)`, agrega estado local
   (`installing`, `installResult`, `installError`) y un botón "Cargar en ATTRACT" junto a
   los dos existentes. Mismo patrón que `handleExport`: `async function`, sin
   TanStack Query — el resto de la pantalla ya está escrito así.

## Decisiones

- **Subproceso al script existente, no reimplementar el merge** — ver
  [`ADR-0021`](../../decisions/0021-instalar-bundle-por-subproceso.md).
- **Síncrono, no job** — ver `ADR-0021` §Decisión y `ADR-0010`.
- **La ruta del bundle se recalcula en el servidor, no la manda el cliente** — mismo
  criterio que el resto del backend: el cliente nunca escribe nombres de archivo.
- **La `salida` va en el mensaje de error, no en `detail`** — porque
  `frontend/src/lib/api/client.ts::fetchJson` hoy solo lee `payload.error`; extender
  `ApiError` para un único caller no se justifica.

## Riesgos

- **`wslpath`/`powershell.exe` no están en `PATH` dentro del proceso de COINDOOR** (puede
  correr con un `PATH` distinto al de una terminal interactiva) — se mitiga porque
  `install-coindoor-wsl.sh` ya valida esas herramientas y sale con mensaje explícito; el
  código de salida no-cero llega igual al usuario como texto de diagnóstico.
- **El timeout de 300 s no alcanza** para una librería en un disco muy lento — si ocurre,
  se sube el valor; no se vuelve un job solo por esto salvo que pase seguido.
