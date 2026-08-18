Listá trucos, códigos, configuraciones y secretos conocidos de "{titulo}" ({sistema},
{anio}). Incluí todo lo que sepas: códigos de botones, configuraciones de DIP switches,
ajustes del menú de servicio, trucos de gameplay, niveles secretos, personajes ocultos,
cualquier cosa que le dé ventaja al jugador. Si no estás seguro de un dato específico,
incluílo de todas formas indicando que es aproximado.

Agrupá por categoría (por ejemplo "Códigos", "DIP Switches", "Menú de Servicio",
"Secretos"). Devolvé **únicamente** un objeto JSON válido, sin texto antes ni después,
sin markdown, con esta forma exacta:

{{"groups": [{{"name": "Códigos", "entries": [{{"name": "30 vidas", "input": "↑ ↑ ↓ ↓ ← → ← → B A"}}]}}]}}

- `groups`: lista de grupos. Cada grupo tiene `name` (texto) y `entries` (lista).
- Cada entrada de `entries` tiene `name` (qué hace) e `input` (la secuencia, código o
  descripción, como texto).

Si realmente no encontrás ninguna información sobre este juego, devolvé
`{{"groups": []}}`.
