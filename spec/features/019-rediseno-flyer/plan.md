# 019 · Rediseño "Flyer 80s" — Plan

_Cómo se implementa lo descrito en `spec.md`. Respeta la `constitution/` actualizada por
[`ADR-0023`](../../decisions/0023-estetica-flyer-reemplaza-dos.md)._

## Enfoque

El detalle de fases, tokens, primitivas y pantallas ya está escrito en
[`docs/coindoor-rediseno/PLAN.md`](../../../docs/coindoor-rediseno/PLAN.md) y
[`DESIGN_SPEC.md`](../../../docs/coindoor-rediseno/DESIGN_SPEC.md); este plan **no los
copia**, fija el orden, las decisiones tomadas y cómo se verifica. Se trabaja en `master`,
una fase por vez, con la app andando al cerrar cada una. Primero tokens y primitivas (los
alias `--dos-*` hacen que lo viejo tome la paleta nueva sin tocarlo) y recién después las
pantallas, de las simples a la ficha. La ficha se parte en componentes **antes** de
rediseñarla, como refactor puro con su propio commit.

## Implementación

Fases del paquete, sin cambios de orden:

0. Preparación: feature, ADR, `PROGRESS.md` (hecha).
1. Tokens, fuentes `@fontsource` y shell (topbar, rail con contadores reales, statusbar).
2. Primitivas de `frontend/src/components/dos/` y `/_catalogo`.
3. Juegos, Sistemas, Configuración (bugs 1 y 2).
4. Ficha de juego: refactor a `src/pages/ficha/`, `useFichaProgress`, UI nueva, autosave,
   revisión de sugerencias, atajos. **Sub-plan y OK antes de empezar.**
5. Nuevo juego, asistente de cuatro pasos (bugs 4 y 5). **Sub-plan y OK antes de empezar.**
6. Exportar: navegación con id, paquete agrupado y cola (bugs 3, 6 y 7).
7. Limpieza (`--dos-*`), accesibilidad y tests.

Cambios de backend previstos, todos chicos y sin cambiar contratos:

- `backend/store/juegos.py` — al aceptar una sugerencia se conserva `source`; al editar a
  mano se escribe `source: "manual"` (hoy escribe `{status: "manual"}` sin fuente en las
  líneas ~137, 150, 158 y 219).
- Causa y arreglo de los bugs 2, 5 y 6, que pueden estar en backend; se confirma en cada fase.

## Decisiones

- **Autosave con debounce (~800 ms y al perder foco) en vez de un solo "Guardar"** — el
  backend ya tiene un endpoint por campo y escritura atómica por `game.json`
  ([`ADR-0008`](../../decisions/0008-persistencia-en-archivos.md)). `useGameMutations`
  invalida hoy cuatro queries en cada mutación; el autosave invalida solo lo necesario y
  no resetea el estado local mientras el campo tiene foco.
- **Conservar `source` al aceptar en vez de solo distinguir en el frontend** — permite el
  chip "ArcadeDB" del diseño; la procedencia sigue interna (ADR-0002).
- **Mandan los deltas D1–D5 sobre el rediseño** — reseña 0–100, revistas sin descarga,
  export con "Siempre incluido" bloqueado.
- **Estética Flyer en vez de DOS** — ver [`ADR-0023`](../../decisions/0023-estetica-flyer-reemplaza-dos.md).
- **Tres dependencias `@fontsource/*`** — aprobadas el 2026-10-08; fuentes sin red.

## Riesgos

- **Pérdida de funcionalidad al reescribir `FichaJuego.tsx` (1376 líneas)** — se mitiga
  con el refactor puro previo y una checklist de funciones existentes por sección en
  `PROGRESS.md`; no se rediseña una sección sin haber verificado su equivalente.
- **Autosave que pisa lo que el usuario escribe** — se mitiga con estado local mientras
  hay foco y con tests del hook de guardado.
- **"Volver a precargar" desde la ficha vs. "sin red al abrir una ficha"**
  ([`ADR-0015`](../../decisions/0015-precarga-con-red-al-alta.md)) — es una acción
  explícita del usuario, no automática; se revisa en la Fase 4 y, si hace falta, va un ADR.
- **Choque con features en curso (015–018)** — se verifica el estado de cada una antes de
  tocar la ficha, para no mezclar cambios.
