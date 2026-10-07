# 017 · Objetivo de la guía, sugerido por IA — Plan

_Cómo se implementa lo descrito en `spec.md`._

## Enfoque

`objetivo` es un campo de texto más, declarado en `fielddefs.json` (ADR-0011). Eso reutiliza
sin código nuevo la API de campos, las sugerencias, la procedencia, la selección del export y
la validación de claves. Lo nuevo es un prompt, una fila en la tabla de proveedores y un
bloque en la ficha. Es la misma vía que `sinopsis`, que es lo pedido.

## Implementación

1. `frontend/src/lib/domain/fielddefs.json` — `texts[]` suma `objetivo` (`required: false`,
   `contractField: "guia"`, `maxLength: 600`). `contract.json` ya lista `guia` (ver 016).
2. `backend/lib/providers/ia/prompts/objetivo.v1.md` — prompt.
3. `backend/lib/providers/ia/generador.py` — `objetivo` en `CAMPOS`; `_validate_shape`
   rechaza vacío, `DESCONOCIDO` y exceso de longitud.
4. `backend/lib/providers/registro.py` — `"objetivo": ("ia_primary", "ia_backup")`.
5. `backend/bundle/datajson.py` y `seleccion.py` — `build_guia` lee `texts.objetivo`; se
   quita la clave de selección `guia` (la fila es la del propio texto) y `GuiaField`.
6. Frontend: `TextSection` con segundo campo, `SUGGESTABLE_LABELS`/`suggestionStatus`,
   `types.ts` con `texts` parcial para claves opcionales, `completeness.ts` tolerante.

## Decisiones

- **Campo de texto en `fielddefs` en vez de un bloque `guia` propio en `StoredGame`** —
  reutiliza todo el flujo de sinopsis; reemplaza el `GuiaField` de 016.
- **Solo IA, sin ArcadeDB** — ArcadeDB no tiene un «objetivo»; su sinopsis es otro texto.
- **`DESCONOCIDO` en vez de dejar al modelo improvisar** — un campo vacío es mejor que uno
  falso (misma idea que ADR-0019 para trucos).
- **`revision` deriva del estado del campo** — `manual` = una persona lo escribió o guardó.

## Riesgos

- **El modelo responde con seguridad sobre un juego que no conoce** — el modal exige una
  acción humana y la revisión queda en `borrador` hasta que se guarda a mano.
- **Fichas con `texts` sin `objetivo`** — el tipo es parcial y todo acceso es tolerante.
