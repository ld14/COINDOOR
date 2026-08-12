---
id: 0009
title: Correr como un proceso local en loopback, que sustituye a la autenticación
status: accepted
date: 2026-08-11
supersedes: null
superseded-by: null
tags: [infra, backend]
---

# 0009 — Correr como un proceso local en loopback, que sustituye a la autenticación

## Contexto

`tech-stack.md` §Límites duros: **«Sin autenticación, usuarios, roles ni permisos. Un
solo usuario, su máquina.»** Y UX §2 lo repite desde el lado del producto.

Eso resuelve qué **no** se construye, pero deja abierto algo que ningún documento define:
**dónde corre COINDOOR y cómo se lo alcanza**. Y esa pregunta no es de despliegue, es de
seguridad, porque sin autenticación la aplicación no tiene ninguna frontera propia.

El riesgo es concreto y no hipotético. La API:

- Acepta **rutas absolutas arbitrarias** del disco (`romSource: 'path'`, y el requisito
  explícito de no copiar el archivo).
- **Ejecuta subprocesos** (`mame -listxml`, `attract doctor`).
- Escribe en el directorio de datos del usuario.

Si el proceso escucha donde cualquiera puede alcanzarlo, eso es lectura arbitraria de
archivos y ejecución de procesos, sin nada que lo impida.

Además hay tres cosas del producto que atan la ejecución a la máquina del usuario: leer
ROMs por ruta, ejecutar el `mame` del host y ejecutar el `attract` del host.

## Decisión

**COINDOOR es un solo proceso que corre en la máquina del usuario y escucha en
`127.0.0.1`.** Ese bind, y no un mecanismo de la aplicación, es la frontera de seguridad
que reemplaza a la autenticación.

El proceso sirve las dos cosas desde el **mismo origen**:

```
GET /api/*     → los routers
GET /media/*   → estáticos del directorio de datos
GET /*         → frontend/dist (build de Vite), con fallback a index.html
```

Servir el frontend desde el backend no es comodidad: es lo que hace que el origen sea uno
solo y saca CORS de la ecuación.

**Tres mitigaciones, y hacen falta las tres:**

1. Bind a `127.0.0.1`, **nunca** a `0.0.0.0`. Contra el acceso desde la red local.
2. Sin CORS permisivo. Mismo origen en producción; en desarrollo, solo el origen de Vite.
   Contra que un sitio remoto **lea** las respuestas.
3. **Validar el header `Host`** contra `127.0.0.1` / `localhost`. Contra **DNS
   rebinding**, que es precisamente lo que sortea el bind a loopback.

Sin la tercera, las dos primeras no alcanzan.

**No se empaqueta en un contenedor ni en una aplicación de escritorio.** Se arranca con
un comando.

## Alternativas consideradas

### A. Empaquetar en Docker

- A favor: instalación reproducible, dependencias aisladas, una forma estándar de
  distribuir.
- En contra: rompe las tres cosas que el producto necesita — leer ROMs por ruta absoluta
  arbitraria, ejecutar el `mame` del host y ejecutar el `attract` del host.
- **Descartada porque:** habría que montar el disco del usuario como volumen y exponer
  dos binarios del host dentro del contenedor. El resultado es más frágil que no usarlo,
  y para una aplicación que corre en una máquina y no se despliega en ningún lado, no
  compra nada. Si algún día hay que distribuir, la respuesta es un ejecutable, no un
  contenedor.

### B. Empaquetar como aplicación de escritorio (Electron, Tauri)

- A favor: doble clic para abrir, sin pedirle al usuario que instale Python. Ventana
  propia en vez de una pestaña del navegador.
- En contra: agrega un runtime, un proceso de build y una cadena de firma por plataforma,
  para un problema —la distribución— que hoy no existe.
- **Descartada por ahora, no descartada del todo:** el usuario es una persona que ya usa
  una CLI y sabe correr un comando. Empaquetar resuelve el día que COINDOOR salga de esa
  máquina, y ese día todavía no llegó. Cuando llegue, esta alternativa vuelve — y arrastra
  también la licencia AGPL de `pymupdf`, que hoy no importa.

### C. Servir el frontend por separado, en su propio puerto, también en producción

- A favor: simetría con el entorno de desarrollo, un solo modo de arranque.
- En contra: dos orígenes, o sea CORS obligatorio y permanente.
- **Descartada porque:** convierte una configuración de desarrollo en superficie de
  ataque permanente. Con un solo origen, la política de CORS más segura —no tener— es
  también la más simple.

### D. Escuchar en `0.0.0.0` para poder usarlo desde otra máquina de la casa

- A favor: cargar juegos desde la laptop mientras el proceso corre en otra máquina.
- En contra: expone una API sin autenticación, con lectura de archivos arbitraria y
  ejecución de subprocesos, a toda la red local.
- **Descartada porque:** es incompatible con el límite duro de no tener autenticación. Si
  el acceso remoto se volviera necesario, primero hay que decidir la autenticación, y eso
  es un cambio de misión, no una opción de configuración.

## Consecuencias

**Positivas**

- La frontera de seguridad es una sola cosa, comprobable y fácil de auditar.
- Un solo origen elimina CORS del modelo de seguridad en lugar de configurarlo.
- El backend puede leer cualquier ruta y ejecutar los binarios del usuario sin que eso
  sea un agujero, porque el usuario y el atacante potencial no son la misma persona.
- Cero infraestructura: no hay nada que desplegar, monitorear ni respaldar más allá del
  directorio de datos.

**Coste asumido**

- La instalación es manual: el usuario necesita Python y correr un comando.
- No se puede usar desde otra máquina, ni desde el teléfono.
- **Las tres mitigaciones tienen que estar las tres.** Es la clase de detalle que se
  omite por parecer redundante, y el que falta —la validación de `Host`— es el menos
  obvio.

**Qué habría que revisar si esto se replantea**

- Si COINDOOR se distribuye a otras personas: aparece el empaquetado (alternativa B) y
  con él la licencia de `pymupdf` y la política de secretos.
- Si aparece la necesidad de usarlo desde otra máquina: primero autenticación, y eso es
  un cambio de misión.

## Referencias

- `spec/constitution/tech-stack.md` §Límites duros — sin autenticación.
- `docs/ux/requerimiento-funcional.md` §2, §6 — un usuario, escritorio, sesiones largas.
- `docs/claude_diseño/data-model.md` §1 — `RomSource = 'upload' | 'path'`.
- [`ADR-0004`](0004-coindoor-fuente-identidad-no-mame.md) — la dependencia opcional del binario `mame`.
- [`ADR-0012`](0012-verificacion-attract-por-subproceso.md) — la dependencia opcional del binario `attract`.
