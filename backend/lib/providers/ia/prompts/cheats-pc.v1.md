Investigá trucos, códigos, comandos, contraseñas, secretos y ventajas especiales para
"{titulo}", juego de PC/MS-DOS/Windows publicado en {anio}. Es un juego de computadora
(DOS o Windows de la época), no de una consola ni de arcade: no incluyas nada que
corresponda a un port, remake o relanzamiento de otra plataforma. Si la información que
encontrás es de otra versión (consola, arcade, remaster), omitila.

Buscá específicamente:

- Códigos de trucos y cómo escribirlos (durante el juego, en un menú, o tecleados como
  si fueran comandos).
- Comandos de consola de desarrollador y cómo habilitarla (parámetro de línea de
  comandos, tecla, o archivo de configuración).
- Contraseñas para acceder a niveles, capítulos o partidas guardadas.
- Atajos de teclado o combinaciones que activen funciones ocultas.
- Invencibilidad, vidas, dinero, munición o recursos ilimitados.
- Desbloqueo de personajes, niveles, campañas u objetos secretos.
- Easter eggs conocidos y relevantes.
- Formas de saltear niveles o partes muy difíciles.
- Parámetros de línea de comandos del ejecutable que habiliten un modo de depuración o
  desarrollador, si este juego tiene alguno documentado.
- Trainers o editores de partida externos reconocidos por la comunidad (no oficiales
  del juego): incluilos solo si son ampliamente conocidos, y dejalo explícito en el
  nombre de la entrada que son una herramienta externa y qué riesgo tienen (partidas
  corruptas, incompatibilidad con una versión de DOSBox, etc.).

Si el juego es multijugador o tiene un modo competitivo, no incluyas nada pensado para
dar ventaja ahí: solo trucos de un jugador. Escribí cada entrada para alguien que nunca
usó DOSBox ni jugó el original: explicá qué efecto tiene, en qué momento se usa y cómo
se aplica, no solo el código en sí.

Agrupá por categoría (por ejemplo "Códigos", "Comandos de consola", "Contraseñas",
"Parámetros de inicio", "Trainers externos", "Secretos"). Devolvé **únicamente** un
objeto JSON válido, sin texto antes ni después, sin markdown, con esta forma exacta:

{{"groups": [{{"name": "NOMBRE DEL GRUPO", "entries": [{{"name": "QUÉ HACE EL TRUCO", "input": "CÓMO SE ACTIVA"}}]}}]}}

Los textos en mayúsculas de arriba son marcadores de posición para mostrar la forma del
JSON: reemplazalos por datos reales de este juego. **No los copies, y no uses como
respuesta ningún código, comando o parámetro de ejemplo que aparezca en estas
instrucciones.**

- `groups`: lista de grupos. Cada grupo tiene `name` (texto) y `entries` (lista).
- Cada entrada de `entries` tiene `name` (qué hace) e `input` (el código, comando,
  contraseña o procedimiento, como texto).

Si no encontrás información confiable sobre este juego para PC/DOS/Windows, devolvé
`{{"groups": []}}`. No inventes códigos.
