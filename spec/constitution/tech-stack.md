# Tech stack y convenciones

> **Estado:** el stack está decidido. Lo que no está verificado va como
> `<PENDIENTE:>` — no lo completes por analogía con otros proyectos.

## Tecnologías

| Capa | Tecnología | Versión | ADR |
|---|---|---|---|
| Lenguaje / runtime | Python | 3.12 | [`0007`](../decisions/0007-fastapi-como-framework-backend.md) |
| Framework backend | FastAPI + Uvicorn | — | [`0007`](../decisions/0007-fastapi-como-framework-backend.md) |
| Validación en el borde | Pydantic v2 | — | [`0007`](../decisions/0007-fastapi-como-framework-backend.md) |
| Persistencia | **Sin base de datos.** Un `game.json` por juego | — | [`0008`](../decisions/0008-persistencia-en-archivos.md) |
| Trabajos largos | `ThreadPoolExecutor` en proceso | — | [`0010`](../decisions/0010-jobs-en-proceso.md) |
| HTTP saliente | httpx (sincrónico) | — | [`0006`](../decisions/0006-fuentes-externas-multiproveedor.md) |
| PDF → páginas | pymupdf | — | — |
| Imágenes / miniaturas / acento | Pillow | — | — |
| Configuración | pydantic-settings + `.env` fuera del repo | — | — |
| Gestor de dependencias | uv | — | — |
| Tests | pytest + `TestClient` + `httpx.MockTransport` | — | — |
| Lint / format | ruff | — | — |
| Tipos | mypy, estricto en `lib/domain/` y `lib/providers/` | — | — |
| Ejecución | Un proceso en `127.0.0.1`, sirve API + build del front | — | [`0009`](../decisions/0009-proceso-local-en-loopback.md) |

**Sin Docker, sin Redis, sin colas, sin object storage, sin CDN, sin monitoring.** Cada
uno tiene su motivo en [`ADR-0009`](../decisions/0009-proceso-local-en-loopback.md) y
[`ADR-0010`](../decisions/0010-jobs-en-proceso.md); ver también §Límites duros.

## Frontend

Decidido en [`docs/claude_diseño/`](../../docs/claude_diseño/README.md). Detalle en
[`frontend-architecture.md`](frontend-architecture.md).

| Capa | Tecnología |
|---|---|
| Framework | React 18 |
| Build | Vite |
| Lenguaje | TypeScript `strict` |
| Estilos | CSS Modules + `tokens.css`. **Sin Tailwind** |
| Estado servidor | TanStack Query v5 |
| Router | React Router v6 |
| Formularios | react-hook-form + zod |
| Tests | Vitest + Testing Library |

**Sin librerías de componentes.** Los bordes 3D `outset`/`inset` del look DOS se
expresan con CSS plano y cualquier librería moderna los rompe.

**Sin autenticación en el cliente:** sin ruta de login, sin token, sin interceptor de 401,
sin lógica de refresh. Es un límite duro, no una simplificación provisional.

## Archivos / módulos clave

> Estructura acordada. No existe todavía: la crean las features
> [003](../features/003-base-frontend/spec.md), [004](../features/004-dominio-y-contrato/spec.md)
> y [005](../features/005-esqueleto-backend/spec.md).

```
frontend/src/
  lib/domain/       contract.json · fielddefs.json · types.ts
                    completeness.ts · validation.ts
  lib/api/          client.ts + un módulo por recurso
  components/dos/   primitivas visuales, sin lógica de negocio
  features/<pantalla>/
  hooks/
backend/
  api/              routers + DTOs Pydantic + errores
  services/         reglas de negocio
  store/            archivo.py (escritura atómica) · juegos · sistemas · cuotas · migracion
  lib/domain/       completeness.py · validation.py · naming.py
  lib/providers/    base · registro · http · cortocircuito · orquestador · api/ scrape/ ia/
  lib/bundle/       seleccion · staging · datajson · verify · pack · manifest
  lib/jobs/         registro · ejecutor
  lib/media/        thumbs · accent · rasterize
```

`lib/domain/contract.json` y `lib/domain/fielddefs.json` **son un solo par de archivos**
que consumen el front y el back
([`ADR-0011`](../decisions/0011-fielddefs-json-compartido.md)). No se copian.

## Comandos

> Los define la feature [003](../features/003-base-frontend/tasks.md) y
> [005](../features/005-esqueleto-backend/tasks.md). Esta tabla refleja lo que hoy corre.

| Comando | Qué hace |
|---|---|
| `uv run coindoor` | Levanta el proceso en `127.0.0.1:8765` y abre el navegador |
| `uv run pytest` | Tests del backend |
| `uv run ruff check .` · `uv run ruff format .` | Lint y formato |
| `uv run mypy backend/lib` | Tipos, estricto solo en `lib/` |
| `npm run dev` | Vite en `5173`, con proxy de `/api` a `8765` |
| `npm run build` | Build estático que sirve el backend |
| `npm test` | Vitest |

## Modelo de datos / dominio

> Verificado contra `docs/CONVENCION.md` §1–§2 de ATTRACT y contra
> `library/arcade/media/goldnaxe/`, el único juego cargado entero y por eso la
> **definición operativa de COMPLETO**.

### Estructura en disco que produce el export

```
<raíz-librería>/
├─ _magazines/<revista>-<número>/      # FUERA del árbol de sistemas (ADR-0024)
│  ├─ magazine.json
│  ├─ cover.jpg                        # la tapa va en la raíz…
│  └─ pages/p001.jpg … pNNN.jpg        # …las páginas en pages/
└─ <sistema>/                          # arcade/, nes/, pc/…
   ├─ metadata.pegasus.txt             # cabecera + un bloque game: por juego
   ├─ _synopsis/<set>.json             # fuente de summary:, NO lo lee el theme
   └─ media/<juego>/                   # PLANO, auto-descubierto por Pegasus
      ├─ boxFront.jpg  marquee.jpeg  poster.jpg  video.mp4
      ├─ data.json
      └─ _manual/manual.pdf + pNNN.png
```

`media/<juego>/` se llama como **el archivo físico sin extensión** (`goldnaxe.zip` →
`goldnaxe`), nunca como el título de presentación (`CONVENCION` §1.2).

### Bloque `game:` en `metadata.pegasus.txt`

```
game: <título>        # OBLIGATORIO — sin esto doctor rechaza la entrada
file: <set>.zip
developer / publisher / genre / players / release / summary    # opcionales
x-set: <set>
x-formato: <Arcade | GD-ROM | …>       # OBLIGATORIO — alimenta el badge FORMATO
```

Cabecera del sistema: `collection:`, `shortname:`, `launch:` — **ruta absoluta
obligatoria** (ADR-0018). Una app de GUI en macOS no hereda el `PATH` del shell.

### `data.json` — los datos ricos (ADR-0001 y ADR-0015 de ATTRACT)

```
accent: "#d4a017"          # color de acento del juego (ADR-0013)
accent2: "#3d2f08"         # segundo color, no es opcional-por-simetría
review: null | {           # null = no hay reseña; el bloque entero dice "Sin Información"
  score: 0..100,
  cats: { graficos: 85, adiccion: 92, … }   # PARCIAL a propósito: las que faltan → "-"
}                          # las 6 posibles: originalidad, graficos, adiccion,
                           # sonido, dificultad, animacion
cheats: {                  # grupos LIBRES (ADR-0020), no un enum cerrado
  <grupo>: [ { name: str, input: str } ]    # combos, codes, secretos, dos_jugadores…
}
manual: [ { file: "manual.pdf", pages: ["p001.png", …] } ]   # ARRAY (ADR-0023)
```

`mags[]` existe en el contrato pero **COINDOOR no lo escribe nunca**. La revista que
sugiere la IA es una pista para conseguirla después: dato interno, no asset del juego. El
`data.json` del bundle sale sin ese campo
([`ADR-0003`](../decisions/0003-bundle-por-juego.md)).

**El modelo del cliente se ajusta al contrato, no al revés.** Las tres correcciones al
paquete de diseño —`review`/`cheats` estructurados, `accent2`, revistas dentro del
alcance— están en [`frontend-architecture.md`](frontend-architecture.md) §Deltas.

`cheats` y `review` **no son texto libre**: son estructuras. El formulario que las
edite no es un `textarea`.

### Cadena de fallback del cover (`CONVENCION` §2.2)

```
boxFront → poster → marquee → genérico
```

Ningún asset visual es obligatorio por separado. Un arcade no tiene caja; se apoya en
`marquee` y `poster`. **Ningún bloque de la pantalla desaparece**: sin dato muestra
`"Sin Información"` (texto) o `"No Disponible"` (juegos/trucos/manuales), y `mags: []`
tiene mensaje propio, `"Sin cobertura en revistas"`.

### Qué significa COMPLETO — política de COINDOOR

Definido en `docs/claude_diseño/data-model.md` §3. **Es más estricto que el contrato de
ATTRACT y eso es deliberado**: ATTRACT solo exige `title` y `x-formato`; COINDOOR exige lo
que hace que un juego se vea bien en el gabinete.

**Obligatorio, exactamente esto:** los 7 campos de identidad (título, año, desarrollador,
editor, género, jugadores, formato), imagen `caratula`, imagen `poster`, texto `sinopsis` y
el color de acento.

**Opcional, nunca bloquea:** marquesina, logo, captura, video, reseña, trucos, manuales.

Consecuencia a tener presente: el contrato tiene cadena de reemplazo
`boxFront → poster → marquee → genérico`, así que un juego con solo marquesina se ve
correcto en el gabinete y COINDOOR igual lo marca incompleto. Es una decisión de calidad
propia, no un requisito heredado, y como tal se puede revisar.

### Mapeo de nombres: UI ↔ contrato

Los nombres de archivo del contrato distinguen mayúsculas y **el usuario nunca los
escribe**. La traducción ocurre al exportar:

| UI (`ImageKey`) | Archivo en `media/<set>/` |
|---|---|
| `caratula` | `boxFront` |
| `marquesina` | `marquee` |
| `poster` | `poster` |
| `logo` | `logo` |
| `captura` | `screenshot` |
| `video` | `video` |

### Dos ejes de estado (`CONVENCION` §4)

- **VÁLIDA** — no rompe nada técnico: NFC, sin CRLF, nombres legales en **Windows**
  (el estándar siempre, por ser el más estricto), JSON bien formado. Fallar es **error**.
- **COMPLETA** — tiene todos los datos deseables. Fallar es **faltante**, no error.

Son ortogonales: el juego pelado tiene que ser VÁLIDO siempre (§4.3), porque la mayoría
de la colección se queda incompleta para siempre y eso es el caso normal, no la falla.

### Identidad: física vs. presentación

- **Física** (nombre de carpeta y `set`): sale siempre del archivo o directorio real en
  disco (`CONVENCION` §1.2). Determinista, en todas las plataformas, nunca se escribe.
- **Presentación** (`game:`, `developer`, `publisher`, `genre`, `players`, `release`,
  `x-formato`): para arcade la da `mame -listxml`, que COINDOOR usa como default cuando
  el binario está disponible; para el resto la produce COINDOOR
  ([`ADR-0004`](../decisions/0004-coindoor-fuente-identidad-no-mame.md)).

**Arcade tiene dos caminos de alta**: `attract ingest` desde la terminal y COINDOOR con
su bundle. Los dos producen el mismo bloque porque **el bundle transporta campos, no
sintaxis**: quien renderiza `metadata.pegasus.txt` es siempre ATTRACT. COINDOOR no
escribe formato Pegasus en ningún lado. El último en escribir gana (`CONVENCION` §3.3).

### `bundle.json` — el manifiesto del export

Es la hoja de instrucciones de `attract install`
([`ADR-0003`](../decisions/0003-bundle-por-juego.md)):

- `coleccion`, `set`, `contrato` — destino y versión con la que se armó.
- `identidad.origen`: `mame` (install consulta `mame -listxml` y le cree; si no está
  MAME, cae a los campos) o `declarada` (install nunca consulta). Editar cualquier campo
  de identidad mueve el juego entero a `declarada`.
- `identidad.campos` — título, developer, publisher, genre, release, players, x-formato.
- `artefactos[].tratamiento`: `copiar` (romset de MAME) o `descomprimir` (carpeta de
  MS-DOS). **Por la extensión no se distinguen**: los dos son `.zip`.

### Procedencia — solo dentro de COINDOOR

Cada campo guarda si lo cargó el usuario o si vino de una sugerencia aceptada. **No
viaja al export**: `CONVENCION` §3.1 decide no distinguir origen y §3.3 que todo
reproceso pisa. Ver [`ADR-0002`](../decisions/0002-procedencia-interna.md).

## Convenciones

- El contrato de ATTRACT se lee de un archivo de datos versionado, nunca se replica en
  código ([`ADR-0001`](../decisions/0001-contrato-coindoor-attract.md)).
- Un campo con procedencia `manual` no se reemplaza sin confirmación explícita del
  usuario. Vale también para los procesos automáticos.
- El usuario nunca escribe un nombre de archivo ni de carpeta. Los nombres salen de la
  regla de `CONVENCION` §1.2 y llevan restricciones que no perdonan: NFC (macOS
  descompone y no avisa), nada de `< > : " / \ | ? *`, nada de `CON PRN AUX NUL COM1-9
  LPT1-9`, sin terminar en espacio ni punto. Un error de capitalización en un asset no
  rompe nada visible: el juego simplemente no muestra la imagen en el gabinete.
- **Todo lo que sale a la red es a pedido del usuario.** Nada corre en segundo plano, ni al
  abrir una ficha, ni al guardar.
- **La latencia no es un problema de este producto.** Se trabaja de a un campo de un juego
  por vez, con una persona esperando a propósito el resultado que pidió. Los timeouts
  existen para que una conexión colgada termine alguna vez, no como presupuesto de
  velocidad. **No se agrega complejidad para ahorrar segundos**: ni streaming de
  resultados, ni respuestas incrementales, ni cachés que no sirvan para ahorrar cuota.
- La sinopsis se escribe en `_synopsis/<set>.json` y la aplica `attract synopsis`. No se
  toca `summary:` directamente (ADR-0011 de ATTRACT).

### Del backend

- **Toda escritura de un `game.json` es atómica**: temporal → `fsync` → `os.replace()`.
  Nunca escribir sobre el archivo en su lugar
  ([`ADR-0008`](../decisions/0008-persistencia-en-archivos.md)).
- **Toda lectura valida** contra su modelo Pydantic y falla nombrando el archivo. El
  formato invita a editarlo a mano; asumí que va a pasar.
- **`status` no se guarda nunca**: se calcula al leer, con la prioridad fija
  `error > incomplete > ready`.
- **Handlers finos.** La lógica va en `services/`, nunca en la ruta. `lib/` no conoce
  HTTP ni el almacenamiento.
- **Routers sincrónicos (`def`) por defecto.** `async` solo donde haya fan-out real de
  red: subprocesos, pymupdf y lectura de archivos son sincrónicos y bloquean el loop.
- **Subprocesos con lista de argumentos, jamás `shell=True`.**
- **Ningún proveedor implementa su propio reintento.** La política vive en un solo lugar,
  `lib/providers/http.py`
  ([`ADR-0006`](../decisions/0006-fuentes-externas-multiproveedor.md)).
- **Un solo patrón de job** para manuales, export, sugerencias y revistas
  ([`ADR-0010`](../decisions/0010-jobs-en-proceso.md)).
- **El staging del export se limpia siempre**, incluso si el export falla a la mitad.
- **Las credenciales viven fuera del repo** y la aplicación arranca sin ellas: sin claves,
  los proveedores de API se saltean, no rompen.

## Límites duros

- **Prohibido reimplementar la lógica de completitud de ATTRACT** — el contrato se
  consume como dato y la CLI de ATTRACT es la autoridad final
  ([`ADR-0001`](../decisions/0001-contrato-coindoor-attract.md)).
- **Sin autenticación, usuarios, roles ni permisos.** Un solo usuario, su máquina. Si
  aparece la necesidad, es un cambio de misión, no una feature.
- **Sin carga masiva ni operaciones en lote.** Un juego por vez.
- **Sin trabajos en segundo plano, colas ni workers.** Se descartaron al confirmar que
  no hay carga masiva; reintroducirlos exige un ADR.
- **COINDOOR no corre en el gabinete.** El gabinete es offline y su runtime es MAME
  vanilla. Todo lo que necesite red vive de este lado.
- **No escaneamos ni producimos revistas.** Vincular un juego con una revista sí está
  dentro del alcance; digitalizarla es otro subsistema.
- **Los bundles que incluyen los archivos del juego son para mover la colección entre
  máquinas propias.** A un tercero, solo si acredita la licencia del original
  ([`ADR-0003`](../decisions/0003-bundle-por-juego.md)). Por eso incluirlos es una opción
  explícita en el export y nunca un default.
- **Cargar, editar y exportar funcionan sin internet.** Solo las sugerencias salen a
  la red.
- **Sin base de datos.** Descartadas SQLite (con y sin ORM), las bases documentales
  embebidas y el archivo único con toda la colección
  ([`ADR-0008`](../decisions/0008-persistencia-en-archivos.md)). Vale hasta unos pocos
  miles de juegos; a partir de ahí se replantea.
- **Sin Docker.** Rompe las tres cosas que el producto necesita: leer ROMs por ruta
  absoluta, ejecutar el `mame` del host y ejecutar el `attract` del host
  ([`ADR-0009`](../decisions/0009-proceso-local-en-loopback.md)).
- **Sin Redis, sin broker, sin object storage, sin CDN, sin monitoring.** Sus usos reales
  acá son un `dict` y un archivo JSON.
- **El proceso escucha en `127.0.0.1`, nunca en `0.0.0.0`.** Ese bind, más la validación
  del header `Host` y la ausencia de CORS permisivo, es la frontera que reemplaza a la
  autenticación ([`ADR-0009`](../decisions/0009-proceso-local-en-loopback.md)). Exponerlo
  a la red sería un cambio de misión.
- **Ninguna regla del contrato ni de la política de completitud se escribe en código.**
  Salen de `contract.json` y `fielddefs.json`, que consumen el front y el back
  ([`ADR-0011`](../decisions/0011-fielddefs-json-compartido.md)).
- **La salida de `attract doctor` no se parsea.** Solo su código de salida
  ([`ADR-0012`](../decisions/0012-verificacion-attract-por-subproceso.md)).
- **Descartados para el backend:** Django, Flask, `http.server` de stdlib y Node
  ([`ADR-0007`](../decisions/0007-fastapi-como-framework-backend.md)); Celery, RQ y
  `BackgroundTasks` ([`ADR-0010`](../decisions/0010-jobs-en-proceso.md)).

## Pendientes que bloquean

1. **`contract.json` no existe todavía.** Hay que traerlo a mano de ATTRACT hasta que lo
   publique ([`ADR-0005`](../decisions/0005-contrato-vendoreado-vs-politica-propia.md)).
   Bloquea la feature [004](../features/004-dominio-y-contrato/spec.md).
2. **Credenciales de ScreenScraper y MobyGames.** Las dos APIs piden cuenta y tienen
   cuotas. Hay que decidir dónde viven las claves y qué pasa cuando se agota la cuota
   ([`ADR-0006`](../decisions/0006-fuentes-externas-multiproveedor.md)). Bloquea la
   feature [002](../features/002-sugerencias-multiproveedor/spec.md), no el arranque.
3. **Qué modelo de IA.** Afecta al coste por juego y a la voz de los textos. Bloquea la
   feature 002, no el arranque.

**Ya no bloquea:** el stack de backend, decidido en los ADRs
[0007](../decisions/0007-fastapi-como-framework-backend.md) a
[0012](../decisions/0012-verificacion-attract-por-subproceso.md). El análisis completo,
con la comparación de alternativas, está en
[`docs/arquitectura/`](../../docs/arquitectura/README.md).

## Contradicciones abiertas del paquete de diseño

`docs/claude_diseño/data-model.md` §1 y §6 son anteriores a los deltas y a las features
001–002, y hoy contradicen a esta constitución en varios puntos. **Manda lo de acá.**
El detalle está en [`docs/arquitectura/`](../../docs/arquitectura/README.md) §16.1; el
resumen accionable:

| Qué dice el diseño | Qué vale |
|---|---|
| `GET /suggestions/:key` sincrónico | `POST` → `jobId` + polling (feature 002) |
| `accent/detect` → `{color}` | `{color, color2}` (delta D2) |
| `download-and-link`, estado `broken` | `link`, y `broken` no existe (delta D3) |
| `texts.resena` / `texts.trucos` como texto | Estructuras `ReviewField` / `CheatsField` (delta D1) |
| `fieldDefs.ts` | `fielddefs.json` ([`ADR-0011`](../decisions/0011-fielddefs-json-compartido.md)) |

**Sin decidir todavía**, y hace falta antes de la feature 001:

- **`identitySource` tiene dos valores y la realidad tiene tres.** `types.ts` dice
  `'catalog' | 'manual'`; [`ADR-0004`](../decisions/0004-coindoor-fuente-identidad-no-mame.md)
  reconoce MAME, ScreenScraper por hash y declarada; el bundle usa `'mame' | 'declarada'`.
  Una identidad resuelta por hash es `catalog` en la UI pero **tiene que exportarse como
  `declarada`**, porque `install` solo sabe consultar MAME. Falta escribir ese mapeo.
- **`players` es `string` en la UI y número en el bundle.** Valores como `"1-2"` o
  `"2 alternados"` no son enteros: hay que decidir qué se escribe en `x-formato`.
