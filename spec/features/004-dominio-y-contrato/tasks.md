# 004 · Dominio, contrato y datos mock — Tareas

_Checklist accionable derivada del `plan.md`._

## Antes de tocar código

- [x] **Conseguir `contract.json`.** Hecho cuando: existe el archivo con su versión, y una
      nota que dice si lo publicó ATTRACT o se derivó a mano de `CONVENCION` §1–§2 y de
      `library/arcade/media/goldnaxe/`. **Bloquea el resto de la feature.**
- [x] Elegir el caso de borde que reemplaza a `Contra · vínculo de revista roto` en el
      seed. Bajo el delta D3 ese estado no existe. Hecho cuando: está escrito qué ejercita
      el juego nuevo y por qué ninguno de los otros nueve ya lo cubre.
- [x] Anotar el hueco de `identitySource` sin bloquear esta feature. Hecho cuando:
      `types.ts` no impide que feature 001 decida el mapeo de export a `identidad.origen`.
      Ver `tech-stack.md` §Contradicciones abiertas.

## Implementación

- [x] `lib/domain/contract.json` + su `README`. Hecho cuando: dice de dónde salió cada
      entrada y cómo se actualiza, y **nadie lo edita a mano** después de vendorearlo.
- [x] `lib/domain/fielddefs.json` — campos con `label`, `ratio`, `required`; identidad; y
      mapeos explícitos UI ↔ contrato. Hecho cuando: no redefine ninguna clave que ya esté
      en `contract.json`.
- [x] `lib/domain/types.ts` con los deltas aplicados. Hecho cuando: `ImageKey`, `VideoKey`
      y `TextKey` se **derivan** de `fielddefs.json`, no se escriben a mano.
- [x] Delta D1 — `ReviewField` y `CheatsField` como estructuras; `texts` queda solo con
      `sinopsis`. Hecho cuando: `review` y `cheats` ya no son `TextField` en ningún lado,
      y `Reseña` / `Trucos` quedan solo como labels de UI.
- [x] Delta D2 — `accentValue` y `accent2Value`. Hecho cuando: solo el primario aparece en
      `missingRequired`.
- [x] Delta D3 — quitar `broken` de `MagazineLink` y del seed.
- [x] `lib/domain/completeness.ts` — `missingRequired()` y `computeGameStatus()`.
- [x] `lib/domain/validation.ts` — los cuatro esquemas zod con los mensajes literales.
- [x] `backend/lib/domain/completeness.py` leyendo **el mismo** `fielddefs.json`. Hecho
      cuando: no hay ninguna lista de campos escrita en Python.
- [x] `backend/lib/domain/validation.py` — las mismas reglas en Pydantic.
- [x] `mocks/handlers.ts` + el seed de los diez juegos y los cuatro sistemas.

## Tests

- [x] **Contrato ↔ política:** assets contra assets, y campos contra campos/datos ricos con
      mapeo explícito UI ↔ contrato. Es el test que exige
      [`ADR-0005`](../../decisions/0005-contrato-vendoreado-vs-politica-propia.md).
- [x] **Paridad TS ↔ Python:** `missingRequired` da el mismo resultado sobre los diez
      juegos del seed. Sin este, la lógica diverge aunque los datos no.
- [x] Un juego al que solo le falta la marquesina es `ready`. **Marquesina, logo, captura,
      video, reseña, trucos, manuales y revista no bloquean nunca.**
- [x] Un juego completo **con** un error de formato es `error`, no `ready`.
- [x] Un juego con `errors` y además faltantes es `error`: la prioridad manda.
- [x] `review` con `score: 88` y solo tres de las seis categorías **no** cuenta como
      faltante. Vacío es un valor legítimo.
- [x] `score: null` y `cats: {}` es «no hay reseña», y tampoco bloquea.
- [x] Un grupo de trucos con nombre inventado sobrevive el ida y vuelta con su nombre.
- [x] `launchCmd` relativo → inválido. `/opt/mame/mame64` y `C:\Emu\bin.exe` → válidos.
- [x] `year` con `197X` → error de formato con el mensaje literal del contrato.
- [x] Un HEX inválido no se acepta y muestra su error.
- [x] El seed cubre los tres estados y los cuatro sistemas, uno con cabecera inválida.

## Cierre

- [x] Validar contra todos los criterios de aceptación de `spec.md`.
- [x] `npm run build`, `npm test`, `uv run pytest`, `uv run mypy backend/lib` y
      `uv run ruff check .` limpios.
- [x] Anotar en `spec/` qué quedó superado por los deltas. No editar
      `docs/claude_diseño/`, que se consulta y no se edita.
- [x] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.
