# 023 · myabandonware como primera fuente de PC/DOS — Tareas

## Antes de tocar código

- [x] Verificar que myabandonware responde a HTTP común, qué permite su `robots.txt` y qué trae
      su `sitemap` (2026-10-30).
- [x] Guardar páginas reales: *Prince of Persia* (DOS y J2ME), *Sid Meier's Civilization*,
      *Civilization* (N-Gage), *Advanced Civilization*, *Dawn of Civilization*, las dos
      *Teenage Mutant Ninja Turtles* de DOS, *Guy Spy and the Crystals of Armageddon* y *Doom*
      (Saturn), más un `sitemap` recortado a esos títulos.
- [x] [`ADR-0027`](../../decisions/0027-myabandonware-primera-fuente-de-pc-dos.md) aceptado.

## Implementación

- [x] `http.py`: `get_text` y `get_bytes`. Hecho cuando: los tests de `get_json` pasan sin
      cambios.
- [x] Catálogo de plataformas con `myabandonware`.
- [x] Parser. Hecho cuando: de la página guardada de *Prince of Persia* sale todo lo del primer
      criterio de la spec, y de *Sid Meier's Civilization*, MPS Labs y MicroProse.
- [x] Cliente: índice, candidatas y elección. Hecho cuando: "Prince of Persia" (1990) y
      "Civilization" (1991) eligen la página de DOS, "Doom" no elige ninguna y las dos *TMNT*
      se desempatan por año.
- [x] Proveedor de myabandonware.
- [x] Cadenas nuevas y `ULTIMO_RECURSO` en `registro.py`; enlace a la ficha de MobyGames.
- [x] Orquestador: último recurso por posición y la IA antes que MobyGames.
- [x] Precarga con el orden nuevo.
- [x] Modal de "Sugerir": orden de las fuentes y "Consultar". Al consultar una fuente puntual,
      su traza queda en su lugar (`useSuggestionsJob`).
- [x] Tests sin red.

## Cierre

- [x] Probar en el sitio real con *Prince of Persia* y *Civilization*, en "Sugerir" y en la
      precarga. Hecho el 2026-10-30 (tabla en el plan, §Lo verificado): la identidad sale de
      myabandonware y Launchbox, MobyGames solo da el formato y la IA no hizo falta.
- [x] `ruff check .`, `mypy backend/lib`, `pytest` y los tests del frontend en verde. En WSL el
      2026-10-30: sin errores de `ruff` ni `mypy` y 533 tests, también sin red. Frontend: `tsc`
      y `eslint` sin errores; Vitest pasa salvo tres tests que ya fallaban antes (dos piden
      Python en el PATH de Windows y uno valida sistemas), ajenos a esta feature.
- [x] `tech-stack.md` (fuentes y regla de identidad), el plan de la 021 y el roadmap al día.
