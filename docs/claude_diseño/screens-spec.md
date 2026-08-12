# COINDOOR — Especificación de pantallas

Cinco pantallas dentro del layout DOS fijo (barra de título cian, menú lateral gris, área de
contenido hundida, barra negra de F-keys). Ver `design-system.md` para el vocabulario visual y
`data-model.md` para tipos y reglas.

---

## 1. Chrome de la aplicación

### 1.1 Barra de título
Franja cian `#00AAAA` de altura automática (padding 4px vertical), texto negro 700 centrado:
`COINDOOR — Carga de juegos retro`. A la izquierda, absoluto, un cuadradito gris de 12×12 con
borde outset (el botón de menú de sistema de una ventana DOS; es decorativo).

### 1.2 Menú lateral
Panel gris de 190px con borde outset. Cabecera azul `Main Menu`. Tres ítems con la primera letra
subrayada:

- `Sistemas` → `/sistemas`
- `Juegos` → `/juegos`
- `Exportar` → `/exportar`

El ítem activo va con fondo cian y peso 700. Al pie, separado por una línea de 1px, el contador
en azul oscuro: `N juegos` / `N sistemas`.

### 1.3 Aviso del contrato
Banner amarillo `#FFFF55`, texto negro, dismissible con `[X]`:

> **¡ CONTRATO** — La copia local del contrato ATTRACT puede estar desactualizada. Los campos
> requeridos mostrados son de referencia.

Aparece sobre el área de contenido. Una vez cerrado, no vuelve en la sesión.

### 1.4 Barra de estado
Franja negra al pie, teclas en amarillo:
`F1 Ayuda · F2 Sistemas · F3 Juegos · F4 Exportar · Esc Cerrar`.
F2/F3/F4 navegan de verdad; Esc cierra el modal abierto.

---

## 2. Sistemas / Plataformas — `/sistemas`

**Título:** `Sistemas / Plataformas`
**Bajada:** "Un juego siempre pertenece a un sistema. La ruta del comando de lanzamiento debe
ser absoluta."
**Acción primaria:** `+ Nuevo sistema` (arriba a la derecha).

**Grilla** `repeat(auto-fill, minmax(270px, 1fr))`, gap 14px. Cada tarjeta (blanca, outset):

- Nombre visible en 14.5px 700 azul oscuro; debajo el nombre corto en 12px gris.
- `N juegos`.
- El comando de lanzamiento en una caja negra con texto verde de terminal, borde inset, truncado
  con elipsis.
- Si el sistema es inválido: borde de la tarjeta rojo `#AA0000`, etiqueta `CABECERA INVÁLIDA` en
  rojo arriba a la derecha, y al pie `X La ruta del comando de lanzamiento debe ser absoluta.`

### Modal "Nuevo sistema" (420px)

Tres campos: Nombre visible, Nombre corto, Comando de lanzamiento del emulador
(placeholder `/opt/emulador/bin %rom%`).

Validación en vivo del comando: si el usuario escribió algo y no es ruta absoluta, mensaje rojo
de 11.5px debajo del campo con el texto completo de `validation.ts`. `Crear sistema` no envía
mientras haya error.

---

## 3. Juegos — `/juegos`

**Título:** `Juegos`. **Acción primaria:** `+ Agregar juego`.

**Filtros** en una fila: buscador por nombre (máx. 300px), select de sistema
(`Todos los sistemas` + uno por sistema), select de estado (`Todos los estados` / `Listo` /
`Incompleto` / `Con errores`). Los tres viven en la query string.

**Lista** dentro de una caja blanca con borde inset. Cada fila (48px aprox., separada por
`1px solid #AAAAAA`, hover cian, click abre la ficha):

```
[ portada 40×40 ]  Título del juego                    [ ESTADO ]
                   Sistema · Año · catálogo|manual
```

La miniatura muestra `coverThumbUrl` en `object-fit: cover`. Si el juego no tiene carátula, cae
al placeholder: fondo gris, borde `1px solid #808080`, iniciales del título en 9px negro.

**Vacíos:**
- Sin resultados de filtro: "Ningún juego coincide con la búsqueda o los filtros."
- Biblioteca vacía: bloque centrado con "Todavía no hay juegos cargados", una línea de ayuda y
  el botón `+ Agregar juego`.

**Paginación:** 50 por página, controles explícitos al pie (`◄ Anterior · Página N de M ·
Siguiente ►`) con estilo de botón ghost.

---

## 4. Alta de un juego — `/juegos/nuevo`

Columna de máx. 560px. **Título:** `Alta de un juego`.
**Bajada:** "Se parte del archivo de ROM. Si el sistema lo reconoce, la identidad viene del
catálogo; si no, se declara a mano."

### Paso 1 — Origen (panel blanco outset)

- **Sistema**: select con todos los sistemas.
- **Origen del archivo**: dos radios en una fila.
  - `Subir ROM` — input de archivo, placeholder `ej: sf2.zip`.
  - `Indicar ruta (juegos pesados)` — input de texto, placeholder `ej: /roms/arcade/sf2.zip`,
    y debajo, en 11.5px gris: "El archivo se queda donde está — no se copia. Útil para ROMs de
    varios GB."
  Cambiar de modo limpia el valor cargado.
- Botón `Continuar` → `POST /roms/identify`.

### Paso 2 — Identidad

Una insignia arriba según el resultado:

- Reconocido: `✓ IDENTIDAD: CATÁLOGO — confirmá los datos` (verde de terminal sobre negro).
- No reconocido: `~ IDENTIDAD: DECLARADA A MANO` (cian sobre negro) + "Este sistema no tiene
  catálogo automático. Completá los datos vos."

Debajo, un panel blanco con los 7 campos de identidad en grilla de 2 columnas — Título ocupa las
dos, el resto una cada uno. Si vino del catálogo, los campos llegan precargados y editables.

Acciones: `Crear ficha` (primary) y `Cancelar` (ghost, vuelve a `/juegos`).
Al crear, navega a `/juegos/:id`.

---

## 5. Ficha del juego — `/juegos/:gameId`

Columna de máx. 920px.

### 5.1 Cabecera (sticky)

Izquierda: enlace `<< Juegos`, luego el título en 16px 700 azul junto a la insignia de origen de
identidad, y debajo `Sistema · Año` en gris.
Derecha, alineado a la derecha: la insignia de estado, el resumen (`N campo(s) faltante(s)` o
`N error(es) de formato`) y el botón `Marcar como listo`.

### 5.2 Recuadros de aviso

Ambos pueden aparecer a la vez, siempre fondo negro con borde rojo de 2px:

- **Errores de formato** (si `game.errors.length`): título rojo
  `ERRORES DE FORMATO (bloquean el export):` y una línea por error: `- **Campo** — mensaje`.
- **Faltantes** (solo tras pulsar "Marcar como listo" sin cumplir): título
  `NO SE PUEDE MARCAR COMO LISTO — faltan campos requeridos:` y una línea por faltante.

### 5.3 Índice lateral

Columna fija de 120px, sticky, con las siete secciones en texto gris:
Identidad · Imágenes · Video · Textos · Presentación · Manual · Revista.
Hace scroll suave a la sección (sin usar `scrollIntoView`: calcular offset y `window.scrollTo`).

### 5.4 Identidad

Cabecera azul `IDENTIDAD` a 100% de ancho. Panel blanco con grilla de 3 columnas: etiqueta en
11px gris, valor en 13.5px. Editable in situ al hacer click en el valor.

### 5.5 Imágenes

Cabecera azul `IMÁGENES`. Grilla `repeat(auto-fill, minmax(185px, 1fr))`, gap 12px. Cinco
tarjetas (Carátula, Marquesina, Póster, Logo, Captura). Cada tarjeta:

```
Etiqueta                      ● MANUAL
┌────────────────────────┐
│  preview negra          │   ← imagen o "carátula · 3:4"
└────────────────────────┘
[Cargar|Reemplazar] [Sugerir] [Borrar]
```

`Borrar` solo aparece si el campo tiene contenido. El botón primario dice `Cargar` cuando está
vacío y `Reemplazar` cuando no.

### 5.6 Video

Cabecera azul `VIDEO`. Una sola tarjeta idéntica a las de imagen, ancho máx. 350px.

### 5.7 Textos

Cabecera azul `TEXTOS`. Tres tarjetas apiladas (Sinopsis, Reseña, Trucos). Cada una: etiqueta +
insignia de estado, un `<textarea>` de mínimo 54px con borde inset (placeholder `Sin cargar…`) y
un botón `Sugerir`. Escribir en el textarea pasa el campo a `manual`; vaciarlo lo devuelve a
`empty`.

### 5.8 Presentación

Cabecera azul `PRESENTACIÓN`. Panel blanco a 100% de ancho, en dos filas separadas por una línea
de 1px:

**Fila 1** — `Color de acento`, los 5 swatches preset de 22×22px (el elegido con borde inset, el
resto outset) y a la derecha la etiqueta de origen (`sin definir` / `cargado` / `sugerido`).

**Fila 2** — `Agregar color HEX:` + input de 100px (placeholder `#RRGGBB`) + botón `Agregar`; si
el valor no valida, mensaje rojo `Formato inválido (ej: #2F6FED)` al lado. A la derecha del todo,
botón `Detectar de la carátula`, que extrae el color predominante de la portada
(`POST /games/:id/accent/detect`) y deja el acento en estado `suggested`. Si no hay carátula
cargada, el botón queda deshabilitado.

### 5.9 Manual

Cabecera azul `MANUAL` a 100% de ancho; el panel blanco también ocupa el 100%. **Un juego puede
tener varios manuales.**

Si no hay ninguno: "Sin manuales todavía. Se pueden adjuntar varios (ej: manual + guía rápida);
cada uno se procesa por separado."

Luego, una entrada por manual (caja con borde de 1px, gap 10px), con el nombre de archivo
precedido de `📎` y, según su estado:

- **unprocessed** — "Adjuntado, sin procesar todavía — estado intermedio, no es 'sin manual'." +
  botón `Procesar`.
- **processing** — "Procesando páginas… N%", barra de progreso y botón `Cancelar`.
- **processed** — "✓ N páginas generadas" y la tira de miniaturas de página (32×44px, negras).

Al pie, el botón de adjuntar: dice `Adjuntar PDF` si la lista está vacía y `+ Adjuntar otro PDF`
si ya hay alguno. Acepta selección múltiple de archivos.

### 5.10 Revista

Cabecera azul `REVISTA`, panel a 100% de ancho. Tres estados:

- **Sin vincular** — "No vinculada. La IA puede buscar revistas de la época que mencionen el
  juego y sugerirlas para descargar y guardar." + botón `Buscar con IA`.
- **Vinculada** — `[R] Nombre de la revista` + enlace `Desvincular`.
- **Rota** — `~ "Nombre" — vínculo roto: no está en el repositorio (faltante, no error)` en
  ámbar + botón `Buscar otra`.

### 5.11 Modal de sugerencias (620px)

Título `Sugerencias — <Campo>`. Bajada: "Elegí una opción. Lo que ya tenés cargado cuenta como
candidato — quedárselo es el default."

Cuatro fases:

1. **Buscando** — spinner + "Buscando en fuentes externas…".
2. **Resultados** — grilla `minmax(155px, 1fr)`. Si el campo ya tiene contenido, la primera
   tarjeta es `Tu archivo actual` (fondo verde pálido) y elegirla simplemente cierra el modal.
   Cada tarjeta: preview negra, nombre en 12.5px 700 y la fuente en 11px gris.
3. **Sin resultados** — "SIN RESULTADOS" + "Pasa seguido con juegos oscuros. Podés reintentar,
   ajustar la búsqueda o cargar a mano." + botones `Reintentar` (primary) y `Cargar a mano`.
4. **Error** — "ERROR DE LA FUENTE EXTERNA" + "Problema temporal y ajeno a tu juego. Reintentá
   en vez de abandonar." + botón `Reintentar`.

Si el campo estaba en `manual`, al elegir un candidato aparece un recuadro negro de confirmación:
"Este campo fue cargado a mano. ¿Reemplazarlo por la sugerencia elegida?" con
`Sí, reemplazar` (rojo) y `Cancelar`.

### 5.12 Modal de búsqueda de revista (460px)

Título `Buscar revista con IA`.

- **Buscando** — spinner + "La IA está buscando revistas de la época que mencionen este juego…".
- **Resultados** — "Encontradas por IA — pueden mencionar el juego en reseñas, tapas o
  publicidades. Elegí cuáles descargar y guardar en el repositorio." Una fila por candidata con
  `[R] Nombre`, el motivo en 10.5px gris (ej: "Menciona el juego en la reseña de tapa") y un
  botón `Descargar y guardar`.
- **Sin resultados** — "La IA no encontró revistas que mencionen este juego."

---

## 6. Exportar — `/exportar`

Columna de máx. 620px. **Título:** `Exportar a la librería`.
**Bajada:** "Por el peso de los archivos, el export se hace de a un juego por vez. COINDOOR arma
su estructura de archivos; ATTRACT la verifica y da el veredicto final."

**Resumen** en un panel blanco, tres cifras en una fila: `N listos` (verde), `N incompletos (no
exportables)` (ámbar), `N con errores (no exportables)` (rojo).

**Lista de exportables** — "Elegí un juego listo para exportar:", un buscador por nombre (máx.
300px) y una fila por juego listo: título en 13px 700 a la izquierda, botón `Exportar` a la
derecha. Paginada igual que la lista de juegos (50 por página), porque puede haber muchas.

Vacíos: "Ningún juego listo coincide con la búsqueda." / "No hay juegos listos para exportar
todavía."

**Ejecución** — reemplaza la lista mientras corre:

1. Spinner + `Armando estructura de archivos de "<Título>"…`
2. Spinner + `ATTRACT verificando "<Título>"…`
3. Resultado: cabecera azul `RESULTADO DE LA VERIFICACIÓN` y una tarjeta con el título y la
   insignia del veredicto (`Verificado` en verde o `Rechazado por ATTRACT` en rojo). Si fue
   rechazado, el detalle en 11.5px gris (ej: `Pac-Man/marquesina.png — nombre de archivo con
   mayúscula inválida (contrato es case-sensitive).`).
   Al pie: botón `Volver a la lista` y la nota "Sin ediciones nuevas, correrlo de nuevo no
   cambia el resultado."
