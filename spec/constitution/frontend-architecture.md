# Arquitectura de frontend

> **La especificación completa vive en [`docs/claude_diseño/`](../../docs/claude_diseño/README.md)**
> y es la fuente de consulta. Este documento no la copia: fija lo que es constitucional
> —lo que una feature no puede cambiar sola— y anota dónde choca con el contrato de ATTRACT.

## Stack

| Capa | Elección |
|---|---|
| Build | Vite |
| Lenguaje | TypeScript `strict` |
| UI | React 18, componentes de función |
| Estado servidor | TanStack Query v5 |
| Estado UI | `useState` local + un único `AppContext` |
| Router | React Router v6 |
| Formularios | react-hook-form + zod |
| Estilos | CSS Modules + `tokens.css` |
| Tests | Vitest + Testing Library |

**Sin librerías de componentes** (MUI, shadcn, Chakra, Tailwind). Todo control se escribe
a mano con las primitivas de `components/dos/`. Es un límite duro, no una preferencia:
cualquier librería moderna rompe el look.

Detalle de carpetas, query keys, invalidaciones y hooks: `frontend-architecture.md` del
paquete de diseño.

## Las cinco pantallas

| Ruta | Pantalla |
|---|---|
| `/sistemas` | Sistemas / plataformas |
| `/juegos` | Lista de juegos (default) |
| `/juegos/nuevo` | Alta de un juego, dos pasos |
| `/juegos/:gameId` | Ficha del juego |
| `/exportar` | Exportar |

Filtros y buscadores viven en la query string, para que la vista sobreviva al refresh.

## Reglas de dominio en el cliente

`lib/domain/completeness.ts` decide el estado de un juego con **prioridad fija**:

1. `game.errors.length > 0` → `error` (formato del contrato ATTRACT; bloquea el export)
2. `missingRequired(game).length > 0` → `incomplete` (bloquea "marcar como listo")
3. si no → `ready`

Los tres estados no son intercambiables y el diseño los pinta distinto a propósito. Ver
`tech-stack.md` §Dos ejes de estado: `error` es el eje VÁLIDA de ATTRACT, `incomplete` es
el eje COMPLETA de COINDOOR.

### Jobs asíncronos

Procesar un manual y exportar son trabajos largos: `POST` devuelve `jobId`, el hook hace
polling de `GET /jobs/:jobId` cada 500 ms, `DELETE /jobs/:jobId` cancela. **El progreso
que se muestra es el del job, nunca un timer del cliente.**

Esto no contradice el límite duro de "sin colas ni workers" de `tech-stack.md`: son dos
trabajos concretos y acotados, no una infraestructura de procesamiento general.

## Deltas sobre el paquete de diseño

`docs/claude_diseño/` se consulta y no se edita. Estas tres correcciones **mandan sobre
él** porque el contrato de ATTRACT no admite lo que el diseño propone.

### D1 · `resena` y `trucos` no son texto

El diseño los modela como `TextField { value: string }`. El contrato los define
estructurados y el export no puede producirlos desde un `<textarea>`.

```ts
export type ReviewCat =
  | 'originalidad' | 'graficos' | 'adiccion' | 'sonido' | 'dificultad' | 'animacion';

export interface ReviewField {
  status: FieldStatus;
  source?: string;
  score: number | null;                        // 0..100. null = no hay reseña
  cats: Partial<Record<ReviewCat, number>>;    // PARCIAL a propósito: 0..100 cada una
}

export interface CheatEntry { name: string; input: string }
export interface CheatGroup { name: string; entries: CheatEntry[] }   // nombre libre
export interface CheatsField { status: FieldStatus; source?: string; groups: CheatGroup[] }
```

`texts` queda solo con `sinopsis`. `review` y `cheats` pasan a ser campos propios de `Game`.

**Delta de UI — `screens-spec.md` §5.7.** La sección TEXTOS deja de ser tres textareas:

- **Sinopsis** — sigue igual, `<textarea>`.
- **Reseña** — nota global 0–100 y seis filas de categoría. **Una categoría vacía es un
  valor legítimo**, no un pendiente: en el gabinete muestra `-` y las demás se ven normal.
  Distinguir en pantalla "no hay reseña" (`score === null`, el bloque entero dice *Sin
  Información*) de "hay reseña con categorías incompletas".
- **Trucos** — editor de grupos. Agregar, renombrar y ordenar grupos; agregar y ordenar
  entradas `nombre` + `cómo se hace` dentro de cada uno. Los nombres de grupo **no salen
  de una lista cerrada** (`combos`, `codes`, `secretos`, `dos_jugadores`… los inventa el
  usuario). Los `input` llevan símbolos de dirección y botones (`←`, `↓`, `↘`,
  `[ATAQUE]`): hay que resolver cómo se escriben sin pelear con el teclado.

Completitud sin cambios: los dos siguen siendo **opcionales**.

### D2 · Hay dos colores de acento, no uno

El contrato lleva `accent` y `accent2` (ADR-0013 de ATTRACT) y `goldnaxe` usa los dos.

```ts
accent: FieldStatus;
accentValue: string;    // primario
accent2Value: string;   // secundario; "" si no se definió
```

**Delta de UI — `screens-spec.md` §5.8.** La sección PRESENTACIÓN pasa a tener dos filas de
color, primario y secundario, cada una con sus swatches y su input HEX. `Detectar de la
carátula` devuelve **los dos** colores en una pasada:

```
POST /games/:id/accent/detect  →  { color: "#RRGGBB", color2: "#RRGGBB" }
```

`PATCH /games/:id` acepta además `accent2Value`.

**Solo el primario es obligatorio.** El secundario queda opcional: pedir dos colores a mano
por juego es fricción que no paga, y `detectar de la carátula` lo llena gratis cuando hay
carátula.

### D3 · Revistas: solo búsqueda y sugerencia, nunca descarga

La feature de revistas se implementa, pero **acotada**: la IA busca en qué revistas de la
época pudo haber notas sobre el juego y lo sugiere. COINDOOR **no descarga ni guarda
revistas**. Digitalizarlas es otro subsistema (ADR-0009 de ATTRACT separa producir de
consumir, y guardar en `_magazines/` cae del lado de producir).

Lo que COINDOOR guarda es la **referencia**, y es **dato interno**: sirve para buscar la
revista más adelante, no para el gabinete. **No se exporta** — el `data.json` del bundle
sale sin `mags[]` ([`ADR-0003`](../decisions/0003-bundle-por-juego.md)). Una referencia que
viajara apuntaría a una revista que el receptor casi nunca tiene.

**Delta de UI — `screens-spec.md` §5.10 y §5.12:**

- El botón `Descargar y guardar` pasa a ser **`Vincular`**. No baja nada.
- `POST /games/:id/magazines/:magazineId/download-and-link` pasa a
  `POST /games/:id/magazines/:magazineId/link`.
- El texto "sugerirlas para descargar y guardar" pasa a decir que se registra la
  referencia, no que se obtiene la revista.

**El estado `broken` desaparece.** El diseño lo trata como anomalía —un juego del seed lo
ejercita, pintado en ámbar como "vínculo roto"— pero si la referencia nunca se exporta, no
hay nada que pueda romperse: es una anotación privada, no un vínculo al repositorio.

| Situación | Cómo se ve |
|---|---|
| Sin buscar | "No vinculada" + `Buscar con IA` |
| Con referencia guardada | La revista y el número, como pista para conseguirla después |

Nunca en rojo ni en ámbar, y nunca "faltante": no bloquea nada, no viaja a ningún lado y no
hay acción pendiente. El seed necesita otro caso de borde en lugar de "Contra · vínculo
roto".

### D4 · El export produce un archivo, no una escritura

`screens-spec.md` §6 y el prototipo describen el export como *"COINDOOR arma su estructura
de archivos; ATTRACT la verifica"*, y van del botón `Exportar` directo a `Armando`. Bajo
[`ADR-0003`](../decisions/0003-bundle-por-juego.md) el resultado es un `.zip` que después
se instala en otra máquina, y eso agrega un paso y cambia el final.

Detalle completo en [`features/001-export-bundle/`](../features/001-export-bundle/spec.md).

**Paso nuevo, entre elegir el juego y arrancar: "Qué incluir".**

Dos bloques. El primero **no se puede tocar**:

```
OBLIGATORIO — no se puede quitar                              1,2 MB
  Identidad · Carátula · Póster · Sinopsis · Color de acento

OPCIONAL
  [x] Marquesina                                              28 KB
  [ ] Logo                                                       —     (vacío)
  [ ] Captura de pantalla                                        —     (vacío)
  [x] Video de gameplay                                       53 MB
  [x] Reseña                                                    ·
  [x] Trucos                                                    ·
  [x] Manuales (1)                                            11 MB
  [ ] Archivos del juego                                     1,15 MB

                                              Total:         64,2 MB
```

**Por qué el bloque obligatorio está bloqueado.** La pantalla solo lista juegos `ready`. Si
el export pudiera quitar la carátula, saldría de una lista de "listos" un bundle que no lo
está, y "marcar como listo" dejaría de significar algo. Lo obligatorio del export es
exactamente lo que hace `ready` a un juego (`tech-stack.md` §Qué significa COMPLETO), ni
más ni menos.

**Los campos vacíos se ven deshabilitados con `—`, no como opciones sin marcar.** No hay
nada que incluir; ofrecer el interruptor sugiere que falta una decisión que no existe.

**El total se actualiza en vivo.** Sin ese número el paso no sirve: es el único motivo por
el que existe. **El corte no es por sistema** —un romset de MAME con CHD pesa lo mismo que
un PSX—, así que no se decide por el usuario según la plataforma.

**Las revistas no aparecen.** No se exportan en ninguna forma (D3): no hay interruptor
porque no hay decisión.

**Las tres etapas se mantienen, con otro contenido:**

1. `Armando estructura de archivos de "<Título>"…` — sin cambio.
2. `ATTRACT verificando "<Título>"…` — corre `attract doctor` sobre el árbol preparado,
   **antes de comprimir**. Si ATTRACT no está en esta máquina, la etapa se salta y el
   resultado lo dice.
3. **Resultado** — ya no es solo un veredicto: es un archivo. Hay que mostrar nombre, peso
   y qué lleva adentro, más el recordatorio de que la colección tiene que existir en la
   máquina de destino.

**Un veredicto de rechazo impide generar el `.zip`.** Un bundle inválido circulando es peor
que un export que no ocurre.

### D5 · El modal de sugerencias consulta varias fuentes

`screens-spec.md` §5.11 tiene cuatro fases —buscando, resultados, sin resultados, error—
pensadas para **una** fuente. Con seis proveedores por campo
([`ADR-0006`](../decisions/0006-fuentes-externas-multiproveedor.md)) esas fases dejan de
alcanzar.

- **La fase "error" casi nunca se da.** Solo cuando ninguna fuente respondió. Que una se
  caiga es normal y no debe verse.
- **Hay que mostrar cuántas fuentes contestaron.** Con una sola fuente, tres resultados
  significaba "el juego es oscuro". Con seis puede significar eso o "tres se cayeron", y
  son cosas distintas. Una línea al pie alcanza: `3 de 6 fuentes respondieron`.
- **Los resultados llegan todos juntos, al final.** Nada de poblar la grilla de a poco: la
  búsqueda es a pedido y esperar no molesta (`tech-stack.md` §Convenciones). La fase
  "buscando" puede durar bastante y está bien; lo que **no** puede es dar la sensación de
  estar colgada.
- **Cada candidato muestra su fuente**, que el diseño ya contempla (`source` en 11px gris).
  Con una fuente era decorativo; con seis es información para decidir.

**Los textos generados por IA se marcan como tales.** Sinopsis, reseña y trucos vienen de
un modelo, no de un catálogo. Vale sobre todo para la reseña: un `GRÁFICOS: 85` inventado
se ve en el gabinete idéntico a una nota real de una revista de la época.

**Hay candidatos que no se pueden aplicar.** Los de clase `referencia` —YouTube, revistas—
solo dicen dónde está el material: su botón abre el enlace y no toca el campo. Tienen que
verse distintos de los aplicables, o el usuario va a hacer click esperando que se cargue
algo. Detalle en
[`features/002-sugerencias-multiproveedor/`](../features/002-sugerencias-multiproveedor/spec.md).

## El contrato y la política son dos archivos

Resuelto en [`ADR-0005`](../decisions/0005-contrato-vendoreado-vs-politica-propia.md) y
precisado en [`ADR-0011`](../decisions/0011-fielddefs-json-compartido.md):

- **`lib/domain/contract.json`** — vendoreado desde ATTRACT, versionado, nunca editado a
  mano. Nombres de asset, capitalización, extensiones, lo que ATTRACT exige.
- **`lib/domain/fielddefs.json`** — política de COINDOOR: etiquetas, ratios y `required`.
  Referencia las claves del contrato, no las redefine.

**Los dos son datos, no código.** El diseño proponía `fieldDefs.ts`; es JSON para que
Python lo lea sin reescribirlo, porque el servidor calcula la misma completitud que el
cliente y esa política no puede vivir dos veces
([`ADR-0011`](../decisions/0011-fielddefs-json-compartido.md)). `types.ts` lo importa con
`with { type: 'json' }` y deriva los tipos.

**Dos tests los atan:**

1. Ningún asset de `fielddefs.json` sin su asset en `contract.json`, ni al revés; los campos
   de identidad/texto/acento se validan contra campos del contrato o datos ricos mediante un
   mapeo explícito UI ↔ contrato. Sin este test los dos archivos se desincronizan igual,
   solo que más despacio.
2. `missingRequired` de TypeScript y de Python dan el mismo resultado sobre los diez
   juegos del seed. Sin este, la lógica diverge aunque los datos no.

## Cómo se sirve el frontend

En producción lo sirve el mismo proceso que la API, desde el mismo origen, y por eso no
hay CORS ([`ADR-0009`](../decisions/0009-proceso-local-en-loopback.md)). La URL base es
`/api` relativa: **cero variables de entorno**. En desarrollo, Vite en `5173` con proxy a
`127.0.0.1:8765`.

Ninguna clave de API vive del lado del cliente. El navegador nunca habla con una fuente
externa: siempre pasa por el backend.
