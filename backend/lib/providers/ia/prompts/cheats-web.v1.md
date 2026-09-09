Abajo van fragmentos de páginas web sobre trucos de "{titulo}" ({sistema}, {anio}), tal como
los devolvió un buscador. Son resultados en crudo: pueden venir cortados a la mitad, mezclados
con menús y publicidad del sitio, o hablar de **otro juego** de nombre parecido o de **otra
plataforma**.

Tu trabajo es **extraer los trucos que estén en ese texto**. No aportes los que creas saber:
si no está en el texto, no existe para esta tarea.

---
{texto}
---

**Descartá sin dudar:**

- Todo lo que sea de otro juego, aunque el nombre se parezca.
- Todo lo que sea de otra versión o plataforma. {sistema} es obligatorio: un mismo juego tiene
  trucos distintos en arcade, consola y computadora, y mezclarlos los vuelve inservibles. Si el
  texto no deja claro a qué versión corresponde un truco, omitilo.
- Navegación del sitio, publicidad, comentarios de usuarios, enlaces de descarga.
- La ficha del juego (año, desarrollador, género, sinopsis) y cómo instalar el emulador.

**Extraé, cuando estén en el texto:**

- Códigos y contraseñas, **y cómo se introducen** (qué tecla los abre, dónde se escriben): sin
  eso el código no sirve.
- Comandos de consola de desarrollador y cómo se habilita la consola.
- Parámetros de línea de comandos del ejecutable.
- Invencibilidad, vidas, dinero, munición o recursos ilimitados.
- Desbloqueo de personajes, niveles, campañas u objetos secretos.
- Formas de saltear niveles o partes difíciles, y easter eggs.
- Controles: qué hace cada botón o tecla, si el texto lo explica.
- Técnicas, estrategias y consejos que el texto presente como tales.

**No inventes ni completes.** Si el texto menciona un truco pero no dice cómo se consigue, no lo
incluyas: una entrada sin `input` es un error. Es preferible devolver poco a devolver algo que no
esté en el texto.

**Escribí todo en castellano.** Las páginas casi siempre están en inglés y la ficha se lee en un
gabinete en castellano: los nombres de las entradas y las explicaciones van traducidos. Lo que
**no** se traduce nunca es lo que hay que teclear —códigos, contraseñas, comandos, parámetros y
nombres de teclas— porque el juego los espera tal cual: si el truco se activa con `Shift+56`, en
`input` va `Shift+56`, no "Mayúsculas+56".

Escribí cada entrada para alguien que nunca jugó el original: explicá qué efecto tiene y en qué
momento se usa, no solo el código.

Agrupá por categoría, usando los encabezados del propio texto como nombre de grupo cuando los
tenga. Cada entrada tiene dos campos y **los dos son obligatorios**:

- `name`: un título corto de qué hace el truco.
- `input`: qué hay que hacer para conseguirlo. Nunca vacío.

**Los dos campos van en una sola línea, sin saltos de línea.** Es un límite duro del formato: el
gabinete muestra cada entrada como un renglón, no como un párrafo. Si una técnica lleva varios
pasos, convertila en varias entradas dentro de un grupo con el nombre de la técnica, una entrada
por paso.

El contenido va como **texto plano**: sacá las marcas de Markdown (`**`, `#`, `` ` ``, viñetas).

Devolvé **únicamente** un objeto JSON válido, sin texto antes ni después, sin markdown, con esta
forma exacta:

{{"groups": [{{"name": "NOMBRE DEL GRUPO", "entries": [{{"name": "QUÉ HACE EL TRUCO", "input": "CÓMO SE ACTIVA"}}]}}]}}

Los textos en mayúsculas son marcadores de posición para mostrar la forma del JSON: reemplazalos
por lo que hayas encontrado en el texto. No los copies.

Si el texto no trae ningún truco de "{titulo}" para {sistema}, devolvé `{{"groups": []}}`.
