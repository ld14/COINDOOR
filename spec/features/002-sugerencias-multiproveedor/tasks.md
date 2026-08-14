# 002 · Sugerencias multiproveedor — Tareas

## Antes de tocar código

- [ ] Elegir el modelo gratuito de IA principal y uno de respaldo. Hecho cuando: ambos
      funcionan sin credenciales pagas y está escrito qué cupo, latencia y límites tienen.
- [x] Decidir dónde viven las claves si el modelo las necesita. Fuera del repo, y que la app
      arranque sin ellas: sin credenciales, el proveedor se saltea, no rompe. `.env` en la
      raíz (leído por `pydantic-settings`, prefijo `COINDOOR_`), agregado a `.gitignore`
      (no lo estaba). Variables: `COINDOOR_AI_PRIMARY_BASE_URL` / `_API_KEY` / `_MODEL`,
      mismo patrón para `_BACKUP_`.
- [ ] Escribir `sinopsis.v1.md`, `resena.v1.md` y `trucos.v1.md`. Hecho cuando: el mismo
      prompt sobre tres juegos distintos produce textos que se leen como escritos por la
      misma persona. **Es el criterio de la feature, no un detalle.**
- [x] Confirmar qué queda cubierto sin ScreenScraper, MobyGames ni scraping HTML. Hecho
      cuando: cada campo queda marcado como `IA`, `referencia`, `manual` o `fuente oficial`.
      Tabla completa en [`ADR-0013`](../../decisions/0013-sin-scraping-ni-catalogo-pago.md).

## Implementación

- [x] `providers/base.py` — `Protocol`, `Consulta`, `Candidato`. Hecho cuando: un proveedor
      falso de diez líneas satisface el contrato.
- [x] `providers/registro.py` — tabla `campo → [proveedores]`. Hecho cuando: agregar una
      fuente es una fila y ninguna función crece.
- [x] `providers/http.py` — clasificación del error, backoff con jitter, `Retry-After`,
      token bucket de ritmo y contador **persistente** de cupo. Hecho cuando: ningún
      proveedor implementa reintentos por su cuenta.
- [x] `providers/orquestador.py` — fan-out, timeout por proveedor, aislamiento de fallas,
      conteo. Hecho cuando: con un proveedor que lanza excepción y otro que responde,
      devuelve los resultados del segundo y `respondieron: 1`.
- [x] Cortocircuito sobre **reintentos agotados**, no sobre intentos sueltos.
- [x] Caché por `(set, campo)`, invalidable al reintentar.
- [x] `providers/ia/generador.py` + prompts `.v1` como primer proveedor real. Guarda qué
      prompt y qué modelo produjeron cada texto. **Pendiente:** ningún vendor de IA
      concreto está configurado todavía — el cliente es genérico OpenAI-compatible, el
      usuario define `base_url`/`api_key`/`model` en `.env`.
- [x] `providers/referencia/youtube.py` — devuelve **solo** candidatos `referencia`.
- [x] Sin ScreenScraper, MobyGames ni scraping HTML en esta fase. La información que antes
      dependía de scraping se obtiene vía IA, marcada como IA y nunca usada para identidad.
- [x] API: `POST /games/:id/suggestions/:key` con el patrón de job ya existente.
- [x] `apply-suggestion` rechaza candidatos de clase `referencia`.
- [ ] UI: candidatos con su fuente, conteo `respondieron / consultados`, marca de IA,
      y acción distinta para `referencia` (abre enlace, no aplica). **Bloqueado:** las
      Fases 3–4 del roadmap (ficha de juego, editor de campos) todavía no tienen carpeta de
      feature — no hay dónde enganchar el modal.

## Tests

- [x] Un proveedor falla, otro responde → resultados del segundo, sin estado de error.
- [ ] **Todos** fallan → estado de error con `Reintentar`. (Es un estado de UI; el backend ya
      devuelve `respondieron: 0` para que el cliente lo renderice.)
- [ ] Un proveedor excede su timeout → no bloquea a los demás. (El orquestador itera
      secuencial, no en paralelo — aísla fallas correctamente pero no acelera con timeouts
      largos. No se tocó: fuera del alcance de esta pasada.)

### Reintentos y límites

- [x] Timeout, corte de conexión, 5xx y 429 → **se reintentan**. (Cubierto por `http.py`,
      preexistente.)
- [x] 401, 403, 404 y "sin resultados" → **no se reintentan**. (Preexistente, con test.)
- [x] Respuesta inválida del modelo → falla explícito, no devuelve candidato con datos
      basura.
- [ ] 429 con `Retry-After: 60` → se espera 60 s, no el backoff propio. (Implementado en
      `http.py`, preexistente; sin test dedicado.)
- [ ] Un proveedor que falla dos veces y a la tercera responde → la búsqueda tiene éxito y
      el cortocircuito **no** cuenta un strike. (El código solo marca `retry_exhausted` si
      los tres intentos fallan, así que ya se comporta así; sin test dedicado.)
- [ ] Una búsqueda que agota los tres reintentos cuenta **un** strike, no tres.
      (`orquestador.py` llama `breaker.strike` una vez por excepción, no por intento; sin
      test dedicado del conteo exacto de strikes.)
- [x] Dos búsquedas con reintentos agotados → salteado en la tercera.
- [ ] Cancelar durante un backoff de 16 s → el job termina en el momento, no al final de
      la espera. (`cancel_event.wait()` ya se usa en los backoffs, preexistente; sin test.)
- [ ] Cupo diario agotado → el proveedor queda fuera hasta el reseteo y el mensaje dice
      "sin cuota", **nunca** "sin resultados". (Preexistente en `QuotasStore`/`http.py`.)
- [ ] El contador de cupo sobrevive a un reinicio de la app. (Persistido en disco vía
      `QuotasStore`, preexistente; sin test de reinicio.)
- [ ] Dos llamadas seguidas al mismo dominio respetan la espera de cortesía. (`espera_min`
      en `http.py`, preexistente; sin test dedicado.)
- [x] Segunda búsqueda del mismo `(set, campo)` → no consulta ninguna fuente.
- [x] `Reintentar` → sí las consulta.
- [x] Candidato `referencia` en `apply-suggestion` → rechazado.
- [ ] Campo en `manual` + aplicar candidato → exige confirmación. En `empty` → no. (Es un
      paso de UI — el backend no distingue: aplica igual sea cual sea el `status` actual.)
- [x] Candidato de IA → llega con `generado_por_ia: true`.
- [x] Sin credenciales → el proveedor que las necesita se saltea y el resto funciona.
- [x] Respuesta inválida del modelo → falla explícito, **nunca** un candidato con datos
      basura. Romperse en silencio es peor que romperse.

## Cierre

- [ ] Validar contra todos los criterios de aceptación de `spec.md`.
- [ ] Cargar un juego real de cada tipo —arcade, consola y MS-DOS— usando solo sugerencias,
      y anotar qué campos quedaron sin cubrir. Es la única medida de si la tabla de
      proveedores sirve.
- [ ] Comparar tres sinopsis generadas: si no se leen con la misma voz, el prompt necesita
      otra versión antes de cerrar la feature.
- [ ] Actualizar `roadmap.md`.
