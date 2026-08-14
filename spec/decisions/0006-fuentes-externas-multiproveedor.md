---
id: 0006
title: Sugerencias con varios proveedores por campo, con resultados parciales
status: superseded
date: 2026-08-11
supersedes: null
superseded-by: 13
tags: [backend, data]
---

# 0006 — Sugerencias con varios proveedores por campo, con resultados parciales

## Contexto

El botón "buscar más carátulas" es el diferencial de COINDOOR. Pero **no hay una fuente que
cubra todo**: las APIs de metadata de videojuegos son fuertes en consolas y flojas en
arcade, casi ninguna tiene marquesinas, y para reseñas con categorías propias o trucos
agrupados no existe ninguna fuente estructurada.

Además los campos son heterogéneos: una carátula es un archivo, una sinopsis es texto que
debería leerse igual en los 200 juegos de la colección, y un manual es un PDF que vive en
archivos históricos.

`data-model.md` §5.1 ya modela `source` por campo y candidatos con su fuente, así que el
modelo soporta múltiples orígenes; falta decidir cuáles y cómo se combinan.

## Decisión

**Cada campo tiene una lista ordenada de proveedores, y los resultados se combinan.**

| Campo | Proveedores, en orden |
|---|---|
| Carátula, póster, marquesina, logo, captura | ScreenScraper → MobyGames → scraping (abandonsocios, myabandonware) |
| Video de gameplay | ScreenScraper → YouTube |
| Sinopsis | **IA con prompt fijo** |
| Reseña (nota + categorías) | **IA con prompt fijo** |
| Trucos | GameFAQs → **IA** |
| Manual (PDF) | archive.org → replacementdocs |
| Identidad | `mame -listxml` (arcade) → ScreenScraper por hash (consolas) → declarada. **Nunca IA** ([`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md)) |

### Dos clases de candidato

No todos los proveedores devuelven algo que se pueda aplicar con un click:

| Clase | Qué es | Qué hace el botón |
|---|---|---|
| **Aplicable** | El proveedor entrega el archivo o el texto | Lo carga en el campo |
| **Referencia** | El proveedor solo dice **dónde** está | Abre el enlace. El usuario consigue el archivo y lo sube a mano |

YouTube es `referencia`: no entrega un `.mp4` y sus términos no permiten descargarlo, pero
como pista para encontrar el video correcto no tiene rival. El usuario mira, consigue el
archivo por su cuenta y usa el botón `Cargar` que ya existe.

La misma forma sirve para las revistas, que también son una pista y no un asset
([`ADR-0003`](0003-bundle-por-juego.md)). Una sola mecánica para los dos casos.

### Cuatro reglas que valen para todos

1. **Se espera a todos los proveedores y se devuelve todo junto.** Cada uno corre aislado
   del resto; el que falla o se cuelga se descarta y los demás siguen. El estado de error
   solo aparece cuando **ninguno** respondió.

   Los timeouts existen para que una conexión colgada termine alguna vez, **no como
   presupuesto de latencia**: las búsquedas son a pedido y esperar no molesta
   (`tech-stack.md` §Convenciones). Por eso son generosos y una llamada a un modelo puede
   tardar treinta segundos sin que eso sea un problema.
2. **La pantalla dice cuántas fuentes contestaron.** Con un solo proveedor, "sin
   resultados" era una respuesta clara. Con seis, un resultado corto puede significar "el
   juego es oscuro" o "tres fuentes se cayeron", y son cosas distintas.
3. **Cada candidato viaja con su fuente y se muestra.** No para el contrato —la procedencia
   no se exporta ([`ADR-0002`](0002-procedencia-interna.md))— sino porque quien elige entre
   cinco carátulas parecidas decide distinto sabiendo cuál vino de dónde.
4. **De los sitios de abandonware se toma metadata e imágenes, nunca el juego.** COINDOOR
   no descarga ROMs de terceros; los archivos del juego son los que ya tenés.

### El prompt de IA es un artefacto versionado

Sinopsis y reseña se generan con IA porque el objetivo no es exactitud enciclopédica: es
que **los 200 juegos de la colección se lean con la misma voz**. Eso solo se sostiene si el
prompt es fijo.

Por lo tanto: el prompt vive en el repo, se versiona, y **se guarda junto al texto qué
prompt y qué modelo lo produjeron** (dato interno, no se exporta). Sin eso, regenerar una
sinopsis dos años después la devuelve escrita distinto y la colección se vuelve un collage.

### Los scrapers son de última prioridad y frágiles por definición

abandonsocios, myabandonware y GameFAQs no tienen API: se leen parseando HTML que puede
cambiar sin aviso. Van últimos, con timeout corto, y su caída **nunca** rompe una búsqueda.
Si un scraper falla dos veces seguidas, se lo salta el resto de la sesión.

## Alternativas consideradas

### A. Un solo proveedor (ScreenScraper) y listo

- A favor: una integración, una cuota que administrar, cero lógica de combinación.
- En contra: sin cobertura para MS-DOS y PC, que es justo donde su catálogo es más flaco, y
  sin nada para reseñas ni trucos.
- **Descartada porque:** la colección incluye plataformas que ScreenScraper cubre mal, y
  dejar esos juegos sin sugerencias los condena a carga 100% manual — que es el problema
  que COINDOOR existe para resolver.

### B. Devolver resultados a medida que cada proveedor contesta

- A favor: la grilla se puebla enseguida con lo que llegó del proveedor más rápido.
- En contra: exige respuesta incremental, una grilla que se repuebla sola y un estado de
  "todavía faltan fuentes" que el usuario tiene que interpretar.
- **Descartada porque:** optimiza una latencia que a este usuario no le importa. Las
  búsquedas son a pedido, de a un campo por vez, y esperar unos segundos más no cambia
  nada. Agregar streaming para eso es complejidad que no compra nada — si algún día la
  espera molesta, se agrega sin tocar el contrato del proveedor.

### C. IA como fuente de todo, incluida la identidad

- A favor: una sola integración, cubre cualquier plataforma y cualquier campo.
- En contra: inventa con seguridad. Un título o un año equivocados viajan dentro de bundles
  a otras máquinas y nadie los vuelve a mirar.
- **Descartada para identidad**, aceptada para sinopsis, reseña y trucos: un error ahí se
  ve leyendo y no rompe nada. Ver §Coste asumido.

## Consecuencias

**Positivas**

- Ninguna plataforma queda sin sugerencias.
- Agregar o quitar una fuente es una entrada en la tabla, no un cambio de arquitectura.
- La colección entera se lee con una voz consistente.

**Coste asumido**

- **Seis integraciones en vez de una**, con cuotas, credenciales y modos de falla distintos.
- **La reseña generada por IA es una opinión inventada con forma de dato.** Una sinopsis
  errónea se lee raro; un `GRÁFICOS: 85` fabricado se ve en el gabinete idéntico a una nota
  real de una revista de la época. La confirmación humana antes de marcar "listo" es la
  única barrera, y conviene que la pantalla deje claro que ese número lo propuso una IA.
- **YouTube entra como `referencia`, no como descarga.** COINDOOR no baja el video ni lo
  recorta: muestra los enlaces y el usuario sube el archivo a mano. Evita el problema de
  términos de uso y el del recorte de una sola vez, a cambio de un paso manual.
  ScreenScraper va primero porque sí entrega loops cortos listos para usar.
- Los scrapers se van a romper solos cada tanto. Es esperable, no un bug.

**Qué habría que revisar si esto se replantea**

- Si una fuente cubriera de verdad todo el catálogo, la combinación deja de pagar su
  complejidad.
- Si las cuotas de ScreenScraper resultan más ajustadas de lo previsto, hay que revisar el
  orden y apoyarse antes en las fuentes sin autenticación.

## Referencias

- `docs/claude_diseño/data-model.md` §5.1 y §6 — `MediaField.source`, endpoint de
  sugerencias.
- `docs/claude_diseño/screens-spec.md` §5.11 — el modal y sus cuatro fases.
- [`ADR-0002`](0002-procedencia-interna.md) — la procedencia no se exporta.
- [`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md) — identidad, nunca por IA.
