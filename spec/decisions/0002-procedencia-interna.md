---
id: 0002
title: Guardar la procedencia de cada campo solo dentro de COINDOOR
status: accepted
date: 2026-08-10
supersedes: null
superseded-by: null
tags: [data]
---

# 0002 — Guardar la procedencia de cada campo solo dentro de COINDOOR

## Contexto

COINDOOR llena cada campo de dos maneras: lo carga el usuario a mano, o lo trae una
fuente externa (scraping, IA) y el usuario acepta la sugerencia. Saber cuál fue es
necesario para la regla que sostiene la confianza en la herramienta: **una sugerencia no
puede pisar en silencio algo que el usuario cargó a mano.**

ATTRACT decidió lo contrario, y lo decidió a conciencia:

> **§3.1** — *"no se distingue. Todos los campos son iguales, sin importar quién o qué
> los escribió. Riesgo aceptado a propósito."*
>
> **§3.3** — *"Todo se pisa siempre. El reproceso más reciente gana, sin excepción. La
> mitigación, dado este contrato, no es técnica sino de proceso — revisar el resultado
> de cualquier reproceso antes de aceptarlo."*

Hay un rastro de la decisión anterior: `fixtures/arcade/metadata.pegasus.txt` conserva
`x-procedencia: manual` en `mok` y `sf2ce`, que hoy no lee nada y quedó a propósito como
ejemplo por si la decisión se revisita.

Nota: [`ATTRAC-015 plan.md`](../../docs/attract/ATTRAC-015-carga-guiada/plan.md)
§Riesgos propone mitigar la metadata inventada "marcando procedencia (`CONVENCION`
§3.1)". **Cita mal el contrato**: §3.1 decide justamente no marcarla. No es apoyo para
este ADR.

## Decisión

**La procedencia es un dato interno de COINDOOR y no viaja a ATTRACT.**

COINDOOR guarda por campo quién lo escribió y desde qué fuente, y lo usa para proteger
el trabajo manual dentro de su propia interfaz. El export produce los archivos que el
contrato define y **nada más**: ni `x-procedencia`, ni campos paralelos.

Con esto, COINDOOR pasa a ser la implementación concreta de la mitigación que
`CONVENCION` §3.3 pide como "de proceso": revisar antes de aceptar deja de depender de
la disciplina de una persona y pasa a ser una confirmación explícita en pantalla.

## Alternativas consideradas

### A. Proponer que ATTRACT revierta §3.1 y acepte `x-procedencia`

- A favor: una sola verdad sobre el origen, útil si algún día ATTRACT reprocesa solo.
- En contra: cambia un contrato ya decidido de otro proyecto, con su propio riesgo
  aceptado, para un beneficio que hoy nadie consume.
- **Descartada porque:** el reproceso automático que haría falta (`attract ingest` sobre
  un juego ya cargado) todavía no existe. Cambiar el contrato ahora es pagar por una
  garantía que ningún código va a leer. Si ese reproceso aparece, esta alternativa vuelve
  a estar sobre la mesa — y el `x-procedencia` de los fixtures muestra cómo se vería.

### B. Abandonar la procedencia también en COINDOOR, por coherencia con ATTRACT

- A favor: un solo modelo mental en las dos aplicaciones, menos que guardar.
- En contra: sin procedencia no hay forma de que la herramienta distinga una carátula
  que el usuario eligió con cuidado de una que llegó de un scraper.
- **Descartada porque:** rompe la regla central del producto. Un usuario que ve su
  trabajo pisado por una sugerencia deja de apretar el botón de sugerir, y ese botón es
  el diferencial de COINDOOR. La coherencia con ATTRACT no vale ese precio: son
  aplicaciones con problemas distintos.

### C. Exportar la procedencia en un archivo lateral fuera del contrato

- A favor: el dato sobrevive al export sin tocar el contrato de ATTRACT.
- En contra: un archivo que ATTRACT no valida ni lee, viajando dentro de su librería.
- **Descartada porque:** `attract doctor` recorre el árbol y marca lo que no reconoce.
  Un archivo huérfano en la librería es basura que ensucia la validación, y para
  recuperarlo hay que volver a COINDOOR, que ya lo tiene.

## Consecuencias

**Positivas**

- El export produce exactamente lo que el contrato define. Cero divergencia.
- COINDOOR protege el trabajo manual sin pedirle nada a ATTRACT.
- La mitigación "de proceso" de §3.3 queda implementada en una herramienta.

**Coste asumido**

- La procedencia se pierde al exportar. Si alguien edita la librería a mano, por fuera
  de COINDOOR, no hay forma de saber qué tocó.
- COINDOOR y la librería pueden divergir si se editan por separado. Este ADR no resuelve
  la reimportación; hoy el flujo es de un solo sentido.

**Qué habría que revisar si esto se replantea**

- Si ATTRACT implementa reproceso automático (`ingest` sobre juegos ya cargados), el
  riesgo que §3.1 acepta se vuelve concreto y conviene reabrir la alternativa A.
- Si aparece la necesidad de reimportar desde la librería hacia COINDOOR, la procedencia
  perdida pasa a ser un problema real y no un coste teórico.

## Referencias

- ATTRACT `docs/CONVENCION.md` §3.1, §3.2, §3.3.
- ATTRACT `fixtures/arcade/metadata.pegasus.txt` — `x-procedencia: manual` vestigial.
- [`ADR-0001`](0001-contrato-coindoor-attract.md) — contrato COINDOOR ↔ ATTRACT.
- [`docs/ux/requerimiento-funcional.md`](../../docs/ux/requerimiento-funcional.md) §5.4, §5.5.
