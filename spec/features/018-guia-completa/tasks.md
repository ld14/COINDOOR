# 018 · Guía completa — Tareas

## Implementación

- [x] `fielddefs.json` — `primerosPasos`, `reglasEsenciales`, `modo` (opcionales, `guia`).
- [x] `CabinetInfo.nplayers` y su carga desde ArcadeDB, también en fichas con gabinete ya
      cargado (se completa solo ese dato, sin pisar lo demás).
- [x] `lib/domain/guia.py` y `build_guia(game, incluir)` — `perifericos`, listas, `modo`,
      `revision` combinada.
- [x] Prompts `primerosPasos`, `reglasEsenciales` y `modo`; validadores por campo; filas de
      proveedores (solo IA); contexto de la ficha con los jugadores.
- [x] Frontend: textos de la guía en la ficha y `DosSelect` para `modo`.
- [x] `guia_checklist` + `GameOut.guiaChecklist` y el panel «Cómo se juega — checklist».
- [x] El modal distingue «sin resultados» de «error de la fuente» y avisa el motivo.

- [x] `problema_texto` (placeholder y nombre interno) usado por export, selección y checklist.
- [x] Migración v2 y `version = 2` por defecto.
- [x] Motivo de «no disponible» en la selección, en el error del export y en `ExportPage`.
- [x] Prompts: nombre comercial, nunca el romset.

## Tests

- [x] Mapeo de controles a `perifericos` (dial, joystick, trackball, spinner, desconocido).
- [x] Listas: viñetas, numeración y líneas vacías; incluir / no incluir; `revision` combinada.
- [x] `modo`: `alt` → `individual`; `sim` → vacío; el elegido gana; fuera de vocabulario se ignora.
- [x] IA: líneas limpias, `DESCONOCIDO`, demasiadas líneas, línea larga, modo fuera de vocabulario.
- [x] Ficha anterior sin campos nuevos exporta igual; precarga completa `nplayers`.
- [x] Placeholder (una línea basta, mayúsculas, viñetas), nombre interno (con y sin coincidencia
      con el título, palabra completa), migración (una sola vez, ficha nueva, `revision`).
- [x] API: un texto de ejemplo no se ofrece, se rechaza con motivo y nunca llega al zip.
- [x] Checklist: listo / falta / obligatorio, motivos, manual vs sugerido, ficha sin gabinete.
- [x] Frontend: componente del checklist, «no se pudo generar» y `deriveFase`.
- [x] Frontend: guardar primeros pasos y elegir el modo, sin tocar las reglas.

## Cierre

- [x] pytest (352), vitest (69 de 70) y `tsc` limpios. La falla restante es
      `validation.test.ts`, anterior a esta feature.
- [x] Caso real: la ficha de Arkanoid (`arkanoidu`) produce un `guia` que el chequeo
      `_chk_guia_bloque` de ATTRACT acepta sin errores ni avisos.
- [ ] Re-ejecutar la precarga de ArcadeDB en Arkanoid (para guardar `nplayers`), cargar o
      sugerir los textos nuevos, exportar y reinstalar en ATTRACT.
- [ ] Mover a «Hecho» en `../../constitution/roadmap.md`.
