Listá trucos y códigos conocidos de "{titulo}" ({sistema}, {anio}), agrupados por
categoría (por ejemplo "Códigos", "Vidas extra", "Niveles secretos"). Devolvé
**únicamente** un objeto JSON válido, sin texto antes ni después, sin markdown, con esta
forma exacta:

{{"groups": [{{"name": "Códigos", "entries": [{{"name": "Vidas infinitas", "input": "↑ ↑ ↓ ↓ ← → ← → B A"}}]}}]}}

- `groups`: lista de grupos. Cada grupo tiene `name` (texto) y `entries` (lista).
- Cada entrada de `entries` tiene `name` (qué hace) e `input` (la secuencia o el código,
  como texto).

Si no conocés trucos reales para este juego, devolvé `{{"groups": []}}` en vez de inventar
uno.
