# 015 · Carga guiada — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

La carga ya funciona: cinco comandos que hacen bien su parte. Lo que falta no
es capacidad, es **saber en qué estado quedó** y **en qué orden seguir**. Por
eso no hay orquestador que encadene comandos —un `attract load` que corre todo
falla a la mitad y deja la librería mentida—, sino un **reporte read-only** que
mira el disco y dice qué falta, más un skill que le pasa el orden al agente.

Escribir sigue siendo de los comandos que ya existen, cada uno con su
"fallar explícito, nunca escritura parcial". El único comando que se toca es
`ingest`, con una bandera para el caso no-MAME.

`attract carga` compara contra un **caso de referencia**: `goldnaxe`. Lo que
ese juego tiene es la definición operativa de COMPLETO (`docs/CONVENCION.md`
§4.2); lo que no tiene, no se exige.

## Implementación

1. `src/attract/carga.py` — el reporte. Funciones puras sobre stdlib:
   `estado_de(set, ruta) -> Estado` recolecta presencia/ausencia leyendo el
   bloque `game:` (reusa `parsear_bloques` de `synopsis.py`), `media/<set>/`,
   `_synopsis/<set>.json`, `data.json` y `_magazines/`. `render(Estado)`
   imprime. Nunca abre un archivo en modo escritura.
2. `src/attract/carga.py::FALTANTES` — tabla de datos, no `if`s: cada entrada
   es `(nombre, detector, comando_sugerido, bloqueante?)`. Sumar un chequeo es
   una fila. Los tres niveles de la salida son los dos ejes de CONVENCION §4
   más el eje "hay fuente pero falta correr el comando", que es el que hoy se
   pierde.
3. `src/attract/ingest.py` — bandera `--titulo` (y opcionales `--dev`,
   `--publisher`, `--genero`, `--year`, `--players`). Con ella, `construir_bloque`
   recibe la identidad declarada y **no** se llama a `mame -listxml`. Sin ella,
   el módulo se comporta exactamente como hoy.
4. `src/attract/doctor.py` — dos chequeos nuevos, en el archivo de siempre
   (regla de `CLAUDE.md`): `chk_cabecera_sistema` (`collection:` presente,
   `launch:` absoluto — ADR-0018) y `chk_asset_case` (aviso cuando un nombre
   difiere solo en mayúsculas de `boxFront|marquee|poster|logo|screenshot|video`).
5. `.claude/skills/carga-juego/SKILL.md` — lo que se le pasa al agente: los
   disparadores, el orden de los siete pasos, y la regla de que ningún paso se
   da por hecho sin `attract carga` en verde. Es el hermano de
   `.claude/skills/attract/`, que cubre validar; este cubre cargar.
6. `docs/guides/cargar-un-juego-nuevo.md` — sección nueva "0 · Plataforma
   nueva" (carpeta, cabecera, `game_dirs.txt`, `x-formato`) y `attract carga`
   como paso de cierre.

## El orden que el skill le pasa al agente

Es el orden real de dependencias, no una preferencia. Cada paso enlaza a la
sección de la guía que ya lo documenta.

| # | Paso | Comando | Depende de |
|---|---|---|---|
| 0 | Sistema (solo si es nuevo) | a mano: carpeta + `collection:`/`shortname:`/`launch:` + `game_dirs.txt` | — |
| 1 | ROM → bloque `game:` | `attract ingest <rom> <ruta>` (`--titulo` si no es MAME) | 0 |
| 2 | Imágenes y video | copiar a `media/<set>/`, plano | 1 |
| 3 | Sinopsis | dejar `_synopsis/<set>.json` **y** correr `attract synopsis` | 1 |
| 4 | `data.json` | a mano: `accent`, `review`, `cheats` | 1 |
| 5 | Manual | PDF a `media/<set>/_manual/` + `attract rasterize` | 4 |
| 6 | Revista | carpeta en `_magazines/` + `attract mags library --apply` | 4 |
| 7 | Cierre | `attract carga <set>` y `make doctor-lib` | 1-6 |

## Decisiones

- **Reporte read-only en vez de orquestador** — un comando que encadena los
  cinco escritores no puede fallar a la mitad sin dejar estado inconsistente, y
  cada escritor ya tiene su propia garantía atómica. El reporte se puede correr
  cuantas veces se quiera, incluso a mitad de una carga.
- **`goldnaxe` como definición de COMPLETO** — evita inventar un contrato de
  completitud nuevo: lo que ya existe en la librería es la vara.
- **Identidad declarada para no-MAME** — es la primera vez que ATTRACT acepta
  una identidad que **nadie autoritativo** confirma, al revés de
  [`ADR-0004`](../../decisions/0004-identidad-set-merged.md). Tiene alternativas
  reales (un provider externo, un catálogo No-Intro) → **necesita ADR propio**
  antes de implementar el punto 3.
- **Los chequeos nuevos van en `doctor.py`** — regla explícita de `CLAUDE.md`:
  nada de scripts de validación aparte.
- **Cero dependencias nuevas** — todo stdlib; el límite duro sigue con sus dos
  excepciones (ADR-0012, ADR-0022).

## Riesgos

- **El reporte se vuelve un segundo validador que contradice a `doctor`.** Se
  mitiga con la frontera: `doctor` dice si algo está **mal**, `carga` dice si
  falta algo. Si un chequeo puede fallar, va a `doctor`; si solo puede estar
  ausente, va a `carga`. Ninguna regla se escribe dos veces.
- **`--titulo` abre la puerta a metadata inventada.** Se mitiga marcando
  procedencia (`docs/CONVENCION.md` §3.1) y dejando la bandera fuera del camino
  de MAME: si `mame` reconoce el set, manda `mame`.
- **`x-formato` es obligatorio (CONVENCION §2.1) y hoy no lo valida nadie** —
  el bloque `mok` de `library/arcade/` no lo tiene. Al agregar el chequeo, la
  librería real va a marcar errores preexistentes; hay que arreglarlos en la
  misma tarea o el `doctor-lib` queda rojo y se empieza a ignorar.
