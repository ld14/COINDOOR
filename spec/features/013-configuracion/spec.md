# 013 · Configuración

**Estado:** implementada

Decisión en [`ADR-0022`](../../decisions/0022-configuracion-no-sensible-en-archivo-propio.md).

## Qué hace

**Agrega** una pantalla `/configuracion` donde se edita la configuración no sensible de
esta instalación de COINDOOR — hoy, la ruta local del checkout de ATTRACT que usa
"Cargar en ATTRACT" ([012](../012-instalar-en-attract/spec.md)). Se guarda en
`configuracion.json` y se aplica sin reiniciar el proceso.

**No** incluye credenciales: las claves de IA y del buscador (`AI_PRIMARY_*`,
`AI_BACKUP_*`, `SEARCH_*`) siguen solo en `.env`, fuera de cualquier pantalla — ver
[`ADR-0022`](../../decisions/0022-configuracion-no-sensible-en-archivo-propio.md)
§Alternativa B.

## Por qué

`COINDOOR_ATTRACT_DIR` nació como variable de `.env`
([`ADR-0021`](../../decisions/0021-instalar-bundle-por-subproceso.md)), pero cambiarla
significa editar un archivo a mano y reiniciar el proceso — la misma fricción que se
resolvió para el paso de instalar, ahora trasladada a configurarlo. Una pantalla y un
archivo propio (mismo patrón que `sistemas.json`) lo resuelven sin ese costo.

## Criterios de aceptación

- [x] Dado `configuracion.json` inexistente, `GET /api/config` devuelve `{"attractDir":
      null}` sin fallar (se crea con default al primer acceso, igual que
      `sistemas.json`).
- [x] Dado un valor absoluto (`/mnt/d/Juegos/attract`), `PATCH /api/config` con
      `{"attractDir": "..."}` lo guarda y el siguiente export/instalación lo usa sin
      reiniciar el proceso.
- [x] Dado un valor no absoluto, `PATCH /api/config` responde 422 con el mismo mensaje
      que ya usa la validación de `launchCmd` en Sistemas (`ABSOLUTE_PATH_MESSAGE`).
- [x] Dado `{"attractDir": ""}`, se limpia el valor (`attractDir` vuelve a `null`).
- [x] La pantalla `/configuracion` carga el valor guardado, permite editarlo y guardar,
      y muestra el error de validación si el backend lo rechaza.
- [x] `POST /games/{id}/install-attract` usa el valor de `configuracion.json`, no una
      variable de entorno — `COINDOOR_ATTRACT_DIR` deja de leerse.

## Textos de la interfaz

No están en `docs/claude_diseño/`. Estos son los literales:

- Título: `Configuración` · subtítulo: `Ajustes de esta instalación de COINDOOR. Las
  credenciales de IA y del buscador van en .env, no acá.`
- Sección: `ATTRACT` · campo: `Ruta de ATTRACT` · ayuda: `Checkout local de ATTRACT.
  Necesaria para "Cargar en ATTRACT" al exportar.`
- Botón: `Guardar` · confirmación: `Guardado.`

## Fuera de alcance

- **Credenciales de IA/buscador en la UI.** Ver `ADR-0022`. Si se pide después, es un
  ADR nuevo, no una ampliación silenciosa de esta pantalla.
- **Editar sistemas desde acá.** Sistemas ya tiene su propia pantalla
  ([003](../003-base-frontend/spec.md)); esta feature no la reemplaza ni la mueve.
- **Migrar automáticamente `COINDOOR_ATTRACT_DIR` de `.env` a `configuracion.json`.**
  Quien ya la tenía configurada la vuelve a cargar una vez desde la pantalla.
