# 022 · Edición correcta en todas las fuentes — Tareas

## Antes de tocar código

- [x] Guardar las páginas reales: búsqueda y ficha de Launchbox de *Prince of Persia*; ficha,
      carátulas, una carátula y capturas de DOS en MobyGames (2026-10-29).
- [x] Verificar que las imágenes de `cdn.mobygames.com` bajan con HTTP común (200).
- [x] [`ADR-0026`](../../decisions/0026-ia-ultimo-recurso-en-sugerir-identidad.md) aceptado.

## Implementación

- [x] `coincidencia.py` y MobyGames usándola. Hecho cuando: los tests de la 020 pasan sin
      cambios.
- [x] Launchbox elige con la regla común. Hecho cuando: con la búsqueda guardada, "Prince of
      Persia" (1990) da el id 13853, no el 83696.
- [x] Launchbox completa el año que falta en la lista y decodifica todas las entidades. Hecho
      cuando: con la búsqueda guardada de *Civilization* (1991), se elige *Sid Meier's
      Civilization* (13599) bajando a lo sumo tres páginas.
- [x] `fetch_details` de Launchbox. Hecho cuando: de la ficha guardada saca Brøderbund Software,
      sus dos editores, "Platform, Action", 1 jugador y 1990.
- [x] Proveedor de Launchbox con identidad.
- [x] Imágenes de MobyGames: parser, cliente y proveedor. Hecho cuando: con las páginas
      guardadas, la primera carátula es la grande de 622×800 y hay capturas de 320×200.
- [x] Image Search con el año.
- [x] Cadenas nuevas en `registro.py`.
- [x] Respaldo de IA en el orquestador. Hecho cuando: sin candidato factual, aparece el de la
      IA marcado; con uno factual, la IA no se consulta; la identidad en bloque hace una sola
      consulta.
- [x] Precarga: Launchbox antes que la IA y carátula de MobyGames.
- [x] Tests sin red.

## Cierre

- [x] Probar en el sitio real con *Prince of Persia* y *Civilization*. Hecho el 2026-10-29
      (tabla en el plan, §Lo verificado), en "Sugerir" y en la precarga del alta:
      *Prince of Persia* toma la identidad de MobyGames y Launchbox y la carátula y las
      capturas de DOS de MobyGames primero; *Civilization*, que MobyGames no encuentra, toma
      la identidad de Launchbox sin IA. La primera prueba mostró que Launchbox no elegía
      *Sid Meier's Civilization* (sin año en la lista, apóstrofo como `&#x27;`); se arregló
      antes de cerrar.
- [x] `ruff check .`, `mypy backend/lib` y `pytest` en verde. En WSL el 2026-10-29: sin
      errores de `ruff` ni `mypy` y 494 tests, también sin red.
- [x] `tech-stack.md` (la regla de la IA en identidad) y el roadmap al día.
