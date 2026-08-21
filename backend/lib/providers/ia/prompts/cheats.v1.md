Listá trucos, códigos, configuraciones y secretos conocidos de "{titulo}" solo para la
versión de {sistema} ({anio}). La plataforma es parte obligatoria del contexto: no mezcles
trucos de ports, remakes, relanzamientos ni versiones de otros sistemas. Un mismo juego puede
tener trucos distintos en MAME/arcade, NES/Famicom, Commodore 64, Amiga, ZX Spectrum,
Amstrad CPC, Atari ST, MSX u otras plataformas.

Incluí solo trucos que correspondan a {sistema}: códigos de botones, configuraciones de DIP
switches, ajustes del menú de servicio, trucos de gameplay, niveles secretos, personajes
ocultos o cualquier cosa que le dé ventaja al jugador en esa versión. Escribí cada truco para
usuarios principiantes: explicá qué significa, dónde se usa y cómo aplicarlo. Si mencionás DIP
switches, explicá que son interruptores/configuración de la máquina o emulador; si mencionás
menú de servicio, explicá cómo se accede de forma general y qué se cambia ahí. Evitá entradas
crípticas como "Switches 1-2: 00 = 3 vidas" sin contexto: agregá una explicación legible del
efecto y del lugar donde se configura. Si un dato parece ser de otra plataforma, omitilo. Si no
podés asociar el truco con {sistema}, omitilo.

Agrupá por categoría (por ejemplo "Códigos", "DIP Switches", "Menú de Servicio",
"Secretos"). Devolvé **únicamente** un objeto JSON válido, sin texto antes ni después,
sin markdown, con esta forma exacta:

{{"groups": [{{"name": "Códigos", "entries": [{{"name": "30 vidas", "input": "↑ ↑ ↓ ↓ ← → ← → B A"}}]}}]}}

- `groups`: lista de grupos. Cada grupo tiene `name` (texto) y `entries` (lista).
- Cada entrada de `entries` tiene `name` (qué hace) e `input` (la secuencia, código o
  descripción, como texto).

Si realmente no encontrás ninguna información sobre este juego, devolvé
`{{"groups": []}}`.
