# 017 · Objetivo de la guía, sugerido por IA — Tareas

## Implementación

- [x] `fielddefs.json` — campo `objetivo` (opcional, `contractField: "guia"`, 600 caracteres).
- [x] Prompt `objetivo.v1.md`, `generador.py` (validación) y `registro.py` (solo IA).
- [x] `datajson.py::build_guia` desde `texts.objetivo`; sin `GuiaField` ni fila `guia`.
- [x] Frontend: segundo campo en `TextSection`, etiquetas del modal, tipos y mocks.

## Tests

- [x] Backend: sugerencia válida, vacía, `DESCONOCIDO` y larga; solo consulta a la IA;
      guardar y borrar por el servicio de campos; export con y sin objetivo; `revision`;
      la fila «Objetivo» en la selección.
- [x] Ficha anterior sin `texts.objetivo`: `completeness.ts` y la ficha lo toleran.
- [x] Frontend: guardar el objetivo sin tocar la sinopsis.
- [ ] Frontend: Sugerir abre el modal del objetivo (cubierto por el modal genérico; sin test propio).

## Cierre

- [x] pytest (283), vitest (59 de 60) y `tsc` limpios. La falla restante es
      `validation.test.ts` («valida sistema nuevo»), anterior a esta feature.
- [ ] Probar Sugerir con un modelo real y revisar el candidato (necesita claves `AI_*`).
- [ ] Marcar «implementada» en `spec.md` y pasar a «Hecho» en `../../constitution/roadmap.md`.
