# 015 · Carga guiada — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas;
marca `[x]` al completarlas._

## Antes de tocar código

- [ ] Crear el ADR de **identidad declarada para sistemas no-MAME** (`/new-adr`).
      Alternativas a evaluar de verdad: catálogo No-Intro/TOSEC, provider
      externo de Pegasus, o declararla a mano. Hecho cuando: el ADR está en
      `spec/decisions/` y `plan.md` §Decisiones lo enlaza en vez de decir
      "necesita ADR propio". **Bloquea la tarea de `--titulo`.**
- [ ] Decidir el sistema no-MAME de prueba (NES / PC) y qué emulador va en
      `launch:`. Hecho cuando: está escrito en el ADR de arriba.

## Implementación

- [ ] `src/attract/carga.py` — `estado_de(set, ruta) -> Estado`, puro, sin
      escritura. Hecho cuando: devuelve el mismo `Estado` corriendo dos veces y
      `git status` queda limpio.
- [ ] `src/attract/carga.py` — tabla `FALTANTES` con `(nombre, detector,
      comando, bloqueante)` y `render()`. Hecho cuando: agregar un faltante
      nuevo es una fila y ninguna función crece.
- [ ] `src/attract/cli.py` — registrar `carga` en `COMANDOS` y en el `--help`.
      Hecho cuando: `attract carga goldnaxe library/arcade` corre.
- [ ] `src/attract/ingest.py` — `--titulo` + opcionales (`--dev`,
      `--publisher`, `--genero`, `--year`, `--players`); saltea
      `mame -listxml`. Hecho cuando: crea el bloque en una máquina **sin**
      `mame` instalado. Depende de: el ADR de identidad declarada.
- [ ] `src/attract/doctor.py` — `chk_cabecera_sistema`: `collection:` presente
      y `launch:` absoluto (ADR-0018). Hecho cuando: un `metadata.pegasus.txt`
      con `launch: mame …` da error con la ruta y la línea.
- [ ] `src/attract/doctor.py` — `chk_asset_case`: aviso ante `boxfront.jpg` y
      compañía. Hecho cuando: `boxFront.jpg` no avisa y `boxfront.jpg` sí.
- [ ] Arreglar los errores preexistentes que destapen los chequeos nuevos
      (empezar por `x-formato`/`x-set` faltantes en el bloque `mok` de
      `library/arcade/metadata.pegasus.txt`). Hecho cuando: `make doctor-lib`
      vuelve a verde.
- [ ] `.claude/skills/carga-juego/SKILL.md` — disparadores + la tabla de siete
      pasos de `plan.md`. Hecho cuando: no duplica el contrato de datos, solo
      enlaza a `docs/guides/cargar-un-juego-nuevo.md` y a los ADRs.

## Tests

- [ ] Caso feliz: fixture equivalente a `goldnaxe` → COMPLETO, cero faltantes.
- [ ] Caso límite: juego recién ingestado, sin `media/` ni `data.json` →
      VÁLIDO + faltantes, **exit 0**.
- [ ] `_synopsis/<set>.json` presente y `summary:` ausente → faltante que
      propone `attract synopsis`. Es el bug de proceso más repetido; sin este
      test la feature no sirve para nada.
- [ ] `manual[].file` sin `pages[]` → faltante que propone `attract rasterize`.
- [ ] `mags[].ref` colgado → faltante, **no** error.
- [ ] Invariante: `attract carga` no abre ningún archivo en modo escritura
      (verificar sobre un árbol de solo lectura).
- [ ] `ingest --titulo` con `mame` ausente → bloque creado; `ingest` sin
      `--titulo` con `mame` ausente → error explícito, nada escrito.
- [ ] `chk_cabecera_sistema` y `chk_asset_case`: un caso positivo y uno
      negativo cada uno.

## Cierre

- [ ] Validar contra todos los criterios de aceptación de `spec.md`.
- [ ] Cargar un juego real de punta a punta en un sistema **nuevo**, siguiendo
      solo el skill, y verlo en el gabinete. Es la única prueba de que el
      procedimiento se sostiene sin el autor al lado.
- [ ] `docs/guides/cargar-un-juego-nuevo.md`: sección "0 · Plataforma nueva" +
      `attract carga` como paso de cierre.
- [ ] `CLAUDE.md`: sumar `carga` a la tabla de comandos y al mapa de
      `src/attract/`.
- [ ] Crear ADR si alguna decisión de implementación tuvo alternativas
      descartadas.
- [ ] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.
