---
id: 0011
title: Publicar la política de completitud como JSON compartido entre TypeScript y Python
status: accepted
date: 2026-08-11
supersedes: null
superseded-by: null
tags: [data, frontend, backend]
---

# 0011 — Publicar la política de completitud como JSON compartido entre TypeScript y Python

## Contexto

[`ADR-0005`](0005-contrato-vendoreado-vs-politica-propia.md) separó dos archivos con
dueños distintos: `contract.json` (vendoreado de ATTRACT, nunca editado a mano) y
`fieldDefs.ts` (política de COINDOOR: `label`, `ratio`, `required`), atados por un test.

Eso resolvió la relación con ATTRACT. Pero al elegir Python para el backend
([`ADR-0007`](0007-fastapi-como-framework-backend.md)) aparece el mismo problema puertas
adentro, y `ADR-0005` no lo cubre porque cuando se escribió no había backend elegido.

El cliente calcula la completitud para dar feedback sin round-trip; el servidor la calcula
para hacerla cumplir. Está en `frontend-architecture.md` §6: *«El servidor valida lo
mismo; el cliente lo replica para dar feedback sin round-trip»*.

Si `fieldDefs` es un `.ts`, Python no puede leerlo, y la política —**qué hace que un juego
esté completo**, el corazón del producto— se escribe dos veces en dos lenguajes. Es
exactamente el fallo que `ADR-0001` existe para evitar con ATTRACT, ocurriendo entre el
front y el back del mismo repo.

## Decisión

**`fieldDefs` deja de ser código TypeScript y pasa a ser un archivo de datos:
`lib/domain/fielddefs.json`.** Lo importa TypeScript y lo lee Python.

```
lib/domain/
  contract.json      ← vendoreado de ATTRACT, versionado, nunca a mano (ADR-0005)
  fielddefs.json     ← política de COINDOOR: label, ratio, required
  types.ts           ← importa fielddefs.json (`with { type: 'json' }`) y deriva los tipos
  completeness.ts    ← lee fielddefs.json
backend/lib/domain/
  completeness.py    ← lee EL MISMO fielddefs.json
```

Se mantienen **dos implementaciones** de la regla —TypeScript y Python— y **una sola
fuente de datos**. La duplicación queda acotada a ~15 líneas de lógica idéntica en dos
lenguajes, sobre datos que no pueden divergir.

El test de `ADR-0005` no cambia y sigue siendo el que hace cumplir `ADR-0001`: ninguna
clave de `fielddefs.json` sin su asset en `contract.json`, ni al revés.

Se agrega un segundo test: **las dos implementaciones de `missingRequired` dan el mismo
resultado sobre los diez juegos del seed.** Sin él, la lógica diverge aunque los datos no.

## Alternativas consideradas

### A. Dejar `fieldDefs.ts` y reescribir la política en Python

- A favor: cada lado en su lenguaje natural, sin importar JSON ni derivar tipos.
- En contra: `required: true` queda escrito dos veces, en dos archivos que nadie obliga a
  coincidir.
- **Descartada porque:** es el mismo mecanismo de fallo que `ADR-0001` documenta con
  ATTRACT — *«las dos definiciones de COMPLETO divergen en silencio y el síntoma aparece
  en el gabinete, que es el peor lugar para enterarse»*. Acá el síntoma sería peor de
  encontrar: el formulario diría que el juego está listo y el export lo rechazaría, o al
  revés.

### B. Generar `fieldDefs.ts` desde una fuente Python en tiempo de build

- A favor: una sola fuente, tipos TypeScript nativos sin importar JSON.
- En contra: agrega un paso de build, y el frontend deja de poder trabajar sin el backend
  presente.
- **Descartada porque:** las fases 1 a 4 del roadmap desarrollan el frontend contra un
  mock server, sin backend. Un paso de generación desde Python los ataría desde el
  principio, justo cuando el backend todavía no existe.

### C. Que el backend sea la única autoridad y el cliente no calcule nada

- A favor: una sola implementación, cero riesgo de divergencia.
- En contra: cada tilde de un campo exigiría un round-trip para saber si el juego pasó a
  `ready`.
- **Descartada porque:** el diseño pide feedback inmediato y el indicador de faltantes
  siempre visible (UX §5.4). Además el cliente ya tiene el juego entero en memoria: pedir
  al servidor que le diga algo que puede calcular es latencia sin motivo.

### D. Compartir también la lógica, con Python transpilado o WASM

- A favor: una sola implementación de verdad.
- En contra: una cadena de build entera para reemplazar quince líneas de código.
- **Descartada porque:** el coste no guarda ninguna proporción con el problema. La lógica
  es un bucle sobre una lista; lo que de verdad diverge son los **datos**, y esos ya
  quedan compartidos.

## Consecuencias

**Positivas**

- La política de completitud tiene una sola fuente, y agregar o quitar un obligatorio es
  editar un archivo de datos.
- Coherencia con el resto de las decisiones: el contrato es un archivo, la política es un
  archivo, y cada juego es un archivo
  ([`ADR-0008`](0008-persistencia-en-archivos.md)).
- El frontend sigue pudiendo trabajar contra mocks, sin backend.

**Coste asumido**

- Los tipos TypeScript se derivan de un JSON importado en vez de estar escritos a mano.
  Con `as const` e `import ... with { type: 'json' }` el resultado es equivalente, pero
  es un patrón menos habitual de leer.
- Sigue habiendo dos implementaciones de la lógica. Se cubren con el test de paridad sobre
  el seed; no se eliminan.
- `data-model.md` §2 muestra `fieldDefs.ts` con su forma de código. Queda superado por
  este ADR, igual que los deltas D1–D5 superan otras partes del paquete de diseño.

**Qué habría que revisar si esto se replantea**

- Si el frontend y el backend dejaran de compartir repositorio, el archivo compartido
  necesitaría publicarse, y esto se parecería a `ADR-0001`.
- Si la política de COMPLETO terminara coincidiendo exactamente con lo que exige ATTRACT,
  `fielddefs.json` se queda solo con etiquetas y ratios — la misma señal que ya anota
  `ADR-0005`.

## Referencias

- [`ADR-0005`](0005-contrato-vendoreado-vs-politica-propia.md) — la separación que este ADR precisa.
- [`ADR-0001`](0001-contrato-coindoor-attract.md) — ninguna regla se escribe dos veces.
- `docs/claude_diseño/data-model.md` §2 y §3 — `fieldDefs` y `completeness` tal como los propone el diseño.
- `spec/constitution/frontend-architecture.md` §Reglas de dominio en el cliente.
