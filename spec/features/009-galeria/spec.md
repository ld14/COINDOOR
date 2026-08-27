# 009 · Galería de imágenes

**Estado:** aprobada

## Qué hace

Agrega a cada juego un banco de imágenes independiente de los cinco campos del
contrato. Trae de ArcadeDB todos los tipos que publica para el romset —y para su
romset padre si el juego es un clon—, los ofrece con selección múltiple, descarga los
elegidos a `media/<sistema>/<juego>/_gallery/` y los guarda en la ficha.

Desde cada imagen guardada se puede asignar esa imagen a cualquiera de los cinco
campos del contrato (carátula, marquesina, póster, logo, captura).

La galería viaja en el bundle como opcional de export: los archivos van a
`media/_gallery/` y se declaran en `data.json → gallery[]` (ver
[ADR-0016](../../decisions/0016-galeria-en-subcarpeta-gallery.md)).

**No** es un asset del contrato ni un campo de `fielddefs.json → images[]`: no cuenta
para la completitud y su ausencia nunca bloquea un export.

## Por qué

ArcadeDB publica entre 8 y 16 tipos de imagen por romset y la precarga usa como mucho
cinco. El resto —`cpanel`, `pcb`, `cabinet`, `decal`, `boss`, `howto`— se descarta en
cada corrida.

Además, cuando la precarga elige mal o el romset no publica el tipo que hace falta, no
hay forma de corregirlo dentro de COINDOOR: hay que buscar la imagen por fuera y
subirla a mano. Se detectó con `ffightub` (Final Fight), que no publica `flyer` ni
`marquee` y dejó carátula y marquesina vacías, mientras su romset padre `ffight` sí
los tiene.

## Criterios de aceptación

- [ ] Dado un juego de un sistema arcade con romset conocido, cuando se piden los
      candidatos, entonces se listan todos los tipos que ArcadeDB publica, cada uno con
      su etiqueta en español.
- [ ] Dado un juego cuyo romset es un clon, cuando se piden los candidatos, entonces
      se incluyen también los tipos que sólo publica el romset padre, marcados como
      tales, y la identidad del padre no toca la del juego.
- [ ] Dado un conjunto de tipos seleccionados, cuando se guardan, entonces se
      descargan a `_gallery/` numerados `g001`…`gNNN`, con la extensión derivada del
      contenido y no del nombre de la URL.
- [ ] Dada una imagen de la galería, cuando se la asigna a un campo del contrato,
      entonces ese campo queda apuntando a esa imagen y la entrada de galería sigue
      existiendo.
- [ ] Dada una imagen de la galería, cuando se la borra, entonces desaparecen la
      entrada y el archivo en disco.
- [ ] Dado un export con la galería tildada, cuando se arma el bundle, entonces los
      archivos aparecen en `media/_gallery/` y `data.json → gallery[]` los lista con
      **nombres sueltos, sin `/` ni `\`**.
- [ ] Dado un export sin la galería tildada, cuando se arma el bundle, entonces no
      aparece ni la carpeta ni la clave.
- [ ] Dado un juego sin galería, cuando se calcula la completitud, entonces el estado
      no cambia: la galería nunca es obligatoria.
- [ ] Dado un romset que ArcadeDB no conoce, cuando se piden los candidatos, entonces
      se devuelve una lista vacía y no un error.

## Fuera de alcance

- Que ATTRACT instale o muestre la galería — es una etapa posterior en `../attract`,
  fuera de este repo. Hasta entonces `attract doctor` la ignora sin fallar.
- Rasterizar, recortar o normalizar las imágenes: se guardan tal como las entrega
  ArcadeDB, igual que hace la precarga con los cinco campos.
- Traer imágenes de galería de otras fuentes (búsqueda de imágenes, IA). Sólo
  ArcadeDB — eso es la feature [002](../002-sugerencias-multiproveedor/spec.md).
- Sistemas sin catálogo de romsets: la galería sólo aplica donde aplica ArcadeDB, con
  el mismo gate de `soporta_arcadedb()`.
