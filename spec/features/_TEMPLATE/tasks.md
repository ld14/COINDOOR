# NNN · <Nombre> — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas;
marca `[x]` al completarlas._

<!-- GUÍA: se escribe DESPUÉS de plan.md. Cada tarea debe ser completable en una
sesión y verificable sin ambigüedad. Si no sabes decir cuándo está hecha, pártela. -->

## Implementación

- [ ] Implementar `<ruta>` — <qué>. Hecho cuando: <criterio verificable>.
- [ ] Implementar `<ruta>` — <qué>. Hecho cuando: <criterio>. Depende de: <tarea>.
- [ ] Definir `<ruta/models>` — <estructuras>. Hecho cuando: <criterio>.
- [ ] Cablear el flujo completo (`<entrypoint>`): <entrada> → <salida>.

## Tests

- [ ] Caso feliz: <escenario>.
- [ ] Caso límite: <entrada vacía / ausente>.
- [ ] Caso de fallo: <entrada corrupta> → error explícito, no salida parcial.
- [ ] <Invariante del dominio que debe cumplirse siempre>.

## Cierre

- [ ] Validar contra todos los criterios de aceptación de `spec.md`.
- [ ] Lint y tipos limpios.
- [ ] Actualizar `../../constitution/tech-stack.md` si cambió el stack,
      el modelo de datos o los límites duros.
- [ ] Crear ADR en `../../decisions/` si alguna decisión tuvo alternativas
      descartadas o revirtió una previa.
- [ ] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.
- [ ] Actualizar `docs/` si cambió la superficie pública.
