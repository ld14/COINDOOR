# 004 · Dominio, contrato y datos mock — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

**Los datos primero, la lógica después.** `contract.json` y `fielddefs.json` se escriben
antes que cualquier función, porque son la fuente y no la consecuencia. Una vez que
existen, `completeness` en TypeScript y en Python son quince líneas cada una que recorren
la misma tabla.

La duplicación queda **acotada a la lógica** y prohibida en los datos. Es una elección
consciente: transpilar quince líneas costaría una cadena de build entera
([`ADR-0011`](../../decisions/0011-fielddefs-json-compartido.md) §Alternativa D), y un test
de paridad sobre el seed las mantiene alineadas por mucho menos.

Los deltas D1–D5 se aplican **acá y no después**. Corregir tipos cuando ya hay componentes
escritos contra la forma vieja es el doble de trabajo y deja restos.

## Implementación

1. `lib/domain/contract.json` — vendoreado de ATTRACT: qué assets existen, sus nombres
   exactos con su capitalización, extensiones aceptadas, campos que ATTRACT exige, y la
   versión. Con un `README` al lado que diga de dónde salió y cómo se actualiza.
2. `lib/domain/fielddefs.json` — política de COINDOOR: `key`, `label`, `ratio`, `required`
   por campo, más los campos de identidad y los mapeos explícitos hacia `contract.json`.
3. `lib/domain/types.ts` — los tipos de `data-model.md` §1 **con los deltas aplicados**.
   Importa `fielddefs.json` con `with { type: 'json' }` y deriva `ImageKey`, `VideoKey` y
   `TextKey` de ahí en vez de repetirlas.
4. `lib/domain/completeness.ts` — `missingRequired()` y `computeGameStatus()`, leyendo
   `fielddefs.json`.
5. `lib/domain/validation.ts` — esquemas zod: `absolutePath`, `hexColor`, `yearField`,
   `newSystemSchema`. Los mensajes son los literales de `data-model.md` §4.
6. `backend/lib/domain/completeness.py` — la gemela, leyendo **el mismo**
   `fielddefs.json`.
7. `backend/lib/domain/validation.py` — las mismas reglas en Pydantic.
8. `mocks/` — handlers de MSW y el seed de `data-model.md` §7, con los deltas aplicados.

## Decisiones

- **`fielddefs` es JSON, no TypeScript** — para que Python lo lea sin reescribirlo.
  Ver [`ADR-0011`](../../decisions/0011-fielddefs-json-compartido.md).
- **Los tipos se derivan del JSON, no se repiten** — si `ImageKey` se escribe a mano,
  agregar un campo al contrato exige tocar dos lugares y uno se olvida.
- **`status` no es un campo, es una función** — nunca se serializa
  ([`ADR-0008`](../../decisions/0008-persistencia-en-archivos.md)).
- **La política de COMPLETO es más estricta que el contrato, a propósito** — ATTRACT solo
  exige `title` y `x-formato`; COINDOOR exige lo que hace que un juego se vea bien.
  Ver `tech-stack.md` §Qué significa COMPLETO.
- **El test de paridad corre sobre el seed, no sobre datos inventados** — los diez juegos
  ya ejercitan los casos de borde; un generador aleatorio ejercitaría otros.
- **MSW y no un servidor mock aparte** — corre en el navegador y en Vitest con los mismos
  handlers, y desaparece solo cuando exista el backend real.

## Riesgos

- **`contract.json` no existe todavía.** ATTRACT no lo publica
  ([`ADR-0005`](../../decisions/0005-contrato-vendoreado-vs-politica-propia.md)). Hay que
  derivarlo a mano de `docs/CONVENCION.md` §1–§2 y de `library/arcade/media/goldnaxe/`, y
  dejar escrito de dónde salió cada entrada. **Es el bloqueante real de esta feature.**
- **`CONVENCION.md` sigue marcado como plantilla** y conserva huecos. Las secciones §1.2,
  §2, §3 y §4 tienen contenido verificable contra `goldnaxe`; el resto no. Verificar contra
  el código y los fixtures, nunca solo contra el documento.
- **Las dos implementaciones divergen igual.** El test de paridad las cubre sobre diez
  casos, no sobre todos. Si la lógica crece más allá de un bucle sobre una tabla, hay que
  replantear [`ADR-0011`](../../decisions/0011-fielddefs-json-compartido.md).
- **El seed queda desactualizado respecto de los deltas.** `Contra · vínculo de revista
  roto` ya no ejercita nada bajo D3, y el checklist de aceptación de
  `docs/claude_diseño/README.md` todavía lo menciona. Elegir el caso de borde de reemplazo
  es parte de esta feature, no un detalle.
