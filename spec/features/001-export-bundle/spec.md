# 001 · Export a bundle instalable

**Estado:** aprobada

## Qué hace

**Recibe** un juego en estado `ready` y las opciones de qué incluir. **Produce** un único
archivo `<set>.coindoor.zip` que contiene todo lo necesario para que ATTRACT lo instale en
otra máquina, y un veredicto de si ese contenido cumple el contrato.

**No** instala nada. `attract install` es trabajo del repo ATTRACT y se define después
([`ADR-0003`](../../decisions/0003-bundle-por-juego.md) fija el formato que va a consumir).

## Por qué

Hoy el material de un juego queda repartido en cuatro lugares de la librería: el bloque
`game:` dentro de `metadata.pegasus.txt`, `_synopsis/<set>.json`, `media/<set>/` y su
`_manual/`. Son 63 MB en `goldnaxe`, con nombres sensibles a mayúsculas que si se escriben
mal no rompen nada visible: el gabinete simplemente no muestra la imagen.

Un solo archivo se copia a un pendrive y viaja a la máquina del gabinete. Sin él, COINDOOR
tendría que escribir directo en la librería, o sea correr en la misma máquina, y el trabajo
de cargar un juego quedaría encerrado en una instalación.

## Criterios de aceptación

- [ ] Dado un juego `ready`, exportar produce un `.zip` con `bundle.json` en la raíz,
      `media/` y `_synopsis.json`.
- [ ] **Lo obligatorio no se puede deseleccionar**: identidad, carátula, póster, sinopsis
      y color de acento van siempre. Es exactamente lo que hace `ready` a un juego; si el
      export pudiera quitarlo, saldría un bundle no-listo de una lista de listos.
- [ ] Dado cualquier campo opcional deseleccionado, ni el archivo ni su referencia en
      `data.json` aparecen en el bundle.
- [ ] Dado un campo opcional vacío, no se ofrece como opción: no hay nada que incluir.
- [ ] Dado `incluir juego = sí`, el `.zip` trae los archivos del juego bajo `juego/` y
      `bundle.json` los declara en `artefactos[]` con su `tratamiento`.
- [ ] Dado un romset de MAME, su `tratamiento` es `copiar`; dada una carpeta de MS-DOS,
      es `descomprimir`. **Los dos son `.zip` y por la extensión no se distinguen.**
- [ ] **El bundle nunca lleva `mags[]`**, esté o no vinculada una revista.
- [ ] Dado un juego cuya identidad no fue editada y su `identitySource` es `mame`,
      `identidad.origen` es `mame`. Si el usuario editó **cualquier** campo de identidad,
      o si `identitySource` es `screenscraper` o `manual`, `identidad.origen` es
      `declarada` — `attract install` solo sabe consultar MAME.
- [ ] El `data.json` del bundle es JSON válido y conforme al contrato: `accent` y
      `accent2` presentes, `review` con `score` y `cats` parciales o `null`, `cheats` con
      sus grupos, `manual[]` con sus páginas.
- [ ] Dado ATTRACT disponible en la máquina, se corre `attract doctor` sobre el árbol
      preparado **antes** de comprimir, y su veredicto se muestra.
- [ ] Dado ATTRACT **no** disponible, el export igual produce el `.zip` y avisa que no se
      pudo verificar. No falla.
- [ ] Dado un juego que no es `ready`, no aparece en la lista de exportables.
- [ ] Exportar dos veces el mismo juego sin editarlo produce un bundle equivalente.
- [ ] Si el árbol preparado no pasa `doctor`, **no se genera el `.zip`**: fallo explícito,
      nunca un bundle a medias.

## Decisiones resueltas antes de implementar

Los cuatro puntos que bloqueaban el arranque (ver `tech-stack.md` §Contradicciones
abiertas y `roadmap.md` §Bloqueado), ya resueltos:

- **`contrato` en `bundle.json`** — placeholder `"1"` hasta que ATTRACT publique su
  propia versión ([`ADR-0001`](../../decisions/0001-contrato-coindoor-attract.md)). No
  se encontró ningún campo de versión en `../attract` a la fecha de esta decisión.
- **Firma de `attract install`** — `attract install <bundle>.zip`, un solo argumento
  posicional. Confirmado como provisional: el comando no existe todavía en
  `attract/src/attract/cli.py`, pero el formato no debería cambiar cuando se implemente.
- **`IdentitySource` pasa de 2 a 3 valores** — `'mame' | 'screenscraper' | 'manual'` en
  `types.ts` (hoy solo `'catalog' | 'manual'`). Sigue a
  [`ADR-0004`](../../decisions/0004-coindoor-fuente-identidad-no-mame.md), que ya define
  tres orígenes reales y exige que se vean distintos en pantalla. Mapeo a
  `identidad.origen`: `mame` → `mame`; `screenscraper` y `manual` → `declarada`, porque
  `attract install` solo sabe consultar MAME.
- **`players` no entero** (`"1-2"`, `"2 alternados"`) — mismo criterio que ATTRACT
  (`CONVENCION.md` Nota 1): si no parsea a entero limpio, se escribe `1`. ATTRACT ya
  acepta esa imprecisión sin distinguir "no sé" de "es de 1 de verdad".

## Fuera de alcance

- **Instalar el bundle.** Eso es `attract install`, en el otro repo.
- **Exportar varios juegos a la vez** — uno por vez, por el peso.
- **Las revistas, en cualquier forma.** Ni el archivo ni la referencia. Lo que COINDOOR
  guarda es una pista para conseguir la revista después: dato interno, no asset del juego.
- **La cabecera del sistema.** Su `launch:` es una ruta absoluta de la máquina de origen
  y no es portable (ADR-0018 de ATTRACT). El bundle exige que la colección ya exista.
