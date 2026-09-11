---
id: 0019
title: Los trucos salen de un buscador propio más el modelo que ya está configurado
status: accepted
date: 2026-09-09
supersedes: 0018
superseded-by: null
tags: [backend, data]
---

# 0019 — Los trucos salen de un buscador propio más el modelo que ya está configurado

## Contexto

[`ADR-0018`](0018-gemini-con-busqueda-para-trucos.md) decidió que los trucos los sugiriera Gemini
con el tool `google_search`, apoyado en que el free tier de Google incluía 5.000 prompts de
grounding por mes. **Ese dato era falso.** Salió de un blog de terceros durante la investigación,
no de la página de precios de Google, y no se verificó contra la fuente antes de aceptar el ADR.

Medido con una API key real de Google AI Studio, en un proyecto sin billing:

| Modelo | Sin `google_search` | Con `google_search` |
|---|---|---|
| `gemini-3.6-flash` | OK | 429 `RESOURCE_EXHAUSTED` |
| `gemini-3.8-flash` | — | 429 `RESOURCE_EXHAUSTED` |
| `gemini-3.5-flash` | — | 429 `RESOURCE_EXHAUSTED` |
| `gemini-3.1-flash-lite` | OK | 429 `RESOURCE_EXHAUSTED` |
| `gemini-flash-lite-latest` | OK | 429 `RESOURCE_EXHAUSTED` |
| `gemini-2.5-flash` | 404 — cerrado para cuentas nuevas | 404 |

Los modelos responden perfecto **hasta que se agrega el tool de búsqueda**. La página de precios
oficial lo dice sin ambigüedad: para *Grounding with Google Search*, el free tier figura como
**"Not available"**; los 5.000 gratis son una franquicia del **paid tier**, y después cuestan $14
por 1.000.

O sea que la decisión de 0018 sigue siendo correcta en su diagnóstico —los modelos sin búsqueda no
sirven para trucos— pero su solución no es gratuita, que era el requisito. El diagnóstico completo
que originó todo esto está en 0018 y no se repite acá.

## Decisión

**Los trucos salen de una búsqueda en Tavily más el modelo que ya está configurado
(`ai_primary`, con `ai_backup` de respaldo), que estructura lo encontrado.**

Es la alternativa C que 0018 había evaluado y descartado, y **es la única que se midió funcionando
de punta a punta**: al mismo `gpt-oss-120b` que devolvía `{"groups": []}` para Civilization,
pasándole el texto ya buscado, produjo 15 entradas correctas en 3 segundos.

El reparto de tareas es la clave: el modelo deja de tener que **recordar** —donde falla— y pasa a
**estructurar** —donde es bueno—. La búsqueda la hace quien sabe buscar.

Concretamente:

1. Una búsqueda por sugerencia contra `https://api.tavily.com/search`, con la evidencia acotada a
   un presupuesto de caracteres (ver Consecuencias).
2. Esa evidencia va al modelo con un prompt propio, `cheats-web.v1.md`, derivado del de pegado de
   texto pero endurecido contra el ruido de los resultados: descartar lo que sea de otro juego, de
   otra plataforma, o que no esté en el texto.
3. Si la búsqueda no devuelve nada, **no hay candidato** y el trace lo dice. Un modelo al que no se
   le pasó evidencia inventa, que es el fallo que este ADR y el 0018 vienen a cerrar.
4. La cadena de trucos sigue siendo `("arcadedb", …)` sin caída a los modelos a secas.

Tavily: **1.000 créditos al mes gratis, sin tarjeta**, una búsqueda básica cuesta un crédito
(verificado en su documentación de créditos, no en un blog).

## Alternativas consideradas

### A. Activar billing en un proyecto de Google y quedarse con 0018

- A favor: el código de 0018 ya estaba escrito, probado y verde — solo faltaba correr la
  aceptación. Con billing son 5.000 búsquedas gratis al mes y $14 por 1.000 después, o sea que
  para un juego por vez el gasto real es cero.
- En contra: exige una tarjeta en el proyecto, y activar billing **borra el free tier** del
  proyecto para todo lo demás, así que obliga a mantener proyectos separados. Nunca se llegó a
  verificar que el grounding funcione, porque el 429 impide probarlo sin pagar.
- **Descartada porque:** el requisito explícito era una fuente gratuita y sin tarjeta. "Gratis
  hasta 5.000" con una tarjeta cargada no es lo mismo que gratis, y la premisa de que sí lo era es
  justo el error que este ADR corrige.

### B. Quedarse solo con el pegado de texto, que ya funciona

- A favor: cero integraciones nuevas, cero credenciales, cero código. La calidad es la mejor de
  todas las opciones porque la fuente la elige una persona.
- En contra: deja de ser una *sugerencia*. Obliga a buscar a mano, abrir la página, copiar y pegar
  para cada juego.
- **Descartada porque:** el campo `cheats` quedaría sin sugerencia automática, que es
  precisamente lo que se está arreglando. Sigue existiendo como camino manual y **se vuelve el
  resguardo real** cuando la búsqueda no encuentra nada.

### C. Otro proveedor de búsqueda: Brave, Perplexity, Exa vía OpenRouter

- A favor: Brave y Perplexity tienen mejor cobertura de páginas de juegos retro que un índice
  genérico.
- **Descartada porque:** Brave eliminó su tier gratuito —ahora son $5 de crédito mensual y después
  factura la tarjeta guardada—, Perplexity no tiene free tier de API, y la búsqueda de OpenRouter
  cuesta aparte incluso con modelos `:free` ($0.007 por request con Exa). Ninguna cumple el
  requisito de gratis sin tarjeta.

## Consecuencias

**Positivas**

- Es la opción **medida**, no la inferida. Las otras dos veces que se decidió sobre trucos se
  decidió sobre una capacidad supuesta; esta ya se vio produciendo 15 entradas correctas.
- El modelo trabaja en el modo en el que es bueno. No hace falta cambiar de proveedor de IA ni
  tocar sinopsis, reseña, identidad ni precarga.
- **La procedencia queda de verdad**: el trace lleva la query y las URLs reales consultadas —no
  redirects opacos que caducan, como los de grounding—, así que se puede ir a la fuente de cada
  truco.
- Sin tarjeta en ningún lado.

**Coste asumido**

- **Se rompe la propiedad de "una sola clase de integración"** que
  [`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md) compró y que 0018 conservaba: ahora hay un
  buscador *además* del proveedor de IA, con su credencial, su cuota y su modo de falla propios.
  Se asume a conciencia: es el precio de que la búsqueda sea gratis.
- Dos llamadas HTTP por sugerencia en vez de una, y por lo tanto más latencia. No importa
  (`tech-stack.md` §Convenciones: la latencia no es un problema de este producto).
- **El presupuesto de caracteres es un límite real, no una precaución.** `gpt-oss-120b` en el tier
  gratuito de Groq tiene 8.000 TPM y cuenta `prompt + max_tokens` contra ese techo, así que la
  evidencia que se le pasa al modelo hay que recortarla. Menos evidencia es menos cobertura: un
  truco que estaba en el párrafo recortado se pierde.
- 1.000 créditos al mes es un techo mensual que `Limite` tampoco puede expresar (solo conoce
  `por_dia`). Con un juego por vez no se llega, pero si algún día se llega, hace falta un bucket
  mensual en `QuotasStore`.
- La calidad depende de qué devuelva el buscador. Para juegos oscuros va a devolver poco, y ahí el
  resultado correcto es no sugerir nada.

**Qué habría que revisar si esto se replantea**

- Que Tavily cambie su free tier o pida tarjeta: ahí vuelve a la mesa la alternativa A, cuyo código
  quedó escrito y probado en el historial de 0018.
- Que aparezca un modelo con búsqueda incluida y gratis por el esquema *chat completions*: eso
  permitiría volver a una sola integración.
- La prueba es reproducible: *Sid Meier's Civilization* (msdos, 1991) tiene que devolver el modo
  cheat de Shift+56.

## Referencias

- [`ADR-0018`](0018-gemini-con-busqueda-para-trucos.md) — el diagnóstico de por qué los modelos sin
  búsqueda no sirven para trucos sigue siendo válido y vive allá.
- Créditos y free tier de Tavily: <https://docs.tavily.com/documentation/api-credits>
- API de búsqueda de Tavily: <https://docs.tavily.com/documentation/api-reference/endpoint/search>
- Precios de Gemini, donde el grounding figura "Not available" en free tier:
  <https://ai.google.dev/gemini-api/docs/pricing>
