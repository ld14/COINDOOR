---
id: 0027
title: myabandonware es la primera fuente de PC/DOS y MobyGames queda como último recurso
status: accepted
date: 2026-10-30
supersedes: null
superseded-by: null
tags: [backend, data]
---

# 0027 — myabandonware es la primera fuente de PC/DOS y MobyGames queda como último recurso

## Contexto

Desde las features [020](../features/020-scrapling-mobygames/spec.md) y
[022](../features/022-edicion-correcta-en-las-fuentes/spec.md), la identidad de PC/DOS sale de
MobyGames, después de Launchbox y, si ninguna la tiene, de la IA
([`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md), punto 4;
[`ADR-0026`](0026-ia-ultimo-recurso-en-sugerir-identidad.md)). MobyGames necesita el navegador
y resolver Cloudflare: unos 20 s por consulta con el perfil ya caliente y hasta 200 s en frío.
Además no encuentra todos los juegos (*Civilization* no está en la primera página de su
búsqueda). El dueño del producto pidió el 2026-10-30 otro orden: myabandonware.com primero,
después Launchbox con la IA y MobyGames al final.

Lo verificado en myabandonware.com el 2026-10-30:

- Responde a HTTP común (200, `nginx`, sin Cloudflare), con cualquier `User-Agent`.
- Cada página de juego (`/game/{slug}-{id}`) es de una plataforma y trae título, nombres
  alternativos, año, desarrollador (no siempre), editores en orden de lanzamiento (JSON-LD),
  género, una descripción en inglés, capturas separadas por plataforma (GIF o PNG, 320×200 o
  640×400) y enlaces a otros sitios, entre ellos su ficha de MobyGames.
- No tiene carátulas. `playMode` dice "SinglePlayer" en todos los juegos, también en
  *One Must Fall*, *Micro Machines* y *Street Fighter II*: no sirve para jugadores.
- Su `robots.txt` prohíbe `/search/`, `/download/` y `/manual/`, y publica un `sitemap` con las
  34 244 páginas de juego (1,2 MB comprimido).
- No tiene los juegos que todavía se venden: *Monkey Island*, *Maniac Mansion* y el *Doom* de
  DOS no están.

## Decisión

**myabandonware.com es la primera fuente de PC/DOS, y MobyGames se consulta solo para el campo
que ninguna fuente anterior tuvo.** En "Sugerir" y en la precarga del alta:

1. **myabandonware por HTTP común**, con la política de `http.py` (ritmo, reintentos,
   cancelación), sin navegador. Aporta título, año, desarrollador, editor, género, sinopsis (en
   inglés) y capturas de la plataforma de la ficha.
2. **El juego se encuentra en el `sitemap`**, guardado en `data_dir` y renovado cada 30 días.
   Solo se bajan las páginas de juego y sus imágenes: nunca `/search/`, `/download/` ni
   `/manual/`.
3. **En myabandonware solo vale el título o un nombre alternativo exacto** (el nivel 1 de la
   regla común), con la plataforma y el año para desempatar. El `sitemap` no es una búsqueda:
   las páginas que *contienen* el título son cualquier juego con esa palabra.
4. **Orden por campo:**

   | Campo | Orden |
   |---|---|
   | Título | ArcadeDB → myabandonware → MobyGames |
   | Año | ArcadeDB → myabandonware → Launchbox → MobyGames |
   | Desarrollador, editor, género, jugadores | ArcadeDB → myabandonware → Launchbox → IA → MobyGames |
   | Formato | ArcadeDB → MobyGames |
   | Carátula | ArcadeDB → Launchbox → MobyGames → buscador de imágenes |
   | Captura | ArcadeDB → myabandonware → Launchbox → MobyGames → buscador de imágenes |
   | Sinopsis | ArcadeDB → myabandonware → IA → MobyGames |
   | Reseña | IA |

   Póster, marquesina, logo, video, "Cómo se juega" y trucos no cambian. myabandonware no
   tiene jugadores ni formato y pasa de largo en esos campos.
5. **MobyGames es el último recurso:** se consulta solo si ninguna fuente anterior de la cadena
   dio un candidato para ese campo. En identidad, la IA va antes que MobyGames. Cuando se
   consulta y myabandonware enlaza su ficha, va directo a esa ficha, sin buscar.
6. **La reseña vuelve a salir solo de la IA**: la nota de críticos de MobyGames sale de la cadena.

Reemplaza el orden "MobyGames primero" de la precarga
([`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md), punto 4) y, solo respecto de MobyGames,
el punto 1 de [`ADR-0026`](0026-ia-ultimo-recurso-en-sugerir-identidad.md): la IA de respaldo ya
no espera a MobyGames. El resto de los dos ADRs sigue vigente: título, año y formato nunca
salen de una IA, y lo que propone la IA va marcado.

## Alternativas consideradas

### A. La búsqueda del sitio (`/search/q/{título}`)

- A favor: la arma el sitio, con su propio orden de relevancia.
- En contra: `robots.txt` la prohíbe, y pedida con HTTP común no trae enlaces a juegos.
- **Descartada porque:** el sitio la excluye explícitamente y el `sitemap` está publicado para
  esto.

### B. Recorrer las páginas por plataforma o por año (`/browse/...`)

- A favor: están permitidas y traen el año.
- En contra: van paginadas; encontrar un juego de DOS obliga a recorrer muchas páginas.
- **Descartada porque:** el `sitemap` es una sola descarga cada 30 días.

### C. myabandonware con Scrapling y el navegador

- A favor: el mismo motor que MobyGames.
- En contra: el sitio no tiene Cloudflare; el navegador suma 20 s o más sin ganar nada.
- **Descartada porque:** HTTP común ya responde 200.

### D. La regla común completa, con el nivel "contiene"

- A favor: encontraría *Guy Spy* (la página se llama *Guy Spy and the Crystals of Armageddon* y
  no tiene nombres alternativos).
- En contra: sin búsqueda del sitio, las candidatas son todas las páginas con esa palabra. Para
  "Doom" hay 56 y ninguna es el *Doom* de DOS; una sola con año cercano se elegiría.
- **Descartada porque:** elegir otro juego contamina la ficha, y lo que myabandonware no
  encuentra lo busca Launchbox, que sí tiene buscador.

### E. MobyGames antes que la IA (myabandonware → Launchbox → MobyGames → IA)

- A favor: un dato verificable antes que uno inventado; la IA dio "MicroProse" como
  desarrollador de *Civilization*, y es MPS Labs.
- En contra: espera al navegador antes de completar con la IA.
- **Descartada porque:** el dueño del producto prefirió la IA antes que MobyGames (2026-10-30).

### F. MobyGames siempre en "Sugerir", con sus candidatos al final

- A favor: siempre se ven sus alternativas, como las carátulas de DOS.
- En contra: cada "Sugerir" espera al navegador.
- **Descartada porque:** el dueño del producto eligió consultarlo solo si falta el dato. En
  "Sugerir" queda un botón para consultarlo igual.

### G. Seguir con MobyGames primero ([`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md))

- A favor: el catálogo más completo de PC/DOS.
- En contra: lento, y no encuentra todos los juegos.
- **Descartada porque:** es lo que el dueño del producto pidió cambiar.

### H. Jugadores desde `playMode` de myabandonware

- **Descartada porque:** dice "SinglePlayer" incluso en juegos de dos jugadores o más.

## Consecuencias

**Positivas**

- La identidad de PC/DOS sale casi siempre sin navegador.
- *Civilization* se resuelve: su página tiene "Civilization" como nombre alternativo, trae
  MPS Labs y enlaza la ficha 585 de MobyGames, que la búsqueda de MobyGames no encontraba.
- Las capturas de DOS de la edición correcta, sin navegador.

**Coste asumido**

- Más identidad propuesta por la IA, marcada como IA, en los juegos que ni myabandonware ni
  Launchbox tienen. MobyGames casi nunca completa desarrollador, editor, género ni jugadores.
- La carátula de DOS de MobyGames deja de ir primero: va la de Launchbox y MobyGames solo si
  Launchbox no tiene.
- El formato solo lo tiene MobyGames: la precarga y "Sugerir" formato siguen abriendo el
  navegador.
- Dependencia del HTML de myabandonware (tabla, JSON-LD, pestañas de capturas) y de su
  `sitemap`, guardado en `data_dir` (~1 MB).

**Qué habría que revisar si esto se replantea**

- Si myabandonware suma Cloudflare o deja de publicar el `sitemap`.
- Si aparecen en el export errores de identidad propuestos por la IA: volver a la alternativa E.
- Si otra fuente da el formato, MobyGames puede dejar de abrirse en la precarga.

## Referencias

- Feature [023](../features/023-myabandonware-primera-fuente/spec.md).
- [`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md), punto 4, y
  [`ADR-0026`](0026-ia-ultimo-recurso-en-sugerir-identidad.md), punto 1: lo que este ADR
  reemplaza.
- `https://www.myabandonware.com/robots.txt` y `https://www.myabandonware.com/sitemap.xml.gz`
  (consultados el 2026-10-30).
