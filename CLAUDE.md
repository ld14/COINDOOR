# COINDOOR

## Qué es esto

Interfaz visual para preparar la metadata completa de un juego arcade —video, carátula,
marquesina, sinopsis, reseña, trucos, manual— y entregarla como un `.zip` instalable en
**ATTRACT**, que la ensambla en la librería que **Pegasus** muestra en el gabinete.

Tres piezas, no confundirlas:

| Pieza | Qué es | Dónde vive |
|---|---|---|
| **Pegasus** | Frontend del gabinete. Muestra los juegos al jugador. | externo |
| **ATTRACT** | CLI en Python que arma y valida la librería que Pegasus lee. | `../attract` |
| **COINDOOR** | *Este repo.* Prepara el material y produce bundles. | acá |

El gabinete es **offline** por diseño y ATTRACT no descarga nada. COINDOOR es la mitad
conectada: busca, propone, arma y empaqueta.

**Estado: sin código, stack decidido.** Doce ADRs y cinco features especificadas. La
Fase 1 puede arrancar.

## Método de trabajo

Este proyecto usa **Spec Driven Development**: primero la spec, luego el plan, luego las
tareas, y solo entonces el código. Ver `spec/README.md`.

**La constitución manda.** Si una feature choca con `spec/constitution/`, se replantea la
feature, no la constitución.

## Comandos

Los define la feature [003](spec/features/003-base-frontend/tasks.md). Hasta que existan
los scripts, la tabla de `spec/constitution/tech-stack.md` §Comandos es el contrato a
cumplir, no una descripción de algo que corre. **No inventes otros.**

## Claude Code en este proyecto (OmniRoute)

Este repo usa Claude Code enrutado por **OmniRoute** (`localhost:20128`), no Anthropic
directo. La config vive en `.claude/settings.local.json` — no es global, no afecta otros
proyectos.

| Archivo | Qué hace |
|---|---|
| `.claude/settings.local.json` | **Activo.** Apunta a `coindoor-auto` (Auto Combo + Cost Saver). Probado: saludos triviales → Sonnet, código → mejor modelo disponible, gratis (mimo/deepseek) como red de resguardo. |
| `.claude/settings.local.emergency.json` | **Inerte** hasta que lo actives. Sin `ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN` → vuelve a Claude directo con tu suscripción normal. |

**Si OmniRoute está caído**, Claude Code no tiene fallback automático — falla la conexión.
Activar el perfil de emergencia:

```bash
cp .claude/settings.local.json .claude/settings.local.json.omniroute-backup
cp .claude/settings.local.emergency.json .claude/settings.local.json
```

Volver al normal:

```bash
cp .claude/settings.local.json.omniroute-backup .claude/settings.local.json
```

**Combos disponibles en OmniRoute** (dashboard → Combos). Ambos son propios de este
proyecto — no tocan `comboInicial` ni otros repos:

- `coindoor-auto` — default, uso diario, prioriza costo.
- `coindoor-heavy` — mismo pool de modelos, prioriza calidad (`taskFit`) sobre costo.
  Activar con `/model coindoor-heavy` en una sesión cuando el pedido sea código o
  análisis pesado.

## Mapa del repo

| Ruta | Qué es |
|---|---|
| `spec/constitution/` | Misión, stack, modelo de datos, límites duros, glosario, roadmap |
| `spec/decisions/` | ADRs: por qué se decidió así y qué se descartó. Son **doce** |
| `spec/features/NNN-*/` | spec + plan + tasks por feature. Hay **cinco**; arrancar por la 003 |
| `docs/arquitectura/` | Análisis del stack con las alternativas comparadas. **Se consulta, no manda**: mandan los ADRs |
| `docs/claude_diseño/` | **Especificación del front-end.** Fuente de consulta: stack, tokens, tipos, las 5 pantallas con textos literales |
| `docs/attract/` | Insumos copiados del repo ATTRACT. **No son features de acá** |
| `docs/ux/` | Requerimiento funcional: el *por qué* de cada pantalla. El *qué* está en `claude_diseño/` |
| `frontend/`, `backend/` | Código. Sin crear. Sus `CLAUDE.md` ya tienen las reglas |

**`docs/claude_diseño/` se consulta, no se edita.** Lo que COINDOOR decide encima —o en
contra— va en `spec/`. Tiene tres conflictos con el contrato de ATTRACT sin resolver:
ver `tech-stack.md` §Conflictos abiertos antes de implementar nada.

**Si dudás de un término** —`set`, colección, marquesina, VÁLIDA vs COMPLETA, bundle,
artefacto, candidato referencia— está en
[`spec/constitution/glosario.md`](spec/constitution/glosario.md). Hay tres sistemas con
vocabulario que se solapa; no lo adivines.

## Contexto que no está en este repo

El contrato de datos real vive en **`../attract`** y es la referencia autoritativa:

| Qué | Dónde |
|---|---|
| Contrato de datos | `docs/CONVENCION.md` — §1 estructura, §2 campos, §3 procedencia, §4 validación |
| 25 ADRs aceptados | `spec/decisions/` |
| Comandos reales | `src/attract/cli.py` — `doctor`, `synopsis`, `ingest`, `rasterize`, `mags`, `mcp` |
| Único juego completo | `library/arcade/media/goldnaxe/` — la vara operativa de COMPLETO |

**Leelo antes de afirmar cómo funciona ATTRACT.** Los documentos de `docs/attract/` son
una copia parcial y ya se les detectaron dos citas equivocadas de su propio contrato.

## Catorce cosas que se dan por decididas

Están en los ADRs con sus alternativas; acá solo para que no se re-propongan:

1. **El contrato de ATTRACT se consume como dato versionado, nunca se replica en código**
   ([`ADR-0001`](spec/decisions/0001-contrato-coindoor-attract.md)).
2. **La procedencia de cada campo es interna y no viaja al export**
   ([`ADR-0002`](spec/decisions/0002-procedencia-interna.md)). `CONVENCION` §3.1 decide
   no distinguir origen y §3.3 que todo reproceso pisa.
3. **La unidad de entrega es un `.zip` por juego** que ATTRACT instala, no una API
   ([`ADR-0003`](spec/decisions/0003-bundle-por-juego.md)). El bundle transporta
   **campos, no sintaxis**: COINDOOR nunca escribe formato Pegasus.
4. **Para plataformas sin catálogo, COINDOOR es la fuente de identidad**
   ([`ADR-0004`](spec/decisions/0004-coindoor-fuente-identidad-no-mame.md)). Arcade
   conserva sus dos caminos: `attract ingest` y COINDOOR.
5. **El contrato vendoreado y la política de completitud son archivos distintos**, atados
   por un test ([`ADR-0005`](spec/decisions/0005-contrato-vendoreado-vs-politica-propia.md)).
6. **Varias fuentes por campo, y una caída no rompe la búsqueda**
   ([`ADR-0006`](spec/decisions/0006-fuentes-externas-multiproveedor.md)). La IA produce
   sinopsis, reseña y trucos; **nunca** identidad.
7. **Un solo usuario, un juego por vez, sin carga masiva.** De ahí se siguen: sin auth,
   sin workers, sin colas.
8. **La latencia no es un problema de este producto.** Todo es a pedido y esperar no
   molesta: no se agrega complejidad para ahorrar segundos. Ver `tech-stack.md`
   §Convenciones y §Límites duros.
9. **El backend es FastAPI**, no Django ni Flask ni Node
   ([`ADR-0007`](spec/decisions/0007-fastapi-como-framework-backend.md)).
10. **No hay base de datos.** Un `game.json` por juego, con su media al lado, escritura
    atómica y migración por campo `version`
    ([`ADR-0008`](spec/decisions/0008-persistencia-en-archivos.md)).
11. **Un proceso en `127.0.0.1` que sirve API y frontend desde el mismo origen.** Ese
    bind, más la validación del header `Host`, reemplaza a la autenticación. **Sin
    Docker** ([`ADR-0009`](spec/decisions/0009-proceso-local-en-loopback.md)).
12. **Los cuatro trabajos largos corren en hilos del propio proceso.** Sin Celery, sin
    Redis ([`ADR-0010`](spec/decisions/0010-jobs-en-proceso.md)).
13. **La política de completitud es `fielddefs.json`**, un archivo que leen TypeScript y
    Python ([`ADR-0011`](spec/decisions/0011-fielddefs-json-compartido.md)).
14. **La salida de `attract doctor` no se parsea**, solo su código de salida
    ([`ADR-0012`](spec/decisions/0012-verificacion-attract-por-subproceso.md)).

## Reglas de trabajo

- Antes de proponer arquitectura, leé `spec/constitution/tech-stack.md` (en especial
  §Límites duros y §Contradicciones abiertas) y el índice de `spec/decisions/`.
- **Empezá por la feature [003](spec/features/003-base-frontend/spec.md).** El orden es
  003 → 004 → 005; las fases 3 y 4 del roadmap todavía no tienen carpeta.
- No propongas nada listado como descartado en un ADR sin decir explícitamente qué
  cambió para reabrirlo.
- Decisión con alternativas descartadas → ADR nuevo (`/new-adr`).
- Los ADRs no se editan: se supersedan con uno nuevo. **Los doce actuales están en
  `accepted`**; cualquier cambio ahora requiere un ADR nuevo que superseda al anterior.
- El paquete de diseño (`docs/claude_diseño/`) se consulta y no se edita. Donde el
  contrato de ATTRACT no admite lo que propone, mandan los **deltas D1–D5** de
  `spec/constitution/frontend-architecture.md`.
- **No inventes campos del contrato.** Verificalos contra `../attract/docs/CONVENCION.md`
  o contra `goldnaxe`. Un campo inventado acá contamina bundles que se instalan en otras
  máquinas.
- No toques código sin que exista `spec.md` y `plan.md` de esa feature.

## Fuera de alcance sin preguntar

- Añadir dependencias nuevas
- Modificar el repo `../attract` — es otro proyecto con su propia constitución
- Editar los archivos de `docs/attract/` — son copia de otro repo
- Cambios en CI/CD o infraestructura
