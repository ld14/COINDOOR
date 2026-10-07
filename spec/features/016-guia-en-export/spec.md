# 016 · Bloque `guia` en el export

**Estado:** en curso

## Qué hace

El `data.json` exportado puede incluir un bloque opcional `guia` con la forma de
[`ADR-0037` de ATTRACT](../../../../attract/spec/decisions/0037-forma-bloque-guia-data-json.md).
Fase 1: `guia.acciones` sale de `cabinet.button_list` (mismos campos `control`, `action`,
`color`), más `objetivo` revisado a mano.

Nunca viaja un botón físico, una posición del panel ni una tecla de salida: eso lo
resuelve ATTRACT. **No** viaja `FieldProvenance` ([`ADR-0002`](../../decisions/0002-procedencia-interna.md)
queda intacto). Un paquete sin `guia` sigue siendo válido.

Fuera de alcance: editar la guía en la UI (feature aparte, ver plan §Fases), y
`multijugador.modo` / `perifericos`, que hoy no existen como dato en COINDOOR.

## Por qué

`button_list` ya se recolecta de ArcadeDB y es correcto en los casos del piloto; solo no
viaja. **Corrección al pedido:** no basta agregarlo a `_tabla()` (`bundle/seleccion.py`
solo mide tamaños para la UI); el `data.json` sale de `bundle/datajson.py`.

## Criterios de aceptación

- [ ] Dado un juego con `button_list` y `objetivo`, cuando se exporta con `guia`
      incluida, entonces `data.json["guia"]["acciones"]` tiene las mismas entradas.
- [ ] Sin `objetivo` no se emite `guia` (ATTRACT `doctor` lo rechazaría) y la selección
      lo indica como no disponible.
- [ ] `guia.revision == "borrador"` salvo que la ficha diga `revisado`; `fuentes` no se
      emite mientras no exista la fecha de consulta.
- [ ] El texto de `texts.sinopsis` nunca se copia a `objetivo`.
- [ ] Ninguna clave del bloque contiene `JOYCODE_*`, posición de panel ni tecla de salida.
- [ ] `attract doctor` sobre el zip resultante termina sin ERROR (código de salida).
- [ ] Un `button_list` vacío no genera `acciones: []`: se omite la clave.

## Fuera de alcance

- Exportar `resolution` / `orientation` de `cabinet` (son del mueble original).
- Procedencia por campo — ver ADR-0002.
