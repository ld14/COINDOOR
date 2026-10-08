# Prompt para Claude Code

Copiá la carpeta `coindoor-rediseno/` en el repo como `docs/rediseno/` y pegale esto a Claude Code, parado en la raíz del proyecto:

---

Vamos a implementar el rediseño visual y de usabilidad de COINDOOR (tema "Flyer 80s"). Toda la documentación está en `docs/rediseno/`:

- `PLAN.md`: fases, tareas y criterios de "listo". Seguilo en orden.
- `DESIGN_SPEC.md`: tokens, tipografía, primitivas, estados de campo y especificación de cada pantalla.
- `tokens/flyer-tokens.css`: tokens CSS listos, con alias de compatibilidad para las variables `--dos-*` actuales.
- `mockups/*.html` y `mockups/png/*.png`: maquetas de referencia por pantalla (estáticas, con imágenes de relleno).
- `BUGS.md`: bugs que aparecieron al recorrer la app. Se corrigen en las fases indicadas.

Cómo quiero que trabajes:

1. Arrancá por la **Fase 0**: leé los docs, mirá los mockups (podés abrir los PNG) y relevá el código que lista el plan. Escribí `docs/rediseno/PROGRESS.md` con lo relevado y las dos decisiones pendientes: **guardado automático o un solo guardar**, y **cómo distinguir "aceptado de ArcadeDB" de "manual"**. Mostrame las dos decisiones antes de seguir.
2. Trabajá en la rama `rediseno-flyer`, **una fase por vez**. Al cerrar cada fase:
   - `npx tsc --noEmit` y lint sin errores
   - la app levanta (`npm run dev`)
   - commit con el mensaje `rediseno: fase N – <resumen>`
   - actualizar PROGRESS.md
3. Antes de las fases 4 (ficha de juego) y 5 (nuevo juego) proponeme un sub-plan y esperá mi OK.
4. No cambies contratos de API ni el modelo de datos. Si algo de la spec necesita backend, dejá `TODO(backend)` en el código y en PROGRESS.md, y seguí.
5. Mantené los textos de la UI en castellano rioplatense (voseo), como están hoy.
6. Primero partí `FichaJuego.tsx` en componentes **sin cambiar la UI** (refactor puro, con su propio commit), y recién después aplicá el diseño nuevo.
7. Si la spec y el código se contradicen, preguntame antes de inventar.

Empezá por la Fase 0.
