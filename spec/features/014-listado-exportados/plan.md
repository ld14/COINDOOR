# 014 · Plan

1. Calcular `exportStatus: pending | exported` al listar, con el ZIP en
   `data_dir/exports/<safe_id>.coindoor.zip` y el `game.json` que localiza GamesStore.
   Verificar estructura ZIP con `zipfile.is_zipfile` y comparar `st_mtime_ns`.
   No persistir un nuevo estado en el juego ni modificar la completitud.
2. Publicar el ZIP con temporal en el mismo directorio, fsync y reemplazo atómico.
   Fecharlo al inicio del export (antes de releer las fichas), de modo que una edición
   durante el trabajo quede pendiente. Para ZIP antiguos se usa su fecha existente.
3. API: parámetro `exportStatus` validado y filtro antes de calcular total/paginar.
4. Frontend: botones de filtro con `aria-pressed`, query string, etiqueta en las filas,
   controles de paginación e invalidación de `['games']` tras exportar con éxito.
   Reutilizar primitivas y CSS existentes. Actualizar mocks.
5. Tests de API (export, edición, reinicio, filtros y paginación), fallo de empaquetado
   y UI (filtro desde URL, navegación, etiquetas). Ejecutar pytest, Vitest y build.
