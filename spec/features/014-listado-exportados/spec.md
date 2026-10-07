# 014 · Separar juegos exportados y pendientes

**Estado:** implementada.

## Comportamiento

El listado ofrece «Todos», «Pendientes de exportar» y «Exportados». Por defecto
muestra todos. Cada fila indica «Exportado» o «Pendiente de exportar», además del
estado de completitud existente. Exportado significa que hay un ZIP local terminado;
no confirma instalación en ATTRACT.

Un juego sin ZIP, con ZIP inválido o con cambios guardados en la ficha posteriores al
export está pendiente. Un export exitoso lo pasa a exportados; un intento fallido no
publica un ZIP parcial ni reemplaza el anterior. Los ZIP anteriores a esta feature se
reconocen por su validez y fecha de modificación.

## Aceptación

- Filtro de exportación persistido en la URL, combinable con búsqueda, sistema y estado.
- Filtrado previo a la paginación; navegación anterior/siguiente y total de resultados.
- Etiqueta visible por juego, sin alterar `ready`, `incomplete` ni `error`.
- Al volver de un export exitoso, el listado consulta el resultado actualizado.
- Una edición posterior devuelve el juego a pendientes, también tras reiniciar.
- Un fallo al generar el ZIP conserva el export anterior y limpia temporales.

## Alcance

Sin dependencias nuevas ni cambios del contrato de ATTRACT. No se mantiene un historial
de exports ni se detectan ediciones externas a archivos de media o ROM que no guarden
la ficha. Si se elimina el ZIP local, el juego vuelve a pendientes.
