# 021 · Imágenes desde SteamGridDB y ScreenScraper — Tareas

## Antes de tocar código

- [ ] Feature [`020`](../020-scrapling-mobygames/tasks.md) hecha: sin `ScrapingClient` no hay
      base para estos proveedores.
- [x] **ScreenScraper, descarga:** el 403 es una protección contra enlaces directos. Con
      `Referer` de la ficha, `medias/1/1/ss(wor).png` baja con 200. Sin cuenta.
- [x] **ScreenScraper, búsqueda:** no se encontró búsqueda por nombre para invitados; el camino es el
      listado `gamesinfos.php?alpha=…&numpage=…&plateforme=…`, 25 por página, con cookie de `/`.
- [x] **SteamGridDB, descarga:** el archivo completo baja con 200 (940 KB y 492 KB).
- [ ] ScreenScraper: cargar en el catálogo `plataformas.json` el `plateforme` de cada sistema
      de COINDOOR (MS-DOS, arcade) desde `systemeinfos.php`. Hecho cuando: el listado devuelve
      juegos de MS-DOS.
- [ ] ScreenScraper: listar todos los tipos de medio de una ficha completa (caja, marquesina,
      logo, video…) y su nombre en la URL. Hecho cuando: cada clave de imagen de COINDOOR y
      `video` tienen su tipo, o se anota que no existe.
- [ ] ScreenScraper, video: confirmar que el MP4 de la ficha baja con el mismo `Referer`.
- [ ] SteamGridDB: medir un grid y un hero de la ficha guardada. Hecho cuando: se confirma
      600×900 (2:3) y ≈3:1, o se corrige el mapeo del plan.
- [ ] Guardar como fixtures una búsqueda y una ficha de cada sitio.

## Implementación

- [ ] `steamgriddb/parser.py`. Hecho cuando: de la ficha guardada saca grids verticales,
      heroes y logos con su URL completa, y descarta los grids horizontales.
- [ ] `steamgriddb/cliente.py` y `proveedor.py`.
- [ ] `screenscraper/parser.py`. Hecho cuando: del listado guardado saca nombre y `gameid`, y de
      la pestaña de medios cada URL con su tipo, video incluido.
- [ ] `screenscraper/cliente.py` y `proveedor.py`, con cookie de sesión y `Referer`.
- [ ] Cabeceras por petición en `scraping.py`, y el `Referer` de `Candidato.meta["referer"]`
      en `services/fields.py::_download_candidate_media`.
- [ ] Filas en `registro.py`: `poster`, `marquesina` y `logo` para SteamGridDB; las cinco
      claves de imagen y `video` para ScreenScraper.
- [ ] Tests sin red para parsers, clientes y proveedores.

## Cierre

- [ ] Probar con 3 juegos (uno arcade, dos MS-DOS) y anotar cuántos candidatos útiles aporta
      cada sitio frente a Launchbox, y si ScreenScraper trae video de los dos MS-DOS.
- [ ] `ruff`, `mypy` y `pytest` en verde.
- [ ] Marcar la feature como hecha en [`roadmap.md`](../../constitution/roadmap.md).
