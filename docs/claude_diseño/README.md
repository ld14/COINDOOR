# COINDOOR — Guía de implementación para Claude Code

Punto de entrada del paquete de especificación. Leer los cuatro documentos en este orden antes
de escribir código:

1. **`frontend-architecture.md`** — stack, estructura de carpetas, rutas, estado, jobs, errores.
2. **`design-system.md`** — paleta MS-DOS, tipografía, bordes 3D, botones, insignias, densidad.
3. **`data-model.md`** — tipos TypeScript, definiciones de campos, reglas de completitud,
   validación, máquinas de estado, contrato de API, datos de ejemplo.
4. **`screens-spec.md`** — las cinco pantallas, sección por sección, con los textos exactos.

La referencia visual viva es `COINDOOR.dc.html` en la raíz del proyecto: un prototipo funcional
de una sola pieza. Ante cualquier ambigüedad entre los documentos y el prototipo, **gana el
prototipo** para lo visual y **ganan los documentos** para la arquitectura.

---

## Orden de trabajo sugerido

**Fase 1 — Base**
Vite + React + TS + React Router. `tokens.css` y `reset.css`. Las primitivas de
`components/dos/` con una página de catálogo interna para verlas todas juntas.
El layout de `App.tsx`: barra de título, menú lateral, área hundida, barra de F-keys, banner.

**Fase 2 — Dominio y datos mock**
`types.ts`, `fieldDefs.ts`, `completeness.ts`, `validation.ts` con tests unitarios.
Un mock server (MSW) con el seed de `data-model.md` §7. Los diez juegos de ejemplo son
deliberados: cada uno ejercita un caso de borde distinto.

**Fase 3 — Pantallas de lectura**
Sistemas, lista de Juegos (con miniatura de portada, filtros, paginación) y la ficha en modo
solo lectura.

**Fase 4 — Edición**
Alta de juego (los dos pasos, con subir ROM vs. indicar ruta), carga y borrado de campos,
textos, presentación (swatches + HEX + detectar de la carátula), marcar como listo.

**Fase 5 — Asíncrono**
Modal de sugerencias con sus cuatro fases y la confirmación de reemplazo. Manuales múltiples con
procesamiento por job y cancelación. Búsqueda IA de revistas.

**Fase 6 — Exportación**
Buscador, lista paginada de exportables, ejecución de a un juego y veredicto de ATTRACT.

---

## Invariantes — no negociables

1. **Los obligatorios son exactamente cinco cosas**: los 7 campos de identidad, Carátula,
   Póster, Sinopsis y el color de acento. Nada más bloquea nunca.
2. **Error ≠ incompleto ≠ faltante.** Un error de formato bloquea el export; un campo requerido
   ausente bloquea "listo"; una revista rota no bloquea nada.
3. **La exportación es de a un juego por vez**, por el peso de los archivos.
4. **Un juego puede tener varios manuales**, cada uno con su propio estado y su propio job.
5. **Reemplazar contenido cargado a mano siempre pide confirmación.**
6. **La ruta del comando de lanzamiento debe ser absoluta** y el error se muestra mientras el
   usuario escribe: una ruta relativa falla en silencio en el gabinete.
7. **Cero `border-radius`, cero sombras difusas, cero transiciones** (salvo el spinner). Una
   sola fuente monoespaciada. Cian `#00AAAA` como único color de marca.
8. **Las barras azules de sección ocupan el 100% del ancho de la columna**, igual que el panel
   que las sigue.
9. **Los textos de la UI son los de `screens-spec.md`, literales.** Están escritos para explicar
   los estados intermedios del sistema; parafrasearlos pierde el punto.
10. **Sin librerías de componentes.** Todo control se escribe a mano con las primitivas DOS.

---

## Checklist de aceptación

- [ ] F2/F3/F4 navegan; `Esc` cierra el modal abierto.
- [ ] Los filtros de la lista y el buscador de export sobreviven al refresh (query string).
- [ ] La miniatura de portada aparece en la lista; sin carátula, caen las iniciales.
- [ ] Un sistema con ruta relativa se ve con borde rojo y `CABECERA INVÁLIDA`.
- [ ] Crear un sistema con ruta relativa es imposible; el error aparece al escribir.
- [ ] Alta de juego: el modo "Indicar ruta" muestra la nota de que el archivo no se copia.
- [ ] Un ROM de sistema con catálogo llega al paso 2 precargado y con la insignia `CATÁLOGO`.
- [ ] "Marcar como listo" en un juego incompleto lista exactamente los campos que faltan.
- [ ] Un juego con error de formato muestra el recuadro de errores aunque esté completo.
- [ ] Aplicar una sugerencia sobre un campo `manual` pide confirmación; sobre `empty`, no.
- [ ] El panel de sugerencias muestra "Tu archivo actual" primero cuando hay contenido.
- [ ] Se pueden adjuntar dos manuales y procesar solo uno; el otro queda `unprocessed`.
- [ ] Cancelar el procesamiento devuelve el manual a `unprocessed`, no lo borra.
- [ ] "Detectar de la carátula" queda deshabilitado si no hay carátula.
- [ ] Un HEX inválido muestra el error y no agrega el color.
- [ ] La búsqueda de revistas muestra el motivo por candidata y el botón dice
      "Descargar y guardar".
- [ ] Un juego con revista rota sigue siendo exportable.
- [ ] La pantalla de exportar solo lista juegos `ready` y exporta de a uno.
- [ ] El veredicto de rechazo nombra el archivo y el motivo concreto.
