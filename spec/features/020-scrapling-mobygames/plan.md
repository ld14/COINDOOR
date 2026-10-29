# 020 · Scrapling y MobyGames — Plan

_Cómo se implementa lo descrito en [`spec.md`](spec.md). Respeta la `constitution/`._

## Enfoque

Un **cliente de scraping** nuevo que hereda la política de `http.py`, y un **proveedor de
MobyGames** partido en las mismas tres piezas que ArcadeDB: `cliente` (baja la página),
`parser` (HTML → datos) y `proveedor` (datos → `Candidato`). El proveedor no sabe de
Scrapling; solo recibe un `Selector`. Así el parser se prueba con una página guardada y sin
navegador.

La política (cuota, ritmo, backoff, cancelación) se **extrae** de `ProviderHttpClient` a una
base común, en vez de copiarla: la regla del backend es que ningún proveedor implementa la suya.

Con MobyGames adentro, la IA sale de las sugerencias de identidad y la precarga de MS-DOS
pasa a complementar fuentes ([`ADR-0024`](../../decisions/0024-scrapling-y-mobygames-para-pc-dos.md),
punto 4).

## Lo verificado el 2026-10-28 y 29

Búsqueda de MobyGames, probada con Pac-Man (arcade):

| | Buscador general | Navegador por plataforma |
|---|---|---|
| URL | `/search/?q={término}&type=game` | `/game/platform:{slug}/title:{término}/` |
| Resultados | `table#search-results`, 12 filas por página; cada `tr` trae el id del juego en `data-track-target-id` | Título y enlace a `/game/{id}/{slug}/`, por relevancia |
| Plataformas | Lista con el año de cada una: "Arcade (1980), VIC-20 (1981), …" | Solo la filtrada |
| Fecha | La del primer lanzamiento, en `span.text-muted`: "(May 22, 1980)" | No trae |
| Títulos alternativos | `small.text-muted` que empieza con "AKA:", separados por comas | No trae |
| Paginación | La primera página va sin `page`; la siguiente es `page=1` | — |

Un mismo título aparece en varias filas: los remakes y algunas conversiones tienen otro id.
La ficha canónica es `/game/{id}/{slug}/`.

**Prueba con Monkey Island en el buscador general:** 5.242 resultados. Las primeras filas son
secuelas y recopilaciones (*The Curse of Monkey Island*, *Monkey Island Madness*…). *The
Secret of Monkey Island* (DOS, 1990) está en la primera página, pero debajo de la séptima
fila: el buscador compara palabras sueltas y el orden no pone primero al título más parecido.
Por eso la regla no usa la posición. Confirma que la plataforma se llama "DOS" y que la lista
no se corta: *Return to Monkey Island* muestra sus diez plataformas completas.

**Prueba con cuatro juegos más de la colección:** la regla del paso 5 eligió bien en los
cuatro.

- *Teenage Mutant Ninja Turtles* (1990): dos filas con el título exacto y DOS, las dos con
  1989 como primer lanzamiento. Las separa el año de DOS: 1990 contra 1992. La fecha del
  primer lanzamiento no sirve para desempatar.
- *Out Run* (1986): MobyGames lo titula "OutRun" y coincide por el AKA "Out Run". Es la única
  fila exacta con DOS, así que se elige aunque su año de DOS (1989) no sea el de la ficha,
  que es el del arcade.
- *Mission: Impossible* (1991): cinco juegos con el mismo título y uno solo con DOS (1991).
  *Impossible Mission II* también tiene DOS, pero no pasa el nivel 1.
- *Guy Spy* (1992): la ficha dice "Guy Spy " (con un espacio de más y sin subtítulo). La
  normalización quita el espacio. Ninguna fila pasa el nivel 1, y en el nivel 2 la única que
  tiene "guy", "spy" y DOS es *Guy Spy and the Crystals of Armageddon*, con DOS (1992), el
  mismo año de la ficha. *Spycraft* (DOS 1996) queda afuera porque le falta "guy".

**Búsquedas guardadas el 2026-10-29** (`backend/tests/fixtures/mobygames/busqueda-*.html`, con
`type=game`). La regla del paso 5 elige bien en dos de las tres y deja una sin resolver:

- *Teenage Mutant Ninja Turtles* (1990): dos filas exactas con DOS, 1990 y 1992; gana la
  de 1990.
- *Guy Spy* (1992): sin fila exacta; en el nivel 2 solo queda *Guy Spy and the Crystals of
  Armageddon*, DOS 1992.
- *Monkey Island* (1990): *The Secret of Monkey Island* está en la fila 12, pero su año de
  DOS es **1992** (la fila es la edición "VGA CD-ROM") y la ficha dice 1990. Con ±1 no se
  resolvía; el 2026-10-29 se acordó **±2 solo en el nivel 2**: siempre exige la plataforma
  (DOS), todas las palabras del título y que quede una sola fila. Las otras filas con DOS
  son de 1997 y 1999, así que queda esa.

**Contra el sitio real, con el arreglo de Cloudflare** (2026-10-29, WSL, tres consultas
seguidas, cada una en su propia sesión y con el mismo perfil):

| Consulta | Ficha elegida | Tiempo | Cloudflare |
|---|---|---|---|
| *Guy Spy* (1992) | *Guy Spy and the Crystals of Armageddon*, DOS 1992 | 198 s | desafío: dos intentos fallidos, el tercero lo resolvió |
| *Teenage Mutant Ninja Turtles* (1990) | la de DOS 1990 (id 6932) | 18 s | sin desafío: usó la cookie del perfil |
| *Monkey Island* (1990) | *The Secret of Monkey Island*, DOS 1992 (id 141074) | 21 s | sin desafío |

Las tres fichas son las correctas. El desafío ahora se detecta a los 5 s del primer pedido
(antes, después del `timeout` entero); lo que queda en la primera consulta es la espera de
Scrapling después de cada clic fallido, acotada por el `timeout` (60 s). Datos que trajo:
*Guy Spy* sin jugadores en las specs de DOS y con dos soportes (disquete y CD), así que la
precarga no escribe el formato; *Monkey Island* elige la edición "VGA CD-ROM": su año (1992)
y su soporte (CD) son de esa edición, no de la de 1990.

La cookie `cf_clearance` que deja el desafío para `.mobygames.com` vence en **un año**
(medido el mismo día, después de un desafío de 187 s). Con el perfil persistente, la
primera consulta paga el desafío y las siguientes no, salvo que Cloudflare lo pida de nuevo:
cambio de IP, de navegador o una decisión suya, que no se puede prever.

**Ficha de Maniac Mansion** (guardada el 2026-10-29 en
`backend/tests/fixtures/mobygames/maniac-mansion.html`):

- El JSON-LD trae `name`, `alternateName`, `genre`, `publisher`, `gamePlatform` y
  `datePublished`, pero no el desarrollador. `datePublished` es "1987-09", el lanzamiento en
  Apple II; el de DOS es 1988 y está en la lista "Releases by Date".
- El editor **sí** se distingue por plataforma: cada editor de `#publisherLinks` lista sus
  plataformas en `data-popover`. Para DOS hay tres (Lucasfilm Games, Erbe Software y
  U.S. Gold); el `publisher` del JSON-LD mezcla los siete de todas las plataformas.
- Las specs de la ficha son de una sola plataforma (acá Apple II). `/specs/` (guardada en
  `maniac-mansion-specs.html`) las trae todas en una tabla, con un encabezado `h4` por
  plataforma. DOS tiene "Media Type: 3.5" Floppy Disk, 5.25" Floppy Disk" y los jugadores
  bajo otra etiqueta: "Number of Offline Players: 1 Player"; Apple II, NES y las demás usan
  "Number of Players Supported". Otros soportes vistos: "Floppy Disk", "Double-sided Disk",
  "Cartridge" y "Download".
- El género llega en inglés ("Adventure"), y la descripción termina con una nota de la
  tienda ("GOG release includes…").
- Lo guardado desde el navegador es el HTML del servidor, con los componentes de Vue sin
  procesar. Scrapling devuelve la página después de correr el JavaScript.

## Implementación

1. `pyproject.toml` — suma `scrapling[fetchers]>=0.5,<0.6`. `scripts/install-deps.sh` suma la
   instalación de Chromium (`scrapling install`).
2. `lib/providers/politica.py` — ritmo, backoff, cuota y `cancel_event`, extraídos de
   `http.py`. `ProviderHttpClient` pasa a usarla sin cambiar su comportamiento.
3. `lib/providers/scraping.py` — `ScrapingClient`, context manager. `get_page(url)` devuelve un
   `Selector`. Prueba HTTP (`Fetcher`) y, ante 403 o "Just a moment...", escala a una
   `StealthySession(solve_cloudflare=True, network_idle=False, user_data_dir=…)`, una por
   consulta, y recuerda el modo por proveedor y host mientras corre el proceso. El perfil
   (`games/navegador`) guarda la cookie de Cloudflare entre consultas; dos Chromium no pueden
   abrirlo a la vez, así que las sesiones van de a una y la espera atiende la cancelación.
   Cierra el navegador al salir o al cancelar. Traduce los fallos a `ProviderRejected`,
   `ProviderNotFound`, `ProviderQuotaExhausted` y `ProviderHttpError`.
4. `lib/providers/mobygames/parser.py` — con la plataforma del catálogo ("DOS"):
   - `title`, los títulos alternativos y `genre`, del JSON-LD (`name`, `alternateName`,
     `genre`).
   - `year`: el de la fila de DOS en "Releases by Date" (`#platformLinks`), no
     `datePublished`, que es el primer lanzamiento en cualquier plataforma. Es el mismo
     criterio que la búsqueda (paso 5).
   - `developer`: de `#developerLinks`; el JSON-LD no lo trae.
   - `publisher`: el primero de `#publisherLinks` cuyo `data-popover` incluye DOS.
   - `players` y `format`: del bloque de DOS en `/specs/` (desde su `h4` hasta el
     siguiente), porque la ficha muestra las specs de una sola plataforma.
     - Jugadores: "Number of Players Supported" o "Number of Offline Players". "1 Player"
       queda "1"; "1-2 Players", "1-2".
     - Soporte, a los formatos físicos de `bundle/gamejson.py`: cualquier disquete
       ("…Floppy Disk", "…-sided Disk") → `Diskette`; "Cartridge" → `Cartucho`; CD y DVD →
       `CD` y `DVD` (sus nombres en MobyGames no se vieron todavía). "Download" no tiene
       equivalente. Si los soportes dan más de un formato, la sugerencia ofrece uno por
       formato y la precarga no escribe ninguno.
   - La nota: el porcentaje de críticos ("Critics 82%"), que ya está en la escala de
     `review.score` (0 a 100, `CONVENCION` nota 3).
   - La descripción, de `#description-text`.

   No lee los atributos de los componentes de Vue (`<player-tools :platforms>`,
   `<critic-reviews :reviews>`): el navegador de Scrapling devuelve la página procesada y
   esos datos pueden no estar.
5. `lib/providers/mobygames/cliente.py` — busca con el buscador general
   (`/search/?q={título}&type=game`) y lee las 12 filas de la primera página, sin importar
   su orden. Se queda con las filas cuya lista de plataformas incluye la del catálogo
   ("DOS"), normaliza los títulos (minúsculas, sin puntuación ni espacios de más) y elige en
   dos niveles:
   1. **Título exacto:** el título o algún "AKA:" es igual al de la ficha. Con una fila, esa
      es la elegida; con varias, desempata el año.
   2. **Título que contiene**, solo si el nivel 1 no dio ninguna: el título tiene todas las
      palabras del de la ficha, enteras ("spy" no coincide con "Spycraft"). Acá el año es
      obligatorio aunque quede una sola fila.

   El año es el de *esa* plataforma en la lista ("DOS (1990)"), no la fecha del primer
   lanzamiento: primero gana el mismo año y, si no hay, ±1 en el nivel 1 y ±2 en el nivel 2. Con una fila elegida baja
   `/game/{id}/{slug}/` y su `/specs/`; con ninguna, o con varias que el año no separa, responde "sin
   resultados". Si la procedencia ya trae el `originUrl` de MobyGames, salta la búsqueda.
   La ficha parseada queda en un memo en memoria por URL mientras corre el
   proceso, como `arcadedb/cliente.fetch`: la reusan las sugerencias de distintos campos y la
   precarga.
6. `lib/providers/mobygames/proveedor.py` — `MobyGamesProvider`, `tipo="scrape"`,
   `Limite(espera_min=3.0)`. Su gate es el catálogo: si el sistema de `Consulta.system` no
   tiene equivalencia en MobyGames (arcade incluido), no consulta. Responde por clave, como
   ArcadeDB, y mapea a las claves de `fielddefs.json`.
6b. `lib/domain/plataformas.json` y `plataformas.py` — **catálogo de plataformas**: por cada
   sistema, indexado por el `name` de `sistemas.json` (es lo que llega en `Consulta.system`:
   `msdos`, `arcade`) con sus alias, y el nombre en cada sitio. La búsqueda no distingue
   mayúsculas. Un sitio sin equivalencia se declara `null`; un sitio ausente de la fila es
   un error. En la 020 los sitios son `mobygames` y `launchbox`; la 021 suma
   `screenscraper`. `steamgriddb` no figura: no distingue plataformas. Es un dato compartido
   por todos los proveedores, como `fielddefs.json`. `Consulta.system` y `Consulta.year` ya
   existen y no cambian.

   | Sistema | Alias | `mobygames` | `launchbox` |
   |---|---|---|---|
   | `msdos` | `ms-dos` | `DOS` | `MS-DOS` |
   | `arcade` | `mame` | `null` | `Arcade` |
   | `nes` | — | `NES` | `Nintendo Entertainment System` |
   | `snes` | — | `SNES` | `Super Nintendo Entertainment System` |
   | `genesis` | — | `Genesis`\* | `Sega Genesis` |
   | `mega drive` | — | `Genesis`\* | `Sega Mega Drive` |
   | `game boy` | — | `Game Boy`\* | `Nintendo Game Boy` |
   | `game boy advance` | — | `Game Boy Advance` | `Nintendo Game Boy Advance` |
   | `game boy color` | — | `Game Boy Color`\* | `Nintendo Game Boy Color` |

   Las dos primeras son los sistemas que existen hoy; el resto son las entradas de
   `_SYSTEM_TO_LAUNCHBOX`, para que Launchbox no pierda ninguna. El nombre de MobyGames es el
   de su lista de plataformas: "DOS", "NES", "SNES" y "Game Boy Advance" se vieron en las
   búsquedas. Los marcados con \* no se vieron todavía; si están mal, el proveedor responde
   "sin resultados".
6c. `lib/providers/launchbox/cliente.py` — lee la columna `launchbox` del catálogo y se borra
   `_SYSTEM_TO_LAUNCHBOX`. Un sistema que no está en el catálogo sigue yendo con su nombre
   tal cual, como hoy.
7. `lib/providers/registro.py` — cadenas nuevas. MobyGames se construye solo si Chromium está
   disponible.

   | Clave | Hoy | Después |
   |---|---|---|
   | Identidad (salvo `year`) | ArcadeDB → IA | ArcadeDB → MobyGames |
   | `year` | Launchbox → IA | ArcadeDB → MobyGames → Launchbox |
   | `sinopsis` | ArcadeDB → IA | ArcadeDB → MobyGames → IA |
   | `review` | IA | MobyGames → IA |

7b. `lib/providers/orquestador.py` — `suggest_identity_batch` deja de partir la respuesta de la
   IA en candidatos de identidad (se borra la rama `IaGenerador`) y pide cada clave de
   identidad a su cadena. El memo de la ficha evita bajarla siete veces.
7c. `services/msdos.py` — la precarga llena cada campo de identidad vacío con MobyGames,
   después con Launchbox y, si ninguno lo tiene, con la IA. La IA solo recibe los campos que
   quedaron vacíos. Cada campo escrito registra su fuente en `provenance`, que hoy la
   precarga no escribe. El género de MobyGames llega en inglés: pasa por `Traductor`, como
   en la precarga de ArcadeDB, y la procedencia lo dice. Si la ficha de MobyGames tiene otro
   año de DOS que el usado para buscarla (el de la ficha o, si falta, el de Launchbox), se
   eligió por año aproximado y es otra edición: la precarga no toma de ella ni el año ni el
   formato (el año sigue la cadena hasta Launchbox). Acordado el 2026-10-29.
7d. `store/juegos.py` — `apply_rich_suggestion`: si la clave es `review` y el candidato no
   trae `cats`, conserva las del campo actual. La procedencia del campo pasa a MobyGames.
8. `config.py` — `COINDOOR_SCRAPING_TIMEOUT` (60 s) y `COINDOOR_SCRAPING_PACE` (3 s por sitio),
   configurables y sin mínimo impuesto; ninguna credencial nueva. El perfil del navegador vive
   en `games/navegador`, fuera de Git y fuera de `tmp/` (que se borra al arrancar).
9. Tests — `parser` contra la ficha guardada de Maniac Mansion; `scraping` con un doble; el
   proveedor con `ScrapingClient` falso; ninguna cadena de identidad con IA; la precarga con
   fuentes falsas; la reseña parcial.
10. `services/precalentar.py` y el `lifespan` de `main.py` — precalentamiento al arrancar
   ([`ADR-0025`](../../decisions/0025-precalentar-mobygames-al-arrancar.md)): un hilo baja
   `/search/?q=dos&type=game` con el mismo `ScrapingClient` y el mismo perfil. Gate: Chromium,
   un sistema con equivalencia en MobyGames, `COINDOOR_SCRAPING_WARMUP` y una marca
   `games/navegador/.precalentado` de menos de 6 horas. Un fallo va al log. Al cerrar la
   aplicación se cancela. Una consulta que llega mientras tanto espera el perfil y reusa la
   cookie.

## Decisiones

- **Un solo módulo importa `scrapling`** — acota el cambio si la librería cambia.
  Ver [`ADR-0024`](../../decisions/0024-scrapling-y-mobygames-para-pc-dos.md).
- **Extraer la política en vez de duplicarla** — la regla del backend lo exige.
- **JSON-LD antes que selectores CSS** — es contrato publicado por el sitio; el HTML cambia más.
- **Buscador general antes que el navegador por plataforma** — en una sola petición trae el
  año de cada plataforma y los títulos alternativos, que es lo que necesita la regla de
  desempate. El navegador por plataforma no trae año: cada empate costaría bajar otra ficha,
  a 3 s cada una.
- **Sin la API oficial** — ya descartada en ADR-0024 (alternativa A). La condición para
  revisarla, mucho volumen de consultas, no se da con un juego por vez.
- **Sesión de navegador por consulta, no global** — el Playwright síncrono ata el navegador al
  hilo que lo creó, y los jobs corren en hilos ([`ADR-0010`](../../decisions/0010-jobs-en-proceso.md)).
  Lo que sobrevive a la consulta es el perfil en disco, no el navegador.
- **Opciones de Scrapling antes que otra herramienta** — para Cloudflare se descartaron
  `real_chrome` (instalar Chrome en WSL), `headless=False` (necesita pantalla) y `cdp_url`
  (depende de un Chrome abierto aparte): la demora era de la configuración y se arregló con
  opciones de la misma sesión.
- **Arcade no consulta MobyGames** — su identidad ya tiene autoridad en el `.dat` de MAME
  (ADR-0024, alternativa H).
- **La IA sale de "Sugerir" en identidad, y en la precarga de MS-DOS solo completa** —
  ADR-0024, punto 4.
- **Aplicar la nota no borra las categorías** — un candidato de reseña sin `cats` pisa solo
  `score`; así el gabinete no muestra "-" en las seis.
- **Ritmo por defecto de 3 s por sitio** — la latencia no es un problema en este producto, y
  un ritmo lento baja el riesgo de que el sitio bloquee la IP.
- **Memo de la ficha en memoria, no en disco** — dura lo que el proceso, igual que la caché
  del orquestador.

## Riesgos

- **Refactor de `http.py`** — toca código con tests. Se mitiga con que sus tests actuales
  sigan en verde antes de agregar nada. Lo mismo para Launchbox al migrar su tabla.
- **Coincidencia equivocada de título** — un juego de otro año o de otra edición con el mismo
  nombre. Se mitiga exigiendo plataforma y comparando el año de la ficha con tolerancia de ±1
  (las fechas varían por región y por plataforma).
- **Sugerencias de identidad vacías** — sin la IA, un juego que ni ArcadeDB ni MobyGames
  conocen (los de NES, por ejemplo) no tiene candidatos y se completa a mano. Es lo que pide
  [`ADR-0004`](../../decisions/0004-coindoor-fuente-identidad-no-mame.md).
- **Alta más lenta** — la precarga de MS-DOS abre el navegador. MobyGames responde 403 a HTTP,
  así que siempre resuelve Cloudflare con el navegador. Medido el 2026-10-29 en WSL, antes del
  arreglo: la primera página tardaba de ~70 s a ~330 s y tres consultas seguidas no terminaron
  en 28 min. **La causa era la configuración, no Cloudflare:** con `network_idle=True`,
  Scrapling espera a que la página deje de pedir antes de resolver el desafío, y una página de
  desafío nunca deja de pedir, así que esperaba el `timeout` entero (60 s → ~70 s; 300 s →
  ~330 s). Después del clic vuelve a esperar la red con el mismo `timeout`. Arreglo, todo con
  opciones de Scrapling: `network_idle=False`, `timeout` de 60 s y un perfil persistente
  (`user_data_dir`) para que las consultas siguientes reusen la cookie de Cloudflare. Ver
  §Lo verificado para lo medido después.
- **Palabras escritas distinto** — si la ficha escribe el título distinto que MobyGames y
  ningún "AKA:" lo cubre, el proveedor responde "sin resultados". Es el lado seguro del
  error. En *Out Run* contra "OutRun", el AKA lo cubrió.
- **Juego fuera de la primera página** — si un título muy común empuja al correcto a la
  segunda página, el proveedor responde "sin resultados". El respaldo posible es el navegador
  por plataforma (`/game/platform:dos/title:{término}/`), que no trae año.
- **Página procesada por el navegador** — la fixture es el HTML del servidor y Scrapling ve
  la página después del JavaScript. El parser usa solo el JSON-LD y listas en HTML, y su
  test corre también contra una ficha bajada con `ScrapingClient`.
