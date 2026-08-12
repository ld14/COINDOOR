# 015 · Carga guiada de un juego

**Estado:** borrador   <!-- borrador | aprobada | en curso | implementada -->

## Qué hace

**Recibe** un sistema (existente o nuevo) y el material crudo de un juego: ROM,
imágenes, video, PDF del manual, `_synopsis/<set>.json` y la revista ya
escaneada. **Produce** el juego cargado al nivel de `goldnaxe` —hoy el único
caso completo de la librería— o un reporte de qué falta y con qué comando se
cierra cada hueco.

Dos piezas, ninguna nueva en el contrato de datos:

1. `attract carga <set> [ruta]` — reporte **read-only** de completitud, con la
   acción concreta por cada faltante.
2. Un skill de proyecto que le da a un agente el **orden** de los pasos (el
   orden importa: `synopsis` después del bloque, `rasterize` después del PDF,
   `mags` después de la revista).

**No** produce contenido. La sinopsis la escribe un scraper externo
([`ADR-0011`](../../decisions/0011-fuente-synopsis-regeneracion-campo.md)), las
revistas un subsistema de escaneo
([`ADR-0009`](../../decisions/0009-frontera-produccion-consumo-revistas.md)),
y el arte lo trae el autor. Esta feature los **ensambla y verifica**.

## Por qué

La carga completa existe una sola vez (`goldnaxe`) y el procedimiento vive
repartido entre `docs/guides/cargar-un-juego-nuevo.md`, cinco comandos y ocho
ADRs. Tres agujeros medidos al reconstruirla:

1. **Plataforma nueva no tiene camino de alta.** `attract ingest` deriva la
   identidad de `mame -listxml`; para NES, PC o cualquier no-MAME no hay
   comando y el bloque `game:` se escribe a mano, sin validación.
2. **Nadie reporta COMPLETA.** `doctor` valida el eje VÁLIDA
   (`docs/CONVENCION.md` §4.1); el eje COMPLETA (§4.2) no lo mide ninguna
   herramienta, así que "ya cargué todo" no es verificable.
3. **La cabecera del sistema se escribe a mano y nada la mira.**
   `chk_metadata` valida encoding, NFC y `assets.*`, pero no que exista
   `collection:` ni que `launch:` sea absoluto — o sea que
   [`ADR-0018`](../../decisions/0018-launch-ruta-absoluta.md) se puede violar
   en silencio y el síntoma aparece recién en el gabinete.

## Criterios de aceptación

- [ ] Dado `goldnaxe`, `attract carga goldnaxe library/arcade` reporta
      **COMPLETO** y no lista ningún faltante.
- [ ] Dado un juego recién ingestado (sin assets, sin `data.json`), reporta
      **VÁLIDO** + la lista de faltantes y **sale con 0**: faltar no es error.
- [ ] Dado `_synopsis/<set>.json` presente y el bloque `game:` sin `summary:`,
      el faltante propone `attract synopsis <set> <ruta>` — es el tropiezo más
      frecuente de la guía.
- [ ] Dado `manual[].file` sin `pages[]`, el faltante propone
      `attract rasterize <set> <ruta>`.
- [ ] Dado `mags[].ref` que no resuelve a una carpeta de `_magazines/`, es
      faltante y **no** error (degradación intencional, `chk_mags_ref`).
- [ ] Dado un sistema sin `mame` disponible,
      `attract ingest <rom> <ruta> --titulo "Dr. Mario"` crea el bloque `game:`
      con la identidad declarada; **sin** `--titulo` y sin `mame`, sigue
      fallando explícito como hoy.
- [ ] `doctor` da **error** si un `metadata.pegasus.txt` no tiene `collection:`
      o si su `launch:` no arranca con `/` (ADR-0018).
- [ ] `doctor` da **aviso** si un archivo de `media/<set>/` difiere solo en
      mayúsculas de un asset conocido (`boxfront.jpg` no lo carga Pegasus, y
      hoy pasa el validador en verde).
- [ ] `attract carga` no escribe **nada**: correrlo dos veces deja la librería
      byte a byte igual.

## Fuera de alcance

- Producir sinopsis, escaneos de revista o arte — llega de afuera (ADR-0009,
  ADR-0011).
- Descargar assets de internet: el gabinete es offline y el runtime es MAME
  vanilla ([`ADR-0005`](../../decisions/0005-runtime-mame-vanilla.md)).
- Crear la carpeta del sistema y registrarla en el `game_dirs.txt` de Pegasus.
  Son dos acciones de una línea cada una y viven fuera del repo: se documentan
  en la guía, no se automatizan.
- Reprocesar o pisar campos ya curados a mano (`docs/CONVENCION.md` §3.3).
- Rasterizar el PDF —eso es [`013-rasterize-manual`](../013-rasterize-manual/spec.md)—
  y linkear revistas —eso es
  [`ADR-0025`](../../decisions/0025-link-revista-juego-difuso.md).
