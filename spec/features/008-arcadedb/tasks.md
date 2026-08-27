# 008 · ArcadeDB — Tareas

## Antes de tocar código

- [x] `spec.md` cerrado. **Hecho cuando:** los criterios de aceptación son testeables uno por uno.
- [x] [`ADR-0014`](../../decisions/0014-arcadedb-fuente-arcade.md) escrito, `supersedes: 13`. **Hecho cuando:** ADR-0013 queda `superseded-by: 14` y el índice lo refleja.
- [x] [`ADR-0015`](../../decisions/0015-precarga-con-red-al-alta.md) escrito. **Hecho cuando:** `tech-stack.md` §Convenciones nombra la excepción.
- [x] Bloqueante obsoleto de ScreenScraper/MobyGames retirado de `tech-stack.md` §Pendientes y de `roadmap.md` §Bloqueado. **Hecho cuando:** ninguno de los dos pide credenciales que ADR-0013 ya descartó.

## Implementación

### Fase 1 — cliente y parser

- [ ] `lib/providers/arcadedb/parser.py`: secciones de `history`, sinopsis, trucos, `buttons_colors`. **Hecho cuando:** un `history` de fixture produce sinopsis sin boilerplate y la lista de tips.
- [ ] `lib/providers/arcadedb/cliente.py`: `fetch()` fusionando los dos endpoints, con memo. **Hecho cuando:** un miss devuelve `None` sin excepción y sin golpear el cortocircuito.

### Fase 2 — proveedor

- [ ] `lib/providers/arcadedb/proveedor.py` con `campos` derivado de `fielddefs.py`. **Hecho cuando:** `mypy backend/lib` lo acepta como `Proveedor` sin `cast`.
- [ ] Filas en `_TABLE` y rama en `_build` de `registro.py`. **Hecho cuando:** un "Sugerir" de carátula en un juego arcade devuelve candidatos de ArcadeDB.

### Fase 3 — precarga

- [ ] Parche a `store/juegos.py::_identity_source` para `"ArcadeDB"`. **Hecho cuando:** aplicar identidad deja `identitySource == "mame"`.
- [ ] Parche a `services/fields.py::_download_candidate_media` para derivar extensión del `content-type`. **Hecho cuando:** una URL sin extensión con `image/png` produce un archivo `.png`.
- [ ] `services/arcadedb.py` con gate por sistema, escritura solo sobre vacíos y estados `ok`/`no-encontrado`/`sin-romset`/`sistema-no-soportado`. **Hecho cuando:** los cuatro estados salen en el payload del job.
- [ ] `POST /api/games/{game_id}/arcadedb` en `api/games.py`. **Hecho cuando:** devuelve `{jobId}` y el job termina `succeeded` también en el miss.
- [ ] Disparo en `NuevoJuego.tsx` tras el `uploadRom` y banner en `FichaJuego.tsx`. **Hecho cuando:** crear un juego arcade llena la ficha sin apretar nada más.

### Fase 4 — gabinete, manual y atribución

- [ ] `CabinetInfo`/`CabinetButton` en `schemas.py` y `StoredGame.cabinet`. **Hecho cuando:** un `game.json` viejo sin el campo sigue leyéndose.
- [ ] `GamesStore.set_cabinet`. **Hecho cuando:** escribe atómico como el resto de los setters.
- [ ] Panel `GABINETE` en `FichaJuego.tsx` con la línea de atribución. **Hecho cuando:** muestra resolución, orientación y controles, y cita a ArcadeDB y arcade-history.
- [ ] `ManualsService.import_url` + `POST /api/games/{id}/manuals/from-url`. **Hecho cuando:** rechaza una URL que no devuelve `application/pdf`.

### Fase 5 — contenido actual

- [ ] `suggestionStatus` en `FichaJuego.tsx` devuelve también el contenido actual. **Hecho cuando:** cubre los cinco tipos de campo que ya despacha.
- [ ] Prop `current` en `SuggestionsModal.tsx`. **Hecho cuando:** el primer tile pinta la imagen o el texto real, no el string literal.
- [ ] Borrar `identity_actual` de `_TABLE` y su proveedor. **Hecho cuando:** `test_providers.py` pasa sin él.

## Tests

- [ ] `test_arcadedb_parser_separa_secciones` — puro, sin red.
- [ ] `test_arcadedb_miss_no_devuelve_candidatos` — `result: []` con HTTP 200, y el cortocircuito **no** se activa.
- [ ] `test_arcadedb_una_sola_fetch_para_muchos_campos` — tres `buscar()` → exactamente 2 peticiones.
- [ ] `test_arcadedb_mapea_identidad_y_media` — `short_title` al título; el flyer en `caratula` **y** en `poster`.
- [ ] `test_precarga_solo_llena_campos_vacios` — protege la regla de la constitución.
- [ ] `test_precarga_miss_no_escribe_nada` — `game.json` idéntico, job `succeeded`.
- [ ] `test_precarga_saltea_sistema_no_arcade` — cero peticiones al handler.
- [ ] `test_precarga_extension_desde_content_type`.
- [ ] `test_precarga_manual_pdf_aterriza_en_manuals`.
- [ ] `test_gabinete_no_viaja_al_bundle` — guarda [`ADR-0002`](../../decisions/0002-procedencia-interna.md).
- [ ] `test_api.py`: `POST /api/games/{id}/arcadedb` de punta a punta.
- [ ] Vitest: `SuggestionsModal` con `current` pinta el contenido y no aplica al clickearlo.

## Cierre

- [ ] Los once criterios de aceptación de `spec.md`, validados uno por uno.
- [ ] `uv run ruff check .`, `uv run mypy backend/lib`, `npm run build` limpios.
- [ ] Prueba a mano con `goldnaxe.zip` y con `Golden Axe (USA).zip`, según §Verificación del plan.
- [ ] `spec.md` a **implementada** y 008 a "Hecho" en `constitution/roadmap.md`.
- [ ] `backend/CLAUDE.md`: mencionar `lib/providers/arcadedb/` en §Estructura.
