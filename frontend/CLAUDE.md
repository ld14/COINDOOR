# Frontend

> **Sin código todavía.** El stack está decidido en `spec/constitution/frontend-architecture.md`
> y la estructura de abajo es la acordada. La crea la feature
> [003](../spec/features/003-base-frontend/spec.md).

Stack: React 18 + TypeScript `strict` + Vite + TanStack Query v5 + CSS Modules.

## Reglas

- Componentes en PascalCase, uno por archivo.
- Estado de servidor: TanStack Query. **NUNCA `useEffect` + `fetch` a mano.**
- Estado de UI: `useState` local + un único `AppContext`. No mezcles estado de servidor acá.
- Estilos: CSS Modules. **Prohibido Tailwind, prohibido CSS inline.**
- Colores, espaciado y tipografía: solo tokens de `styles/tokens.css`. **Nunca un hex ni un
  px literal** fuera de ese archivo.
- **Sin librerías de componentes** (MUI, shadcn, Chakra). Todo control se escribe a mano
  con las primitivas de `components/dos/`. Es un límite duro: cualquier librería moderna
  rompe los bordes 3D.
- **Cero `border-radius`, cero sombras difusas, cero transiciones** salvo el spinner.
- Renderizado condicional: un campo sin dato **nunca desaparece**. Muestra
  `"Sin Información"` (texto) o `"No Disponible"` (juegos, trucos, manuales).
- Las primitivas de `components/dos/` no conocen el dominio: reciben props y pintan.
- Los textos de la UI son los de `docs/claude_diseño/screens-spec.md`, **literales**.
- Los filtros viven en la query string, para sobrevivir al refresh.
- Actualización optimista solo en `setField` y `setAccent`. El resto espera la respuesta.
- Todo control interactivo es un elemento real. **Nunca `outline: none`.**
- Sin autenticación: sin login, sin token, sin interceptor de 401.
- Todo componente nuevo con lógica necesita test en Vitest + Testing Library.

## Estructura

```
frontend/src/
├── styles/         # tokens.css · reset.css
├── lib/domain/     # contract.json · fielddefs.json · types · completeness · validation
├── lib/api/        # client.ts + un módulo por recurso
├── components/dos/ # primitivas visuales, sin lógica de negocio
├── features/       # una carpeta por pantalla
└── hooks/
```

## Contexto ampliado

- Arquitectura: `spec/constitution/frontend-architecture.md` — sobre todo los **deltas D1–D5**
- Design system: `spec/constitution/design-system.md` y `docs/claude_diseño/design-system.md`
- Especificación de pantallas: `docs/claude_diseño/` — se consulta, no se edita
