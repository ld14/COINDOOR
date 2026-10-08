# Bugs detectados al recorrer la app (8/10/2026)

Se observaron en la UI con el servidor de desarrollo en `localhost:5173`. La causa está sin confirmar: verificar en el código antes de corregir.

| # | Dónde | Qué pasa | Esperado | Pista |
|---|---|---|---|---|
| 1 | Barra lateral (todas las páginas) | Dice "0 juegos cargados" con 29 fichas en `/juegos` | Cantidad real de fichas | `MenuBar.tsx`: de dónde sale el número (¿hook distinto o query sin datos?) |
| 2 | `/sistemas` | Cada sistema muestra "0 juegos" (arcade tiene 8, msdos 21) | Contador real | `System.gameCount` en `lib/api/systems.ts` y en el backend |
| 3 | Ficha → botón **Exportar** | Navega a `/exportar` sin id y muestra "Seleccioná un juego…" | Ir a `/exportar/:gameId` | `navigate(...)` del botón en `FichaJuego.tsx` |
| 4 | `/juegos/nuevo` → Identidad | Los labels son las claves `title`, `year`, `developer`, `publisher`, `genre`, `players`, `format` | Labels de `fielddefs.json` ("Título", "Año", …) | Usar `FIELDDEFS.identity[].label` |
| 5 | `/juegos/nuevo` → Instalados sin ficha | Aparecen `arkanoidu.zip` y `lethalen.zip`, que ya tienen ficha | Solo ROMs sin ficha | `useRomCandidates` / `lib/api/roms.ts`: comparación por `romRef` (¿ruta absoluta vs. relativa, o id distinto del nombre del archivo?) |
| 6 | `/exportar/:gameId` | Trucos figura con "2 B" sin trucos cargados (probablemente un `[]` serializado) | "vacío" y deshabilitado | Cálculo de tamaño en `ExportPage` / `lib/api/export.ts` |
| 7 | `/exportar/:gameId` | Todos los opcionales vienen destildados, incluso los que tienen datos (video, guía) | Tildados por defecto los que tienen datos | Estado inicial de la selección |
| 8 | Ficha `?precarga=<id>` | La URL pierde el parámetro tras cargar (puede ser intencional) | Confirmar el comportamiento | — |
