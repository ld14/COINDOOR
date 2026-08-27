---
id: 0014
title: Usar ArcadeDB como fuente de imágenes, video, manual y texto para arcade
status: accepted
date: 2026-08-24
supersedes: 13
superseded-by: null
tags: [backend, data]
---

# 0014 — Usar ArcadeDB como fuente de imágenes, video, manual y texto para arcade

## Contexto

[`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md) sacó ScreenScraper, MobyGames y todo
scraping HTML de la tabla de proveedores. El motivo fue concreto y sigue siendo válido: *"seis
integraciones con cuotas y términos distintos, media docena de las cuales parsean HTML que
puede cambiar sin aviso, resultaron más caras de mantener de lo que compraban en cobertura"*.

El coste que ese ADR asumió también fue explícito: carátula, póster, marquesina, logo, captura
y manual quedaron **sin ningún camino de sugerencia automática**, y reseña y trucos pasaron a
depender de una IA que puede inventar de forma convincente.

Y dejó escrita la señal de reapertura:

> Una fuente de imágenes/manuales sin scraping con términos claros sería **candidata a una fila
> nueva en la tabla — decisión explícita, no un default**.

**Qué cambió:** apareció esa fuente. ArcadeDB (`adb.arcadeitalia.net`, de motoschifo) es una API
JSON documentada, **sin API key, sin registro y sin cuota**, indexada por nombre de romset MAME.
Verificado en vivo contra `goldnaxe` el 2026-08-24:

- `query_mame` → identidad (`short_title`, `year`, `manufacturer`, `genre`, `players`), 6 URLs de imagen, `youtube_video_id`, dos URLs de MP4 y el campo `history`.
- `query_mame_media` → 21 slots de imagen más `url_manual`.
- Descargas comprobadas: marquesina PNG 1200×385 (866 KB), flyer PNG 850×1123 (829 KB), MP4 de gameplay (3,7 MB), manual PDF (3,0 MB). Todo HTTP 200, sin autenticación.
- Un romset desconocido devuelve `{"release":6,"result":[]}` con HTTP 200.

Los dos motivos por los que ADR-0013 descartó a ScreenScraper y MobyGames —credencial de
terceros y cuota diaria— **no le aplican**. La fragilidad del HTML tampoco: es JSON con
contrato publicado.

## Decisión

**ArcadeDB es el primer proveedor de identidad, imágenes, video, sinopsis y trucos para los
sistemas arcade**, por delante de la IA. Reabre exactamente los campos que ADR-0013 dejó
vacíos, y solo para arcade.

| Campo | Proveedores, en orden | Cambia respecto a 0013 |
|---|---|---|
| Identidad | **ArcadeDB** → IA | Antes: IA (ver nota abajo) |
| Carátula, póster, marquesina, logo, captura | **ArcadeDB** → búsqueda de imágenes | Antes: **ninguno** |
| Video | **ArcadeDB** (MP4 aplicable) → YouTube (referencia) | Antes: solo YouTube, siempre referencia |
| Sinopsis | **ArcadeDB** → IA | Antes: solo IA |
| Trucos | **ArcadeDB** → IA | Antes: solo IA |
| Manual (PDF) | **ArcadeDB** | Antes: **ninguno** |
| Reseña | IA | Sin cambio — ArcadeDB no la tiene (`rate: 0`) |

Para los sistemas que no son arcade, la tabla de ADR-0013 queda **intacta**: ArcadeDB solo
indexa MAME y no tiene nada que aportar ahí.

**Sobre la identidad:** ArcadeDB no es una IA, así que no choca con la prohibición de
[`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md). Al contrario: ese ADR nombra
`mame -listxml` como autoridad de identidad arcade, y ArcadeDB deriva del mismo `.dat` de MAME
—`Mame 0.289 (jul-31 2026)` según el propio campo `emulator_name`—. Por eso la identidad que
escribe se registra como `identitySource: "mame"`.

**Atribución.** Los términos del servicio exigen citar la fuente y `history` viaja con
`history_copyright_short: "(C) arcade-history.com"`. El crédito vive **dentro de la aplicación**
—en la procedencia por campo, en el `source` de cada campo y en una línea fija del panel de
gabinete—, nunca en el bundle: [`ADR-0002`](0002-procedencia-interna.md) manda.

**Una conexión por vez.** Los términos recomiendan una sola conexión por IP. Lo cubre el
`Limite(por_segundo=1.0)` que `lib/providers/http.py` ya serializa con un lock de clase.

## Alternativas consideradas

### A. Dejar todo como está: carga 100% manual

- A favor: cero integraciones nuevas, cero superficie que mantener, cero texto de terceros. Es la decisión vigente y no ha roto nada.
- En contra: es el coste que ADR-0013 asumió a sabiendas, y se está cobrando. Un juego arcade necesita seis imágenes cargadas a mano más un manual buscado por fuera; el botón "Sugerir" ofrece IA para dos campos de texto y un link a YouTube.
- **Descartada porque:** la condición que el propio ADR-0013 puso para reabrir —fuente sin scraping, con términos claros— se cumple de forma verificable. Mantener el coste cuando desapareció el motivo es inercia, no decisión.

### B. Volver a ScreenScraper

- A favor: cobertura 18/18 campos y multiplataforma, no solo arcade. Es la fuente más completa que existe.
- En contra: exige credencial de usuario y tiene cuota de 20k requests/día. Son las dos razones exactas por las que ADR-0013 lo sacó.
- **Descartada porque:** nada cambió en ScreenScraper desde esa evaluación. Reintroducirlo sería revertir ADR-0013 sin hecho nuevo que lo justifique — justo lo que ese ADR pidió no hacer.

### C. Ejecutar `mame -listxml` localmente

- A favor: sin red, sin términos de terceros, sin atribución. Autoridad de identidad que ADR-0004 ya nombra.
- En contra: da **solo identidad**. Cero imágenes, cero video, cero manual, cero texto — que es exactamente el hueco a llenar. Además exige un binario de MAME instalado y un `.dat` de cientos de MB.
- **Descartada porque:** no resuelve el problema de esta decisión. Sigue siendo una opción válida y complementaria para identidad offline; no entra acá.

### D. Bajar el dump de LaunchBox Games Database

- A favor: gratis, sin key, 1.322.348 imágenes sobre 190 plataformas — no solo arcade.
- En contra: son 107 MB comprimidos y 509 MB de XML que hay que indexar, contra ADR-0008 (sin base de datos). **Cero videos, cero manuales, cero trucos** (verificado escaneando el dump entero). Y sus términos de reuso no están publicados.
- **Descartada porque:** cubre un tercio del pedido a cambio de un problema de indexación que ADR-0008 prohíbe resolver como corresponde. Queda como candidata futura para imágenes de plataformas no-arcade, con la licencia verificada primero.

## Consecuencias

**Positivas**

- Los seis campos que ADR-0013 dejó huérfanos vuelven a tener proveedor, con archivos reales y no links de referencia.
- Sinopsis y trucos de arcade pasan de texto generado a texto documentado. La IA queda de respaldo para cuando ArcadeDB no conoce el romset.
- Una integración nueva, sin credencial, sin cuota y sin HTML parseado: no reabre ninguno de los tres modos de falla que ADR-0013 quiso eliminar.
- La identidad arcade gana una fuente derivada de MAME, que es la que ADR-0004 pide.

**Coste asumido**

- **La sinopsis de arcade-history llega al bundle** como `summary`. Es el único texto de terceros que cruza al export, y ADR-0002 impide acompañarlo de su atribución ahí. Mitigación de proceso, no técnica: el campo aterriza como `suggested` y editable, y el usuario lo revisa antes de exportar.
- Carátula y póster salen del mismo archivo (el flyer): ArcadeDB no tiene un asset con forma de portada y los dos campos son `required`. Se duplican ~1,6 MB por juego para que el juego pueda llegar a COMPLETO.
- `developer` y `publisher` reciben el mismo valor (`manufacturer`): MAME tiene un solo campo de empresa.
- Una dependencia de red más en el camino de sugerencias. Acotada: si ArcadeDB cae, el cortocircuito la apaga y la IA sigue respondiendo.
- El crédito a motoschifo y a arcade-history solo es visible dentro de la aplicación.

**Qué habría que revisar si esto se replantea**

- Si ArcadeDB empieza a pedir credencial, cuota o deja de responder, aplica el mismo criterio que ADR-0013 usó con ScreenScraper: sale de la tabla.
- Si aparece un reclamo sobre el `summary` de arcade-history en bundles instalados, hay que decidir entre dejar de importar ese texto o reabrir ADR-0002 para que la atribución viaje.
- Si alguna vez se soportan plataformas no-arcade con la misma ambición de cobertura, ArcadeDB no sirve y la pregunta vuelve a abrirse desde cero.

## Referencias

- Feature [008-arcadedb](../features/008-arcadedb/spec.md)
- API: `https://adb.arcadeitalia.net/service_scraper.php` — endpoints `query_mame`, `query_mame_media`, `query_mame_like`, `download_status`
- Verificación en vivo contra `goldnaxe`, 2026-08-24
- [`ADR-0013`](0013-sin-scraping-ni-catalogo-pago.md) §"Qué habría que revisar" — la señal que habilita este ADR
- [`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md) — MAME como autoridad de identidad arcade
- [`ADR-0002`](0002-procedencia-interna.md) — la procedencia no viaja al export
