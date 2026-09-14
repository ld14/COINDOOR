# 012 · Instalar en ATTRACT — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas;
marca `[x]` al completarlas._

## Implementación

- [x] `backend/config.py` — agregar `attract_dir: Path | None`. Hecho cuando:
      `COINDOOR_ATTRACT_DIR=/ruta Settings()` produce `settings.attract_dir ==
      Path("/ruta")`, y sin la variable es `None`.
- [x] `backend/bundle/install.py` — `install_bundle()`. Hecho cuando: con un script que
      sale 0 devuelve `ok: True`; con un script que sale distinto de 0 devuelve `ok:
      False` y la `salida` con lo que imprimió; con una ruta de script inexistente
      devuelve `ok: False, estado: "no_disponible"` sin lanzar.
- [x] `backend/services/export.py::ExportService.install()`. Hecho cuando: sin export
      previo lanza `Conflict`; sin `attract_dir` configurado lanza `BadRequest`; con todo
      presente pero el script fallando, lanza `Conflict` con la salida en el mensaje.
      Depende de: tarea anterior.
- [x] `backend/api/export.py` — `POST /games/{game_id}/install-attract`. Hecho cuando:
      responde 200 con `InstallOut` en el caso feliz, y el código de error correcto
      (409/422) en cada caso de `service.install()`.
- [x] `backend/api/schemas.py::InstallOut`. Hecho cuando: el router lo usa como tipo de
      retorno.
- [x] `frontend/src/lib/api/export.ts` — `InstallResult` + `installAttract()`. Hecho
      cuando: llama a `POST /games/{gameId}/install-attract` y tipa la respuesta.
- [x] `frontend/src/pages/ExportPage.tsx` — botón "Cargar en ATTRACT" en el bloque de
      resultado. Hecho cuando: al tocarlo se ve un spinner, y al terminar se ve el
      mensaje de éxito o el error con la salida del script.
- [x] Cablear el flujo completo: pantalla de resultado del export → botón → `POST
      /games/{gameId}/install-attract` → mensaje de éxito o error visible sin recargar.

## Tests

- [x] Regresión: stdout y stderr con bytes no UTF-8 no lanzan excepciones; conservar
      el resultado del código de salida tanto para éxito como para fallo y preservar UTF-8 válido.

- [x] Caso feliz: script que sale 0 → `InstallOut.ok == True`.
- [x] Caso límite: no hay export previo para ese juego → 409 con mensaje explícito.
- [x] Caso límite: `COINDOOR_ATTRACT_DIR` no configurado → 422 con mensaje explícito.
- [x] Caso de fallo: script que sale distinto de 0 → 409, y el mensaje incluye lo que
      imprimió el script (no un genérico).
- [x] Invariante: el endpoint nunca genera un export nuevo, solo instala el que ya existe
      en disco.

## Cierre

- [x] Validar contra todos los criterios de aceptación de `spec.md`.
- [x] Lint y tipos limpios (`ruff`, `mypy`, `tsc`).
- [x] `../../constitution/tech-stack.md` actualizado (§Límites duros, nueva variable de
      entorno documentada en `backend/CLAUDE.md`).
- [x] ADR creado: [`0021`](../../decisions/0021-instalar-bundle-por-subproceso.md).
- [x] Roadmap actualizado (`../../constitution/roadmap.md` §Dependencias fuera de este
      repo y tabla de fases).
- [x] `docs/` — no hay superficie pública nueva fuera de este repo que documentar; el
      instalador que se invoca ya está documentado del lado de `../attract`.
