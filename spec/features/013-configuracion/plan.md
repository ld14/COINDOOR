# 013 · Configuración — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Mismo patrón que `SystemsStore`/`sistemas.json`: un `ConfigStore` que lee y escribe
`configuracion.json` bajo `data_dir` con `store/archivo.py` (atómico, migración por
`version`). La validación de ruta absoluta reutiliza
`lib/domain/validation.py::validate_absolute_path`, la misma que ya usa Sistemas — nada
nuevo que mantener.

El backend deja de leer `COINDOOR_ATTRACT_DIR` de `Settings`: `ExportService.install()`
pasa a resolver `attract_dir` desde `ConfigStore`. Una sola fuente de verdad para ese
valor, leída en cada pedido (no cacheada al arrancar como hace `pydantic-settings` con
`.env`), que es justo lo que permite aplicar el cambio sin reiniciar.

El frontend copia la estructura de `Sistemas.tsx` (TanStack Query, no `useEffect` +
`fetch` a mano) en vez de la de `ExportPage.tsx`, que es anterior a esa regla.

## Implementación

1. `backend/config.py` — se saca `attract_dir` (era de
   [`ADR-0021`](../../decisions/0021-instalar-bundle-por-subproceso.md), reemplazado por
   este ADR). Se agrega `Settings.config_path -> data_dir/configuracion.json`.
2. `backend/store/config.py` (nuevo) — `ConfigDocument(version, attractDir: str | None)`
   y `ConfigStore` con `get() -> ConfigOut`, `set_attract_dir(value) -> ConfigOut`,
   `attract_dir() -> Path | None` (para el consumidor interno, no la API).
3. `backend/services/config.py` (nuevo) — `ConfigService`: valida ruta absoluta (o
   vacía, que limpia) antes de delegar en el store, mismo criterio que
   `services/systems.py::create`.
4. `backend/api/schemas.py` — `ConfigOut(attractDir: str | None)`,
   `ConfigPatch(attractDir: str = "")`.
5. `backend/api/config.py` (nuevo) — `GET /api/config`, `PATCH /api/config`. Registrar en
   `backend/main.py`.
6. `backend/services/export.py::ExportService.install()` — cambia
   `self.settings.attract_dir` por `ConfigStore(self.settings.config_path).attract_dir()`.
7. `frontend/src/lib/api/config.ts` (nuevo) — `getConfig()`, `updateConfig(attractDir)`.
8. `frontend/src/hooks/useConfig.ts` (nuevo) — `useQuery(['config'], getConfig)`.
9. `frontend/src/pages/Configuracion.tsx` (nuevo) — mismo layout que `Sistemas.tsx`
   (`ReadPages.module.css`, sin CSS nuevo).
10. `frontend/src/App.tsx`, `MenuBar.tsx`, `StatusBar.tsx` — ruta `/configuracion`, ítem
    de menú, atajo `F5`.

## Decisiones

- **Archivo propio en vez de seguir en `.env`** — ver
  [`ADR-0022`](../../decisions/0022-configuracion-no-sensible-en-archivo-propio.md).
- **Sin credenciales en esta pantalla** — ver `ADR-0022` §Alternativa B.
- **Validación por rechazo (422), no por bandera `valid`/`errorMsg` en el registro** —
  mismo criterio que `SystemsService.create()` ya aplica para `launchCmd`: se prueba en
  su test `test_systems_create_rejects_relative_launch`.

## Riesgos

- **Quien ya configuró `COINDOOR_ATTRACT_DIR` en su `.env`** dejará de tener efecto sin
  aviso en pantalla — se documenta en `backend/CLAUDE.md` y en el `spec.md` de esta
  feature, no se agrega una migración automática por un solo caso conocido (esta misma
  sesión).
