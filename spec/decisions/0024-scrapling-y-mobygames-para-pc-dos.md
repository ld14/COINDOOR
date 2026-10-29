---
id: 0024
title: Scrapling como motor de scraping de COINDOOR y MobyGames como fuente de PC/DOS
status: accepted
date: 2026-10-21
supersedes: 13
superseded-by: null
tags: [backend, data]
---

# 0024 — Scrapling como motor de scraping de COINDOOR y MobyGames como fuente de PC/DOS

## Contexto

[`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md) sacó todo scraping HTML por costo de
mantenimiento y dejó escrita la señal de reapertura: una fuente nueva es *"decisión
explícita, no un default"*. [`ADR-0014`](0014-arcadedb-fuente-arcade.md) reabrió solo
arcade; para el resto, la tabla de 0013 quedó intacta.

**Qué cambió.** Los juegos de MS-DOS son 21 de los 29 de la colección y son los peor
servidos:

- Launchbox es la única fuente de imágenes, y su propio cliente admite en el docstring que
  *"Cloudflare puede bloquear"*. Solo aporta imágenes y año.
- La identidad y la reseña de esos juegos las resuelve la IA (`registro.py`), que inventa de
  forma convincente. No hay ninguna fuente factual.
- MobyGames es el catálogo de referencia de PC/DOS: desarrollador, editor, género, fechas por
  plataforma, nota de críticos y de jugadores, nombres alternativos.

Verificado en vivo el 2026-10-21 contra `/game/714/maniac-mansion/`: un GET simple devuelve
**403 "Just a moment..."** (Cloudflare); `StealthyFetcher.fetch(..., solve_cloudflare=True)`
de Scrapling devuelve **200 y 117 KB**, con un bloque JSON-LD `schema.org/VideoGame` y la ficha
lateral completa.

## Decisión

**Scrapling es el único motor de scraping de COINDOOR, y MobyGames entra como proveedor de
los sistemas que no son arcade.**

1. `scrapling[fetchers]` es **dependencia obligatoria** de `pyproject.toml`. Ningún otro
   módulo importa `scrapling` salvo `lib/providers/scraping.py`.
2. Ese módulo aplica a Scrapling la misma política que `http.py` aplica a `httpx`: cuota,
   ritmo, reintento con backoff, cancelación y clasificación de errores. Ningún proveedor
   implementa lo suyo.
3. MobyGames es un proveedor `tipo="scrape"` que atiende los sistemas **que no son arcade** y
   tienen equivalencia en su sitio. Arcade sigue con ArcadeDB, cuya identidad deriva del
   `.dat` de MAME ([`ADR-0014`](0014-arcadedb-fuente-arcade.md)).
   **La plataforma y el año los pone COINDOOR** en la consulta (`Consulta.system` y
   `Consulta.year`); un juego que existe en varias plataformas se busca en la que COINDOOR
   indica. Cada sitio traduce el sistema a su propio identificador con un **catálogo de
   plataformas**: un archivo de datos, no un `dict` escondido en cada proveedor. Launchbox
   también pasa a leerlo.
   **SteamGridDB** y **ScreenScraper** entran como proveedores de imágenes de todos los
   sistemas, también por scraping, con el mismo motor (feature
   [`021`](../features/021-imagenes-steamgriddb-screenscraper/spec.md)).
4. **La IA sale de las sugerencias de identidad**, en todos los sistemas: ninguna cadena de
   identidad de `registro.py` la incluye, tampoco la sugerencia de identidad en bloque.
   Vuelve a regir [`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md) y queda sin efecto
   la fila *"Identidad: ArcadeDB → IA"* de la tabla de 0014.
   **Excepción: la precarga del alta de MS-DOS** ([`ADR-0015`](0015-precarga-con-red-al-alta.md)).
   Ahí las fuentes se complementan campo por campo: MobyGames primero, Launchbox después, y
   la IA llena solo lo que ninguna de las dos tuvo. Cada campo escrito registra su fuente en
   la procedencia interna.
5. **El scraping no tiene restricciones propias en COINDOOR:** ni lista de sitios permitidos,
   ni prohibición por tipo de sitio, ni requisito previo de verificar términos o cuotas. Deja
   sin efecto la prohibición de [`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md) y la
   tabla de ese ADR que [`ADR-0014`](0014-arcadedb-fuente-arcade.md) mantuvo para no arcade.
   El resto de 0014 sigue vigente: ArcadeDB no cambia.
6. Fuera de la precarga del alta, que ya escribe campos vacíos por
   [`ADR-0015`](0015-precarga-con-red-al-alta.md), todo es sugerencia: una persona acepta cada
   candidato.

## Alternativas consideradas

### A. API oficial de MobyGames

- A favor: términos y contrato explícitos; JSON en vez de HTML.
- En contra: credencial y cuota propias, justo lo que 0013 evitó
  (alternativa B de ese ADR). No verifiqué el plan gratuito vigente.
- **Descartada porque:** resuelve MobyGames y nada más; el motor de scraping sirve también a
  Launchbox y a futuras fuentes sin API.

### A2. APIs oficiales de SteamGridDB y ScreenScraper

- A favor: contrato estable, sin parsear HTML.
- En contra: piden claves o cuenta de desarrollador y tienen cuota propia.
- **Descartada porque:** se decidió no usarlas; ambos sitios se leen solo por scraping. No hay
  que reabrirlo salvo que el scraping deje de funcionar.

### B. Seguir con `httpx` y un parser propio, como Launchbox

- A favor: cero dependencias nuevas.
- En contra: **comprobado** el 403 de Cloudflare sobre MobyGames; superarlo es reimplementar
  la suplantación de TLS y el navegador.
- **Descartada porque:** no funciona contra el sitio objetivo.

### C. Playwright directo, sin Scrapling

- A favor: una capa menos.
- En contra: se pierde la resolución del desafío de Cloudflare, la huella de navegador y los
  selectores (CSS, XPath, búsqueda por texto) que Scrapling ya trae sobre Playwright.
- **Descartada porque:** duplicaría ese trabajo sin ganar nada.

### D. Script auxiliar fuera de COINDOOR

- A favor: no toca el código ni la constitución.
- En contra: contradice la misión —*"cargar un juego completo sin abrir una terminal"*— y deja
  los datos fuera del flujo de procedencia y aceptación.
- **Descartada porque:** se decidió que COINDOOR tenga la facultad completa.

### E. Scrapling como extra opcional

- A favor: COINDOOR arranca liviano sin él.
- En contra: dos modos de instalación que probar.
- **Descartada porque:** se prefirió la instalación única. El costo se acota igual: sin
  Chromium el proveedor no se construye y el resto sigue funcionando.

### F. MobyGames delante y la IA de respaldo en las sugerencias de identidad

- A favor: siempre hay un candidato; es el patrón que 0014 aceptó para arcade.
- En contra: la IA respondería solo cuando ninguna fuente encontró el juego, que es justo el
  caso en que más inventa.
- **Descartada porque:** la identidad viaja en el bundle y nadie la vuelve a mirar
  ([`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md)).

### G. Precarga del alta sin IA en identidad

- A favor: coherente con F y con 0004, sin excepciones.
- En contra: el alta de un juego que ni MobyGames ni Launchbox conocen deja la identidad
  vacía.
- **Descartada porque:** se prefirió que el alta complemente todas las fuentes disponibles y
  no deje huecos; la IA entra solo después de las fuentes factuales.

### H. MobyGames también para arcade

- A favor: aportaría una nota de críticos donde ArcadeDB no tiene reseña (`rate: 0`).
- En contra: títulos y años de otra fuente que contradicen al `.dat` de MAME, y el navegador
  abierto en cada sugerencia arcade.
- **Descartada porque:** la identidad arcade ya tiene autoridad. Se reabre si la reseña
  arcade necesita una nota factual.

## Consecuencias

**Positivas**

- Identidad factual de PC/DOS (desarrollador, editor, género, año) donde hoy hay IA.
- La nota de críticos reemplaza una nota inventada por una medida.
- "Sugerir" deja de ofrecer identidad inventada en todos los sistemas.
- Launchbox puede migrar al mismo motor, sin cambiar su contrato.

**Coste asumido**

- Dependencia pesada: Playwright, patchright, curl_cffi, browserforge. `uv sync` más lento y
  Chromium como paso de instalación (`scripts/install-deps.sh`).
- Una búsqueda con navegador tarda segundos; es aceptable ([`tech-stack.md`](../constitution/tech-stack.md)
  §Convenciones: la latencia no es un problema). El alta de un juego MS-DOS también abre el
  navegador.
- El HTML de MobyGames puede cambiar sin aviso. Se mitiga leyendo primero el JSON-LD y con
  tests contra una página guardada.
- En las sugerencias, un juego que ninguna fuente conoce se completa a mano.
- La precarga de MS-DOS todavía puede escribir identidad generada por IA cuando ninguna
  fuente factual conoce el juego. Es la excepción del punto 4, y queda registrada en la
  procedencia.

**Qué habría que revisar si esto se replantea**

- Si el mantenimiento de los parsers supera lo que aportan, que es lo que pasó con 0006.
- Si el desafío de Cloudflare deja de resolverse con `solve_cloudflare`.
- Si la identidad que la IA completa en la precarga resulta equivocada en la comparación de
  cierre de la feature 020: entonces se saca también de ahí (alternativa G).

## Referencias

- [`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md), [`ADR-0014`](0014-arcadedb-fuente-arcade.md)
- [`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md) — la identidad no la propone una IA.
- [`ADR-0015`](0015-precarga-con-red-al-alta.md) — la precarga del alta.
- [`ADR-0002`](0002-procedencia-interna.md) — la procedencia no viaja al export.
- Features [`020`](../features/020-scrapling-mobygames/spec.md) y
  [`021`](../features/021-imagenes-steamgriddb-screenscraper/spec.md).
