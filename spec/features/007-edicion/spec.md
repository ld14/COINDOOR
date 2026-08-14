# 007 · Edición

**Estado:** implementada

## Qué hace

Recibe las pantallas de lectura de la feature [006](../006-pantallas-lectura/spec.md) y la API
real de juegos, campos y media de la feature [005](../005-esqueleto-backend/spec.md). Produce el
flujo de alta `/juegos/nuevo` y el modo edición en `/juegos/:gameId`: identidad, sinopsis,
reseña estructurada, trucos estructurados, imágenes, video, acentos y `mark-ready`.

Quedan fuera sugerencias automáticas —feature [002](../002-sugerencias-multiproveedor/spec.md)—,
export —feature [001](../001-export-bundle/spec.md)— y manuales PDF reales hasta que exista su
job específico.

## Por qué

Desbloquea convertir la colección de lectura en una herramienta usable: crear fichas, completar
faltantes, corregir errores y dejar juegos listos para exportar sin editar JSON a mano.

## Criterios de aceptación

- [x] Dado `/juegos/nuevo`, cuando se completa sistema, origen de ROM e identidad válida,
      entonces se crea la ficha y navega a `/juegos/:gameId`.
- [x] Dado un `launchCmd` o `romRef` relativo donde se exige ruta absoluta, cuando se envía el
      formulario, entonces se muestra el mensaje del contrato y no guarda datos inválidos.
- [x] Dado un campo de identidad, texto, media o acento editado, cuando el backend responde OK,
      entonces la ficha refleja el valor y el estado de completitud se recalcula.
- [x] Dado un campo vacío, cuando se borra desde la UI, entonces no desaparece la sección y vuelve
      a `Sin Información` o `No Disponible`.
- [x] Dado un campo con `status: manual` y contenido, cuando se pulsa `Borrar`, entonces pide
      confirmación antes de vaciarlo. El punto de montaje para que sugerencias (feature 002)
      reemplacen un campo `manual` con el mismo aviso queda documentado ahí, no acá.
- [x] Dado un juego incompleto, cuando se pulsa `Marcar como listo`, entonces muestra faltantes
      exactos y no cambia a `ready`.
- [x] Dado `review` o `cheats`, cuando se editan, entonces se guardan como estructuras, no como
      texto plano.

## Fuera de alcance

- Buscar y aplicar sugerencias de IA o referencias — feature [002](../002-sugerencias-multiproveedor/spec.md).
- Exportar bundles y pantalla `/exportar` conectada — feature [001](../001-export-bundle/spec.md).
- Rasterizar manuales PDF, cancelar ese job o mostrar miniaturas reales.
- Autodetectar colores desde carátula si requiere Pillow o endpoint nuevo.
