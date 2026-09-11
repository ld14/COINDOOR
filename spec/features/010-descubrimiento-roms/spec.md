# 010 · Descubrimiento de ROMs sin ficha

**Estado:** aprobada

## Qué hace

Lee lo que hay en `games/juegos/<sistema>/` y ofrece, en la pantalla de alta, la lista
de juegos instalados que todavía no tienen ficha. Cada entrada suelta —un archivo de
ROM o una carpeta sin `game.json`— es un **candidato**.

Al elegir un candidato, el formulario de alta queda precargado: sistema, origen del
archivo (`path`), ruta de la ROM, formato, tratamiento y un título propuesto derivado
del nombre en disco. Nada se escribe hasta que el usuario aprieta `Crear ficha`; ahí
sigue el flujo que ya existe, incluida la precarga externa (ArcadeDB o Launchbox+IA)
cuando el sistema la soporta.

El descubrimiento **no** inventa identidad: el título propuesto es una lectura del
nombre del archivo, no un dato de catálogo. Quien completa identidad sigue siendo la
precarga o el usuario.

## Por qué

Hoy dar de alta un juego ya instalado obliga a tipear a mano la ruta absoluta de la
ROM y el título. Es la única parte del alta donde un error de tipeo produce un
`romRef` que apunta a nada: la ficha se crea igual, y el problema recién aparece al
exportar, cuando el bundle sale sin `juego/` y ATTRACT lo rechaza (el mismo síntoma
que documenta `store/juegos.py::_mover_a_sistema`). La ficha existente
`ms-dos/out-of-this-world` tiene `romRef: "/"`, prueba de que la ruta escrita a mano
no se valida contra el disco.

Además, con la colección creciendo, no hay forma dentro de COINDOOR de responder
"¿qué instalé y todavía no documenté?".

## Criterios de aceptación

- [ ] Dado `games/juegos/mame/sf2.zip` sin ficha, cuando se piden los candidatos,
      entonces aparece uno con `systemId: "mame"`, la ruta absoluta del archivo y el
      título propuesto `Sf2`.
- [ ] Dada una carpeta `games/juegos/nes/Super Mario Bros/` sin `game.json`, cuando se
      piden los candidatos, entonces aparece como candidato de tipo carpeta.
- [ ] Dada una carpeta con `game.json` dentro, cuando se piden los candidatos,
      entonces **no** aparece: ya tiene metadata.
- [ ] Dada una ficha cuyo `romRef` apunta a una entrada de `games/juegos/<sistema>/`,
      cuando se piden los candidatos, entonces esa entrada **no** aparece, aunque el
      título le haya limpiado el nombre: `Indiana Jones … (1992)` en disco da la ficha
      `indiana-jones-and-the-fate-of-atlantis`, sin el año.
- [ ] Dada una ficha guardada corriendo el backend en WSL (`romRef` = `/mnt/d/…`),
      cuando el escaneo corre desde Windows y lee `D:\…`, entonces la entrada tampoco
      reaparece.
- [ ] Dado un alta desde una carpeta descubierta, cuando se guarda, entonces el
      `game.json` queda **dentro de esa carpeta** y no se crea una hermana
      ([ADR-0017](../../decisions/0017-ficha-en-la-carpeta-del-juego.md)).
- [ ] Dada esa carpeta ya documentada, cuando se la renombra, entonces el juego
      **no** vuelve a aparecer como candidato: la ficha viajó con ella.
- [ ] Dado un alta desde una ROM suelta en la raíz del sistema, cuando se guarda,
      entonces el archivo se mueve a la carpeta de su ficha, `romRef` apunta al
      destino y la entrada deja de ofrecerse.
- [ ] Dado un juego cuya carpeta contiene el `game.json`, cuando se exporta el
      bundle, entonces ese archivo interno **no** viaja dentro del `.zip` del juego.
- [ ] Dado el mismo nombre de ROM en dos sistemas y una ficha para uno solo, cuando se
      piden los candidatos, entonces el del otro sistema sigue apareciendo: la
      ocupación es por sistema.
- [ ] Dado `games/juegos/` vacío o inexistente, cuando se piden los candidatos,
      entonces se devuelve una lista vacía y no un error.
- [ ] Dados archivos ocultos, temporales (`.tmp`, `.part`) o `game.json` sueltos,
      cuando se piden los candidatos, entonces se omiten.
- [ ] Dado un candidato de tipo archivo, cuando se lo selecciona, entonces el
      formulario queda con `romSource: "path"`, `romRef` = la ruta absoluta,
      `file_format` = la extensión sin punto y `tratamiento: "copiar"`.
- [ ] Dado un candidato de tipo carpeta, cuando se lo selecciona, entonces
      `file_format` queda vacío y `tratamiento: "descomprimir"`.
- [ ] Dado un candidato de un sistema distinto al seleccionado, cuando se lo elige,
      entonces el selector de sistema pasa a ese sistema.
- [ ] Dado un juego recién creado desde un candidato, cuando se vuelve al alta,
      entonces ese candidato ya no está en la lista.

## Fuera de alcance

- Escanear el `launchCmd` del sistema (p. ej. `D:\Juegos\PC\eXoDOS`) — es un árbol de
  LaunchBox con 171 plataformas y su propio catálogo; leerlo es otra feature.
- Alta masiva. Sigue siendo un juego por vez (`tech-stack.md` §Límites duros).
- Mover, copiar o renombrar archivos en disco. El descubrimiento solo lee.
- Identificar el juego por hash, CRC o consulta a catálogo. El título propuesto sale
  del nombre del archivo; corregirlo es trabajo de la precarga.
