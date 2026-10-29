# 021 · Imágenes desde SteamGridDB y ScreenScraper

**Estado:** aprobada

## Qué hace

**Recibe** un juego, un campo de imagen (carátula, póster, marquesina, logo, captura) o el
video, y la **plataforma** y el **año** que COINDOOR tiene en la ficha. **Consulta** SteamGridDB y ScreenScraper con el motor de scraping
de la feature [`020`](../020-scrapling-mobygames/spec.md) y **ofrece candidatos** con su
vista previa y su fuente, junto a los de ArcadeDB, Launchbox y la búsqueda de imágenes.

- **SteamGridDB:** *grids* verticales como póster, *heroes* (banners anchos) como marquesina y
  logos, elegidos por la comunidad.
- **ScreenScraper:** medios de la ficha del juego —caja, captura, rueda/logo y el video MP4—
  y el resto del catálogo que la ficha exponga.

Elegir un candidato descarga el archivo a la carpeta del juego, como cualquier otro proveedor.

**No cubre** texto ni identidad de estos sitios, ni manuales.

## Por qué

Hoy las imágenes de MS-DOS salen solo de Launchbox, que Cloudflare puede bloquear, y arcade
depende de ArcadeDB. Más fuentes significan más carátulas, logos y marquesinas entre las que
elegir, y menos carga manual. Y el video de MS-DOS hoy es solo una referencia de YouTube para
bajar a mano.

## Criterios de aceptación

- [ ] Dado un juego con título, cuando se pide sugerir `caratula`, `poster`, `marquesina`,
      `logo` o `captura`, aparecen candidatos de SteamGridDB y/o ScreenScraper con vista
      previa y fuente "SteamGridDB" o "ScreenScraper" a la vista.
- [ ] SteamGridDB ofrece sus grids verticales solo como `poster`, sus heroes como `marquesina`
      y sus logos como `logo`. Nunca un grid como `caratula`, y los grids horizontales no se
      ofrecen.
- [ ] Dado un juego MS-DOS, cuando se pide sugerir `video`, ScreenScraper ofrece el MP4 de su
      ficha como candidato aplicable, antes de la referencia de YouTube.
- [ ] Dado un candidato elegido, el archivo completo queda guardado en la carpeta del juego,
      no su miniatura.
- [ ] Dado un título con varios juegos posibles en el sitio, no se devuelven imágenes de uno
      elegido al azar: o hay coincidencia clara, o el proveedor responde "sin resultados".
- [ ] Dada la plataforma de la ficha, ScreenScraper busca en ella y no en otra; SteamGridDB,
      que no distingue plataformas, desempata con el año de la ficha (±1).
- [ ] Dado un sistema sin equivalencia en ScreenScraper, ese proveedor no se consulta y el
      rastro dice "plataforma sin equivalencia".
- [ ] Dado que un sitio falla, vence su tiempo o exige sesión, ese proveedor falla aislado y
      los demás siguen ([`002`](../002-sugerencias-multiproveedor/spec.md)).
- [ ] Dado que el navegador no está instalado, ambos proveedores se omiten sin romper el arranque.
- [ ] Dado un candidato de imagen, nunca se aplica solo; su fuente queda en la procedencia
      interna y no viaja al export ([`ADR-0002`](../../decisions/0002-procedencia-interna.md)).
- [ ] Dos búsquedas del mismo juego en la sesión reutilizan lo ya descargado.
- [ ] Los tests corren sin red, contra páginas guardadas.

## Fuera de alcance

- **Texto, identidad y manuales** de estos sitios.
- **Íconos de SteamGridDB:** COINDOOR no tiene campo de ícono.
- **Grids de SteamGridDB como carátula:** la carátula es la caja (`boxFront`) y los grids son
  arte de la comunidad.
- **Generar o recortar imágenes** para ajustarlas a una proporción.
