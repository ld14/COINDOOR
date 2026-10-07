# 015 · `set` con el romset real — Plan

_Cómo se implementa lo descrito en `spec.md`._

## Enfoque

Una sola función decide el `set` exportado y la usan los dos lugares que hoy copian
`game["id"]`. El romset se **deriva** de `romRef`, igual que ya hacen la precarga de
ArcadeDB y la galería, en vez de guardarse: un campo persistido podría desactualizarse
si cambia `romRef`, y obligaría a migrar `game.json` (ADR-0008).

## Implementación

1. `backend/bundle/identidad.py` (nuevo) — `set_exportado(game) -> str`: si
   `identitySource == "mame"` y `romRef` no vacío, devuelve el nombre normalizado del
   romset; si no, `str(game["id"])`.
2. `backend/bundle/gamejson.py` — línea de `"set"` usa `set_exportado(game)`.
3. `backend/bundle/manifest.py` — ídem.
4. Derivación: los `\` de `romRef` se normalizan a `/`; si la extensión es `.zip`, `.7z`
   o `.chd` se toma el `stem`, si no (carpeta) el nombre entero, en minúsculas. Coincide
   con `services/arcadedb.py` y `services/gallery.py` para archivos. Si el resultado no
   cumple `^[a-z0-9_]+$` (nombre de romset MAME), se descarta y se usa el slug.

## Decisiones

- **Derivar de `romRef` en vez de persistir un campo** — evita dato duplicado y migración.
- **Regla de validez local (`^[a-z0-9_]+$`) en vez de consultar ArcadeDB al exportar** —
  el export no debe depender de la red (la latencia no importa, pero la disponibilidad sí).
  Es un filtro contra basura, no una verificación de existencia.
- **Un módulo nuevo en `bundle/`** en vez de duplicar la regla — dos consumidores.

## Riesgos

- **`romRef` apunta a una carpeta con nombre no-romset** — el filtro cae al slug; el
  resultado es el comportamiento actual, no un empeoramiento.
- **Romset padre vs. clon** — el `stem` de la ROM subida es el del clon si eso es lo que
  se instaló; es lo correcto para `-listxml`. Si el usuario subió la ROM padre bajo otro
  nombre, es un dato de entrada mal cargado, fuera de este alcance.
