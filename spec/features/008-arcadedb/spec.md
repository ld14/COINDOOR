# 008 · ArcadeDB

**Estado:** implementada

## Qué hace

**Recibe** un juego arcade recién creado, con su `romRef` apuntando a un archivo cuyo nombre
es un romset de MAME. **Consulta** ArcadeDB por ese romset y **escribe** de una vez identidad,
carátula, póster, marquesina, logo, captura, video, sinopsis, trucos, manual y datos de
gabinete. Solo toca los campos que están vacíos.

**Alimenta** además los botones "Sugerir" que ya existen: ArcadeDB pasa a ser el primer
proveedor de esos campos, por delante de la IA. Y el modal muestra el contenido actual del
campo junto a las opciones nuevas, en vez del cartel muerto de hoy.

**No cubre** los sistemas que no son arcade: ArcadeDB solo indexa MAME. Para el resto, la
tabla de proveedores queda como está.

## Por qué

[`ADR-0013`](../../decisions/0013-sin-scraping-ni-catalogo-pago.md) dejó carátula, póster,
marquesina, logo, captura y manual **sin ningún proveedor**: se cargan a mano, uno por uno.
Sinopsis y trucos los produce una IA que inventa de forma convincente. Dar de alta un juego
arcade es, hoy, trabajo manual largo, y el botón "Sugerir" —el diferencial del producto—
ofrece poco.

Ese mismo ADR dejó escrita la señal de reapertura: *"una fuente de imágenes/manuales sin
scraping y con términos claros sería candidata a una fila nueva en la tabla — decisión
explícita, no un default"*. ArcadeDB la cumple: API JSON documentada, sin credencial, sin
cuota, con términos publicados. Ver [`ADR-0014`](../../decisions/0014-arcadedb-fuente-arcade.md).

## Criterios de aceptación

- [x] Dado un juego en un sistema arcade con `romRef` `/roms/goldnaxe.zip` y la ficha vacía, cuando termina la precarga, entonces identidad, 5 imágenes, video, sinopsis, trucos, manual y gabinete quedan escritos con `source: ArcadeDB`.
- [x] Dado un romset que ArcadeDB no conoce, entonces el job termina **`succeeded`** con `estado: "no-encontrado"`, ningún campo cambia, y la interfaz lo dice sin pantalla de error.
- [x] Dado un campo ya cargado a mano, cuando corre la precarga, entonces ese campo **no se pisa** y aparece en `omitidos`.
- [x] Dado un sistema que no es arcade, cuando se crea un juego, entonces la precarga no hace **ninguna** petición de red.
- [x] Dado un `romRef` vacío, entonces el job termina con `estado: "sin-romset"` sin salir a la red.
- [x] Dada una imagen servida en una URL sin extensión, cuando se guarda, entonces la extensión sale del `content-type` y el archivo en disco es `.png` si los bytes son PNG.
- [x] Dado un campo con candidatos de ArcadeDB, cuando se pide sugerencia de 15 campos del mismo juego, entonces se hacen **exactamente 2** peticiones de red.
- [x] Dado un romset desconocido, entonces el cortocircuito de proveedores **no** se activa: el siguiente juego vuelve a consultar ArcadeDB.
- [x] Dado un campo con contenido, cuando se abre el modal de sugerencias, entonces el primer tile muestra el contenido real —la imagen o el texto—, y clickearlo no aplica nada.
- [x] Dada la identidad escrita por ArcadeDB, entonces `identitySource` queda en `mame`, no en `manual`.
- [x] Dado un juego con datos de gabinete, cuando se exporta el bundle, entonces **ninguna** clave de gabinete aparece en `game.json` ni en `data.json`.

## Fuera de alcance

- **Los datos de gabinete no llegan a Pegasus.** `attract/instalar.py` escribe un conjunto fijo de campos, sin passthrough. Exportarlos exige cambiar ATTRACT, que es otro repo. Se guardan y se muestran dentro de COINDOOR; no viajan al bundle ([`ADR-0002`](../../decisions/0002-procedencia-interna.md)).
- **Sistemas que no son arcade** — ArcadeDB solo indexa MAME.
- **Ejecutar `mame -listxml` local** — es otra fuente de identidad, con otro coste; no entra acá.
- **Reseña** — ArcadeDB no la tiene (`rate` viene en 0). Sigue siendo IA.
- **Carga masiva** — un juego por vez, como todo el producto.
