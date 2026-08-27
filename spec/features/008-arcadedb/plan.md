# 008 · ArcadeDB — Plan

## Enfoque

Un proveedor nuevo que implementa el `Protocol` de `lib/providers/base.py` y entra por una fila
en `_TABLE`, más un servicio de precarga que aplica sus candidatos de una sola vez al crear el
juego. El proveedor sirve a los botones "Sugerir" que ya existen; la precarga reusa los setters
de `store/juegos.py` sin inventar caminos de escritura nuevos.

ArcadeDB se indexa por **romset de MAME**, no por título. La clave sale de
`Path(game.romRef).stem.lower()`, que el proveedor lee del `GamesStore` igual que ya hace
`IdentityActualProvider`. **`Consulta` no se toca**: cambiarla obligaría a tocar los otros
proveedores y sus tests.

Una consulta cuesta **dos peticiones** (`query_mame` + `query_mame_media`) y alimenta quince
campos. Un memo por proceso evita que quince llamadas a `buscar()` se conviertan en treinta
peticiones.

## Implementación

1. **`backend/lib/providers/arcadedb/parser.py`** — puro, sin red. Corta `history` por
   `^\s*-\s*([A-Z][A-Z '&]+?)\s*-\s*$`: la sinopsis es lo anterior a la primera sección (menos
   el boilerplate `published N years ago:` y la línea de copyright), los trucos son
   `- TIPS AND TRICKS -`. Parsea `buttons_colors` (`"P1_BUTTON1:Red:Attack;…"`) a una lista
   tipada, descartando las entradas sin acción.
2. **`backend/lib/providers/arcadedb/cliente.py`** — `fetch(romset, http) -> ArcadeGame | None`.
   Fusiona los dos endpoints. `result == []` con HTTP 200 devuelve `None`, **no** excepción, y
   **no** golpea el cortocircuito. Memo `dict[str, ArcadeGame | None]` con lock.
3. **`backend/lib/providers/arcadedb/proveedor.py`** — `ArcadeDbProvider`. `campos` sale de
   `fielddefs.py`. Devuelve solo los candidatos de `consulta.key`.
4. **`backend/lib/providers/registro.py`** — filas en `_TABLE` con `"arcadedb"` primero, más su
   rama en `_build`.
5. **`backend/services/arcadedb.py`** — `ArcadeDbPrecargaService.run(game_id, *, force)`
   devuelve un `Callable[[JobState], dict]` para `submit()`. Gate por sistema antes de la red;
   escribe solo campos vacíos; devuelve `{estado, romset, escritos, omitidos}`.
6. **`backend/api/games.py`** — `POST /api/games/{game_id}/arcadedb` → `SuggestionJob`.
7. **`backend/store/juegos.py`** — `set_cabinet()`, y `_identity_source()` reconoce `"ArcadeDB"`.
8. **`backend/services/fields.py`** — `_download_candidate_media` deriva la extensión del
   `content-type` cuando la URL no la tiene.
9. **`backend/api/schemas.py`** — `CabinetInfo`, `CabinetButton`, `StoredGame.cabinet`.
10. **`frontend/src/pages/NuevoJuego.tsx`** — dispara la precarga tras el `uploadRom` y pasa el
    `jobId` por query string.
11. **`frontend/src/pages/FichaJuego.tsx`** — banner de precarga, panel `GABINETE`, y
    `suggestionStatus` extendido para devolver el contenido actual.
12. **`frontend/src/components/SuggestionsModal.tsx`** — prop `current`, que pinta el contenido
    real en vez del texto literal de hoy.

## Decisiones

### El romset sale de `romRef`, y `Consulta` no cambia

Agregar el romset a `Consulta` obligaría a tocar los cinco proveedores existentes, sus tests y
las dos rutas del orquestador, para un dato que solo usa uno. El proveedor lee el `GamesStore`,
que es el precedente que ya sentó `IdentityActualProvider`.

### `short_title`, no `title`

`title` trae `"Golden Axe (set 6, US) (8751 317-123A)"`. Ese texto terminaría en el `set` del
bundle vía `safe_id`. `title` se ofrece igual, como segundo candidato en el modal.

### Carátula y póster salen del mismo flyer

`url_image_box` viene vacío en arcade y los dos campos son `required` en `fielddefs.json`. Dejar
`poster` sin llenar deja el juego `incomplete` para siempre, que es peor que duplicar 830 KB.
`contract.json` ya declara `fallbacks.cover: [boxFront, poster, marquee, generic]`.

### `manufacturer` va a `developer` **y** a `publisher`

MAME tiene un solo campo de empresa. En arcade coinciden casi siempre. Cuando la línea de
copyright de `history` nombra otra, se ofrece como segundo candidato.

### La precarga es un endpoint propio, no un efecto de `POST /api/games`

Mantiene el alta sincrónica, da progreso y cancelación, y permite distinguir "falló crear" de
"falló ArcadeDB". Además `romRef` solo es la ruta final **después** del `uploadRom`. Ver
[`ADR-0015`](../../decisions/0015-precarga-con-red-al-alta.md).

### La identidad de ArcadeDB se registra como `mame`

ArcadeDB deriva del `.dat` de MAME (`emulator_name: "Mame 0.289"`), que es la autoridad que
[`ADR-0004`](../../decisions/0004-coindoor-fuente-identidad-no-mame.md) nombra para arcade. Sin
esto, `_identity_source` la colapsa a `"manual"` y cada "Sugerir" posterior pediría confirmación
de reemplazo.

### El tile "contenido actual" se resuelve en el frontend

Un proveedor de backend estaría roto para media: `fields.py` exige que `mediaUrl` sea `http(s)`,
y el valor actual de una imagen es una ruta local. Además la acción correcta es **no mutar
nada**, y el frontend ya tiene el `Game` entero en memoria.

### Los datos de gabinete no se exportan

`attract/instalar.py` escribe un conjunto fijo de campos, sin passthrough, y `build_gamejson`
construye desde una allowlist. Un campo nuevo en `StoredGame` que ningún exportador lee no puede
llegar al bundle. Consistente con [`ADR-0002`](../../decisions/0002-procedencia-interna.md).

## Riesgos

- **El caso común es el miss.** Una ROM llamada `Golden Axe (USA).zip` no matchea ningún romset. La interfaz tiene que decirlo en claro y no como error, o la feature parece rota cuando funciona bien.
- **Colisión de romset.** `sf2.zip` en un sistema SNES matchearía el Street Fighter II de arcade. Doble mitigación: gate por sistema antes de la red, y escritura solo sobre campos vacíos.
- **`_identity_source` colapsa a `"manual"`** si no se parchea. Falla silenciosa: no rompe ningún test existente, solo degrada la experiencia de los "Sugerir" posteriores.
- **Extensión mal derivada.** Las URLs de ArcadeDB no tienen extensión; sin el parche se guardan bytes PNG en archivos `.jpg`. Pasa la validación del contrato y explota recién en el gabinete.
- **El `summary` exportado lleva texto de arcade-history.** Único dato de terceros que cruza al bundle, y ADR-0002 impide acompañarlo de su atribución. Sin mitigación técnica; el campo queda editable.
- **El memo no expira.** `force=true` tiene que invalidar la entrada, no solo saltear el chequeo de campo vacío, o corregir el `romRef` y reintentar devuelve el mismo miss cacheado.
