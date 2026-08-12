---
id: 0012
title: Verificar el export invocando attract doctor como subproceso, sin parsear su salida
status: accepted
date: 2026-08-11
supersedes: null
superseded-by: null
tags: [backend, proceso]
---

# 0012 — Verificar el export invocando `attract doctor` como subproceso, sin parsear su salida

## Contexto

[`ADR-0001`](0001-contrato-coindoor-attract.md) decide que **la CLI de ATTRACT es la
autoridad final**: tras armar el staging, COINDOOR corre `attract doctor` y si contradice
al formulario, manda la CLI. La feature 001 lo convierte en etapa del export —
*«ATTRACT verificando…»*, antes de comprimir— y exige que el veredicto de rechazo
**nombre el archivo y el motivo concreto**.

Falta decidir **cómo se invoca**. Leyendo el código de ATTRACT aparecen dos hechos que
condicionan la respuesta:

1. **`doctor` no tiene salida legible por máquina.** `doctor.main()` imprime texto para
   humanos y devuelve `0 if rep.ok else 1`. No hay `--json`.
2. **La estructura sí existe, pero no se expone por CLI.** `doctor.revisar()` devuelve un
   `Reporte` con `errores` y `avisos` separados, y `mcp_server.py` lo serializa a `dict` —
   pero solo a través de MCP.

`ADR-0001` §Alternativa C ya descartó MCP **para el problema de la validación en vivo**, y
dejó explícitamente abierto su uso al exportar: *«Sigue en pie como forma de invocar
`doctor` al exportar — es una decisión de implementación, no de contrato»*. Este ADR cierra
esa decisión.

## Decisión

**COINDOOR invoca `attract doctor <staging>` como subproceso, usa su código de salida como
veredicto, y muestra su `stdout` literal como detalle. No lo parsea.**

- **Veredicto:** `returncode == 0` → verificado. Distinto de 0 → rechazado, y **no se
  genera el `.zip`** (feature 001: un bundle inválido circulando es peor que un export que
  no ocurre).
- **Detalle:** el `stdout` tal cual, en el recuadro de resultado. Ese texto está escrito
  para que lo lea una persona, y la persona está mirando la pantalla.
- **Si el binario no está:** el export continúa y el resultado dice `no verificado`. No
  falla. El manifiesto lo declara en `verificado`.
- **Invocación con lista de argumentos**, nunca `shell=True`.

Parsear el texto sería acoplarse a un formato que ATTRACT no se comprometió a mantener.
El código de salida sí es contrato, y es lo único que la máquina necesita decidir.

**Consecuencia que hay que aceptar por escrito:** `attract doctor` sobre un staging con
forma de bundle **no cubre el bloque `game:`**. `revisar()` recorre con `rglob` y aplica
los chequeos universales a cada archivo —encoding, NFC, CRLF, nombres legales en Windows,
JSON válido, contrato de `data.json`—, pero `chk_metadata` solo corre sobre archivos
`*.pegasus.txt`, y el bundle no lleva ninguno **por diseño**
([`ADR-0003`](0003-bundle-por-juego.md): transporta campos, no sintaxis).

Por eso el staging se arma **con forma de librería** —`<sistema>/media/<set>/`,
`<sistema>/_synopsis/<set>.json`, y un `metadata.pegasus.txt` mínimo generado **solo para
verificar** y descartado antes de comprimir—. Es lo que hace que `verificado: true`
signifique lo que promete.

## Alternativas consideradas

### A. Parsear el `stdout` de `attract doctor`

- A favor: detalle estructurado sin cambiar nada de ATTRACT: se podría resaltar cada
  error por archivo.
- En contra: el formato de impresión no es contrato y puede cambiar en cualquier commit
  de otro repo.
- **Descartada porque:** convierte texto pensado para humanos en una interfaz de máquina,
  y el día que ATTRACT ajuste una línea, COINDOOR reporta «verificado» sobre un bundle
  rechazado o al revés. Un fallo silencioso en el peor lugar posible.

### B. Importar `attract.doctor.revisar()` como librería

- A favor: `Reporte` estructurado, con `errores` y `avisos` separados. Sin parsear nada.
  Los dos proyectos son Python.
- En contra: convierte a ATTRACT en dependencia de código de otro repositorio, que **no
  se publica como paquete** y tiene su propia constitución.
- **Descartada porque:** ata la versión de ATTRACT a la de COINDOOR y rompe la
  degradación limpia — hoy, si el binario no está, el export sigue y avisa; con un import,
  la ausencia es un `ImportError` al arrancar. Además contradice el desacoplamiento que
  `ADR-0003` construyó deliberadamente: *«COINDOOR y la librería se desacoplan: no
  necesitan compartir máquina ni filesystem»*.

### C. Hablar con `attract mcp`

- A favor: `attract_doctor` ya devuelve un `dict` con `ok`, `errores` y `avisos`. Salida
  estructurada sin importar nada ni parsear texto.
- En contra: el SDK `mcp` es dependencia **opcional** de ATTRACT (su ADR-0012) y el
  servidor bloquea sirviendo por stdio: hay que gestionarle el ciclo de vida.
- **Descartada porque:** para una llamada por export, levantar y supervisar un servidor
  es complejidad desproporcionada, y agrega una dependencia opcional de ATTRACT a la
  cadena — si el usuario no instaló `mcp`, la verificación deja de funcionar por un motivo
  que no tiene nada que ver con ATTRACT. La degradación pasa a depender de dos cosas en
  vez de una.

### D. No verificar: confiar en la validación propia contra `contract.json`

- A favor: cero dependencia del binario, export más rápido, una sola implementación.
- En contra: contradice `ADR-0001`, donde la CLI es la autoridad final.
- **Descartada porque:** la doble validación es deliberada. `ADR-0001`: *«la contradicción
  es la señal de que el contrato publicado quedó mal, y es preferible detectarla al
  exportar que en el gabinete»*. Sin la segunda opinión, un `contract.json` desactualizado
  produce bundles inválidos sin que nada avise.

## Consecuencias

**Positivas**

- Acoplamiento cero: funciona con cualquier versión de ATTRACT instalada, y sin ninguna.
- El detalle del rechazo lo lee la persona que puede corregirlo, en las palabras del
  propio ATTRACT.
- Si ATTRACT agrega `doctor --json`, migrar es cambiar una función.

**Coste asumido**

- El detalle del veredicto es texto opaco para la aplicación: no se puede resaltar el
  campo culpable en la ficha ni ofrecer un «arreglar esto».
- El staging tiene que armarse con forma de librería, con un `metadata.pegasus.txt`
  temporal que **no viaja en el bundle**. Es un archivo generado para ser descartado, y hay
  que dejarlo claro en el código o alguien lo va a incluir por error.
- La verificación depende de un binario externo. Se mitiga con la degradación explícita;
  no se elimina.

**Qué habría que revisar si esto se replantea**

- Si ATTRACT expone `doctor --json`, cae la alternativa A y con ella la mitad de este ADR.
- Si ATTRACT se publica como paquete instalable, la alternativa B vuelve a ser razonable.
- Si `attract install` termina haciendo su propia verificación al instalar, conviene
  revisar si la de COINDOOR sigue pagando su coste.

## Referencias

- ATTRACT `src/attract/doctor.py` — `main()` devuelve `0 if rep.ok else 1`; `revisar()` devuelve `Reporte`.
- ATTRACT `src/attract/mcp_server.py` — `_run_doctor()` serializa el reporte a `dict`.
- ATTRACT `src/attract/cli.py` — `attract doctor [ruta] [--target windows]`.
- [`ADR-0001`](0001-contrato-coindoor-attract.md) §Alternativa C — MCP quedó abierto para el export.
- [`ADR-0003`](0003-bundle-por-juego.md) — el bundle no lleva el bloque `game:` escrito.
- [`001-export-bundle/plan.md`](../features/001-export-bundle/plan.md) — `bundle/verify.py` y la etapa de verificación.
