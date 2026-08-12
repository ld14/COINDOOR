# 002 · Sugerencias con varios proveedores

**Estado:** borrador

## Qué hace

**Recibe** un juego y un campo. **Produce** una lista de candidatos de varias fuentes, cada
uno con su procedencia, que el usuario compara y elige.

Dos clases de candidato ([`ADR-0006`](../../decisions/0006-fuentes-externas-multiproveedor.md)):
**aplicable** (el proveedor entrega el archivo o el texto) y **referencia** (solo dice dónde
está; el usuario lo consigue y lo sube a mano).

**No** decide nada por su cuenta: toda sugerencia la acepta una persona.

## Por qué

Es el diferencial del producto. Sin sugerencias, COINDOOR es un formulario y cargar 200
juegos a mano es el trabajo que hoy nadie hace.

Ninguna fuente cubre todo: las APIs de metadata son fuertes en consolas y flojas en arcade,
casi ninguna tiene marquesinas, y para reseñas con categorías propias o trucos agrupados no
existe fuente estructurada. Por eso son varias, y por eso una sola caída no puede dejar al
usuario sin nada.

## Criterios de aceptación

- [ ] Dado un campo con varios proveedores, se consultan todos y los candidatos llegan
      juntos al terminar, mezclados y con su fuente a la vista.
- [ ] **Dado un proveedor que falla o vence su timeout, la búsqueda igual devuelve lo que
      consiguieron los demás.** Un solo proveedor caído no produce un error.
- [ ] Una búsqueda puede tardar decenas de segundos sin que se considere una falla; lo que
      no puede es parecer colgada.
- [ ] Dado que **ningún** proveedor respondió, y solo entonces, se muestra el estado de
      error con `Reintentar`.
- [ ] La respuesta informa cuántos proveedores contestaron sobre cuántos se consultaron.
- [ ] Dado un candidato de clase `referencia`, su acción abre el enlace y **no** modifica el
      campo.
- [ ] Dado un campo con contenido, el primer candidato es "Tu archivo actual" y quedárselo
      es la opción por defecto.
- [ ] Dado un campo en estado `manual`, aplicar un candidato pide confirmación explícita.
- [ ] Dado un texto generado por IA, se ve marcado como tal antes de aceptarlo.
- [ ] Dos búsquedas del mismo campo y juego en la misma sesión no vuelven a consumir cuota.
- [ ] Dado un fallo pasajero —timeout, corte, 5xx, 429— se reintenta con espera creciente.
- [ ] Dado un 404, un 401 o una respuesta sin resultados, **no** se reintenta: son
      respuestas, no fallas.
- [ ] Dado un proveedor con dos búsquedas cuyos reintentos se agotaron, se lo saltea el
      resto de la sesión.
- [ ] Dado un cupo diario agotado, el mensaje dice "sin cuota" y no "sin resultados".
- [ ] Ninguna fuente recibe llamadas más rápido que el ritmo que declara.
- [ ] Ningún proveedor de identidad es una IA: identidad sale de MAME, de ScreenScraper por
      hash, o de una persona ([`ADR-0004`](../../decisions/0004-coindoor-fuente-identidad-no-mame.md)).

## Fuera de alcance

- **Descargar videos de YouTube.** Es `referencia`: enlace, y el archivo lo sube el usuario.
- **Descargar ROMs de ningún sitio.** De las fuentes de abandonware se toma metadata e
  imágenes, nunca el juego.
- **Sugerir sin que el usuario lo pida.** Nada corre en segundo plano ni al abrir la ficha.
- **Carga masiva.** Un campo de un juego por vez.
- **El color de acento**, que se deriva de la carátula y no consulta ninguna fuente.
