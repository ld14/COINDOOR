# 006 · Pantallas de lectura

**Estado:** implementada

## Qué hace

Recibe el frontend base de la feature [003](../003-base-frontend/spec.md), el dominio/mock de
la feature [004](../004-dominio-y-contrato/spec.md) y la API real de la feature
[005](../005-esqueleto-backend/spec.md). Produce las pantallas de solo lectura: `/sistemas`,
`/juegos` y `/juegos/:gameId`, mostrando sistemas, lista filtrable de juegos y ficha completa
sin modificar datos.

Quedan fuera la creación y edición de juegos —feature [007](../007-edicion/spec.md)—, las
sugerencias —feature [002](../002-sugerencias-multiproveedor/spec.md)— y exportar bundles
—feature [001](../001-export-bundle/spec.md).

## Por qué

Desbloquea navegar la colección real antes de tocar datos. Es el paso mínimo para ver qué falta,
validar estados `ready | incomplete | error` y confirmar que el backend local reemplaza al mock
sin cambiar reglas de dominio.

## Criterios de aceptación

- [ ] Dado el backend con sistemas y juegos, cuando se abre `/sistemas`, entonces se muestran
      tarjetas con nombre, shortName, cantidad de juegos, `launchCmd` y estado inválido si aplica.
- [ ] Dado `/juegos`, cuando se filtra por texto, sistema o estado, entonces la URL conserva esos
      filtros en query string y refresh mantiene la vista.
- [ ] Dado un juego sin carátula, cuando aparece en la lista, entonces se muestra placeholder y no
      se rompe la fila.
- [ ] Dado `/juegos/:gameId`, cuando el juego tiene campos vacíos, entonces todas las secciones
      siguen visibles con `Sin Información` o `No Disponible` según corresponda.
- [ ] Dado un `gameId` inexistente, cuando se abre la ficha, entonces se muestra error explícito y
      navegación de vuelta a `/juegos`, no pantalla en blanco.
- [ ] Dado un juego con `errors`, cuando se abre la ficha, entonces se muestran los errores de
      formato como bloqueantes de export.

## Fuera de alcance

- Alta, edición, carga/borrado de media y `mark-ready` — feature [007](../007-edicion/spec.md).
- Modal de sugerencias y aplicación de candidatos — feature [002](../002-sugerencias-multiproveedor/spec.md).
- Panel “Qué incluir” y generación de `.zip` — feature [001](../001-export-bundle/spec.md).
- Procesamiento de manuales PDF y detección de acento desde imagen.
