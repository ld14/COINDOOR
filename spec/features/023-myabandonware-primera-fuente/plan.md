# 023 · myabandonware como primera fuente de PC/DOS — Plan

_Cómo se implementa lo descrito en [`spec.md`](spec.md). Respeta la `constitution/`._

## Enfoque

myabandonware entra como un proveedor más, con la forma de MobyGames y Launchbox (`parser`,
`cliente`, `proveedor`), pero sin navegador: baja por `ProviderHttpClient`, que suma la lectura
de texto y bytes a la de JSON con la misma política. El orden vive en las cadenas de
`registro.py`; lo único que cambia en el orquestador es que las fuentes de **último recurso**
(MobyGames) se saltan si el campo ya tiene candidato y que la IA de respaldo corre justo antes
de ellas ([`ADR-0027`](../../decisions/0027-myabandonware-primera-fuente-de-pc-dos.md)).

## Lo verificado el 2026-10-30

- **HTTP común:** `robots.txt`, la búsqueda, el `sitemap`, las páginas de juego y las capturas
  responden 200 desde `nginx`, sin Cloudflare, con el `User-Agent` de COINDOOR.
- **`robots.txt`** prohíbe `/search/`, `/download/`, `/manual/` y las acciones de usuario
  (`/game/rate/`, `/game/comment/`…). La búsqueda, además, no trae enlaces a juegos.
- **`sitemap.xml.gz`** (1,2 MB): un solo `urlset` con 34 244 páginas `/game/{slug}-{id}`, una
  por juego y plataforma principal. El último tramo del slug es el id del sitio.
- **Página de juego** (guardadas en `backend/tests/fixtures/myabandonware/`):
  - `table.gameInfo`: filas `th`/`td` con "Alt names" (separados por coma), "Year", "Platform"
    ("DOS"), "Genre", "Publisher" (orden alfabético), "Developer" (no siempre: *Prince of
    Persia* no lo tiene).
  - JSON-LD `VideoGame`: `name`, `datePublished`, `publisher` en orden de lanzamiento
    (*Civilization*: MicroProse antes que Hasbro), `author` (el desarrollador), `genre`.
    `playMode` es "SinglePlayer" en todos, también en juegos de dos jugadores: no se usa.
  - `div.gameDescription`: párrafos; termina en la firma (`span.revhotud`, "Review By …") y
    después vienen notas del sitio.
  - Capturas: una pestaña por plataforma (`a[data-platform]` con el nombre) y su
    `div.items.screens[data-platform]` con enlaces a la imagen grande y miniatura. GIF o PNG.
    Las de DOS no vienen clasificadas: la primera de *Prince of Persia* es la pantalla de
    título y la de *Civilization*, "Caesar will return!".
  - "External links": la ficha de MobyGames (`/game/196/prince-of-persia/`,
    `/game/585/sid-meiers-civilization/`).
  - "How to play" son instrucciones de DOSBox: no es "Cómo se juega".
  - No tiene carátulas.
- **Qué elige el `sitemap`:**
  - "Prince of Persia": dos slugs exactos (DOS 1990 y J2ME 2008).
  - "Civilization": el slug exacto es de N-Gage; *Sid Meier's Civilization* es la cuarta
    candidata y tiene "Civilization" como nombre alternativo.
  - "Teenage Mutant Ninja Turtles": dos páginas de DOS (1990 y 1992).
  - "Doom": 56 slugs que contienen la palabra y ninguno es el de DOS. *Monkey Island* y
    *Maniac Mansion* no están.

**Prueba en el sitio real** (2026-10-30, WSL, con el orquestador y la precarga de la app):

| | *Prince of Persia* (1990) | *Civilization* (1991) |
|---|---|---|
| Identidad en "Sugerir" | Título, año, editor y género de myabandonware; desarrollador y jugadores, de Launchbox | Todo de myabandonware (MPS Labs, MicroProse) menos jugadores, de Launchbox |
| Formato en "Sugerir" | MobyGames, "Diskette" (186 s: el navegador en frío) | MobyGames por el enlace de myabandonware, que su búsqueda no encontraba (13 s) |
| Sinopsis y reseña | Sinopsis: myabandonware (en inglés) y después las dos IA; reseña: solo las IA | Igual |
| Carátula en "Sugerir" | 4 de Launchbox y 10 de Image Search | 2 de Launchbox y 10 de Image Search |
| Captura en "Sugerir" | 8 de DOS de myabandonware primero, después 4 de Launchbox y 4 de Image Search | 8 de myabandonware, 3 de Launchbox y 10 de Image Search |
| Precarga del alta | 9 s: editor y género de myabandonware, desarrollador y jugadores de Launchbox, formato de MobyGames | 7 s: identidad de myabandonware, jugadores de Launchbox; sin formato (MobyGames lista dos soportes) |

En los dos juegos, MobyGames quedó "no hizo falta" en todo lo que no es formato, y la IA no
completó ningún campo de identidad.

## Implementación

1. `lib/providers/http.py` — `get_text` y `get_bytes`, con el mismo ciclo que `get_json`
   (reserva de cuota, ritmo, reintentos, cancelación y errores clasificados).
2. `lib/domain/plataformas.json` — sitio `myabandonware`: MS-DOS es "DOS"; el resto, `null`.
3. `config.py` — `myabandonware_dir`: la carpeta del índice en `data_dir`.
4. `lib/providers/myabandonware/parser.py` — `Ficha` (url, título, alias, año, plataforma,
   desarrollador, editor, género, descripción, capturas de la plataforma, enlace a MobyGames)
   desde la página, con `pagina_desde_html`; y las URLs de juego del `sitemap`.
5. `lib/providers/myabandonware/cliente.py`:
   - `indice(http, carpeta)`: el `sitemap` de disco si tiene menos de 30 días; si no, lo baja y
     lo guarda con escritura atómica. Si bajarlo falla y hay uno viejo, usa el viejo.
   - `candidatas(slugs, título)`: primero los slugs iguales al título; después los que lo
     contienen, primero los que terminan en él (*Sid Meier's Civilization*) y con menos
     palabras de más.
   - `buscar(http, carpeta, título, año, plataforma)`: lee hasta 5 candidatas, se queda con las
     de la plataforma cuyo título o nombre alternativo es el buscado y elige con
     `coincidencia.elegir` (el año desempata). Para en cuanto encuentra una exacta entre las
     que contienen el título. Memoria por URL y por búsqueda.
6. `lib/providers/myabandonware/proveedor.py` — `title`, `year`, `developer`, `publisher`,
   `genre` ("Género (en inglés)"), `sinopsis` ("Sinopsis (en inglés)") y `captura` (hasta 8).
   Recibe una fábrica de `ProviderHttpClient`, como MobyGames la de `ScrapingClient`.
7. `lib/providers/registro.py` — las cadenas de la tabla de ADR-0027; `ULTIMO_RECURSO` con
   MobyGames; MobyGames recibe el enlace a su ficha que da myabandonware.
8. `lib/providers/mobygames/proveedor.py` — si la procedencia no tiene su ficha, usa el enlace
   de myabandonware.
9. `lib/providers/orquestador.py` — en `suggest`, las fuentes hasta la primera de último
   recurso; después la IA de respaldo; después el resto, salteando las de último recurso si el
   campo ya tiene candidato, con la traza "no hizo falta". En la identidad en bloque, lo mismo
   en tres pasos (fuentes, una consulta a la IA, último recurso), sin trazas de lo salteado.
10. `services/msdos.py` — precarga: myabandonware, Launchbox (con el año de myabandonware si la
    ficha no tiene), la IA y MobyGames solo si falta algo que tiene (formato, año, un campo que
    la IA no dio o la carátula). Imágenes: carátula de Launchbox y si no de MobyGames; captura
    de juego de Launchbox y si no la primera de DOS de myabandonware.
11. `frontend/src/components/SuggestionsModal.tsx` — las secciones en el orden de las trazas;
    "Consultar" en vez de "Reintentar" para una fuente que "no hizo falta".
12. Tests sin red; `conftest.py` deja el índice vacío por defecto, así ningún test sale a
    myabandonware sin querer.

## Decisiones

- **Solo el nivel 1 de la regla común en myabandonware** — ver
  [`ADR-0027`](../../decisions/0027-myabandonware-primera-fuente-de-pc-dos.md), alternativa D.
- **El último recurso se decide por posición en la cadena** — MobyGames se saltea solo si una
  fuente *anterior* dio candidato. Así el buscador de imágenes, que va después y siempre trae
  algo, no lo apaga.
- **La precarga toma la captura de Launchbox antes que la de myabandonware** — carga una sola
  imagen sin que nadie la mire: Launchbox dice cuál es de juego; myabandonware no, y su primera
  puede ser la pantalla de título o la de fin. En "Sugerir" van primero las de myabandonware.
- **El índice guarda solo los slugs** — una línea por juego; la URL se arma con el slug.
- **El primer editor del JSON-LD** — está en orden de lanzamiento; la tabla, en orden
  alfabético.

## Riesgos

- **myabandonware cambia el HTML o deja de publicar el `sitemap`** — el proveedor queda "sin
  resultados" y siguen Launchbox, la IA y MobyGames. Los tests contra páginas guardadas avisan
  el cambio de forma.
- **Más identidad de la IA** — en juegos que myabandonware no tiene (los que se venden hoy) y
  Launchbox tampoco. Va marcada como IA (ADR-0026).
- **Capturas GIF** — el contrato no admite `.gif` en ningún asset y `attract doctor` lo rechaza
  en la galería. Los de un cuadro, que son casi todas las capturas, se convierten a PNG con
  ffmpeg al bajarlas (`sin_gif`, 2026-10-30); los animados se rechazan (2026-10-31).
