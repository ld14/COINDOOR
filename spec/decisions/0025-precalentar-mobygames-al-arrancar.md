---
id: 0025
title: Precalentar MobyGames al arrancar COINDOOR con una página de búsqueda en segundo plano
status: accepted
date: 2026-10-29
supersedes: null
superseded-by: null
tags: [backend, proceso]
---

# 0025 — Precalentar MobyGames al arrancar COINDOOR con una página de búsqueda en segundo plano

## Contexto

[`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md) trae MobyGames por scraping con
Scrapling. MobyGames está detrás de Cloudflare: a un pedido HTTP le responde 403, y el
navegador tiene que resolver un desafío antes de ver la página. Medido el 2026-10-29 en WSL,
ya con el arreglo de la feature 020 (`network_idle=False`, timeout de 60 s y perfil de
navegador persistente):

| Consulta | Tiempo |
|---|---|
| Primera, con desafío | 187 s y 198 s (dos intentos fallidos y el tercero lo resuelve) |
| Siguientes, con la cookie del perfil | 18 s y 21 s |

La cookie `cf_clearance` que deja el desafío vence en un año. La espera larga cae sobre la
primera consulta después de que el perfil está vacío o de que Cloudflare vuelve a pedir el
desafío (según fuentes de terceros, sobre todo al cambiar la IP). Esa primera consulta es un
alta de MS-DOS o un "Sugerir", con la persona esperando.

`constitution/tech-stack.md` dice:

> **Todo lo que sale a la red es a pedido del usuario.** Nada corre en segundo plano, ni al
> abrir una ficha, ni al guardar. **Única excepción:** la precarga de ArcadeDB al dar de alta
> un juego arcade.

y en §Límites duros: *"Sin trabajos en segundo plano, colas ni workers… reintroducirlos exige
un ADR."* [`ADR-0015`](0015-precarga-con-red-al-alta.md), que creó la primera excepción,
advierte que una segunda feature que quiera salir a la red sola debería reescribir la regla
de raíz en vez de acumular excepciones.

El dueño del producto pidió, después de que se le presentaran las alternativas de abajo, que
la espera se consuma al arrancar y que la excepción alcance solo a esta página.

## Decisión

**Al arrancar, COINDOOR baja una página de búsqueda de MobyGames en un hilo propio**, con el
mismo cliente y el mismo perfil de navegador que usan las consultas, para que el desafío de
Cloudflare ya esté resuelto cuando el usuario pida algo. La excepción queda acotada a esto:

1. **Una sola página** (`/search/?q=dos&type=game`), **un solo hilo**, **una vez por
   arranque**. No es una cola ni un worker: el hilo termina cuando baja la página.
2. **Un gate antes de cualquier pedido.** Solo sale a la red si hay Chromium instalado y algún
   sistema configurado tiene equivalencia en MobyGames según el catálogo de plataformas. Con
   solo arcade, no sale.
3. **No se repite si hubo un precalentamiento exitoso hace menos de 6 horas**, según una marca
   en el perfil. El modo desarrollo (`--reload`) reinicia el proceso en cada cambio de código.
4. **No demora ni rompe el arranque.** El hilo arranca y la aplicación sigue. Un fallo queda en
   el log y nada más.
5. **La misma política que cualquier consulta**: ritmo, cuota y perfil de a uno. Una consulta
   del usuario que llega durante el precalentamiento espera el perfil y después reusa la
   cookie.
6. **Se apaga** con `COINDOOR_SCRAPING_WARMUP=false` y **se cancela** al cerrar la aplicación.

`constitution/tech-stack.md` §Convenciones y §Límites duros se editan para nombrar esta
excepción. Todo lo demás sigue sin salir a la red sin pedido.

## Alternativas consideradas

### A. Dejarlo a pedido, apoyado en la cookie de un año

- A favor: no toca la constitución. Con el perfil persistente la espera es rara.
- En contra: la primera consulta después de un cambio de IP sigue esperando minutos, y cae
  justo cuando la persona pidió algo.
- **Descartada porque:** el dueño del producto quiere que el sistema esté listo al usarlo; esta
  opción se le presentó como recomendada y la descartó.

### B. Un botón "Preparar MobyGames" en Configuración

- A favor: respeta la regla al pie de la letra; el usuario decide cuándo.
- En contra: es un clic que nadie va a decidir no hacer, el mismo argumento que descartó el
  botón de [`ADR-0015`](0015-precarga-con-red-al-alta.md) (alternativa A). Además suma
  frontend.
- **Descartada porque:** el dueño del producto pidió que fuera automático.

### C. Reescribir la regla de raíz, como sugiere ADR-0015

- A favor: deja de acumular excepciones; la regla diría con qué condiciones cualquier feature
  puede salir a la red sola.
- En contra: abre la puerta a que otras features salgan a la red sin pedido, que es justo lo
  que la regla protege.
- **Descartada porque:** el dueño del producto limitó la excepción a esta página.

### D. Precalentar al abrir el formulario de alta de un juego MS-DOS

- A favor: solo sale a la red cuando hay intención de usar MobyGames.
- En contra: §Convenciones prohíbe salir a la red al abrir pantallas, y la espera seguiría
  cayendo mientras la persona trabaja.
- **Descartada porque:** ensancha la excepción a "abrir algo", que es más amplio que arrancar
  una vez, y no consume la espera antes de que se la necesite.

## Consecuencias

**Positivas**

- Si el precalentamiento terminó, la primera consulta de MobyGames tarda lo mismo que las
  siguientes (~20 s), aunque Cloudflare haya pedido un desafío nuevo.
- Una consulta que llega mientras el precalentamiento resuelve el desafío no paga un segundo
  desafío: espera el perfil y reusa la cookie.

**Coste asumido**

- Cada arranque, fuera de la ventana de 6 horas, hace un pedido a MobyGames y abre Chromium
  por unos segundos, o minutos si hay desafío, sin que el usuario lo pida. Es trabajo
  invisible salvo en el log.
- §Convenciones pasa a tener dos excepciones, contra la advertencia de ADR-0015. Es una
  decisión explícita del dueño del producto (2026-10-29).
- Con el precalentamiento en curso, la primera consulta de MobyGames espera a que termine; si
  el desafío tarda, esa espera se nota igual, aunque es una sola.

**Qué habría que revisar si esto se replantea**

- Si una tercera feature quiere salir a la red sola, hay que reescribir la regla de raíz
  (alternativa C) en vez de sumar otra excepción.
- Si MobyGames deja Cloudflare, si se pasa a la API oficial o si el desafío empieza a
  resolverse en segundos, el precalentamiento sobra y conviene borrarlo.
- Si el precalentamiento empieza a fallar seguido, el log lo va a mostrar y la consulta del
  usuario vuelve a pagar la espera: hay que revisar la versión de Scrapling antes de nada.

## Referencias

- [`ADR-0024`](0024-scrapling-y-mobygames-para-pc-dos.md): la fuente que obliga al desafío.
- [`ADR-0015`](0015-precarga-con-red-al-alta.md): la primera excepción y su advertencia.
- [`ADR-0010`](0010-jobs-en-proceso.md): trabajos en hilos del propio proceso.
- Feature [020](../features/020-scrapling-mobygames/plan.md), §Riesgos ("Alta más lenta") y
  §Lo verificado: la causa de la demora y las mediciones.
