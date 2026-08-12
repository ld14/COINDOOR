# spec/ — Spec Driven Development

Primero se escribe la spec, luego el plan, luego las tareas, y **solo entonces**
se toca el código.

## Estructura

```
spec/
├── constitution/            ← reglas estables (cambian poco)
│   ├── mission.md           ← qué construimos y para quién
│   ├── tech-stack.md        ← tecnologías, convenciones y límites duros
│   ├── roadmap.md           ← orden y estado de las features
│   ├── frontend-architecture.md   ← (si hay frontend) capas, estado, routing
│   └── design-system.md           ← (si hay frontend) tokens y componentes
├── decisions/               ← ADRs: decisiones con alternativas descartadas
│   ├── README.md
│   └── NNNN-titulo.md
└── features/                ← una carpeta por feature
    └── NNN-nombre-feature/
        ├── spec.md          ← qué hace + criterios de aceptación
        ├── plan.md          ← cómo se implementa
        └── tasks.md         ← checklist accionable
```

## Flujo para una feature nueva

1. `/new-feature <nombre>` — crea `features/NNN-nombre/` con el siguiente número.
2. Escribir `spec.md`: qué hace, por qué, criterios de aceptación medibles.
3. Escribir `plan.md`: enfoque técnico, respetando `constitution/tech-stack.md`.
4. Desglosar en `tasks.md` y marcar el progreso.
5. Implementar y validar contra los criterios de aceptación.
6. Mover la feature a "Hecho" en `constitution/roadmap.md`.

> **La constitución manda.** Si una feature choca con `mission.md` o
> `tech-stack.md`, se replantea la feature, no la constitución.

## Constitución vs. decisiones: dónde va cada cosa

| Situación | Dónde |
|---|---|
| "Aquí se hace así" — sin debate previo | `constitution/` |
| Elegiste entre alternativas reales | `decisions/` (ADR) |
| Descartaste una tecnología | ADR + una línea en §Límites duros |
| Cambiaste de opinión sobre algo ya decidido | ADR nuevo que supersede al viejo |
| Detalle de implementación de una feature | `plan.md` de esa feature |

**Regla:** `plan.md` §Decisiones lista lo que se decidió; si una de esas
decisiones tuvo alternativas con peso, se extrae a un ADR y el plan la enlaza.
Así el plan describe el estado actual y no se convierte en un historial.

## Tamaño

Cada archivo debe caber en una pantalla o dos. Si `spec.md` pasa de ~60 líneas,
probablemente sean dos features. Un documento largo que nadie lee es contexto
desperdiciado en cada sesión.
