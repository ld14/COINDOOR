---
id: 0018
title: Los trucos los sugiere Gemini con búsqueda de Google, no un modelo de memoria
status: superseded
date: 2026-09-09
supersedes: null
superseded-by: 0019
tags: [backend, data]
---

# 0018 — Los trucos los sugiere Gemini con búsqueda de Google, no un modelo de memoria

## Contexto

[`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md) sacó GameFAQs de la cadena de trucos y dejó
el campo `cheats` con una sola fuente: "IA con prompt fijo". Casi un mes después se midió qué
produce esa fuente, y el resultado es que **no produce nada**.

Las mediciones, sobre *Sid Meier's Civilization* (msdos, 1991), con los prompts reales del repo:

| Modelo | Rol en la cadena | Intentos | Resultado |
|---|---|---|---|
| `groq/compound` | `ia_cheats` | 11 | 100% HTTP 413/429 |
| `groq/compound-mini` | alternativa evaluada | 2 | 100% HTTP 413 |
| `openai/gpt-oss-120b` | `ia_primary` | 6 | 6 × `{"groups": []}` |
| `openai/gpt-oss-20b` | `ia_backup` | 3 | 3 × `{"groups": []}` |

La familia `compound` de Groq es la única con búsqueda web del proveedor, y en el tier gratuito
no responde nunca: cada request suyo pide ~14k tokens contra un límite de 30.000 TPM del
`llama-4-scout` que la respalda, así que se rechaza antes de empezar. Falla incluso con un prompt
de 200 caracteres, y siguió fallando con la ventana de rate limit fría después de 40 minutos.

Los `gpt-oss` responden, pero no pueden cumplir el prompt: dice "Investigá" y "Buscá
específicamente" y no tienen acceso a la web. Los trucos de Civilization existen y están
documentados (Shift+56 activa el modo cheat, Alt+R aleatoriza los líderes rivales, el Space Barge,
los comandos de debug), y aun así devolvieron vacío nueve veces de nueve.

Tres hallazgos más, del mismo diagnóstico:

- **Un fallo se disfraza de "no hay trucos".** Con `reasoning_effort=high` el modelo razonó 28.745
  caracteres tratando de recordar, se truncó (`finish_reason=length`, `content` vacío), y
  `_extract_response` sacó un `{"groups": []}` del **razonamiento** — que era el ejemplo del propio
  prompt citado dentro del thinking. La llamada falló y el usuario vio "la IA no encontró trucos".
- **Cuando responden, alucinan.** Con DOOM devolvió `doom -nomap` como truco real, y `-nomap` es
  literalmente un ejemplo de formato del prompt. También afirmó que `idkfa` mata a todos los
  enemigos y que `noclip` da munición infinita.
- **El cuello de botella es la búsqueda, no el modelo.** Al mismo `gpt-oss-120b`, pasándole el
  texto ya buscado con el prompt `cheats-parse.v1.md`, produjo 15 entradas correctas en 3 segundos.
  El modelo es bueno estructurando y malo recordando.

## Decisión

**El campo `cheats` — y solo ese — lo sirve Google Gemini contra el endpoint nativo
`:generateContent` con el tool `google_search`, y una respuesta que no buscó se rechaza.**

Concretamente:

1. La cadena de trucos pasa de `("arcadedb", "ia_cheats", "ia_primary", "ia_backup")` a
   `("arcadedb", "ia_cheats")`. Los dos `gpt-oss` salen de trucos y **siguen intactos** en
   sinopsis, reseña, identidad, precarga al alta y parseo de texto pegado.
2. `ia_cheats` deja de significar "otro modelo del mismo proveedor" y pasa a significar "Gemini con
   grounding", con credenciales propias (`COINDOOR_AI_CHEATS_BASE_URL` / `_API_KEY` / `_MODEL`).
3. Se usa el **endpoint nativo**, no la capa OpenAI-compatible de Google.
4. Si `groundingMetadata` viene vacío o sin `webSearchQueries`, **no hay candidato**: el trace dice
   que el modelo respondió de memoria. Una respuesta sin búsqueda es exactamente el fallo que este
   ADR corrige, y aceptarla con formato válido sería reintroducirlo disfrazado.

## Alternativas consideradas

### A. Subir Groq a Dev tier y quedarse con `compound`

- A favor: cambio de cero líneas — la cadena y el modelo ya están configurados.
- En contra: es pago, y el proyecto es una app local de un solo usuario sin presupuesto asignado.
- **Descartada porque:** el requisito era una fuente gratuita. El diagnóstico confirma que en el
  tier gratuito `compound` no entrega nunca, así que "seguir igual" no es una opción neutral.

### B. OpenRouter con el sufijo `:online`

- A favor: encaje perfecto con el código actual — `OpenAiCompatibleClient` ya habla ese esquema, y
  activar la búsqueda es cambiar el string del modelo. Cero código nuevo.
- En contra: la búsqueda se cobra aparte del modelo.
- **Descartada porque:** su documentación es explícita — *"Using web search will incur extra costs,
  even with free models"*. Exa cobra $0.007 por request, Perplexity $0.005, Parallel $0.001. No
  existe combinación gratuita, ni siquiera con modelos `:free`.

### C. Un buscador gratuito (Tavily) + los `gpt-oss` que ya están configurados

- A favor: **es la única alternativa demostrada end-to-end** en el diagnóstico — 15 entradas
  correctas en 3s. Reusa `cheats-parse.v1.md`, que ya existe y ya funciona, y no cambia de modelo.
  Tavily da 1.000 créditos al mes sin tarjeta.
- En contra: suma un segundo tipo de integración (un buscador además del proveedor de IA), con su
  propia credencial, su propia cuota y su propio modo de falla. Y son dos llamadas por sugerencia
  en vez de una.
- **Descartada porque:** contradice la consecuencia que [`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md)
  compró explícitamente — *"una sola clase de integración (HTTP a un modelo compatible con el
  esquema chat completions), no seis modos de falla distintos"*. Gemini consigue el mismo resultado
  manteniendo esa propiedad: una credencial, un POST, un proveedor. **Queda como el reemplazo
  inmediato si el free tier de Google cambia**, y es la razón por la que este ADR no toca
  `parse_cheats_text`: ese camino ya es la mitad del plan B.

### D. Gemini a través de su capa OpenAI-compatible

- A favor: `OpenAiCompatibleClient` funcionaría casi sin tocar nada — solo cambiar `base_url`, la
  key y el modelo. Ni cliente nuevo ni parseo nuevo.
- En contra: esa capa documenta `tools` con `google_search` **solo para el modelo de imagen**; para
  chat no hay ejemplo ni garantía de que el tool se propague.
- **Descartada porque:** si la capa descarta el tool en silencio, obtenemos una respuesta **no
  grounded con formato válido** — es decir, el fallo original disfrazado de éxito, que es el modo
  de falla más caro de todos los medidos. El endpoint nativo devuelve `groundingMetadata`, que
  permite **verificar** que hubo búsqueda en vez de confiar.

### E. Brave Search API o Perplexity Sonar como fuente de búsqueda

- A favor: ambas son APIs de búsqueda maduras y con buena cobertura.
- **Descartada porque:** Brave eliminó su tier gratuito (ahora son $5 de crédito mensual y después
  factura la tarjeta guardada) y Perplexity no tiene free tier de API. Ninguna cumple el requisito.

## Consecuencias

**Positivas**

- Los trucos pasan a salir de una búsqueda real, no de la memoria de un modelo. Es el único cambio
  que ataca la causa medida.
- **Una respuesta sin búsqueda ya no puede hacerse pasar por "no hay trucos".** El trace distingue
  "buscó y no encontró" de "no buscó" de "la llamada falló", que hoy se ven los tres iguales.
- El modal gana procedencia: las queries que se ejecutaron y los dominios consultados quedan en el
  trace, así que se puede auditar de dónde salió cada truco.
- Se mantiene la propiedad de ADR-0013: una sola clase de integración por campo, una credencial.
- Los ejemplos concretos de los prompts (`IDDQD`, `doom -nomap`, `--level=5`, el código Konami) se
  reemplazan por placeholders. Con un modelo que sí busca, esa fuga contamina resultados que ahora
  tendrán contenido real.

**Coste asumido**

- **Si falta la key de Gemini, `cheats` se queda sin sugerencia de IA.** No hay red de resguardo, y
  es deliberado: el resguardo anterior producía falsos vacíos y trucos inventados, que es peor que
  no producir nada. El campo sigue editable a mano y por texto pegado.
- Una credencial más que administrar, con la trampa de que **activar billing en ese proyecto de
  Google borra el free tier** — hay que dejarlo sin billing.
- El cliente de Gemini no comparte transporte con `OpenAiCompatibleClient`: son dos formas de body
  y de respuesta que mantener. Los otros campos no se benefician.
- **La cuota mensual de grounding (5.000 prompts) no se puede expresar en `Limite`**, que solo
  conoce `por_dia` y resetea por fecha de calendario. Se controla por `espera_min` (~10 RPM) y se
  confía en que un solo usuario editando un juego por vez no se acerca al techo. Si alguna vez se
  acerca, hace falta un bucket mensual en `QuotasStore`, no un parche en el proveedor.
- El JSON estructurado (`responseMimeType`) es **incompatible** con el tool de búsqueda: Google
  devuelve 400 *"Search Grounding can't be used with JSON/YAML/XML mode"*. El JSON se sigue pidiendo
  por prompt y extrayendo del texto, con la fragilidad que eso implica.
- **Los ToS de grounding piden mostrar el `searchEntryPoint.renderedContent`** (las sugerencias de
  búsqueda de Google) junto al resultado. COINDOOR es una app local de un solo usuario que no
  publica nada, y se decide **no renderizarlo**, dejándolo registrado acá en vez de omitirlo en
  silencio. Si algún día la salida se publica, hay que revisarlo.

**Qué habría que revisar si esto se replantea**

- Que el free tier de Google deje de incluir grounding, o que el proyecto quede con billing activo:
  ahí entra la alternativa C, que ya está medida y cuya mitad (`cheats-parse.v1.md`) ya existe.
- Que algún proveedor de IA con búsqueda quede accesible por el esquema *chat completions* gratis:
  eso permitiría borrar el cliente nativo y volver a un solo transporte.
- Que un modelo sin búsqueda empiece a acertar en trucos: la prueba es reproducible — *Sid Meier's
  Civilization* (msdos, 1991) tiene que devolver el modo cheat de Shift+56.

## Referencias

- Diagnóstico completo de la sesión del 2026-09-08/09: 22 llamadas reales medidas contra los cuatro
  modelos, con los prompts del repo sin modificar.
- [`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md) — de dónde viene "IA con prompt fijo" como
  única fuente de trucos, y la propiedad de "una sola clase de integración" que este ADR conserva.
- [`ADR-0015`](0015-precarga-con-red-al-alta.md) — la precarga al alta sigue con `ia_primary`/`ia_backup`;
  este ADR no la toca.
- Grounding with Google Search: <https://ai.google.dev/gemini-api/docs/google-search>
- Incompatibilidad grounding + modo JSON:
  <https://discuss.ai.google.dev/t/rest-api-grounding-and-json-responses-not-compatible/73101>
- Precios de búsqueda en OpenRouter: <https://openrouter.ai/docs/features/web-search>
