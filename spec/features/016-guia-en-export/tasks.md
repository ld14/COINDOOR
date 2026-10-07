# 016 · Bloque `guia` en el export — Tareas

## Implementación

- [x] Confirmar la forma de `guia` en ATTRACT (`doctor.py::_chk_guia_bloque`): `objetivo`
      obligatorio; `acciones[]` con `control` y `action`; el resto opcional o AVISO.
- [x] `objetivo` sale de `texts.objetivo` (feature [017](../017-objetivo-guia-ia/spec.md)); sin
      bloque `guia` propio en el modelo, así que las fichas viejas se leen igual.
- [x] `datajson.py::build_guia` y su inclusión en `build_datajson`.
- [x] Inclusión: la fila «Objetivo» de «qué incluir»; `guia` no viaja sin ese texto.
- [x] Reemplazar `frontend/src/lib/domain/contract.json` por el publicado por ATTRACT
      (`python -m attract.contrato`, ADR-0039 de ATTRACT). Suma `guia`, `gallery`,
      `x-procedencia` y `.mov`. `contract-policy` y `parity` pasan (4 tests).
- [ ] Entrada de `objetivo`: feature [017](../017-objetivo-guia-ia/spec.md).

## Tests

- [x] `acciones` idénticas a `button_list`; `color` vacío se omite.
- [x] Sin `objetivo` o no incluida → sin `guia`.
- [x] `button_list` vacío → sin `acciones`.
- [x] La sinopsis no aparece en el bloque; sin `perifericos`, `fuentes` ni `modo`.
- [x] `players` no entero limpio → sin `multijugador`.
- [x] Ficha anterior sin `guia` sigue leyéndose.
- [ ] `attract doctor` sobre un zip real con `guia` → sin ERROR.

## Cierre

- [x] pytest (275 pasan) y ruff limpio en los archivos tocados.
- [ ] Corregir el comentario de `tests/test_arcadedb.py:389` (ADR-0002 no habla de `cabinet`).
- [ ] Marcar "implementada" y mover a "Hecho" en `../../constitution/roadmap.md`.
