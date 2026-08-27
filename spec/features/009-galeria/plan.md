# 009 · Galería de imágenes — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

La galería es una lista, no un `MediaField`, así que vive en `StoredGame.gallery` y
no en `images`. Eso la mantiene fuera de los tres consumidores de
`fielddefs.json → images[]` —completitud, `contract_asset()` y `_copy_assets`— que
asumen un campo con una sola `url` y un asset del contrato al que mapear.

El módulo se apoya en lo que ya existe: el cliente de ArcadeDB y su memo, el
detector de extensión por magic bytes de `backend/lib/media.py`, la escritura atómica
de `store/archivo.py`, el registro de jobs en proceso y `apply_media_suggestion` del
store. No introduce ningún proveedor nuevo.

Listar candidatos es sincrónico, como `magazines/search` y `manuals/search`: es un
fetch memoizado, sin descargas. Guardar es un job porque son hasta 14 descargas y la
ficha ya tiene el polling de progreso que usa la precarga.

## Implementación

1. `backend/lib/domain/gallery.py` — mapa estático tipo de ArcadeDB → etiqueta en
   español, y el `label_para(tipo)` que cae al nombre crudo si el tipo es nuevo.
2. `backend/lib/providers/arcadedb/cliente.py` — `fetch_con_padre(romset, http)`:
   cuando `cloneof` está seteado, trae el padre y fusiona **sólo `images`**.
3. `backend/api/schemas.py` — `GalleryImage` (`id`, `tipo`, `label`, `file`, `url`,
   `source`) y `StoredGame.gallery: list[GalleryImage]`.
4. `backend/store/juegos.py` — `add_gallery_images`, `remove_gallery_image`.
5. `backend/services/gallery.py` — `candidatos`, `guardar` (job), `usar_como`,
   `eliminar`.
6. `backend/api/gallery.py` — router `/api/games/{id}/gallery`, registrado en
   `backend/main.py`.
7. `backend/bundle/seleccion.py` — `galeria` como opcional de export.
8. `backend/bundle/staging.py` — copia a `root/media/_gallery/` cuando está
   seleccionada.
9. `backend/bundle/datajson.py` — clave `gallery` con `{file, label}`.
10. `frontend/src/lib/api/gallery.ts` + panel GALERÍA en
    `frontend/src/pages/FichaJuego.tsx`.

## Decisiones

- **`media/_gallery/` con guión bajo y declaración en `data.json`, en vez de assets
  inventados en `media/` plano** — el contrato tiene seis assets fijos y la
  cardinalidad de la galería es variable.
  Ver [`ADR 0016`](../../decisions/0016-galeria-en-subcarpeta-gallery.md).
- **`gallery` fuera de `fielddefs.json → images[]`** — ese array exige
  `contractAsset` y un `MediaField` de una sola `url`.
  Ver [`ADR 0016`](../../decisions/0016-galeria-en-subcarpeta-gallery.md).
- **Etiquetas en español por mapa estático y no por IA** — son ~16 valores conocidos
  y cerrados: determinista, instantáneo y sin gastar cuota, a diferencia de los
  textos libres de la precarga, que sí se traducen.
- **Del padre se fusionan sólo las imágenes, nunca la identidad** — el romset padre
  puede ser otra región y pisaría título y año del juego que el usuario cargó.
- **Numeración `gNNN` y no el nombre del tipo** — sigue la convención de
  `pages/pNNN.jpg`; el tipo se conserva en `label`, que es donde el theme lo va a
  leer.

## Riesgos

- **ATTRACT empieza a rechazar claves desconocidas en `data.json`** — hoy
  `chk_data_contrato` valida sólo la forma de lo que conoce, y hay un test de
  staging que fija la forma que se emite. Si cambia, el export falla en
  `verify_staging` con el código de salida de `attract doctor`, no en silencio.
- **ArcadeDB agrega un tipo que el mapa no conoce** — `label_para` cae al nombre
  crudo; la imagen se guarda igual, sólo se ve con etiqueta en inglés.
- **El fetch del romset padre suma una petición por juego clon** — sólo cuando
  `cloneof` está seteado, y el memo del cliente evita repetirla dentro del proceso.
