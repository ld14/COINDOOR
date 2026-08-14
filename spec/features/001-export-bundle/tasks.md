# 001 · Export a bundle — Tareas

## Antes de tocar código

- [x] Confirmar la versión de contrato que estampa `bundle.json`. Placeholder `"1"` hasta
      que ATTRACT publique el suyo — ver spec.md §Decisiones resueltas.
- [x] Acordar con ATTRACT el nombre y la firma de `attract install <bundle>.zip`.
      Confirmado como provisional: `attract install <bundle>.zip`, un solo argumento
      posicional.
- [x] Resolver el mapeo `identitySource` → `identidad.origen` (bloqueaba en
      `roadmap.md`). `IdentitySource` pasa a `'mame' | 'screenscraper' | 'manual'`.
- [x] Resolver qué se escribe en `players` cuando no es un entero limpio (bloqueaba en
      `roadmap.md`). Mismo criterio que ATTRACT: default `1`.

## Implementación

- [x] `frontend/src/lib/domain/types.ts` — ampliar `IdentitySource` a
      `'mame' | 'screenscraper' | 'manual'`. También `backend/api/schemas.py` (mismo
      tipo del lado Python) y `mocks/seed.ts` (se deriva de `systemId`).
- [x] Prerrequisito no listado originalmente: `PUT /api/games/:id/media/:key` — no había
      forma de guardar un archivo real en el backend. Sin esto `seleccion.py` no tenía
      nada real que pesar.
- [x] `bundle/seleccion.py` — tabla `(campo, obligatorio, disponible, bytes)`. Hecho: lo
      obligatorio sale de `fielddefs.json`, la misma fuente que `completeness.py`. Pesos
      reales para imágenes/video/texto/review/cheats/accent. `manual` y `juego`
      (romSource=upload) quedan en `bytes: 0` marcados `ponytail:` — no tienen
      almacenamiento real todavía, ver tareas nuevas abajo.
- [ ] **Deuda marcada con `ponytail:` en `seleccion.py`, pendiente de su propio
      prerrequisito** (no bloquea lo demás, pero el peso de `manual`/`juego` en el
      bundle final va a ser incorrecto hasta resolverlo):
      - Endpoint que guarde el PDF de un manual y sus páginas rasterizadas en disco.
      - Endpoint que guarde el ROM subido cuando `romSource: upload` (hoy solo
        funciona si `romRef` ya es una ruta real en esa máquina, es decir
        `romSource: path`).
- [x] `bundle/datajson.py` — serializa `accent`, `accent2`, `review`, `cheats` y
      `manual[]`. Test con el `data.json` real de `goldnaxe` copiado en el test (no como
      dependencia de `../attract` en tiempo de test) — coincide exacto, menos `mags[]`.
      `manual[].pages` deriva nombres `pNNN.png` por convención de ATTRACT (mismo hueco
      de rasterizado pendiente que ya marca `seleccion.py`).
- [x] `bundle/staging.py` — árbol temporal con los nombres del contrato, respetando la
      selección. `caratula`→`boxFront`, `captura`→`screenshot` vía `contractAsset` de
      `fielddefs.json`. Dos corridas producen árboles equivalentes (test con
      `filecmp.dircmp`). `manual` se descarta siempre de `incluir` antes de armar
      `data.json` — mismo hueco de rasterizado marcado en `seleccion.py`/`datajson.py`,
      acá con la consecuencia real: nunca miente sobre páginas que el zip no trae.
- [x] `bundle/manifest.py` — `bundle.json` con identidad, artefactos, `incluye[]` y
      `verificado`. `origen` sale de `identitySource` directo (`mame`→`mame`, el resto
      →`declarada`). **Deuda marcada `ponytail:`**: no hay tracking de "identidad
      editada a mano después de precargarse desde MAME" (ADR-0004 regla 1) —
      `StoredGame` no guarda los valores originales para diffear. El lado elegido es el
      seguro: nunca dice `mame` de algo no confirmado, en el peor caso subreporta
      `declarada`.
- [x] **Fix de raíz encontrado al escribir manifest.py**: `staging.py` copiaba una
      carpeta de MS-DOS tal cual (`copytree`) en vez de comprimirla — spec.md exige que
      **los dos casos terminen en `.zip`**. Corregido: `_copy_rom` ahora zippea
      carpetas y devuelve `(nombre, tratamiento)`; `build_staging` devuelve
      `StagingResult` (root + incluye efectivo + rom_archivo + rom_tratamiento) en vez
      de un `Path` pelado.
- [x] `bundle/verify.py` — `attract doctor` sobre el staging, con degradación si el binario
      falta. Hecho: en una máquina sin ATTRACT devuelve `no_verificado` y no lanza; si
      `doctor` falla, bloquea el zip.
- [x] `bundle/pack.py` — `ZIP_STORED`, y limpieza del staging pase lo que pase.
- [x] API: `POST /export`, `GET /export/:runId`. Hecho: crea job y el polling usa el
      registro de jobs en memoria existente.
- [x] API: `GET /games/:id/export-options` con los pesos calculados en el servidor.
- [ ] UI: panel "Qué incluir" — bloque obligatorio bloqueado, opcionales con su peso,
      vacíos deshabilitados con `—`, y el total en vivo.
- [ ] UI: pantalla de resultado con el archivo generado, su peso y qué lleva adentro.

## Tests

- [ ] `goldnaxe` completo → bundle con `bundle.json`, `media/`, `_synopsis.json` y
      `juego/`. Es el caso de referencia.
- [ ] Romset de MAME → `tratamiento: copiar`. Carpeta de MS-DOS → `descomprimir`.
      **Sin este test los dos `.zip` se tratan igual y el juego de DOS no arranca.**
- [ ] `incluir video = no` → ni el archivo ni la referencia en `data.json`.
- [ ] `incluir juego = no` → `artefactos: []` y el `.zip` sin la carpeta `juego/`.
- [x] **Intentar deseleccionar un obligatorio → rechazado en la API**. La UI queda
      pendiente con el panel "Qué incluir".
- [ ] Un juego con revista vinculada → el `data.json` del bundle **no tiene `mags[]`**.
- [x] Un campo opcional vacío → llega como `disponible: false` y no se puede marcar.
- [ ] Identidad editada → `origen: declarada`. Sin editar y con catálogo → `mame`.
- [ ] `review: null` se escribe como `null`; una `cats` parcial no se completa con ceros.
- [ ] `cheats` con un grupo de nombre inventado sobrevive el viaje con su nombre.
- [ ] `doctor` con error → **no se genera el `.zip`** y el staging queda limpio.
- [x] Sin `attract` en el `PATH` → el `.zip` se genera y el resultado dice `no verificado`.
- [ ] Export interrumpido a la mitad → no queda staging huérfano.
- [ ] Dos exports seguidos sin editar → bundles equivalentes.

## Cierre

- [ ] Validar contra todos los criterios de aceptación de `spec.md`.
- [ ] Instalar un bundle a mano en una librería real —desarmando el `.zip` con las reglas
      de `bundle.json`— y ver el juego en el gabinete. Es la única prueba de que el formato
      sirve antes de que `attract install` exista.
- [ ] Actualizar `roadmap.md`.
