# 002 · Sugerencias multiproveedor — Tareas

## Antes de tocar código

- [ ] Conseguir credenciales de ScreenScraper y MobyGames y **verificar sus cuotas y
      términos actuales**. Hecho cuando: está escrito qué límite diario hay y qué pasa al
      agotarlo. La documentación de referencia puede estar desactualizada.
- [ ] Decidir dónde viven las claves. Fuera del repo, y que la app arranque sin ellas: sin
      credenciales los proveedores de API se saltean, no rompen.
- [ ] Elegir el modelo de IA y escribir `sinopsis.v1.md`. Hecho cuando: el mismo prompt
      sobre tres juegos distintos produce textos que se leen como escritos por la misma
      persona. **Es el criterio de la feature, no un detalle.**

## Implementación

- [ ] `providers/base.py` — `Protocol`, `Consulta`, `Candidato`. Hecho cuando: un proveedor
      falso de diez líneas satisface el contrato.
- [ ] `providers/registro.py` — tabla `campo → [proveedores]`. Hecho cuando: agregar una
      fuente es una fila y ninguna función crece.
- [ ] `providers/http.py` — clasificación del error, backoff con jitter, `Retry-After`,
      token bucket de ritmo y contador **persistente** de cupo diario. Hecho cuando:
      ningún proveedor implementa reintentos por su cuenta.
- [ ] `providers/orquestador.py` — fan-out, timeout por proveedor, aislamiento de fallas,
      conteo. Hecho cuando: con un proveedor que lanza excepción y otro que responde,
      devuelve los resultados del segundo y `respondieron: 1`.
- [ ] Cortocircuito sobre **reintentos agotados**, no sobre intentos sueltos.
- [ ] Caché por `(set, campo)`, invalidable al reintentar.
- [ ] `providers/api/screenscraper.py` — imágenes, video e identidad por hash. **El primer
      proveedor real, antes que cualquier otro**: valida el contrato contra una fuente que
      existe.
- [ ] Cálculo de hash perezoso y persistido, leyendo en su lugar los ROM de `romSource:
      'path'`.
- [ ] `providers/ia/generador.py` + prompts `.v1` de sinopsis, reseña y trucos. Guarda qué
      prompt y qué modelo produjeron cada texto.
- [ ] `providers/scrape/youtube.py` — devuelve **solo** candidatos `referencia`.
- [ ] El resto: mobygames, abandonsocios, myabandonware, gamefaqs, archive_org,
      replacementdocs. Uno por uno, cada uno con sus tests.
- [ ] API: `POST /games/:id/suggestions/:key` con el patrón de job ya existente.
- [ ] `apply-suggestion` rechaza candidatos de clase `referencia`.
- [ ] UI: candidatos con su fuente, conteo `respondieron / consultados`, marca de IA,
      y acción distinta para `referencia` (abre enlace, no aplica).

## Tests

- [ ] Un proveedor falla, otro responde → resultados del segundo, sin estado de error.
- [ ] **Todos** fallan → estado de error con `Reintentar`.
- [ ] Un proveedor excede su timeout → no bloquea a los demás.

### Reintentos y límites

- [ ] Timeout, corte de conexión, 5xx y 429 → **se reintentan**.
- [ ] 401, 403, 404 y "sin resultados" → **no se reintentan**. Es el test que más cuota
      ahorra: sin él, cada juego que una fuente no conoce se consulta tres veces.
- [ ] Un scraper que devuelve HTML inesperado → no se reintenta. Va a fallar igual.
- [ ] 429 con `Retry-After: 60` → se espera 60 s, no el backoff propio.
- [ ] Un proveedor que falla dos veces y a la tercera responde → la búsqueda tiene éxito y
      el cortocircuito **no** cuenta un strike.
- [ ] Una búsqueda que agota los tres reintentos cuenta **un** strike, no tres. Sin este
      test, un hipo de red saca de la sesión a una fuente sana.
- [ ] Dos búsquedas con reintentos agotados → salteado en la tercera.
- [ ] Cancelar durante un backoff de 16 s → el job termina en el momento, no al final de
      la espera.
- [ ] Cupo diario agotado → el proveedor queda fuera hasta el reseteo y el mensaje dice
      "sin cuota", **nunca** "sin resultados".
- [ ] El contador de cupo sobrevive a un reinicio de la app.
- [ ] Dos llamadas seguidas al mismo dominio respetan la espera de cortesía.
- [ ] Segunda búsqueda del mismo `(set, campo)` → no consulta ninguna fuente.
- [ ] `Reintentar` → sí las consulta.
- [ ] Candidato `referencia` en `apply-suggestion` → rechazado.
- [ ] Campo en `manual` + aplicar candidato → exige confirmación. En `empty` → no.
- [ ] Candidato de IA → llega con `generado_por_ia: true`.
- [ ] Sin credenciales → los proveedores de API se saltean y el resto funciona.
- [ ] Un scraper que devuelve HTML inesperado → falla explícito, **nunca** un candidato con
      datos basura. Romperse en silencio es peor que romperse.

## Cierre

- [ ] Validar contra todos los criterios de aceptación de `spec.md`.
- [ ] Cargar un juego real de cada tipo —arcade, consola y MS-DOS— usando solo sugerencias,
      y anotar qué campos quedaron sin cubrir. Es la única medida de si la tabla de
      proveedores sirve.
- [ ] Comparar tres sinopsis generadas: si no se leen con la misma voz, el prompt necesita
      otra versión antes de cerrar la feature.
- [ ] Actualizar `roadmap.md`.
