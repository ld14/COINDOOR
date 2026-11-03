# 024 · Ficha completa al cargar — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Un servicio nuevo, `services/completar.py`, orquesta lo que ya existe: corre la precarga de la
fuente y recorre los campos vacíos con `SuggestionsService.suggest` y
`FieldsService.apply_suggestion`, los mismos pasos que hace el usuario en el modal. Así la
procedencia, la cadena de fuentes y las reglas de cada campo no se duplican. Lo único nuevo es
elegir el candidato, y solo las imágenes del buscador necesitan criterio. Las demás fuentes ya
dicen qué tipo de imagen es cada una.

## Implementación

1. `backend/lib/providers/referencia/images.py` — sin tope; `_search_ddg_images` sigue `next`
   hasta el final con una pausa entre páginas. Cada candidato lleva `meta` con ancho, alto y
   texto. `encaja_en(key, meta, titulo, anio)` es el criterio de ADR-0028.
2. `backend/lib/providers/myabandonware/proveedor.py` — sin `MAX_CAPTURAS`.
3. `backend/lib/providers/mobygames/cliente.py` — sin `MAX_CAPTURAS` ni `MAX_PORTADAS`.
   `buscar_imagenes` recibe `cuantas`; `services/msdos.py` pide 1, porque usa solo la primera y
   cada portada es una página más por el navegador.
4. `backend/lib/media.py` — `colores_dominantes(ruta)`: la misma cuantización de
   `useDominantColors`, con ffmpeg, prefiriendo colores con saturación.
5. `backend/store/juegos.py` — `apply_accent_suggestion`.
6. `backend/lib/providers/orquestador.py` — `suggest(..., sin_memo=True)`: consulta de nuevo sin
   reiniciar el cortocircuito, como sí hace `reintentar`.
7. `backend/services/completar.py` — el job. La precarga de la fuente corre con un `JobState`
   propio que comparte `cancel_event`, para que su progreso no pise el del job.
8. `backend/api/games.py` — `POST /api/games/{game_id}/completar`.
9. `backend/services/gallery.py` — el buscador consulta los cinco casilleros, y el buscador y
   Launchbox reciben el año, que es lo que les deja elegir la edición.
10. `frontend/src/lib/api/games.ts` — `startCompletar`; salen `startPrecarga*`.
11. `frontend/src/pages/NuevoJuego.tsx`, `pages/nuevo/ResumenAlta.tsx`, `pages/FichaJuego.tsx`,
    `pages/ficha/PrecargaCard.tsx`, `pages/ficha/PrecargaBanner.tsx` — el alta y la ficha usan
    el job nuevo, en todos los sistemas.
12. `frontend/src/components/GalleryPanel.tsx` — una petición por fuente y carga diferida de
    miniaturas.

## Decisiones

- **Un job que compone lo existente en vez de reescribir las precargas** — ver
  [`ADR-0028`](../../decisions/0028-la-precarga-completa-toda-la-ficha.md).
- **Pausa de 1 s entre páginas del buscador** — `ImageSearchProvider` no pasa por `Politica`;
  sin tope son unas 15 páginas por casillero y no hay por qué pedirlas de golpe.
- **La galería pide cada fuente por separado** — el buscador pasa de segundos a un par de
  minutos, y myabandonware o Launchbox no tienen por qué esperarlo.
- **Rangos de proporción en el código, no en `fielddefs.json`** — los de `fielddefs` son el
  encuadre de la interfaz; estos toleran cajas reales, que no miden 3:4 exacto.
- **Los filtros de dominios confiables y de `www.mobygames.com/images/` siguen** — son calidad,
  no un tope.

## Riesgos

- **El buscador limita por exceso de pedidos** — la pausa lo reduce; si corta en una página, se
  conserva lo ya traído.
- **Una imagen de otra edición pasa el filtro** — el título de "Prince of Persia: The Sands of
  Time" contiene el del juego. Por eso lo que sobra en el título tiene que ser vocabulario
  genérico: lo que no esté en la lista lo rechaza, y el error queda del lado del casillero
  vacío. Medido sobre 1.440 resultados reales de tres juegos: pasan 76.
- **Títulos cortos que no son el comercial** — buscar "Monkey Island" no acepta "The Secret of
  Monkey Island". Queda vacío y el usuario elige en "Sugerir".
- **Muchas miniaturas en el modal** — `loading="lazy"`: solo se piden las visibles.
- **Cuota de IA en cada alta** — hay una casilla para no completar.
