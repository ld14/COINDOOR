# 022 · Edición correcta en todas las fuentes

**Estado:** hecha (2026-10-29)

## Qué hace

Ancla todas las fuentes a la edición que COINDOOR tiene en la ficha (título, plataforma y año),
como ya hace MobyGames desde la feature [020](../020-scrapling-mobygames/spec.md):

1. **Launchbox elige con la misma regla que MobyGames:** título exacto primero, plataforma y
   año. Hoy se queda con el primer título que *contiene* el buscado.
2. **Launchbox es la segunda fuente de identidad:** desarrollador, editor, género, jugadores y
   año salen de la página del juego elegido, en "Sugerir" y en la precarga, cuando MobyGames
   no los tiene.
3. **Carátula y capturas de la edición correcta:** primero las de la plataforma de la ficha de
   MobyGames ya elegida. Image Search queda al final y busca con el año.
4. **La IA como último recurso en "Sugerir" identidad**
   ([`ADR-0026`](../../decisions/0026-ia-ultimo-recurso-en-sugerir-identidad.md)): propone
   desarrollador, editor, género y jugadores solo si ninguna fuente factual tuvo el dato.

## Por qué

Probado con *Prince of Persia* (MS-DOS, 1990) el 2026-10-29:

- MobyGames eligió la ficha correcta: Brøderbund, 1990, disquete, 1 jugador.
- **Launchbox eligió *4D Prince of Persia*** (otro juego, de 1994) porque "contiene" el título y
  aparece antes en su lista alfabética. La captura y el logo del juego salieron de ahí.
- **Image Search trajo portadas de *Sands of Time*, *Warrior Within* y *The Lost Crown*:**
  imágenes alojadas en mobygames.com, pero de cualquier juego con ese nombre.
- **"Sugerir" quedó vacío** en juegos o campos que MobyGames no tiene (*Civilization*; los
  jugadores de *TMNT* y *Guy Spy*), porque la identidad ya no cae a la IA (ADR-0024, punto 4).

## Criterios de aceptación

- [x] Dada la búsqueda de Launchbox de *Prince of Persia* en MS-DOS (1990), se elige *Prince of
      Persia* (1990), no *4D Prince of Persia*.
- [x] Launchbox aplica los dos niveles de MobyGames: título exacto (con un año de tolerancia
      para desempatar) y, solo si no hay exacto, título que contiene todas las palabras con el
      año obligatorio (dos de tolerancia). Sin una coincidencia clara, no elige ninguno.
- [x] Dado un juego MS-DOS que MobyGames no tiene, "Sugerir" ofrece desarrollador, editor,
      género y jugadores de la página de Launchbox, con fuente "Launchbox".
- [x] Dada el alta de un juego MS-DOS, cada campo de identidad vacío se llena con MobyGames;
      si no lo tiene, con Launchbox; si ninguno lo tiene, con la IA. La procedencia lo dice.
- [x] Dado un juego MS-DOS con ficha de MobyGames, "Sugerir" carátula ofrece primero la portada
      frontal de DOS de esa ficha, y "Sugerir" captura, sus capturas de DOS.
- [x] Image Search incluye el año en sus búsquedas y aparece después de las fuentes de la
      edición.
- [x] Dado un campo entre desarrollador, editor, género y jugadores sin candidato de ninguna
      fuente factual, "Sugerir" ofrece el de la IA, marcado como IA. Si hay un candidato
      factual, la IA no se consulta.
- [x] La IA de respaldo nunca propone título, año ni formato, y se consulta una sola vez por
      juego aunque falten varios campos.
- [x] Los tests corren sin red, contra páginas guardadas de Launchbox y MobyGames.

## Fuera de alcance

- SteamGridDB y ScreenScraper: siguen en la feature [021](../021-imagenes-steamgriddb-screenscraper/spec.md).
- El navegador por plataforma de MobyGames como respaldo cuando el juego no está en la primera
  página de la búsqueda (*Civilization*).
- Imágenes de póster, marquesina y logo desde MobyGames: no las publica como tales.
