---
id: 0004
title: COINDOOR es la fuente de identidad de los juegos sin catálogo autoritativo
status: accepted
date: 2026-08-10
supersedes: null
superseded-by: null
tags: [data, proceso]
---

# 0004 — COINDOOR es la fuente de identidad de los juegos sin catálogo autoritativo

## Contexto

`attract ingest` da de alta un juego preguntándole a `mame -listxml` quién es. Funciona
para arcade y para nada más: MAME no conoce MS-DOS, PSX, NES ni PC. Para esas
plataformas ATTRACT **no tiene camino de alta**
([`ATTRAC-015`](../../docs/attract/ATTRAC-015-carga-guiada/) §Por qué, hueco 1) y el
bloque `game:` se escribe a mano, sin validación.

`ingest.py` es explícito sobre por qué: *"identidad real, no inventada… si no puede
identificarla con certeza, no agrega nada. Fallar explícito, nunca escritura parcial ni
silenciosa."*

`ATTRAC-015 plan.md` propone una salida —una bandera `--titulo` en `ingest`— y la marca
como bloqueada: *"es la primera vez que ATTRACT acepta una identidad que nadie
autoritativo confirma, al revés de ADR-0004… necesita ADR propio antes de implementar."*

**Esa lectura de ADR-0004 es más amplia que el ADR.** ADR-0004 resuelve cómo tratar un
set merged de MAME —una página por familia, varias versiones lanzables— y no establece
que toda identidad deba venir de una autoridad externa. El obstáculo real es la
filosofía de `ingest`, que es más acotada.

## Decisión

**Para las plataformas que ningún catálogo cubre, la metadata de presentación la produce
COINDOOR y viaja dentro del bundle como un bloque `game:` ya armado.**

`attract install` es el camino de alta de esas plataformas.
[`ADR-0003`](0003-bundle-por-juego.md) ya lo define instalando el bloque; acá se afirma
que para no-MAME ese bloque es **la única fuente** y no una copia de algo verificable en
otro lado.

`attract ingest` no se toca. Sigue siendo el camino de MAME, con su regla intacta.

### Para arcade conviven los dos caminos

Un juego de MAME se puede dar de alta por `attract ingest` —directo, desde la terminal,
como hoy— o por COINDOOR y su bundle. Las dos rutas son de primera clase y ninguna
reemplaza a la otra: `ingest` es más rápido cuando solo se quiere el bloque; COINDOOR es
el camino cuando además hay media, textos y manual que cargar.

Eso obliga a fijar dos reglas, o el mismo juego termina existiendo dos veces con datos
distintos:

1. **Cuando MAME conoce el set, su respuesta es el default también dentro de COINDOOR.**
   COINDOOR consulta `mame -listxml` si el binario está disponible y precarga el
   formulario con lo que devuelve. Sobrescribir un campo que MAME confirmó es una acción
   deliberada del usuario, no un descuido de tabulador. Si MAME no está instalado en esa
   máquina, se cae al camino declarado.
2. **El último en escribir gana, sin excepción.** Instalar un bundle sobre un juego que
   `ingest` ya había creado lo pisa entero, y al revés. Es lo que manda `CONVENCION`
   §3.3 y no se inventa una regla nueva para este caso.

### Lo que NO cambia: la identidad física

`CONVENCION` §1.2 deriva el nombre de la carpeta del **archivo o directorio real**, no
del título. `DOT/` se llama `DOT` porque así se llama la carpeta en disco, igual que
`goldnaxe` se llama así por `goldnaxe.zip`. Eso es determinista y sigue sin inventarse
en ninguna plataforma.

Lo que COINDOOR aporta es la **metadata de presentación**: título, año, desarrollador,
editor, género, jugadores, formato. Son los campos que la pantalla muestra, no los que
resuelven qué archivo se lanza.

La distinción es lo que hace tolerable la decisión: un error de presentación se ve y se
corrige; un error de identidad física rompe el lanzamiento y contamina las rutas.

### El conjunto "sin catálogo" es más chico de lo que parecía

ScreenScraper identifica ROMs **por hash** (CRC32/MD5/SHA1), no solo por nombre, y cubre
NES, SNES, Genesis y PSX. O sea que las consolas **sí** tienen una autoridad externa, igual
que arcade tiene MAME ([`ADR-0006`](0006-fuentes-externas-multiproveedor.md)).

```
Arcade        →  mame -listxml
Consolas      →  ScreenScraper por hash
MS-DOS / PC   →  declarada a mano        ← el único caso sin catálogo
```

Lo que queda sin autoridad es lo que vive como **carpeta de archivos sueltos**, que no
tiene un hash único que consultar. Es un conjunto acotado, no "todo lo que no es arcade".

### La identidad nunca la propone una IA

Decidido: para los campos de identidad no hay generación automática. Un LLM que se
equivoca de juego escribe un título, un año y un desarrollador que parecen correctos,
viajan dentro de bundles a otras máquinas y nadie los vuelve a mirar. El ahorro sería de
seis campos de tipeo en el único caso que queda sin catálogo.

La IA sí produce sinopsis, reseña y trucos, donde un error se detecta leyendo y no
contamina la identidad del juego.

## Alternativas consideradas

### A. Agregar `--titulo` y compañía a `attract ingest` (la propuesta de ATTRAC-015)

- A favor: no depende de COINDOOR; sirve desde la terminal.
- En contra: mete siete campos de presentación como banderas de CLI y obliga a `ingest`
  —cuya única razón de ser es consultar a MAME— a tener un modo en que no consulta nada.
- **Descartada porque:** es un formulario disfrazado de flags, y el formulario ya existe
  del lado de COINDOOR, con previews y validación contra el contrato. Duplicar la
  captura en dos interfaces garantiza que diverjan. Además fuerza el cambio filosófico
  justo en el módulo cuya identidad es "le pregunto a la autoridad".

### B. Sumar un catálogo externo (No-Intro, TOSEC) como segunda autoridad

- A favor: mantiene intacta la regla de identidad verificada, ahora para consolas.
- En contra: cubre ROMs de consola por hash, pero no un juego de MS-DOS que vive como
  carpeta de archivos sueltos — justo el caso que motiva este ADR.
- **Descartada como requisito, no como idea:** no resuelve el caso que bloquea, y suma
  una base de datos que mantener. Encaja mejor como **fuente de sugerencias dentro de
  COINDOOR** —una propuesta más que el usuario acepta o rechaza— que como autoridad que
  habilita el alta.

### C. Soportar solo las plataformas que MAME conoce

- A favor: cero decisiones nuevas, la regla de ATTRACT queda intacta.
- En contra: deja afuera NES, PC, PSX y MS-DOS.
- **Descartada porque:** contradice la misión. La colección no es solo arcade, y
  `ATTRAC-015` ya identifica la falta de camino de alta para no-MAME como el hueco más
  grande del proceso actual.

## Consecuencias

**Positivas**

- Se destraba el alta de no-MAME sin tocar `ingest` ni su garantía.
- Arcade conserva su camino rápido de terminal y gana el camino con interfaz. Quien ya
  usa `ingest` no tiene que cambiar de herramienta.
- `ATTRAC-015` pierde una tarea: la bandera `--titulo` y su ADR bloqueante dejan de
  hacer falta si el alta entra por `install`.
- La identidad declarada nace donde hay una persona mirando, no en un script.
- Un solo lugar donde se capturan esos campos: el formulario de COINDOOR.

**Coste asumido**

- ATTRACT pasa a aceptar metadata que ninguna autoridad confirmó. Es un cambio real de
  postura, aunque acotado a los campos de presentación y con la identidad física intacta.
- **Para no-MAME, COINDOOR se vuelve dependencia dura del alta.** Sin COINDOOR, esos
  juegos se siguen cargando a mano y sin validación, como hoy.
- El origen de cada identidad tiene que verse en pantalla: no valen lo mismo una que
  confirmó MAME, una que resolvió ScreenScraper por hash y una que escribió una persona.
- Arcade tiene dos caminos de alta que deben producir el mismo bloque. **Resuelto por
  construcción**: el bundle transporta campos, no sintaxis, y ATTRACT renderiza el
  bloque con el mismo código en los dos caminos
  ([`ADR-0003`](0003-bundle-por-juego.md) §Por qué campos y no el bloque).
- COINDOOR gana una dependencia opcional del binario `mame` para poder precargar el
  formulario de arcade. Sin él sigue funcionando, con más trabajo manual.

**Qué habría que revisar si esto se replantea**

- Si aparece un catálogo que cubra bien las plataformas de carpeta, la alternativa B pasa
  de sugerencia a autoridad y este ADR se acota a lo que ese catálogo no cubra.
- Si el alta por fuera de COINDOOR se vuelve necesaria (cargar un juego sin abrir la
  interfaz), vuelve a tener sentido la alternativa A.

## Referencias

- ATTRACT `src/attract/ingest.py` — filosofía "identidad real, no inventada".
- ATTRACT `docs/CONVENCION.md` §1.2 — el nombre sale del archivo o directorio real.
- ATTRACT ADR-0004 — identidad en sets merged; acotado a MAME, no es una regla general.
- [`ATTRAC-015 plan.md`](../../docs/attract/ATTRAC-015-carga-guiada/plan.md) §Decisiones — la propuesta `--titulo`.
- [`ADR-0003`](0003-bundle-por-juego.md) — el bundle y `attract install`.
