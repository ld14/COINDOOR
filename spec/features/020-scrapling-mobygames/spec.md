# 020 · Scrapling y MobyGames

**Estado:** aprobada

## Qué hace

**Recibe** un juego y un campo que el usuario pide sugerir, junto con la **plataforma** y el
**año** que COINDOOR tiene en su ficha. **Consulta** MobyGames con un navegador controlado por
Scrapling, en esa plataforma y con ese año, y **ofrece candidatos** con su fuente a la vista,
junto a los de los demás proveedores.

Un mismo juego existe en varias plataformas. COINDOOR dice en cuál está buscando; MobyGames no
adivina. Cada sistema se traduce a su equivalente en el sitio con el
[catálogo de plataformas](../../decisions/0024-scrapling-y-mobygames-para-pc-dos.md).
**Arcade no se consulta:** su identidad sale de ArcadeDB, que deriva del `.dat` de MAME.

Campos de la primera versión:

- **Identidad:** título, año, desarrollador, editor, género, jugadores, formato.
- **Reseña:** solo la nota global (`score`, de 0 a 100), desde el porcentaje de críticos.
  Aplicarla cambia la nota y conserva las categorías que ya estén cargadas.
- **Sinopsis:** la descripción oficial, como candidato a revisar.

Con MobyGames como fuente factual, **la IA sale de las sugerencias de identidad** en todos
los sistemas. En la precarga del alta de MS-DOS, MobyGames y Launchbox se complementan campo
por campo, y la IA llena solo lo que ninguno de los dos tuvo
([`ADR-0024`](../../decisions/0024-scrapling-y-mobygames-para-pc-dos.md), punto 4).

El catálogo de plataformas también reemplaza la tabla que Launchbox guarda en su código.

**No cubre** imágenes, créditos, series, trivia ni revistas, y no toca el contrato de ATTRACT.

## Por qué

La identidad y la reseña de MS-DOS hoy las inventa la IA. MobyGames es el catálogo de
referencia de esa plataforma y bloquea el HTTP simple, así que hace falta un navegador. Ver
[`ADR-0024`](../../decisions/0024-scrapling-y-mobygames-para-pc-dos.md).

## Criterios de aceptación

- [ ] Dado un juego MS-DOS con título, cuando se pide sugerir `developer`, aparece un
      candidato con fuente "MobyGames" y el valor de la ficha.
- [ ] Dado un juego que existe en varias plataformas, los datos que se ofrecen son los de la
      plataforma de la ficha (año, editor, formato), no los de otra edición.
- [ ] Dado un año en la ficha, entre ediciones del mismo título gana la del mismo año; se
      acepta un año de diferencia. Sin año, un título con más de una edición en esa plataforma
      responde "sin resultados" en vez de elegir una.
- [ ] Dado un sistema sin equivalencia en el catálogo de plataformas, MobyGames no se consulta
      y el rastro dice "plataforma sin equivalencia", no "sin resultados".
- [ ] Dado un juego arcade, MobyGames no se consulta y el rastro dice "plataforma sin
      equivalencia".
- [ ] Agregar una plataforma nueva es una fila en el catálogo, sin tocar código.
- [ ] Launchbox lee sus plataformas del catálogo; `_SYSTEM_TO_LAUNCHBOX` no existe más.
- [ ] Dado un título sin coincidencia clara por nombre y plataforma, **no** se devuelve un
      candidato adivinado: el proveedor responde "sin resultados".
- [ ] Dado cualquier campo de identidad, en cualquier sistema, "Sugerir" no ofrece ningún
      candidato generado por IA, tampoco en la sugerencia de identidad en bloque.
- [ ] Dado el alta de un juego MS-DOS, cada campo de identidad vacío se llena con MobyGames;
      si MobyGames no lo tiene, con Launchbox; si ninguno lo tiene, con la IA. Un campo con
      valor no se pisa, y cada campo escrito registra su fuente en la procedencia.
- [ ] Dada una reseña con categorías cargadas, aplicar la nota de MobyGames cambia `score` y
      deja las seis categorías como estaban.
- [ ] Dado Cloudflare sin resolver o un 403 persistente, el proveedor falla aislado y los
      demás siguen ([`002`](../002-sugerencias-multiproveedor/spec.md)).
- [ ] Dado que Chromium no está instalado, el proveedor no se construye y el resto de
      COINDOOR arranca y funciona.
- [ ] Dada una búsqueda cancelada, el navegador se cierra: no queda ningún proceso huérfano.
- [ ] Dos peticiones seguidas al mismo sitio quedan separadas por al menos 3 s, salvo que se
      configure otro ritmo.
- [ ] Un candidato nunca se aplica solo, y su fuente "MobyGames" queda en la procedencia
      interna y **no** viaja al export ([`ADR-0002`](../../decisions/0002-procedencia-interna.md)).
- [ ] Dos sugerencias del mismo juego mientras corre el proceso reutilizan la ficha ya
      descargada, también entre la precarga y "Sugerir".
- [ ] Los tests corren sin red, contra una página guardada.
- [ ] Al arrancar COINDOOR con Chromium y un sistema con equivalencia en MobyGames, se baja
      una página de búsqueda en segundo plano sin demorar el arranque, y la consulta que pide
      el usuario después ya no espera el desafío de Cloudflare
      ([`ADR-0025`](../../decisions/0025-precalentar-mobygames-al-arrancar.md)). Sin Chromium,
      solo con arcade, con `COINDOOR_SCRAPING_WARMUP=false` o con uno exitoso hace menos de
      6 horas, no sale a la red.

## Fuera de alcance

- **Imágenes de MobyGames.** Launchbox las cubre y tienen derechos; se evalúa aparte.
- **Créditos, series y trivia.** No tienen campo en el contrato de ATTRACT y no se inventan.
- **Revistas.** Las reseñas de MobyGames podrían alimentar `magazine_search`; es otra feature.
- **Migrar Launchbox a Scrapling.** Posible con el mismo motor, pero es su propia feature. Su
  tabla de plataformas sí pasa al catálogo en esta.
- **MobyGames para arcade.** Descartado en
  [`ADR-0024`](../../decisions/0024-scrapling-y-mobygames-para-pc-dos.md) (alternativa H).
