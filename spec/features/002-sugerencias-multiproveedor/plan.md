# 002 · Sugerencias multiproveedor — Plan

## Enfoque

Un **orquestador** y N **proveedores** que no se conocen entre sí. El orquestador sabe qué
proveedores atienden cada campo, los lanza en paralelo, y devuelve lo que haya llegado.

La regla que ordena todo el diseño: **un proveedor es una fuente de fallas, no de
garantías.** modelos gratuitos con cupo variable y llamadas que tardan
treinta segundos. El sistema se diseña asumiendo que en cada búsqueda alguno va a fallar, y
que eso es normal y no se muestra. El scraping HTML queda fuera del plan: si no hay API o
modelo usable, el candidato será `referencia` o carga manual.

## El contrato del proveedor

```python
class Proveedor(Protocol):
    nombre: str                  # "ScreenScraper" — se muestra en cada candidato
    campos: frozenset[str]       # qué campos sabe resolver
    timeout: float               # guardia de liveness, no presupuesto de latencia:
                                 # generoso, y más alto todavía para los de IA
    limite: Limite               # ritmo, cupo diario y cortesía. Ver §Límite propio

    def buscar(self, consulta: Consulta) -> list[Candidato]: ...
```

```python
@dataclass(frozen=True)
class Consulta:
    titulo: str
    sistema: str
    anio: str | None
    hashes: Hashes | None   # crc32/md5/sha1 del ROM, si se pudo calcular

@dataclass(frozen=True)
class Candidato:
    id: str
    nombre: str
    fuente: str
    clase: Literal["aplicable", "referencia"]
    preview_url: str | None   # miniatura o primeras líneas
    origen_url: str | None    # a dónde lleva si es referencia
    generado_por_ia: bool = False
```

Agregar una fuente es una clase nueva y una fila en la tabla de prioridad. Nada más se toca.

## Los proveedores

```text
lib/providers/
  base.py                    # Protocol + Consulta + Candidato + Limite
  registro.py                # tabla campo → [proveedores, en orden]
  orquestador.py
  http.py                    # reintentos, backoff, Retry-After, ritmo y cupo
  cortocircuito.py
  ia/
    generador.py             # modelos gratuitos para textos y candidatos no autoritativos
    prompts/
      sinopsis.v1.md
      resena.v1.md
      trucos.v1.md
  referencia/
    youtube.py               # SOLO referencias
```

No hay `scrape/` ni sustituto basado en HTML: COINDOOR no parsea ScreenScraper, MobyGames
ni sitios de terceros. La información que antes se pensaba obtener por scraping pasa a
salir del proveedor de IA, marcada como IA y nunca usada para identidad.

## Decisiones

### El prompt de IA es un artefacto versionado, no una constante

El objetivo de generar sinopsis y reseñas con IA no es exactitud enciclopédica: es que los
200 juegos de la colección **se lean con la misma voz**. Eso solo se sostiene si el prompt
no se mueve.

- Vive en `ia/prompts/<campo>.vN.md`, en el repo.
- **Nunca se edita en su lugar.** Cambiarlo es un archivo `.v2`, igual que con los ADRs.
- Se guarda **junto a cada texto** qué prompt y qué modelo lo produjeron. Dato interno, no
  se exporta ([`ADR-0002`](../../decisions/0002-procedencia-interna.md)).

Sin ese registro, regenerar una sinopsis dos años después la devuelve escrita distinto y la
colección se convierte en un collage de voces.

### Se espera a todos, y se devuelve una sola vez

Nada de resultados incrementales. El orquestador lanza los proveedores en paralelo, espera a
que terminen todos, y devuelve la lista completa con `respondieron / consultados`.

**La latencia no es un problema de este producto** (`tech-stack.md` §Convenciones): las
búsquedas son a pedido, de a un campo por vez, con una persona esperando el resultado que
pidió. Poblar la grilla de a poco optimizaría segundos que a nadie le importan, a cambio de
respuesta incremental, una grilla que se repuebla sola y un estado intermedio que el usuario
tiene que interpretar.

Los timeouts por proveedor **se quedan, con otro propósito**: que una conexión colgada
termine alguna vez. Son generosos —decenas de segundos, no unos pocos— y una llamada a un
modelo puede tardar treinta sin que eso sea un problema.

El conteo sí importa, y no por velocidad: con seis fuentes, tres resultados puede significar
que el juego es oscuro o que la mitad se cayó, y sin el número no hay forma de saber si
conviene reintentar.

### Las sugerencias son un job, como los manuales y el export

El diseño ya tiene el patrón (`POST` → `jobId` → polling → `DELETE` cancela) y lo usa para
procesar manuales, exportar y buscar revistas. Las sugerencias entran ahí en vez de inventar
un cuarto mecanismo.

Justamente porque las búsquedas pueden ser largas, un request sincrónico sería frágil:
navegadores y proxies cortan solos, no hay forma de cancelar, y un refresh pierde el
trabajo. El job resuelve las tres cosas.

Esto no rompe el límite duro de "sin colas ni workers" de `tech-stack.md`: son tareas
acotadas y en proceso, no infraestructura de procesamiento.

### Tres capas distintas: reintento, límite propio y cortocircuito

Se confunden fácil y resuelven cosas diferentes:

| Capa | Contra qué protege | Alcance |
| --- | --- | --- |
| **Reintento** | Un fallo pasajero: timeout, corte de conexión, 5xx, 429 | Una llamada |
| **Límite propio** | Que nos baneen o que se agote la cuota | Todas las llamadas a ese proveedor |
| **Cortocircuito** | Una fuente que está muerta de verdad | El resto de la sesión |

#### Reintento: lo que importa es qué **no** se reintenta

```text
Se reintenta:     timeout · error de conexión · 5xx · 429
No se reintenta:  401/403 (credenciales) · 404 · sin resultados · HTML que no parsea
```

**"Este juego no está en ScreenScraper" es una respuesta válida, no una falla.**
Reintentarla tres veces devuelve lo mismo tres veces y gasta el triple de cuota. Es el error
más caro de esta parte del sistema y el más fácil de cometer.

Backoff exponencial con jitter y hasta tres intentos: 1 s, 4 s, 16 s. Podemos permitirnos
esperas largas porque la latencia no es un problema acá.

**Si el servidor manda `Retry-After`, se obedece eso y no nuestro backoff.** Un 429 con
`Retry-After: 60` significa exactamente eso; insistir antes es lo que convierte un límite
temporal en un baneo.

#### Límite propio: son dos cosas, ritmo y cupo

```python
@dataclass(frozen=True)
class Limite:
    por_segundo: float | None   # ritmo sostenido
    por_dia: int | None         # cupo diario de la cuenta
    espera_min: float = 0.0     # cortesía entre llamadas al mismo dominio
```

Cada proveedor declara el suyo como **dato**; el orquestador lo aplica. Un token bucket para
el ritmo, un contador persistente para el cupo diario.

- Los modelos gratuitos tienen sobre todo **cupo diario o mensual**, y pueden cambiarlo sin
  aviso.
- Las fuentes `referencia/` no descargan ni parsean HTML: devuelven enlaces o pistas para que
  el usuario consiga el material y lo suba a mano.
- ScreenScraper y MobyGames quedan fuera del camino principal. Si algún día vuelven por API
  oficial, requieren verificación de términos/cuotas y una decisión explícita antes de
  escribir código.

**Agotar el cupo no es una falla que se reintente.** Es un "volvé mañana": el proveedor
queda fuera hasta que resetee, y la pantalla lo dice con esas palabras. Confundirlo con "sin
resultados" hace que cargues a mano algo que mañana estaría disponible.

#### Cómo se componen, que es donde está la trampa

**El cortocircuito cuenta reintentos agotados, no intentos sueltos.** Si contara intentos,
una sola búsqueda con tres reintentos dispararía un cortocircuito de dos strikes al
instante, y una fuente perfectamente sana quedaría fuera de la sesión por un hipo de red.

Con eso: dos búsquedas que agotan sus reintentos y recién ahí el proveedor queda fuera.

**Cancelar interrumpe el backoff.** Si el usuario cierra el modal durante una espera de
16 s, el job termina ahí. Un `DELETE /jobs/:jobId` que hay que esperar no cancela nada.

**La política vive en un solo lugar**, un envoltorio del cliente HTTP. Cada proveedor
declara sus límites; ninguno implementa reintentos por su cuenta. Seis implementaciones de
backoff es exactamente la clase de duplicación que después nadie corrige.

### Por qué el cortocircuito sigue haciendo falta

Con timeouts generosos y tres reintentos, una fuente muerta cuesta hasta un minuto en
**cada** campo de **cada** juego. Cargar cincuenta campos en una sesión son casi cincuenta
minutos de espera pura por algo que nunca va a responder.

### Caché por sesión

Clave `(set, campo)`. ScreenScraper y MobyGames tienen cuota diaria, y volver a abrir el
mismo modal no debería gastarla. Se invalida al reintentar explícitamente.

### Sin identidad por IA

La IA puede proponer textos, trucos y pistas de búsqueda. No decide identidad, año, sistema ni
campos que el contrato use como identificadores. Esos datos quedan en MAME para arcade o en
la persona que carga el juego, como ya exige
[`ADR-0004`](../../decisions/0004-coindoor-fuente-identidad-no-mame.md).

## Implementación

1. `lib/providers/base.py` — el `Protocol`, `Consulta`, `Candidato`.
2. `lib/providers/registro.py` — tabla `campo → [proveedor, …]` en orden de prioridad. Es
   **datos, no `if`s**: sumar una fuente es una fila.
3. `lib/providers/http.py` — el envoltorio con la política: reintentos según la
   clasificación del error, backoff con jitter, `Retry-After`, token bucket de ritmo y
   contador persistente de cupo. **Antes que cualquier proveedor**: si esto llega después,
   cada uno ya trae su propio reintento a mano.
4. `lib/providers/orquestador.py` — fan-out con timeout individual, aislamiento de fallas,
   cortocircuito sobre reintentos agotados, caché y conteo.
5. `lib/providers/ia/generador.py` + los prompts `.v1` como primer proveedor real: valida
   el contrato contra el camino principal nuevo, no contra ScreenScraper ni MobyGames.
6. `lib/providers/referencia/` para enlaces que el usuario aplica a mano.
7. API:

   ```text
   POST   /games/:id/suggestions/:key        → { jobId }
   GET    /jobs/:jobId                       → { status,
                                                 candidatos: [...],   # completos, al final
                                                 respondieron: 3, consultados: 6 }
   DELETE /jobs/:jobId
   POST   /games/:id/fields/:key/apply-suggestion { candidateId }   → Game
   ```
   `apply-suggestion` rechaza un candidato de clase `referencia`: no hay nada que aplicar.

## Riesgos

- **Un candidato de IA se ve igual que uno de catálogo.** Sobre todo la reseña: un
  `GRÁFICOS: 85` inventado se ve en el gabinete idéntico a una nota real de una revista de
  la época. El marcado en pantalla es la única barrera antes de que el número quede fijo.
- **El cortocircuito puede esconder una caída permanente.** Si una fuente muere para
  siempre, el usuario solo ve que aparecen menos resultados. El conteo
  `respondieron / consultados` es lo único que lo hace visible.
- **El contador de cupo tiene que sobrevivir al reinicio de la app.** Si vive en memoria,
  reiniciar lo pone en cero y volvemos a pegarle a un proveedor que ya nos cortó. Va
  persistido, con la fecha de reseteo.
- **Los modelos gratuitos pueden cambiar límites o desaparecer.** El respaldo y el salto
  limpio del proveedor son parte del diseño, no optimización futura.
- **Una respuesta inválida de IA se puede ver convincente.** Tiene que fallar explícito,
  nunca convertirse en candidato con datos basura.
