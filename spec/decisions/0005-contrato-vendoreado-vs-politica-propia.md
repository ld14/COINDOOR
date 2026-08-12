---
id: 0005
title: Separar el contrato vendoreado de la política de completitud propia
status: accepted
date: 2026-08-11
supersedes: null
superseded-by: null
tags: [data, frontend]
---

# 0005 — Separar el contrato vendoreado de la política de completitud propia

## Contexto

[`ADR-0001`](0001-contrato-coindoor-attract.md) decide que el contrato de ATTRACT se
consume como dato versionado y **nunca se replica en código**. El paquete de diseño define
`lib/domain/fieldDefs.ts` escrito a mano, con los campos obligatorios codificados como
`required: true`. A primera vista se contradicen.

Mirando qué hay realmente en ese archivo, la contradicción es más chica y más precisa:

| Contenido | ¿Lo posee el contrato de ATTRACT? |
|---|---|
| `required: true/false` | **No.** Es la política de COMPLETO de COINDOOR, deliberadamente más estricta: ATTRACT solo exige `title` y `x-formato` |
| `key` / `label` (`caratula` → "Carátula") | **No.** Vocabulario de la UI de COINDOOR |
| `ratio` (`3:4`) | **No.** Ayuda visual de la preview |
| Qué assets existen y su nombre en disco (`boxFront`) | **Sí** |
| Capitalización exacta y extensiones aceptadas | **Sí** |
| Qué campos exige ATTRACT | **Sí** |

O sea que la mayor parte de `fieldDefs.ts` no es el contrato. Lo que sí lo es, hoy está
duplicado sin que nada lo vigile.

## Decisión

**Dos archivos con dueños distintos.**

- **`lib/domain/contract.json`** — vendoreado desde ATTRACT, versionado, **nunca editado a
  mano**. Contiene lo que el contrato posee: qué assets existen, sus nombres exactos en
  disco, extensiones aceptadas y los campos que ATTRACT exige.
- **`lib/domain/fieldDefs.ts`** — política de COINDOOR, escrita a mano. Etiquetas, ratios y
  `required`. Referencia las claves de `contract.json`; no las redefine.

**Y un test que falla cuando divergen**: cada clave de `fieldDefs.ts` debe existir en
`contract.json`, y cada asset de `contract.json` debe estar contemplado en `fieldDefs.ts`.
Sin huérfanos en ninguna dirección.

Eso es lo que hace cumplir `ADR-0001` de verdad. La separación sola no alcanza: sin el
test, los dos archivos se desincronizan igual, solo que más despacio.

### Precisión sobre ADR-0001

"No replicar el contrato" aplica a **lo que el contrato posee**. La definición de COMPLETO
es de COINDOOR —más estricta a propósito, ver `tech-stack.md`— y vive en este repo por
derecho propio, no por comodidad.

## Alternativas consideradas

### A. Generar todo `fieldDefs.ts` desde el contrato

- A favor: una sola fuente, cero posibilidad de divergencia.
- En contra: obliga a que el contrato de ATTRACT conozca `label`, `ratio` y la política de
  completitud de COINDOOR.
- **Descartada porque:** contamina el contrato de otro proyecto con decisiones de interfaz
  de este. ATTRACT no tiene por qué saber que a `boxFront` acá le decimos "Carátula" ni que
  exigimos póster cuando su propia cadena de fallback lo hace opcional.

### B. Bajar el contrato en runtime desde ATTRACT

- A favor: siempre fresco, sin versión que sincronizar.
- En contra: exige que ATTRACT esté accesible cuando el formulario valida.
- **Descartada porque:** contradice que cargar y editar funcionen sin red
  (`tech-stack.md` §Límites duros). El formulario tiene que decir "falta la marquesina" con
  el cable desenchufado.

### C. Dejarlo a mano y confiar en `attract doctor` al exportar

- A favor: cero trabajo, es el estado actual del diseño.
- En contra: el desajuste se descubre al final, cuando el juego ya está cargado entero.
- **Descartada porque:** es el estado que el banner amarillo del diseño ("la copia local
  del contrato puede estar desactualizada") intenta parchear con un aviso. Un aviso
  permanente que el usuario no puede accionar es ruido, no una solución.

## Consecuencias

**Positivas**

- La divergencia con ATTRACT falla en CI, no en el gabinete.
- COINDOOR puede endurecer su definición de COMPLETO sin tocar nada de ATTRACT.
- Actualizar el contrato es reemplazar un archivo y ver si el test pasa.

**Coste asumido**

- Hay que traer `contract.json` a mano hasta que ATTRACT lo publique
  ([`ADR-0001`](0001-contrato-coindoor-attract.md) §Qué implica de cada lado).
- Dos archivos donde el diseño proponía uno.

**Qué habría que revisar si esto se replantea**

- Si la política de COMPLETO de COINDOOR terminara coincidiendo exactamente con lo que
  exige ATTRACT, `fieldDefs.ts` se queda solo con etiquetas y ratios, y conviene revisar
  si sigue justificando ser un archivo aparte.

## Referencias

- [`ADR-0001`](0001-contrato-coindoor-attract.md) — el contrato como dato versionado.
- `docs/claude_diseño/data-model.md` §2 — `fieldDefs.ts` tal como lo propone el diseño.
- `spec/constitution/tech-stack.md` §Qué significa COMPLETO.
