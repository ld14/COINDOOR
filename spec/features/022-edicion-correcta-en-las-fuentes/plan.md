# 022 · Edición correcta en todas las fuentes — Plan

_Cómo se implementa lo descrito en [`spec.md`](spec.md). Respeta la `constitution/`._

## Enfoque

La regla de dos niveles de MobyGames (feature 020) pasa a un módulo común y la usa también
Launchbox. Con el juego bien elegido en las dos fuentes, cada una aporta lo que tiene de esa
edición: Launchbox, la identidad de su página; MobyGames, la carátula y las capturas de la
plataforma. La IA queda como último recurso en "Sugerir", decidido por el orquestador y no por
la tabla de cadenas ([`ADR-0026`](../../decisions/0026-ia-ultimo-recurso-en-sugerir-identidad.md)).

## Lo verificado el 2026-10-29

- **Búsqueda de Launchbox** "Prince of Persia" en MS-DOS (guardada en
  `backend/tests/fixtures/launchbox/busqueda-prince-of-persia.html`): doce tarjetas por orden
  alfabético. *4D Prince of Persia* (sin año) va antes que *Prince of Persia* (1990), y la
  regla actual (el primer título que *contiene* el buscado) se queda con el primero. Cada
  tarjeta trae título, plataforma y, casi siempre, año.
- **Página de un juego en Launchbox** (`ficha-prince-of-persia.html`): pares `dt`/`dd` con
  "Release Date" (1990), "Max Players" (1), "Developers" (Brøderbund Software), "Publishers"
  (Brøderbund Software, Softgold Computerspiele) y "Genre" (Platform, Action). Los valores son
  enlaces; cada uno aparece dos veces en el texto, así que se deduplican.
- **Carátulas de MobyGames** (`prince-of-persia-covers-dos.html`): una `<section>` por edición
  (país en la tabla) y una `<figure>` por imagen, con `figcaption` "Front Cover", "Back Cover"…
  La miniatura es WebP (~345×440). La imagen grande está en la página de cada carátula
  (`prince-of-persia-cover-383.html`): `covers/4008841-prince-of-persia-dos-front-cover.jpg`,
  622×800, con `alt` "Front Cover for Prince of Persia (DOS)".
- **Capturas de MobyGames** (`prince-of-persia-screenshots-dos.html`): 32 `<figure>` de 320×200,
  la resolución nativa de DOS, con su leyenda.
- **La ficha procesada por el navegador pierde las carátulas por plataforma** (venían en un
  atributo de Vue): hay que ir a la página de carátulas.
- **Las imágenes de `cdn.mobygames.com` bajan con HTTP común** (200, JPEG y WebP): aplicarlas no
  necesita navegador.
- **Búsqueda de Launchbox "Civilization"** en MS-DOS (`busqueda-civilization.html`): ninguna
  tarjeta se llama *Civilization*; el original es *Sid Meier's Civilization* (13599), que en la
  lista **no trae año** y escribe el apóstrofo como `&#x27;`. La regla común no podía elegirlo,
  porque el nivel 2 exige el año, y el año está en la página del juego.

**Prueba en el sitio real** (2026-10-29, WSL, con el orquestador y la precarga de la app):

| | *Prince of Persia* (1990) | *Civilization* (1991) |
|---|---|---|
| Juego elegido en Launchbox | 13853, *Prince of Persia* | 13599, *Sid Meier's Civilization* |
| Identidad en "Sugerir" | MobyGames y Launchbox: Brøderbund, 1 jugador; género "Action" y "Platform, Action" | Launchbox: MPS Labs, MicroProse Software, Strategy, 1 jugador. Sin IA |
| Carátula en "Sugerir" | 3 portadas de DOS de MobyGames primero; después, 4 de Launchbox y 10 de Image Search | 2 de Launchbox y 10 de Image Search, ya de este juego |
| Captura en "Sugerir" | 8 de MobyGames (DOS), 4 de Launchbox y 8 de Image Search | 3 de Launchbox y 10 de Image Search |
| Precarga del alta | Identidad y formato de MobyGames (ficha 196), carátula de DOS de MobyGames; captura y logo de Launchbox | Identidad de Launchbox; la IA, solo la sinopsis |

- Antes de leer el año de la página, *Civilization* caía al respaldo de IA, que propuso
  "MicroProse" como desarrollador (marcado como IA); es MPS Labs. Sirvió de prueba real del
  respaldo.
- Image Search varía entre corridas (búsqueda web en vivo): las capturas de *Prince of
  Persia* fueron entre 2 y 8 en tres corridas. MobyGames y Launchbox dieron siempre lo mismo.

## Implementación

1. `lib/providers/coincidencia.py` — la regla de dos niveles, extraída de
   `mobygames/cliente.elegir`: `normalizar`, título exacto (título o alias) con desempate por
   año ±1 y, solo si no hay exacto, título que contiene todas las palabras con el año
   obligatorio ±2. Genérica: recibe cómo leer los títulos y el año de cada opción.
   `mobygames.cliente.elegir` filtra por plataforma y la usa.
2. `lib/providers/launchbox/cliente.py`:
   - `_parse_search_results(html, título, sistema, año)` lee todas las tarjetas de la
     plataforma y elige con la regla común. `search_game` recibe el año.
   - Sin tarjeta exacta, las que contienen todas las palabras se completan con su página, que
     queda en memoria para la identidad, antes de elegir (ver
     [025](../025-launchbox-nombres-alternativos/plan.md)). Las entidades del HTML se decodifican
     todas (`html.unescape`).
   - `fetch_details(game_id, slug)` → `LaunchboxFicha` (desarrolladores, editores, géneros,
     jugadores, año), con memo por juego. Lee la página con `pagina_desde_html`, así Scrapling
     sigue importado solo desde `scraping.py`.
3. `lib/providers/launchbox/proveedor.py` — suma `developer`, `publisher`, `genre` y `players`;
   `year` sale de la página y, si falta, de la búsqueda. Jugadores: "1" o "1-N". Género en
   inglés, como el de MobyGames ("Género (en inglés)").
4. `lib/providers/mobygames/` — imágenes de la ficha ya elegida:
   - parser: el slug de la plataforma (de `#platformLinks`), las portadas frontales de la
     página de carátulas (en orden, con el país), la imagen grande de una carátula y las
     capturas;
   - cliente: `buscar_imagenes(...)` reusa `buscar_ficha` y guarda en memoria por ficha. Hasta
     3 portadas (una página más por cada una, para la imagen grande) y hasta 8 capturas;
   - proveedor: responde `caratula` y `captura`.
5. `lib/providers/referencia/images.py` — las búsquedas llevan el año cuando la ficha lo tiene.
6. `lib/providers/registro.py` — cadenas:

   | Clave | Cadena |
   |---|---|
   | `developer`, `publisher`, `genre`, `players`, `year` | ArcadeDB → MobyGames → Launchbox |
   | `title`, `format` | ArcadeDB → MobyGames |
   | `caratula`, `captura` | ArcadeDB → MobyGames → Launchbox → Image Search |
   | `poster`, `marquesina`, `logo` | ArcadeDB → Launchbox → Image Search |

   Ninguna cadena de identidad tiene IA: el respaldo es del orquestador.
7. `lib/providers/orquestador.py` — respaldo de IA (ADR-0026): para `developer`, `publisher`,
   `genre` y `players`, si la cadena no dio ningún candidato, pide `identidad` a la IA (primario
   y, si falla, respaldo), una vez por juego y con memo, y ofrece el campo marcado como IA. En
   la identidad en bloque, una sola consulta cubre todos los campos que quedaron vacíos. Si el
   usuario reintenta una fuente puntual, no corre.
8. `services/msdos.py` — precarga: Launchbox elige con el año; los campos de identidad que
   MobyGames no tiene salen de la página de Launchbox antes que de la IA (género traducido,
   como el de MobyGames); la carátula, primero de MobyGames y si no de Launchbox.
9. Tests sin red contra las páginas guardadas.

## Decisiones

- **Una sola regla para todas las fuentes que buscan por título** — la misma tolerancia y los
  mismos dos niveles; si se ajusta, se ajusta en un lugar.
- **El respaldo de IA lo decide el orquestador, no la tabla** — la tabla dice qué fuentes
  factuales se consultan; la IA solo entra cuando ninguna respondió.
- **La imagen grande de la carátula se baja al sugerir** — aplicar un candidato no tiene
  navegador, y la miniatura (~345×440) es chica para una carátula.
- **Las capturas de DOS se usan tal cual** — 320×200 ya es la imagen completa.
- **La precarga toma de MobyGames solo la carátula** — las capturas siguen de Launchbox, que
  las clasifica ("gameplay", "título"); MobyGames solo tiene leyendas libres.

## Riesgos

- **Más pedidos por consulta** — carátula: 1 página de carátulas + hasta 3 de detalle, a 3 s
  cada una. Se acepta: la latencia no es un problema del producto.
- **Launchbox más estricto** — un título que solo coincide en parte deja de elegirse si ni la
  lista ni su página traen el año. Es el lado seguro: antes elegía otro juego.
- **IA de respaldo** — vuelve a haber candidatos inventados donde ninguna fuente sabe; van
  marcados como IA (ADR-0026, costo asumido).
