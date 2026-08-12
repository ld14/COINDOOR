# Glosario

Solo los términos que de verdad se confunden. Si una palabra significa lo obvio, no está
acá.

## Las tres aplicaciones

| Término | Qué es |
|---|---|
| **Pegasus** | El frontend que corre en el gabinete y le muestra los juegos al jugador. Externo, no lo tocamos |
| **ATTRACT** | CLI en Python que arma y valida la librería que Pegasus lee. Vive en `../attract` |
| **COINDOOR** | Este repo. Prepara el material de cada juego y produce bundles |
| **Gabinete** | La máquina física del arcade, donde corre Pegasus. **Offline por diseño** |
| **Librería** | El árbol de archivos que Pegasus consume (`library/` en ATTRACT) |

## Lo mismo con tres nombres

**Sistema = colección = plataforma.** Arcade, NES, MS-DOS. Los tres nombres aparecen y
significan lo mismo:

- `collection:` es como se llama en el `metadata.pegasus.txt`.
- "Sistema" es el nombre en la UI de COINDOOR y el de la carpeta.
- "Plataforma" aparece en la pantalla `/sistemas`.

## Identidad de un juego

Dos cosas distintas que el proyecto separa a propósito
([`ADR-0004`](../decisions/0004-coindoor-fuente-identidad-no-mame.md)):

| Término | Qué es | De dónde sale |
|---|---|---|
| **Identidad física** | El `set`: el nombre de la carpeta y del archivo | **Siempre** del archivo o directorio real en disco. Nunca se escribe a mano |
| **Identidad de presentación** | Título, año, desarrollador, editor, género, jugadores, formato | MAME (arcade), ScreenScraper por hash (consolas), o declarada (PC/DOS) |

- **`set`** — el identificador del juego dentro de un sistema: `goldnaxe`, no
  *Golden Axe*. Sale de `goldnaxe.zip` sin extensión.
- **Romset merged** — un `.zip` de MAME que puede contener el juego padre y todos sus
  clones. Por eso un archivo **no siempre es un juego**.
- **CHD** — archivo de disco de MAME que acompaña a un romset. Pesa cientos de MB o GB, y
  es la razón por la que "arcade = liviano" es falso.

## Archivos del contrato

| Archivo | Qué lleva |
|---|---|
| `metadata.pegasus.txt` | Uno por sistema. Cabecera (`collection:`, `launch:`) + un **bloque `game:`** por juego |
| `data.json` | Uno por juego, en `media/<set>/`. Los datos ricos: `accent`, `review`, `cheats`, `manual[]` |
| `_synopsis/<set>.json` | La fuente de la que `attract synopsis` escribe el campo `summary:`. **No lo lee el gabinete** |

**Assets**: los archivos de media. Sus nombres en disco distinguen mayúsculas y **no
coinciden con los de la UI**:

| En COINDOOR | En disco |
|---|---|
| Carátula | `boxFront` |
| Marquesina | `marquee` |
| Póster | `poster` |
| Logo | `logo` |
| Captura de pantalla | `screenshot` |

**Marquesina**: el cartel luminoso de la parte de arriba de un gabinete arcade. No es una
captura ni un banner.

## Estados, que son tres cosas distintas

| Término | Significa | Bloquea |
|---|---|---|
| **VÁLIDA** | Bien formada técnicamente: NFC, sin CRLF, nombres legales en Windows, JSON parseable | Sí. Es **error** |
| **COMPLETA** | No falta nada de lo que hace que el juego se vea bien | No. Es **faltante** |
| `ready` / `incomplete` / `error` | Los tres estados de un juego en la UI | `error` bloquea el export; `incomplete` bloquea "marcar como listo" |

Son **ortogonales**: un juego puede estar completo e inválido, o incompleto y perfecto.
La mayoría de una colección se queda incompleta para siempre, y eso es lo normal.

Ojo: **la definición de COMPLETO es de COINDOOR y es más estricta que el contrato.** ATTRACT
solo exige `title` y `x-formato`.

## Del export

| Término | Qué es |
|---|---|
| **Bundle** | El `.zip` de un juego, instalable en otra máquina ([`ADR-0003`](../decisions/0003-bundle-por-juego.md)) |
| **`bundle.json`** | El manifiesto: qué colección, qué identidad, cómo tratar cada artefacto |
| **Artefacto** | Un archivo del juego dentro del bundle, con su `tratamiento` |
| **`tratamiento`** | `copiar` (romset de MAME) o `descomprimir` (carpeta de MS-DOS). Los dos son `.zip` y **por la extensión no se distinguen** |
| **Staging** | El árbol temporal que COINDOOR arma y verifica **antes** de comprimir |

## De las sugerencias

| Término | Qué es |
|---|---|
| **Proveedor** | Una fuente externa: una API, un scraper o un modelo de IA |
| **Candidato aplicable** | El proveedor entrega el archivo o el texto: un click lo carga |
| **Candidato referencia** | El proveedor solo dice **dónde** está. Abre el enlace; el archivo lo sube el usuario. Es el caso de YouTube y las revistas |
| **Procedencia** | Si un campo lo cargó una persona (`manual`) o vino de una sugerencia (`suggested`). **Dato interno: no se exporta** ([`ADR-0002`](../decisions/0002-procedencia-interna.md)) |

## Nuestros

- **Delta** — una corrección al paquete de diseño, en
  [`frontend-architecture.md`](frontend-architecture.md) §Deltas. Manda sobre el diseño y
  sobre el prototipo, porque corrige donde el contrato de ATTRACT no admite lo propuesto.
- **Contrato** — según el contexto: el de **datos** de ATTRACT (`CONVENCION.md`) o el de
  **API** entre el front y el back de COINDOOR (`data-model.md` §6). Casi siempre el
  primero.
