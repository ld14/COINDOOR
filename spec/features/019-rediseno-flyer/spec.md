# 019 · Rediseño "Flyer 80s"

**Estado:** aprobada (Fase 0 hecha; falta el sub-plan de las fases 4 y 5)

## Qué hace

Reemplaza el look & feel de toda la app por el tema Flyer y reorganiza la usabilidad de
las cinco pantallas, según el paquete [`docs/coindoor-rediseno/`](../../../docs/coindoor-rediseno/README.md)
(`DESIGN_SPEC.md`, `PLAN.md`, `BUGS.md`, `tokens/`, `mockups/`). Ese paquete manda en lo
visual y en el comportamiento de cada pantalla; los deltas D1–D5 mandan donde discrepan
([`ADR-0023`](../../decisions/0023-estetica-flyer-reemplaza-dos.md)).

Incluye: tokens y fuentes locales, shell (topbar, rail, statusbar), primitivas nuevas y
actualizadas, Juegos, Sistemas, Configuración, ficha de juego (partida en secciones, con
autosave y revisión de sugerencias), alta en cuatro pasos, Exportar con cola, y la
corrección de los ocho bugs de `BUGS.md`.

**Regla transversal: no se pierde ninguna funcionalidad existente.** Todo lo que hoy se
puede hacer (sugerir, precargar, subir media, descargar de YouTube, manuales, galería,
trucos, reseña, exportar, instalar en ATTRACT, configurar) sigue disponible y compatible
con el diseño nuevo.

Fuera de alcance: paleta de comandos `Ctrl+K` (solo se reserva el atajo), endpoints de
backend nuevos para estado de servicios y preferencias (`TODO(backend)`), y las opciones
Refinado y Cabina de `tokens.json`.

## Por qué

El recorrido de la app con las cinco pantallas funcionando mostró problemas de
legibilidad (todo en una fuente monoespaciada), de jerarquía (la ficha es una pared de
campos sin guía de qué falta para exportar) y de fricción (botones "Guardar" por sección).
Además hay bugs visibles (contadores en 0, Exportar sin id, labels en inglés).

## Criterios de aceptación

- [ ] Todas las pantallas cargan con la paleta y las fuentes nuevas, sin pedir nada por red
      (fuentes empaquetadas con `@fontsource`).
- [ ] El rail muestra contadores reales; ya no dice "0 juegos cargados" con fichas
      existentes (bug 1) y `/sistemas` muestra los juegos reales por sistema (bug 2).
- [ ] `/juegos/lethal-enforcers` se ve y se comporta como `02-ficha-en-carga` y
      `/juegos/arkanoidu` como `01-ficha-completa`.
- [ ] No queda ningún botón "Guardar X" por sección; la ficha guarda sola (~800 ms y al
      perder foco) y la topbar muestra Guardando / Guardado / Error con Reintentar.
- [ ] Escribir en un campo no se pisa por una recarga de datos mientras se edita.
- [ ] Aceptar una sugerencia conserva su `source` (el chip muestra "ArcadeDB"); editar a
      mano deja `source: 'manual'`. El `source` no viaja al export (ADR-0002).
- [ ] Exportar de la ficha navega a `/exportar/:gameId` y está deshabilitado con el motivo
      mientras falten obligatorios; `/exportar` sin id es la cola (bug 3).
- [ ] En Exportar, lo opcional con datos viene tildado y lo vacío deshabilitado con el
      motivo; Trucos vacío no figura como "2 B" (bugs 6 y 7).
- [ ] En `/juegos/nuevo` los labels salen de `fielddefs.json` y solo se listan ROMs sin
      ficha (bugs 4 y 5).
- [ ] Las categorías de reseña siguen siendo 0–100 (D1); las revistas solo se vinculan (D3).
- [ ] Ningún componente usa `--dos-*` al final; `/_catalogo` muestra todas las primitivas.
- [ ] Teclado completo, foco visible, `aria-live` en progreso, sin roturas a 900 px.
- [ ] Los tests existentes siguen pasando; se suman los de `useFichaProgress` y del mapeo
      de origen.

## Fuera de alcance

- Cambiar contratos de API o el modelo de datos, salvo conservar `source` al aceptar
  (cambio chico en `store/juegos.py`, sin campos nuevos).
- Descargar revistas o exportar su referencia — ver D3 en
  [`frontend-architecture.md`](../../constitution/frontend-architecture.md).
