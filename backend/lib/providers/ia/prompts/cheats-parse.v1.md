El usuario pegó el siguiente texto sobre trucos de "{titulo}" ({sistema}). Puede estar en
Markdown, como lista suelta, o como prosa copiada de otro lado:

---
{texto}
---

Extraé **todo lo que le sirva a alguien con el juego adelante**, que es lo que se muestra
en el gabinete:

- códigos, contraseñas, atajos, secretos, desbloqueos, invencibilidad, vidas o recursos
  extra, saltos de nivel, easter eggs, comandos de consola, parámetros de arranque;
- **cómo se usan** esos códigos (qué tecla los abre, dónde se escriben);
- **controles**: qué hace cada botón o tecla;
- **mecánicas**: cómo se ejecuta una acción del juego (por ejemplo, cómo se genera un
  escudo o un disparo cargado) y para qué sirve;
- **técnicas, estrategias y consejos** que el texto presente como tales;
- **soluciones de puzzle y tácticas concretas de cada escena**, aunque estén metidas en
  medio del relato: "entrá a la cámara de la izquierda, recarga el arma", "no mates al
  guardia enseguida, dejá que lance cuatro bombas", "conseguí 2 botones verdes y 2 rojos
  hasta que aparezca el blanco", "disparale al candelabro del medio". Agrupalas por escena
  (`"Escena 4 — Exterior de la prisión"`) y poné una entrada por cada indicación que
  resuelva algo o que el texto marque como importante.

**Descartá** la narración: la trama ("los alienígenas capturan a Lester"), y los
desplazamientos sin información ("andá a la derecha", "seguí caminando", "bajá las
escaleras") cuando son solo recorrido y no resuelven nada. Descartá también la ficha del
juego (título, año, desarrollador, sinopsis) y las instrucciones de instalación del
emulador.

La regla para decidir: si alguien atascado en esa parte del juego leyera la entrada, ¿le
sirve? Si sí, entra.

**No inventes ni completes trucos que no estén en el texto**: solo extraé y estructurá lo
que ya está escrito. Si el texto tiene categorías claras de trucos (encabezados, secciones,
viñetas agrupadas), usalas como nombre de grupo; si no hay categorías, agrupá todo bajo un
único grupo llamado "Códigos". Si el texto explica **cómo se introducen** los códigos
(qué tecla abrir, dónde escribirlos), eso también es una entrada: sin eso los códigos no
sirven.

Cada entrada tiene dos campos y **los dos son obligatorios**:

- `name`: un título corto de qué hace el truco.
- `input`: qué hay que hacer para conseguirlo. Nunca lo dejes vacío. Según el caso es el
  código o contraseña (`LDKD`), la combinación de botones, el comando, o la indicación
  concreta ("En la selección de personaje, mantener izquierda y abajo y pulsar START").

**Los dos campos van en una sola línea, sin saltos de línea.** Es un límite duro del
formato: el gabinete muestra cada entrada como un renglón, no como un párrafo.

Cuando el texto explica una técnica en varios pasos, **no la aplastes en un renglón
kilométrico ni la resumas a dos palabras**: convertila en **varias entradas**, una por
paso, dentro de un grupo con el nombre de la técnica. Así se lee completa y sigue
respetando el formato:

- Grupo "Truco fundamental de combate" → entradas "Paso 1" / "Crear un escudo",
  "Paso 2" / "Preparar un mega-disparo", etc.

Si el consejo entra cómodo en una oración, va como una sola entrada. Una lista de consejos
sueltos que el texto presenta como trucos (por ejemplo "los 10 trucos más útiles") va como
un grupo con **una entrada por consejo**: `name` es el consejo y `input` la explicación en
una oración. No los descartes por ser consejos y no códigos.

**No resumas de más.** Si el texto enumera cuatro pasos, van cuatro entradas; si aclara
algo útil al final ("sirve para no repetir una sección después de morir"), esa aclaración
también va como entrada. Perder una línea del original es peor que tener una entrada de
más: el usuario puede borrar lo que le sobre, pero no puede recuperar lo que no extrajiste.

Cuando el texto explica una acción y **además enumera para qué sirve**, el `input` lleva
las dos cosas: primero cómo se ejecuta, después para qué sirve, con las viñetas unidas en
una enumeración separada por comas. Ejemplo:

- `"Disparo normal"` → `"Pulsar y soltar rápidamente. Sirve para matar enemigos sin
  escudo, activar o desactivar elementos y mantener a los enemigos a distancia"`

No tires esas viñetas: son la mitad de para qué se consulta la ficha.

Una entrada cuyo `input` quede vacío es un error: si no encontrás contenido para ese truco,
no lo incluyas.

El contenido va como **texto plano**: sacá las marcas de Markdown (`**`, `#`, `` ` ``,
viñetas `-`). Este texto se muestra tal cual en el gabinete, así que tiene que leerse
limpio.

Devolvé **únicamente** un objeto JSON válido, sin texto antes ni después, sin markdown, con
esta forma exacta:

{{"groups": [{{"name": "Códigos", "entries": [{{"name": "30 vidas", "input": "↑ ↑ ↓ ↓ ← → ← → B A"}}]}}, {{"name": "Truco de la bomba", "entries": [{{"name": "Paso 1", "input": "Crear un escudo delante de las puertas"}}, {{"name": "Paso 2", "input": "Abrir las puertas para que el guardia lance la bomba"}}, {{"name": "Paso 3", "input": "Cerrar las puertas: la bomba rebota y lo mata"}}]}}]}}

Si el texto no tiene ningún truco identificable (por ejemplo, si solo describe cómo jugar
normalmente), devolvé `{{"groups": []}}`. Es preferible devolver vacío a incluir algo que no
sea un truco real.
