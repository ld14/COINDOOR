# 018 · Guía completa — Plan

_Cómo se implementa lo descrito en `spec.md`._

## Enfoque

Los tres textos nuevos son campos de texto en `fielddefs.json`, como `objetivo`: heredan
API, sugerencias, selección del export y procedencia. Las listas se guardan como texto
con **una línea por ítem** y se parten al exportar. `perifericos` y el modo por turnos se
derivan de datos de ArcadeDB, que son hechos y no suposiciones.

## Implementación

1. `fielddefs.json` — `texts[]` suma `primerosPasos`, `reglasEsenciales` y `modo`
   (opcionales, `contractField: "guia"`).
2. `backend/api/schemas.py` + `services/arcadedb.py` — `CabinetInfo.nplayers`, guardado
   desde `ArcadeGame.nplayers`. Si la ficha ya tenía gabinete, se completa solo ese dato.
3. `backend/bundle/datajson.py::build_guia(game, incluir)` — `perifericos` desde
   `cabinet.controls`, listas desde las líneas, `multijugador.modo`, `revision` combinada.
4. `backend/lib/providers/ia/` — prompts `primeros-pasos`, `reglas` y `modo`; validación
   por campo en `generador.py`; filas en `registro.py` (solo IA). El contexto de la ficha
   de 017 se reutiliza y suma los jugadores.
5. `lib/domain/guia.py::guia_checklist` y `GameOut.guiaChecklist` — qué hay y qué falta,
   con las mismas funciones del export; el frontend solo lo muestra (`GuiaChecklist`).
6. Frontend — `TextSection` renderiza los textos de la guía desde una lista; `modo` usa
   `DosSelect`.

## Salvaguardas automáticas

- `lib/domain/guia.py::problema_texto` es la única regla: placeholder o, solo en el objetivo,
  nombre interno. `texto_guia` devuelve `None` si hay problema, así que el export
  (`build_guia`), la selección (`SeleccionItem.motivo`), la validación del export y el
  checklist usan la misma regla y no pueden diferir.
- `store/migracion.py` v2 baja los textos de la guía de `manual` a `suggested`; `StoredGame`
  nace con `version = 2`. Se aplica al leer y se persiste en el siguiente guardado.
- Los prompts piden nombrar el juego por su nombre comercial, nunca por el romset.

## Decisiones

- **Lista como texto de varias líneas en vez de un tipo de campo nuevo** — reutiliza todo el
  flujo de texto; el costo es partir líneas al exportar.
- **`perifericos` derivado, no editable** — ArcadeDB lo publica; si falta, se omite.
- **`modo` derivado solo en el caso seguro** — `alt` no admite cooperar ni competir a la
  vez; `sim` sí, y ahí decide una persona.
- **Rechazar en el export, no solo ocultar en la UI** — la selección marca el texto como no
  disponible y la API lo rechaza con el motivo; además el bloque lo excluye por su cuenta.
- **Migrar `manual` → `sugerido` en vez de un campo nuevo de revisión** — `revision` ya se
  deriva del estado de cada texto; bajar el estado es lo que lo hace bajar a `borrador`.
- **`acciones` sin cambios** — el dato falta en ArcadeDB para algunos juegos (Arkanoid) y
  no se completa con IA: es justo lo que el piloto detectó como error.

- **Reglas del checklist en el backend, no en TypeScript** — para que lo que se muestra no
  pueda diferir de lo que viaja.
- **«No se pudo generar» sale del modal, no del servidor** — el resultado de una sugerencia
  es transitorio; se recuerda en la ficha mientras está abierta.

## Riesgos

- **Control con texto inesperado** — se compara por palabra clave y lo no reconocido se omite.
- **El modelo inventa un paso** — mismo modal de revisión; el prompt prohíbe nombrar controles.
