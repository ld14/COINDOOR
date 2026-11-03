---
id: 0026
title: La IA vuelve a "Sugerir" identidad como último recurso, marcada como IA
status: accepted
date: 2026-10-29
supersedes: null
superseded-by: null
tags: [backend, data]
---

# 0026 — La IA vuelve a "Sugerir" identidad como último recurso, marcada como IA

## Contexto

[`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md), punto 4, sacó a la IA de las
sugerencias de identidad en todos los sistemas: la identidad sale de una fuente factual
(ArcadeDB, MobyGames) o de una persona, como pide
[`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md). La única excepción es la precarga del
alta de MS-DOS, donde la IA completa lo que las fuentes factuales no tuvieron.

Usado de verdad (2026-10-29), "Sugerir" quedó vacío en casos comunes:

- MobyGames no encuentra todos los juegos: *Civilization* no está en la primera página de su
  búsqueda y responde "sin resultados".
- MobyGames no tiene todos los campos: *Teenage Mutant Ninja Turtles* y *Guy Spy* no traen
  jugadores para DOS.

La feature [022](../features/022-edicion-correcta-en-las-fuentes/spec.md) suma Launchbox como
segunda fuente factual, pero no cubre todos los huecos. Cuando ninguna fuente tiene el dato,
el modal queda vacío y la persona lo escribe a mano. El dueño del producto pidió que, en ese
caso, la IA proponga.

## Decisión

**En "Sugerir" —un campo o la identidad en bloque— la IA propone desarrollador, editor, género
y jugadores solo cuando ninguna fuente factual ofreció un candidato para ese campo.** Reemplaza
el punto 4 de ADR-0024 únicamente en "Sugerir"; el resto de ADR-0024 sigue vigente.

1. **Último recurso, no un proveedor más.** Las fuentes factuales (ArcadeDB, MobyGames,
   Launchbox) se consultan primero. Si alguna trae un candidato para el campo, la IA no se
   consulta.
2. **Una consulta por juego.** La IA responde la identidad entera en un JSON (`identidad`) y
   cada campo sale de esa misma respuesta, que queda en memoria mientras corre el proceso.
3. **Marcada como IA y nunca aplicada sola.** El candidato lleva `generadoPorIa` y la persona
   decide.
4. **Título, año y formato nunca salen de una IA.** Son datos de una edición; la IA los
   confunde (aplicó "Diskette" o el año de otra versión en fichas de la colección).
5. **La precarga del alta de MS-DOS no cambia:** ya completaba con IA lo que faltaba, con los
   mismos cuatro campos.

## Alternativas consideradas

### A. Dejar "Sugerir" sin IA, como dice ADR-0024

- A favor: ninguna identidad inventada llega a la ficha; la regla de ADR-0004 queda entera.
- En contra: el modal vacío obliga a escribir a mano datos que la IA suele saber.
- **Descartada porque:** el dueño del producto la eligió en ADR-0024 y, después de usarla, pidió
  el respaldo.

### B. La IA siempre, junto a las fuentes factuales (como antes de la feature 020)

- A favor: más opciones a la vista.
- En contra: mezcla un dato verificable con una suposición, y la suposición puede ganar por
  aparecer primero. Cuesta una llamada al modelo en cada juego aunque el dato ya exista.
- **Descartada porque:** con un candidato factual a la vista, la IA no aporta y confunde. El
  caso real: la IA dijo "Sierra" para *Elvira*; MobyGames, "Horror Soft".

### C. La IA de respaldo también para título, año y formato

- A favor: ningún campo de identidad queda sin propuesta.
- En contra: el año y el formato dependen de la edición, y la IA da los de otra.
- **Descartada porque:** es el mismo criterio que la precarga, que ya los excluye.

## Consecuencias

**Positivas**

- "Sugerir" deja de quedar vacío en desarrollador, editor, género y jugadores.
- La IA solo aparece donde no hay un dato verificable, y siempre a la vista como IA.

**Coste asumido**

- Vuelven candidatos de identidad inventados, aunque solo cuando ninguna fuente factual sabe y
  con la marca de IA. Un error como el de *Elvira* puede repetirse en juegos que ni MobyGames
  ni Launchbox conocen.
- Una llamada al modelo por juego cuando falta algún campo.

**Qué habría que revisar si esto se replantea**

- Si los candidatos de IA de respaldo se aplican sin revisar y aparecen errores en el export, la
  marca no alcanza: volver a la alternativa A.
- Si una fuente factual nueva (por ejemplo ScreenScraper, feature 021) cubre casi todo, el
  respaldo deja de hacer falta.

## Referencias

- [`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md), punto 4: lo que este ADR reemplaza en
  "Sugerir".
- [`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md): COINDOOR como fuente de identidad.
- Feature [022](../features/022-edicion-correcta-en-las-fuentes/spec.md): Launchbox como segunda
  fuente factual y el respaldo de IA.
