# 023 · myabandonware como primera fuente de PC/DOS

**Estado:** hecha (2026-10-30)

## Qué hace

Suma myabandonware.com como fuente de PC/DOS y reordena las fuentes según
[`ADR-0027`](../../decisions/0027-myabandonware-primera-fuente-de-pc-dos.md), en "Sugerir" y en
la precarga del alta:

1. **myabandonware primero:** título, año, desarrollador, editor, género, sinopsis (en inglés) y
   capturas de DOS, por HTTP común. El juego se encuentra en su `sitemap`; solo vale el título o
   un nombre alternativo exacto.
2. **Después Launchbox y la IA;** **MobyGames al final, solo para el campo que nadie tuvo.** Si
   myabandonware enlaza la ficha de MobyGames, MobyGames va directo a ella. En "Sugerir" queda
   un botón para consultar MobyGames igual.
3. **La reseña vuelve a ser solo de la IA.** Video, "Cómo se juega" y trucos no cambian.
4. **El modal de "Sugerir" muestra las fuentes en el orden en que se consultaron.**

## Por qué

MobyGames necesita el navegador y Cloudflare (20 s o más por consulta) y no encuentra todos los
juegos. myabandonware responde a HTTP común, es de juegos de DOS, tiene a *Civilization* (con
"Civilization" como nombre alternativo) y enlaza la ficha exacta de MobyGames. El dueño del
producto pidió el orden nuevo el 2026-10-30.

## Criterios de aceptación

- [x] Dada la página guardada de *Prince of Persia* (DOS, 1990), se leen el título, los nombres
      alternativos, el año, la plataforma, el primer editor del JSON-LD, el género, la
      descripción sin la firma ni las notas del sitio, solo las capturas de DOS y el enlace a
      MobyGames. Sin desarrollador en la página, no hay desarrollador.
- [x] Dado el `sitemap` y las páginas guardadas, "Prince of Persia" (MS-DOS, 1990) elige la
      página de DOS y "Civilization" (MS-DOS, 1991) elige *Sid Meier's Civilization*, no la de
      N-Gage, leyendo a lo sumo cinco páginas.
- [x] Un título que solo está *contenido* en otros no elige ninguno ("Doom").
- [x] Dos páginas de DOS con el mismo título las desempata el año; sin año, ninguna.
- [x] El `sitemap` se baja una vez y se reusa 30 días; si bajarlo falla y hay uno guardado, se
      usa ese. Nunca se pide `/search/`, `/download/` ni `/manual/`.
- [x] "Sugerir" desarrollador, editor, género o jugadores: candidatos de myabandonware y
      Launchbox; si ninguno tiene el dato, la IA (marcada); MobyGames solo si la IA tampoco.
- [x] "Sugerir" no consulta MobyGames si una fuente anterior ya dio un candidato para el campo;
      en ese caso el modal ofrece "Consultar" MobyGames. Reintentar MobyGames lo consulta.
- [x] Cuando se consulta MobyGames y myabandonware enlaza su ficha, MobyGames no busca.
- [x] En la precarga, cada campo de identidad vacío se llena con myabandonware, si no con
      Launchbox, si no con la IA y, por último, con MobyGames; la procedencia lo dice. El
      formato sale de MobyGames. La carátula, de Launchbox y si no de MobyGames; la captura, la
      de Launchbox (de juego o, si no, de título) y si no la primera de DOS de myabandonware.
- [x] La reseña solo tiene IA en su cadena; video, "Cómo se juega" y trucos no cambian.
- [x] El modal de "Sugerir" lista las fuentes en el orden de la cadena.
- [x] Los tests corren sin red, contra páginas guardadas de myabandonware.

## Fuera de alcance

- myabandonware para otras plataformas: solo se declara MS-DOS en el catálogo, las demás quedan
  sin equivalencia hasta probarlas.
- Las capturas de myabandonware en la galería (`media/_gallery/`): se sumaron después, en la
  [spec de la galería](../009-galeria/spec.md).
- Usar la descripción de myabandonware para que la IA escriba la sinopsis en español.
- Manuales: `robots.txt` prohíbe `/manual/`.
- SteamGridDB y ScreenScraper: siguen en la feature
  [021](../021-imagenes-steamgriddb-screenscraper/spec.md).
