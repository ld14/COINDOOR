# 021 · Imágenes desde SteamGridDB y ScreenScraper — Plan

_Cómo se implementa lo descrito en [`spec.md`](spec.md). Depende del `ScrapingClient` de la
feature [`020`](../020-scrapling-mobygames/plan.md). Solo scraping: las APIs de ambos sitios
están descartadas ([`ADR-0024`](../../decisions/0024-scrapling-y-mobygames-para-pc-dos.md))._

## Enfoque

Dos proveedores nuevos con la misma forma que ArcadeDB y MobyGames: `cliente` (baja la
página), `parser` (HTML → datos) y `proveedor` (datos → `Candidato`). Los dos reutilizan
`ScrapingClient`, así que heredan cuota, ritmo (3 s por sitio por defecto), reintentos y
cancelación.

## Lo verificado el 2026-10-21

| | SteamGridDB | ScreenScraper |
|---|---|---|
| Contenido | Lo arma JavaScript: con HTTP simple llegan 2.5 KB; con navegador, ~450 KB | HTML de servidor, ~550 KB con HTTP simple |
| Sesión | No hace falta | Una visita a `/` da la cookie; el listado la necesita. **Sin cuenta** |
| Buscar un juego | `/search/grids?term=…` devuelve enlaces `/game/{id}` | No se encontró búsqueda por nombre para invitados (las páginas solo traen los formularios de login; probé 9 nombres de parámetro sin éxito). **Sí hay listado alfabético por plataforma** |
| Ficha | `/game/{id}` con pestañas grids, heroes, logos e icons | `gameinfos.php?plateforme={p}&gameid={id}`; medios en `action=onglet&zone=gameinfosmedias` |
| Descarga | Archivo completo en 200: `…/grid/….png` (940 KB) y `….jpg` (492 KB) | **403 sin `Referer`; 200 con `Referer` de la ficha** (PNG de 16.8 KB comprobado) |

El listado de ScreenScraper es `gamesinfos.php?alpha={letra}&numpage={n}&plateforme={p}`: 25
juegos por página, ordenados por nombre, con enlace `gameinfos.php?plateforme=…&gameid=…`. En
Mega Drive, "Battletoads" cae en la página 1 de la letra B.

## Implementación

1. `lib/providers/steamgriddb/` — `parser.py` lee los enlaces `/game/{id}` de la búsqueda y las
   URLs `cdn*.steamgriddb.com/{grid,hero,logo}` de la ficha, y descarta los grids
   horizontales. `cliente.py` usa el modo navegador con espera fija, no `network_idle` (agotó
   60 s en la búsqueda). `proveedor.py` mapea a las claves de `fielddefs.json`.
2. `lib/providers/screenscraper/` — `cliente.py` visita `/` para obtener la cookie, recorre las
   páginas de la letra inicial del título hasta encontrar la coincidencia y baja la pestaña de
   medios. `parser.py` extrae nombre, `gameid` y las URLs de medios, video incluido. El índice
   de una plataforma y letra ya recorrido se guarda en la sesión.
3. `lib/providers/scraping.py` — la descarga de páginas acepta cabeceras por petición. Para
   ScreenScraper envía `Referer: …/gameinfos.php?gameid={id}`.
4. `lib/providers/registro.py` — filas nuevas (el orden es provisional, es un dato):
   - `caratula` y `captura`: ArcadeDB → ScreenScraper → búsqueda de imágenes → Launchbox.
   - `poster`, `marquesina` y `logo`: ArcadeDB → ScreenScraper → SteamGridDB → búsqueda de
     imágenes → Launchbox.
   - `video`: ArcadeDB → ScreenScraper → YouTube (referencia).
5. `services/fields.py` — `_download_candidate_media` hoy manda siempre
   `Referer: https://duckduckgo.com/`, y con eso ScreenScraper responde 403. El proveedor
   declara el `Referer` en `Candidato.meta["referer"]` y la descarga lo usa si está, así
   `Candidato` no cambia.
6. Tests — parsers contra páginas guardadas; proveedores con `ScrapingClient` falso.

## Decisiones

- **Navegador para SteamGridDB, HTTP para ScreenScraper** — `ScrapingClient` ya escala solo;
  no se fija a mano por sitio.
- **El archivo completo, no la miniatura** — la miniatura es de baja resolución.
- **Sin credenciales nuevas** — ScreenScraper no exige cuenta para ver fichas ni bajar medios.
- **SteamGridDB → COINDOOR:** grid vertical → póster (600×900 es 2:3, la proporción del
  póster), hero → marquesina, logo → logo. Ni carátula ni captura: la carátula es la caja
  (`boxFront`) y los grids son arte de la comunidad. El hero (≈3:1) no tiene la proporción de
  la marquesina (4:1) y no suele traer el logo, pero MS-DOS no tiene otra fuente de
  marquesina; el usuario lo elige mirándolo.
- **ScreenScraper → COINDOOR:** caja 2D → carátula, `ss` → captura, `wheel` → logo, video →
  video. El resto del catálogo se completa al ver una ficha completa.
- **El video de ScreenScraper es aplicable** — mismo camino que el MP4 de ArcadeDB. Va antes
  de la referencia de YouTube porque es el único video de MS-DOS que se aplica directo.

## Riesgos

- **Búsqueda de ScreenScraper por recorrido** — encontrar un título puede costar varias
  páginas de 25, a 3 s cada una. Se mitiga con el caché del índice y con que cada consulta es
  a pedido.
- **Id de plataforma** — el listado necesita el `plateforme` de ScreenScraper para cada sistema
  de COINDOOR. Vive en el catálogo `plataformas.json` de la feature
  [`020`](../020-scrapling-mobygames/plan.md), no en el proveedor. No verificado: los valores
  salen de `systemeinfos.php`.
- **SteamGridDB no distingue plataformas** — un mismo título trae ediciones y remakes (la
  búsqueda mostró "Monkey Island 2: Special Edition (2010)"). Se desempata con el año de la
  ficha, y sin coincidencia clara responde "sin resultados".
- **El `Referer` es una protección contra enlaces directos** — si el sitio la endurece, la
  descarga vuelve al 403. El parser de la ficha lo detecta y el proveedor falla nombrando el
  motivo.
- **No verificado:** que el MP4 de ScreenScraper baje con el mismo `Referer` que las imágenes,
  y las medidas de grids y heroes, que salen del estándar de SteamGridDB y no de la ficha
  guardada.
- **Páginas pesadas** — 400–900 KB y varios segundos por consulta; justifica el caché.
- **Cambios de HTML sin aviso** — se mitiga con fixtures y con parsers que fallan nombrando la
  página.
