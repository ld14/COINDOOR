---
id: 0021
title: Instalar el bundle exportado por subproceso, sin esperar a `attract install`
status: accepted
date: 2026-09-12
supersedes: null
superseded-by: null
tags: [backend, proceso]
---

# 0021 — Instalar el bundle exportado por subproceso, sin esperar a `attract install`

## Contexto

[`ADR-0003`](0003-bundle-por-juego.md) dejó la instalación explícitamente fuera de
COINDOOR: *"Un comando nuevo del lado de ATTRACT — `attract install <bundle>.zip`"*, y su
Alternativa A — *"COINDOOR escribe directo en el árbol de la librería"* — quedó
descartada porque *"ata COINDOOR a una topología de máquinas que hoy no está decidida"*.
El roadmap lo confirma en §Dependencias fuera de este repo: *"el comando que instala el
bundle no existe [...] decidido posponerlo hasta cerrar el funcionamiento de COINDOOR"*.
`../attract/src/attract/cli.py` sigue sin ese subcomando.

Lo que cambió: la topología **ya no es hipotética**. Este proyecto corre con COINDOOR y
el checkout de ATTRACT en la misma máquina (WSL), y quien mantiene ambos repos ya
construyó y usa a mano un instalador provisional del lado de ATTRACT:
`install-coindoor-wsl.sh` (lanzador WSL) → `install-coindoor.ps1` (hace el trabajo real
en Windows: lee `bundle.json`... — ver el propio script), con sus pares
`install-coindoor.sh`/`.ps1` para macOS. Ese instalador ya existe, ya resuelve exactamente
lo que la sección "Cómo se instala" de ADR-0003 describía para `attract install`, y hoy se
invoca a mano copiando una ruta larga por juego después de cada export.

Eso es fricción operativa repetida en el flujo de un usuario, un juego por vez que define
la misión del proyecto — exactamente el tipo de paso que vale la pena automatizar, sin
que sea un problema de latencia (`tech-stack.md` §Convenciones ya dice que no se optimiza
por eso).

## Decisión

**COINDOOR ofrece una acción "Cargar en ATTRACT"** en la pantalla de export, visible
junto al resultado de un export recién generado. Al activarla, el backend corre por
`subprocess` el instalador que **ya existe en `../attract`** —
`<ATTRACT_DIR>/install-coindoor-wsl.sh <bundle>.coindoor.zip <ATTRACT_DIR>/library` — y
reporta éxito o fracaso según su código de salida, igual que ADR-0012 hace con
`attract doctor`: **no se parsea ni se reinterpreta la salida**, solo se muestra como
texto de diagnóstico si el proceso falla.

`ATTRACT_DIR` es una ruta de esta máquina, nueva variable `COINDOOR_ATTRACT_DIR` en la
config del backend ([`backend/config.py`](../../backend/config.py)). Sin configurar, la
acción falla explícito pidiendo que se configure — no se oculta el botón ni se asume una
ruta por convención (`../attract` cambia según quién clona el repo).

**Esto no reemplaza el objetivo de ADR-0003.** El `.zip` generado sigue siendo
autocontenido y portable a otra máquina; lo que cambia es que, cuando ambos proyectos
conviven en la misma máquina —el caso real hoy—, COINDOOR ofrece el atajo de dispararlo
sin salir de la pantalla, en vez de forzar a copiar y pegar el comando a mano en otra
terminal.

**Esta acción es síncrona, no un job.** Copia unos pocos archivos de media y corre
`doctor` sobre el resultado; encaja en el mismo criterio que ya usa `verify_staging()`
dentro del propio export (ADR-0012), y no en el patrón de job de ADR-0010 — no introduce
una quinta operación asíncrona, solo reutiliza el patrón de subproceso que ya existe para
`attract doctor`.

**Sigue sin reimplementarse nada del lado de ATTRACT.** COINDOOR no lee `bundle.json`, no
escribe `metadata.pegasus.txt`, no resuelve identidad ni corre `doctor` sobre la librería
instalada — todo eso lo hace el script existente, tal como manda
[`ADR-0001`](0001-contrato-coindoor-attract.md): *"prohibido reimplementar la lógica de
ATTRACT [...] la CLI de ATTRACT es la autoridad final"*.

**Alcance de esta decisión: solo WSL.** El instalador tiene variantes para macOS
(`install-coindoor.sh`/`.ps1`) y Windows nativo, pero el único entorno real hoy es WSL.
Cablear las otras variantes es trabajo futuro si aparece esa máquina, no algo a
generalizar de antemano.

## Alternativas consideradas

### A. Esperar a que `attract install <bundle>.zip` exista como subcomando de la CLI de Python

- A favor: cero acoplamiento nuevo; respeta la letra original de ADR-0003 y del
  roadmap.
- En contra: bloquea indefinidamente un flujo real y diario por un comando que vive en
  otro repo, con su propio roadmap y sin fecha — mientras tanto, quien mantiene ambos
  repos ya construyó y usa a mano el reemplazo provisional.
- **Descartada porque:** el roadmap etiquetó esto como "pospuesto hasta cerrar el
  funcionamiento de COINDOOR" cuando la instalación no tenía ninguna solución, ni
  siquiera provisional. Esa condición ya no es cierta: existe un instalador funcionando
  del lado de ATTRACT, y encadenarlo por subprocess no es distinto en espíritu de lo que
  ADR-0012 ya hace con `attract doctor`.

### B. Reimplementar el merge (parsear `bundle.json`, escribir `metadata.pegasus.txt`, copiar `media/`, correr `doctor`) en Python, del lado de COINDOOR

- A favor: no depende de Windows/PowerShell ni de `wslpath`; un solo lenguaje, sin
  cruzar el límite WSL↔Windows.
- En contra: es exactamente lo que [`ADR-0001`](0001-contrato-coindoor-attract.md)
  prohíbe, y el mismo riesgo de divergencia entre `ingest` y COINDOOR que ADR-0003
  identificó como motivo para que el bundle lleve campos y no el bloque `game:` ya
  renderizado.
- **Descartada porque:** duplicaría lógica que ya existe, se mantiene del lado de
  ATTRACT y **hoy funciona**. Reescribirla en COINDOOR no resuelve nada que el subproceso
  no resuelva, y sí introduce el riesgo de divergencia que otro ADR ya pagó el costo de
  evitar.

### C. Dejar el paso 100% manual

- A favor: cero código nuevo, cero riesgo.
- En contra: es exactamente la fricción que motivó este ADR — copiar una ruta larga a
  mano, por juego, siempre, en otra terminal.
- **Descartada porque:** no es una decisión técnica sino la ausencia de una. El pedido es
  automatizar un paso que ya se hace a mano y de forma idéntica cada vez.

## Consecuencias

**Positivas**

- Cierra exportar → instalar sin salir de COINDOOR, para el caso de uso real de hoy (un
  usuario, una máquina, un juego por vez).
- No reimplementa nada del lado de ATTRACT: sigue delegando el 100% de la lógica de
  instalación en su script, consistente con ADR-0001.
- El bundle sigue siendo portable: nada en esta decisión le quita esa propiedad ni toca
  el formato definido en ADR-0003.

**Coste asumido**

- COINDOOR pasa a conocer una ruta de esta máquina (`COINDOOR_ATTRACT_DIR`, el checkout
  de ATTRACT). Es configuración local, no dato del contrato ni del bundle.
- La acción solo funciona en WSL con interoperabilidad Windows habilitada — el mismo
  requisito que ya tiene `install-coindoor-wsl.sh`. En cualquier otra plataforma, la
  acción falla explícito en vez de silencioso.
- Cuando `attract install` exista como subcomando real de la CLI de Python, este ADR se
  vuelve a supersedir para invocar ese comando en lugar del script `.sh`/`.ps1` — no es
  la solución final, es la que cierra la fricción real de hoy.

**Qué habría que revisar si esto se replantea**

- Si `attract install` se implementa en `../attract/src/attract/cli.py`, este ADR se
  supersede para apuntar ahí.
- Si aparece una segunda máquina real (no solo teórica) que reciba bundles, hay que
  revisar si la acción necesita soportar más de un destino configurado, o si ese caso
  vuelve a ser puramente manual (llevar el `.zip` y usar el instalador de esa máquina).

## Referencias

- [`ADR-0003`](0003-bundle-por-juego.md) — formato del bundle y manifiesto, sin cambios.
- [`ADR-0001`](0001-contrato-coindoor-attract.md) — por qué COINDOOR no reimplementa la
  lógica de ATTRACT.
- [`ADR-0012`](0012-verificacion-attract-por-subproceso.md) — mismo patrón de subprocess
  sin parsear salida, aplicado a `attract doctor`.
- [`ADR-0010`](0010-jobs-en-proceso.md) — por qué esta acción no es un job.
- `spec/features/001-export-bundle/spec.md` §Fuera de alcance.
- `spec/constitution/roadmap.md` §Dependencias fuera de este repo.
- `../attract/install-coindoor-wsl.sh`, `install-coindoor.ps1` — el instalador que esta
  decisión invoca, sin modificarlo.
