---
id: 0015
title: Permitir una precarga con red al dar de alta un juego
status: accepted
date: 2026-08-24
supersedes: null
superseded-by: null
tags: [backend, proceso]
---

# 0015 — Permitir una precarga con red al dar de alta un juego

## Contexto

`constitution/tech-stack.md` §Convenciones dice, en presente y sin excepciones:

> **Todo lo que sale a la red es a pedido del usuario.** Nada corre en segundo plano, ni al
> abrir una ficha, ni al guardar.

La regla nació para proteger dos cosas: que la aplicación funcione offline salvo cuando el
usuario pide una sugerencia, y que no haya trabajo invisible consumiendo cuotas de terceros.

La feature [008](../features/008-arcadedb/spec.md) necesita romperla. Con
[`ADR-0014`](0014-arcadedb-fuente-arcade.md), una sola consulta a ArcadeDB llena una ficha
arcade entera: identidad, cinco imágenes, video, sinopsis, trucos, manual y gabinete. Obligar
a apretar "Sugerir" trece veces seguidas, con su modal y su confirmación cada una, para
aplicar lo que ya vino en la misma respuesta, es fricción sin ninguna contrapartida.

## Decisión

**Crear un juego dispara una precarga contra ArcadeDB, sin que el usuario apriete nada.** La
excepción a §Convenciones queda acotada a esto y a nada más:

1. **Un endpoint con nombre propio**, `POST /api/games/{game_id}/arcadedb`, no un efecto lateral escondido dentro de `POST /api/games`. El alta sigue siendo sincrónica y sin red.
2. **Un juego por vez.** Sigue sin haber carga masiva.
3. **Escribe solo campos vacíos.** La regla *"un campo con procedencia manual no se reemplaza sin confirmación explícita"* **no se enmienda**: lo que el usuario tipeó en el alta queda intacto y aparece como candidato en el modal.
4. **Corre como job cancelable**, con el mismo patrón de `lib/jobs/` que ya usan sugerencias, manuales, export y revistas. El usuario ve progreso y puede cortarlo.
5. **No encontrar el juego no es un error.** El job termina `succeeded` con `estado: "no-encontrado"`.
6. **Un gate por sistema antes de cualquier petición.** Si el sistema no es arcade, la precarga termina sin tocar la red.

`constitution/tech-stack.md` §Convenciones se edita para nombrar la excepción. Todo lo demás
—abrir una ficha, guardar un campo, listar juegos, exportar— sigue sin salir a la red.

## Alternativas consideradas

### A. Un botón "Buscar en ArcadeDB" en el formulario de alta

- A favor: no toca la constitución. El usuario ve qué encontró antes de confirmar, y la regla de "a pedido del usuario" queda literalmente intacta.
- En contra: el botón no tiene ninguna decisión real detrás. Nadie va a crear un juego arcade y elegir *no* traer su carátula. Es un clic ceremonial que existe solo para satisfacer la letra de una regla.
- **Descartada porque:** el dueño del producto pidió explícitamente que fuera automático, después de que se le presentara esta alternativa como opción recomendada. La regla protege contra trabajo invisible; una precarga con banner, progreso y botón de cancelar no es invisible.

### B. Hacer la precarga dentro de `POST /api/games`

- A favor: un solo viaje. El juego nace completo, sin endpoint nuevo ni estado intermedio en la interfaz.
- En contra: convierte el alta en una petición de 20 a 40 segundos —dos JSON, cinco imágenes, un MP4 y un PDF— sin progreso, sin cancelación y sin forma de distinguir "falló crear el juego" de "falló ArcadeDB". Además, en el camino de subida de ROM, `romRef` todavía es el nombre del archivo y no su ruta final, así que ni siquiera habría romset del que partir.
- **Descartada porque:** rompe el contrato del endpoint de creación y deja al usuario sin salida durante medio minuto. El segundo motivo es además un impedimento técnico duro, no una preferencia.

### C. Precargar al abrir la ficha por primera vez

- A favor: no toca el alta y aprovecha que el usuario ya está mirando el juego.
- En contra: §Convenciones prohíbe explícitamente salir a la red "al abrir una ficha". Y abrir una ficha es una acción repetible: habría que llevar registro de si ya se precargó, o pegarle a ArcadeDB en cada visita.
- **Descartada porque:** enmendar la parte de la regla que habla de abrir fichas es mucho más ancho que enmendar el alta. Un juego se crea una vez; una ficha se abre cien.

## Consecuencias

**Positivas**

- Crear un juego arcade y tener la ficha llena es una sola acción.
- La excepción queda escrita y acotada a un endpoint que se puede nombrar, no a "crear un juego a veces toca la red".
- El mismo endpoint sirve, con `force=true`, para un botón "Traer de ArcadeDB" en la ficha: reprocesar un juego ya cargado no necesita mecanismo nuevo.
- Cargar, editar y exportar siguen funcionando sin internet. El límite duro de la constitución sobre eso no se toca.

**Coste asumido**

- §Convenciones deja de ser absoluta y pasa a tener una excepción. Cualquier feature futura que quiera salir a la red sola va a citar este ADR como precedente; la respuesta por defecto sigue siendo no, y estos seis límites son la vara.
- Un alta de un juego arcade descarga entre 8 y 10 MB sin preguntar. Aceptable en una aplicación de escritorio de un solo usuario; no lo sería con carga masiva, que es un límite duro aparte.
- Si ArcadeDB está caído, crear un juego muestra un job fallido que no tiene nada que ver con el alta, que sí funcionó. La interfaz tiene que distinguirlo con claridad.

**Qué habría que revisar si esto se replantea**

- Si aparece una segunda feature que quiera salir a la red sin pedido explícito, no alcanza con citar este ADR: la regla habría que reescribirla de raíz en vez de acumular excepciones.
- Si alguna vez se soporta carga masiva —hoy prohibida por §Límites duros—, esta precarga automática pasa a ser un problema de cuota y hay que volver al modelo del botón.

## Referencias

- Feature [008-arcadedb](../features/008-arcadedb/spec.md)
- [`ADR-0014`](0014-arcadedb-fuente-arcade.md) — la fuente que hace valer la pena la excepción
- [`ADR-0010`](0010-jobs-en-proceso.md) — el patrón de jobs que usa la precarga
- `constitution/tech-stack.md` §Convenciones — la regla enmendada
