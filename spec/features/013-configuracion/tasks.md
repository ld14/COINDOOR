# 013 · Configuración — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas;
marca `[x]` al completarlas._

## Implementación

- [x] `backend/config.py` — sacar `attract_dir`, agregar `config_path`. Hecho cuando:
      `Settings(data_dir=...).config_path == data_dir / "configuracion.json"`.
- [x] `backend/store/config.py::ConfigStore`. Hecho cuando: `get()` sobre un archivo
      inexistente lo crea con `attractDir: null` sin fallar; `set_attract_dir()` persiste
      atómico y `attract_dir()` devuelve `Path | None` para el consumidor interno.
- [x] `backend/services/config.py::ConfigService`. Hecho cuando: ruta no absoluta ->
      `BadRequest` con `ABSOLUTE_PATH_MESSAGE`; cadena vacía -> limpia el valor.
- [x] `backend/api/schemas.py` — `ConfigOut`, `ConfigPatch`.
- [x] `backend/api/config.py` + registro en `backend/main.py`. Hecho cuando: `GET
      /api/config` y `PATCH /api/config` responden con `ConfigOut`.
- [x] `backend/services/export.py::ExportService.install()` usa `ConfigStore`, no
      `Settings.attract_dir`. Depende de: tarea anterior.
- [x] `frontend/src/lib/api/config.ts` + `hooks/useConfig.ts`.
- [x] `frontend/src/pages/Configuracion.tsx`. Hecho cuando: carga el valor guardado,
      permite editarlo, muestra "Guardado." al éxito y el error del backend al fallar.
- [x] `App.tsx` + `MenuBar.tsx` + `StatusBar.tsx` — ruta, ítem de menú y atajo `F5`.
- [x] Cablear el flujo completo: pantalla → `PATCH /api/config` → siguiente "Cargar en
      ATTRACT" usa el valor nuevo sin reiniciar el backend.

## Tests

- [x] Caso feliz: `PATCH` con ruta absoluta, `GET` la devuelve.
- [x] Caso límite: `configuracion.json` no existe todavía → `GET` no falla.
- [x] Caso límite: `PATCH` con `""` limpia `attractDir`.
- [x] Caso de fallo: `PATCH` con ruta relativa → 422, `ABSOLUTE_PATH_MESSAGE`.
- [x] `install-attract` deja de depender de `COINDOOR_ATTRACT_DIR`: el test de la
      feature 012 se actualiza para configurar vía `PATCH /api/config`.

## Cierre

- [x] Validar contra todos los criterios de aceptación de `spec.md`.
- [x] Lint y tipos limpios (`ruff`, `mypy`, `tsc`, `eslint`).
- [x] `../../constitution/tech-stack.md` actualizado (Configuración deja de ser solo
      `.env`).
- [x] `backend/CLAUDE.md` — tabla de variables de entorno: sacar `ATTRACT_DIR`.
- [x] ADR creado: [`0022`](../../decisions/0022-configuracion-no-sensible-en-archivo-propio.md).
- [x] `../012-instalar-en-attract/spec.md` y `plan.md` actualizados para reflejar que
      `attractDir` viene de Configuración, no de una variable de entorno.
- [x] Roadmap actualizado.
