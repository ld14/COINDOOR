---
id: 0013
title: Sugerencias sin scraping ni catálogos de terceros — solo IA y referencias
status: accepted
date: 2026-08-13
supersedes: 6
superseded-by: null
tags: [backend, data]
---

# 0013 — Sugerencias sin scraping ni catálogos de terceros — solo IA y referencias

## Contexto

[`ADR-0006`](0006-fuentes-externas-multiproveedor.md) definió una tabla campo→proveedor
apoyada en ScreenScraper, MobyGames y varios scrapers HTML (abandonsocios, myabandonware,
GameFAQs, replacementdocs, archive.org). Durante la implementación de la feature
[002](../features/002-sugerencias-multiproveedor/spec.md) se decidió no seguir ese camino:
seis integraciones con cuotas y términos distintos, media docena de las cuales parsean HTML
que puede cambiar sin aviso, resultaron más caras de mantener de lo que compraban en
cobertura.

## Decisión

**Ningún proveedor de esta feature scrapea HTML ni depende de ScreenScraper o MobyGames.**
La cobertura queda así:

| Campo | Proveedores, en orden | Cambia respecto a 0006 |
|---|---|---|
| Sinopsis | IA con prompt fijo | Sin cambio |
| Reseña (nota + categorías) | IA con prompt fijo | Sin cambio |
| Trucos | IA con prompt fijo | Antes: GameFAQs → IA. Se saca GameFAQs |
| Video de gameplay | YouTube, como `referencia` | Antes: ScreenScraper → YouTube. Se saca ScreenScraper |
| Carátula, póster, marquesina, logo, captura | **Ninguno** | Antes: ScreenScraper → MobyGames → scraping |
| Manual (PDF) | **Ninguno** | Antes: archive.org → replacementdocs |
| Identidad | Sin cambio: `mame -listxml` → ScreenScraper por hash → declarada. **Nunca IA** | Sin cambio ([`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md)) |

Carátula, póster, marquesina, logo, captura y manual quedan **sin sugerencia automática**:
el usuario los carga a mano, como cualquier campo sin proveedor. Si ScreenScraper o
MobyGames vuelven algún día por API oficial, requieren verificación de términos/cuotas y
una decisión explícita — no un ADR que los reintroduzca por default.

## Alternativas consideradas

### A. Mantener la tabla de ADR-0006 tal cual

- A favor: cobertura más ancha (carátulas, pósters, manuales con proveedor real).
- En contra: seis integraciones con modos de falla, cuotas y términos de uso distintos;
  media docena de ellas HTML frágil que se rompe sin aviso y sin API que lo avise.
- **Descartada porque:** el costo de mantenimiento de esa superficie superó lo que la
  feature necesitaba para su criterio de aceptación real — cobertura pareja entre
  plataformas para los campos de texto, no cobertura total de imágenes.

### B. Sacar el scraping HTML pero mantener MobyGames (API oficial, no scraping)

- A favor: MobyGames es API con términos, no HTML parseado — el argumento de fragilidad no
  le aplica igual que a los scrapers.
- En contra: sigue siendo una integración con credencial, cuota propia y un `game_id`
  externo que viaja en `meta` — la clase de complejidad que el pivot buscaba reducir, y una
  fuente que la spec.md actualizada de la feature 002 excluye explícitamente del camino
  principal.
- **Descartada porque:** ya hay código de MobyGames escrito contra el plan viejo y se
  decidió borrarlo en vez de mantenerlo como excepción — dejar una sola API paga activa
  contradice el `spec.md` reescrito ("ScreenScraper y MobyGames no son camino principal").

## Consecuencias

**Positivas**

- Una sola clase de integración (HTTP a un modelo compatible con el esquema *chat
  completions*), no seis modos de falla distintos.
- Cero credenciales de terceros que administrar salvo la del proveedor de IA, opcional.
- Nada que se rompa por un cambio de HTML ajeno sin aviso.

**Coste asumido**

- Carátula, póster, marquesina, logo, captura y manual pierden su único camino de
  sugerencia automática: vuelven a carga 100% manual hasta que una decisión explícita
  reintroduzca una fuente para esos campos.
- La reseña y los trucos, antes con una fuente estructurada real (GameFAQs) como primera
  opción, dependen ahora enteramente de una IA que puede inventar de forma convincente
  (riesgo ya señalado en 0006 §Coste asumido, ahora sin la opción de preferir GameFAQs
  cuando existe).

**Qué habría que revisar si esto se replantea**

- Si aparece una fuente de imágenes/manuales sin scraping y con términos claros (API
  oficial, cuota razonable), es candidata a una fila nueva en la tabla — decisión explícita,
  no un default.
- Si la calidad de reseña/trucos generados por IA resulta insuficiente en la comparación de
  tres juegos que pide `tasks.md` §Cierre, vale la pena reconsiderar GameFAQs como primera
  opción para trucos.

## Referencias

- [`ADR-0006`](0006-fuentes-externas-multiproveedor.md) — decisión que este ADR supersede.
- `spec/features/002-sugerencias-multiproveedor/{spec,plan,tasks}.md` — reescritos con este
  pivot antes de este ADR.
