# 014 · Tareas

- [x] Calcular y exponer estado de exportación; filtrar antes de paginar.
- [x] Publicar ZIP atómico con fecha de inicio y conservar el anterior ante errores.
- [x] Filtros URL, etiquetas, paginación e invalidación del listado en frontend.
- [x] Mocks y pruebas de backend/frontend; build y lint de backend.
- [x] Actualizar roadmap y cerrar criterios de aceptación.

Validación: 263 tests de pytest, 9 tests de pantallas de lectura y build TypeScript/Vite
exitosos. Ruff limpio en módulos modificados; en `test_api.py` se excluyó E501 por
líneas largas preexistentes. Se actualizó una expectativa vieja del dashboard al texto
actual «pendiente(s)».
