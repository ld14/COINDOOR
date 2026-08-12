---
id: 0003
title: Entregar cada juego como un bundle .zip instalable, no por API
status: accepted
date: 2026-08-10
supersedes: null
superseded-by: null
tags: [data, proceso]
---

# 0003 — Entregar cada juego como un bundle .zip instalable, no por API

## Contexto

COINDOOR tiene almacenamiento propio y el resultado tiene que llegar a la librería de
ATTRACT ([`ADR-0001`](0001-contrato-coindoor-attract.md)), pero **cómo** llega quedó sin
definir. `goldnaxe` muestra el volumen del trabajo que hay detrás de un juego completo:
video, carátula, marquesina, póster, sinopsis, reseña con categorías, trucos agrupados,
manual rasterizado a 26 páginas y una nota de revista vinculada.

Ese trabajo es caro y **no depende de la máquina**: es el mismo en cualquier instalación
que tenga el juego. El caso de uso principal es mover la propia colección entre las
propias máquinas —del equipo donde se carga al gabinete— sin rehacer nada. Que el
artefacto además se pueda pasar a otra persona es consecuencia del formato, no su
objetivo.

Una restricción del contrato de ATTRACT acota lo que puede viajar: **`launch:` es ruta
absoluta obligatoria** (ADR-0018), porque una app de GUI en macOS arranca con `PATH`
mínimo y `mame` pelado no resuelve. Es una ruta de *esa* máquina: la cabecera del sistema
**no es portable**.

Segunda restricción: **`_magazines/` vive fuera del árbol de sistemas** (ADR-0024) porque
una revista cubre juegos de varios sistemas y copiarla los duplicaría. Medido:
`micromania-34` pesa 142 MB contra 63 MB del juego completo.

## Decisión

**La unidad de entrega es un bundle `.zip` por juego**, autocontenido salvo dos
exclusiones deliberadas, instalable en cualquier ATTRACT que ya tenga configurada la
colección de destino.

### Qué lleva

- `bundle.json`, el manifiesto: **la hoja de instrucciones de `install`** (ver abajo).
- `media/<set>/` completo: imágenes, video, `data.json`, `_manual/` con el PDF y sus
  páginas rasterizadas.
- `_synopsis/<set>.json`, la fuente de la que `attract synopsis` escribe `summary:`.
- Los archivos del juego, si se eligió incluirlos.

**No lleva el bloque `game:` ya escrito.** Lleva los campos; el bloque lo renderiza
ATTRACT al instalar. Ver "Por qué campos y no el bloque".

### `bundle.json` — el manifiesto

```json
{
  "bundle": 1,
  "contrato": "<versión del contrato de ATTRACT usada al armar>",
  "coleccion": "Arcade",
  "set": "goldnaxe",

  "identidad": {
    "origen": "mame",
    "campos": {
      "title": "Golden Axe",
      "developer": "Sega",
      "publisher": "Sega",
      "genre": "Beat 'em up",
      "release": "1989",
      "players": 2,
      "x-formato": "Arcade"
    }
  },

  "artefactos": [
    { "archivo": "juego/goldnaxe.zip", "destino": "goldnaxe.zip", "tratamiento": "copiar" }
  ]
}
```

**`identidad.origen` le dice a `install` a quién creerle:**

| `origen` | Qué hace `install` |
|---|---|
| `mame` | Consulta `mame -listxml <set>` en la máquina de destino y usa **su** respuesta. Si `mame` no está instalado, cae a `campos` sin fallar. |
| `declarada` | **Nunca consulta.** Usa `campos` tal cual. No hay autoridad a la que preguntar, o el usuario decidió no seguirla. |

Con `origen: mame`, los `campos` viajan igual: son el respaldo para una máquina sin MAME
y dejan el bundle legible sin dependencias.

**Si el usuario editó cualquier campo de identidad, el origen pasa a `declarada`.** Es
por juego, no por campo: quien pisa deliberadamente al catálogo quiere que esa decisión
sobreviva el viaje, y una regla por campo se vuelve imposible de razonar.

`artefactos[].tratamiento` resuelve la ambigüedad de los dos `.zip`: `copiar` para un
romset de MAME, `descomprimir` para una carpeta de MS-DOS. `install` obedece al
manifiesto, nunca a la extensión.

### Por qué campos y no el bloque ya escrito

`attract ingest` y COINDOOR son dos caminos de alta para el mismo juego de arcade
([`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md)), y tienen que producir un
bloque idéntico a partir de la misma ROM. Si cada uno escribe su propia sintaxis, van a
divergir en el primer detalle sutil — `ingest.py` documenta, por ejemplo, que deja crudo
el `<description>` de MAME con su basura de región pegada al título.

Llevando campos, **el renderizado ocurre una sola vez y de un solo lado**. La divergencia
deja de ser un riesgo a testear y pasa a ser imposible por construcción. Como efecto
lateral, COINDOOR no necesita conocer la sintaxis de `metadata.pegasus.txt`.

### Los archivos del juego van o no van — lo elige quien exporta

La ROM es **opcional y se decide por bundle**, porque el peso no tiene nada que ver con
el resto del contenido:

| Caso | Orden de magnitud |
|---|---|
| Cartucho de NES, romset simple de MAME | KB a pocos MB |
| Romset de MAME con CHD (`mok`) | cientos de MB a GB |
| Disco de PSX (`.bin`/`.cue`, `.chd`, multi-disco) | cientos de MB a varios GB |

**El corte no es por sistema.** Un romset de MAME con CHD pesa lo mismo que un PSX; la
decisión es caso por caso, del lado de quien exporta.

Consecuencias de que sea opcional:

- El manifiesto **declara si los archivos van incluidos** y cuáles. No se deduce
  mirando el zip.
- Un juego puede ocupar más de un archivo (`.bin` + `.cue`, multi-disco) o una carpeta
  entera (`CONVENCION` §1.2, caso 3). El bundle transporta la unidad completa o ninguna:
  media ROM no sirve.

#### Juegos de varios archivos: el manifiesto declara el tratamiento

Un juego que vive en una carpeta —MS-DOS con su `.exe`, sus `.cfg` y sus assets— se
empaqueta comprimiendo **la carpeta padre**, cuyo nombre es la identidad del juego
(`CONVENCION` §1.2, caso 3). Al instalar, ATTRACT la descomprime en su lugar.

Eso crea una ambigüedad que hay que resolver explícitamente: **dentro del bundle van a
convivir dos `.zip` que se tratan al revés.**

| Origen | Dentro del bundle | Qué hace `install` |
|---|---|---|
| Romset de MAME (`goldnaxe.zip`) | `.zip` | **Copiar tal cual.** MAME lee el zip; descomprimirlo rompe el romset. |
| Carpeta de MS-DOS (`DOT/`) | `.zip` | **Descomprimir.** El juego es la carpeta; dejar el zip lo deja sin lanzar. |

Por la extensión no se distinguen. **El manifiesto declara, por cada artefacto, si se
copia o se descomprime**, y `install` obedece al manifiesto, nunca a la extensión.

Corolario: **el `.zip` de transporte no puede aparecer en `file:`.** El bloque `game:`
referencia lo que queda instalado —la carpeta, no el contenedor—, o el juego apunta a
algo que no se puede lanzar. Es la misma clase de error silencioso que el `file:` sin
validar.
- **`attract install` tiene que verificar que la ROM esté**, porque `doctor` **no**
  valida `file:` — solo los `assets.*`. Sin ese chequeo, un bundle sin ROM instalado en
  una máquina que tampoco la tiene pasa en verde y el juego aparece en el gabinete pero
  no arranca. Es exactamente la clase de falla silenciosa que `CONVENCION` §4.4 evita en
  todos los demás campos.
- Si el archivo falta, es **aviso al instalar**, no error: el juego es válido y su ficha
  se ve entera. Lo único que no se puede es jugarlo.

### Qué NO lleva, y por qué

- **La cabecera del sistema.** Su `launch:` es de otra máquina (ADR-0018). El bundle
  **exige** que la colección ya exista y falla explícito si no.
- **Las revistas, ni el archivo ni la referencia.** Lo que COINDOOR guarda es una pista de
  la IA sobre en qué publicaciones de la época pudo haber notas del juego: sirve para
  buscarlas más adelante, no para el gabinete. Es **dato interno** y el `data.json` del
  bundle sale sin `mags[]`.

  Llevar la referencia sería peor que no llevarla: apuntaría a una revista que el receptor
  casi nunca tiene, y el theme mostraría un vínculo que no resuelve. Sin `mags[]`, el
  gabinete dice "Sin cobertura en revistas", que es exactamente lo que pasa.

### Cómo se instala

Un comando nuevo del lado de ATTRACT — `attract install <bundle>.zip`:

1. Lee `bundle.json` y verifica que la colección de destino exista.
2. Resuelve la identidad según `identidad.origen` y **renderiza** el bloque `game:` con
   el mismo código que usa `ingest`.
3. Mergea el bloque en el `metadata.pegasus.txt` de la colección.
4. Copia `media/<set>/` e instala los artefactos según su `tratamiento`.
5. Comprueba que `file:` resuelva —`doctor` no lo mira— y corre `doctor` sobre lo
   instalado.

Si `doctor` da error, revierte.

Un juego que ya existe se pisa entero, sin preguntar: es lo que manda `CONVENCION` §3.3.

## Alternativas consideradas

### A. COINDOOR escribe directo en el árbol de la librería

- A favor: cero formato intermedio, cero comando nuevo en ATTRACT.
- En contra: obliga a que COINDOOR tenga acceso de escritura al filesystem de la
  librería, o sea a correr en la misma máquina.
- **Descartada porque:** el resultado no se puede compartir. El trabajo de cargar un
  juego —lo más caro del sistema— queda encerrado en una instalación, y cada dueño de un
  gabinete lo rehace. Además ata COINDOOR a una topología de máquinas que hoy no está
  decidida.

### B. ATTRACT expone una API que COINDOOR llama para crear el juego

- A favor: instalación transaccional, validación inmediata, sin artefacto que gestionar.
- En contra: convierte una CLI stdlib en un servicio con ciclo de vida y despliegue.
- **Descartada porque:** contradice el límite de cero dependencias de ATTRACT y no
  resuelve el problema que importa. Una API entrega un juego a *una* máquina; un archivo
  se comparte, se guarda y se reinstala. La portabilidad es el objetivo, no un extra.

### C. Un solo bundle con la colección entera

- A favor: un archivo por sistema, menos piezas que mover.
- En contra: cientos de juegos por archivo, imposible de compartir de a partes.
- **Descartada porque:** el trabajo se hace de a un juego (`mission.md`) y el
  intercambio también sucede de a uno — alguien carga un juego y lo comparte. Un bundle
  por colección obliga a mover gigabytes para entregar un juego, y arrastra la cabecera
  del sistema, que no es portable.

### D. El bundle transporta las revistas, o al menos su referencia

- A favor: verdaderamente autocontenido; el receptor ve la nota sin conseguir nada más.
- En contra: `micromania-34` pesa **142 MB** contra 63 MB del juego completo y se
  duplicaría en cada juego que esa revista cubre. Llevar solo la referencia pesa nada,
  pero apunta a algo que el receptor no tiene.
- **Descartada porque:** el archivo replica dentro del bundle justo lo que ADR-0024 evitó
  en el disco, y la referencia sola es una promesa que no se cumple. Lo que COINDOOR
  guarda es una pista para buscar la revista después, no un asset del juego. El receptor
  vincula las suyas con `attract mags --apply`.

## Consecuencias

**Positivas**

- El trabajo de cargar un juego se hace una vez y lo usa cualquiera con ATTRACT.
- COINDOOR y la librería se desacoplan: no necesitan compartir máquina ni filesystem.
- El bundle es archivable: sirve de respaldo y permite reinstalar sin COINDOOR.
- La entrega es inspeccionable — un `.zip` se abre y se mira, a diferencia de una
  llamada de API.

**Coste asumido**

- ATTRACT gana un comando (`install`) y un formato que mantener. Es la mitad de lo que
  hay que "definir de ambos lados".
- COINDOOR no puede garantizar que el bundle instale bien en otra máquina: el veredicto
  final de `doctor` ocurre allá. Se mitiga validando contra el contrato antes de zipear,
  no se elimina.
- **El bundle no es reproducible desde la librería.** Instalar pierde la procedencia
  ([`ADR-0002`](0002-procedencia-interna.md)), así que quien recibe un juego no puede
  volver a editarlo en COINDOOR con el mismo detalle. Si compartir-y-seguir-editando
  pasa a ser un caso de uso, esto se replantea.
- Un video de 53 MB domina el peso cuando no van los archivos del juego. Comprimir no
  ayuda: los `.mp4`, `.jpg` y las ROMs empaquetadas ya están comprimidos, así que el zip
  es un contenedor, no un compresor.
- **Dos bundles del mismo juego pueden no pesar lo mismo ni contener lo mismo.** El
  manifiesto es la única forma de saber qué hay adentro sin descomprimir; que sea
  legible sin abrir el zip entero deja de ser un lujo.
- **Con `origen: mame`, instalar no es determinista.** El mismo bundle en dos máquinas
  con versiones distintas de MAME puede producir títulos distintos. Es deliberado —MAME
  es la autoridad y su versión más nueva suele ser la correcta— pero significa que el
  bundle no congela el resultado. Con `origen: declarada` sí lo congela.
- Incluir los archivos del juego convierte al bundle en un vehículo de distribución de
  ROMs. **Política del proyecto:** los bundles con juego se mueven entre máquinas
  propias; a un tercero solo si acredita la licencia del original. No es una restricción
  que el software imponga —no puede— sino la razón por la que la opción de incluir o no
  los archivos existe y está a la vista en la pantalla de export.

- Para las plataformas que MAME no conoce, `install` deja de ser solo un instalador y
  pasa a ser **el camino de alta**: el bloque `game:` del bundle es la única fuente de
  esa metadata ([`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md)).

**Qué habría que revisar si esto se replantea**

- Si aparece la necesidad de que quien recibe un bundle lo siga editando, hace falta que
  el bundle transporte el modelo de COINDOOR y no solo el artefacto de ATTRACT.
- Si el intercambio entre personas nunca ocurre y COINDOOR siempre corre junto a la
  librería, la alternativa A es más simple y este ADR sobra.

## Referencias

- ATTRACT `docs/CONVENCION.md` §1.2 (nombre de carpeta: archivo único, romset, o directorio), §1.3, §3.3, §4.4.
- ATTRACT `src/attract/doctor.py` — valida `assets.*` pero **no** `file:`.
- ATTRACT `src/attract/cli.py` — `attract mags [ruta] [--apply]` vincula revistas del lado del receptor.
- ATTRACT ADR-0018 (`launch:` absoluto), ADR-0024 (`_magazines/` fuera del árbol).
- Medición: `library/arcade/media/goldnaxe/` 63 MB · `library/_magazines/micromania-34/` 142 MB.
- [`ADR-0001`](0001-contrato-coindoor-attract.md) — qué se valida y contra qué.
