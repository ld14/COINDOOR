# COINDOOR · Requerimiento funcional para diseño UX

**Estado:** el diseño ya se produjo. Este documento pasa a ser el **por qué**; el **qué** —las
pantallas, los textos literales, los tipos— está en
[`docs/claude_diseño/`](../claude_diseño/README.md), que es la fuente de consulta.

Se conserva porque el paquete de diseño describe *qué* hace cada pantalla pero no *por qué*
existe, y ese razonamiento es lo que evita que una decisión se deshaga sin darse cuenta.
Ante discrepancia sobre la interfaz, gana `claude_diseño/`.

**Corregido:** este documento decía que las revistas estaban fuera de alcance. **Están dentro**
—vincular sí, escanear no— tal como las diseña el paquete. Las tres correcciones al diseño
están en `spec/constitution/frontend-architecture.md` §Deltas.

---

## 1. Qué es COINDOOR

Tres piezas encadenadas, y conviene no confundirlas:

| Pieza | Qué es |
|---|---|
| **Pegasus** | El frontend que corre en el gabinete arcade y muestra los juegos al jugador. |
| **ATTRACT** | Herramienta de línea de comandos que arma y valida la librería que Pegasus lee. |
| **COINDOOR** | *Esta app.* Interfaz visual para preparar el material de cada juego antes de que ATTRACT lo ensamble. |

**Por qué existe COINDOOR:** el gabinete es **offline** por decisión de arquitectura, y ATTRACT
declara explícitamente fuera de alcance descargar contenido de internet. Pero la metadata rica
—carátulas, videos, sinopsis, manuales— vive en internet. COINDOOR es la mitad conectada del
sistema: busca, propone y arma; ATTRACT valida y ensambla; el gabinete nunca se conecta.

**El valor está en la completitud.** Un juego con video, carátula, marquesina y sinopsis se ve
bien en el gabinete. Un juego a medias se ve roto. Todo el diseño debe empujar hacia
"este juego está completo".

## 2. Quién lo usa

**Un solo usuario: el dueño de la instalación arcade.** Trabaja solo, en su propia máquina.

Consecuencias directas para el diseño:

- **No hay login, ni registro, ni perfiles, ni roles, ni permisos, ni colaboración.**
- No hay onboarding multi-paso: la app abre directo en la lista de juegos.
- El usuario conoce el dominio (sabe qué es una marquesina). No hace falta explicar
  vocabulario arcade; sí hace falta mostrar **qué aspecto tiene cada cosa** — un preview vale
  más que un tooltip.

Herramienta de trabajo, no producto de consumo. Prioridad: densidad de información y pocos
clics por juego, por encima de amplitud visual.

## 3. Los dos ejes: VÁLIDO y COMPLETO

Esta distinción viene de ATTRACT y **el diseño la tiene que respetar visualmente**, porque son
dos problemas distintos que se resuelven de manera distinta:

| Eje | Significa | Cómo se ve |
|---|---|---|
| **VÁLIDO** | Lo que hay está bien formado. Un dato mal escrito rompe la librería. | **Error.** Bloquea. Hay que arreglarlo. |
| **COMPLETO** | No falta nada de lo que Pegasus puede mostrar. | **Faltante.** No bloquea. Se puede seguir trabajando. |

**Faltar no es error.** Un juego incompleto es un estado normal y frecuente; el sistema no debe
tratarlo como falla. Un juego inválido sí. Si el diseño los muestra con el mismo color o el mismo
ícono, el usuario aprende a ignorar los dos.

## 4. Cómo trabaja: el modelo mental

```
Sistemas/plataformas  →  Lista de juegos  →  Ficha de un juego
                                          →  (por campo) cargar a mano o pedir sugerencia
                                          →  marcar como completo
                                          →  exportar a la librería de ATTRACT
```

Reglas que el diseño debe reflejar:

- **Se trabaja de a un juego por vez.** No hay carga masiva, ni selección múltiple, ni
  operaciones en lote. No diseñes checkboxes de fila.
- **Nada es definitivo.** Una ficha se edita N veces, siempre sumando contenido.
- **Se puede abandonar a medias.** Todo se guarda incompleto sin protestar.
- **El trabajo manual nunca se pisa.** Regla dura heredada de ATTRACT: un campo curado a mano
  no se reemplaza automáticamente, nunca.
- **El export es un acto aparte y explícito**, no ocurre al guardar.

## 5. Pantallas

### 5.1 Sistemas / plataformas

Un juego no existe suelto: pertenece a un sistema (Arcade/MAME, NES, PC…). Hoy dar de alta un
sistema nuevo es el hueco más grande del proceso — se hace a mano y nada lo valida.

Debe permitir:
- Ver los sistemas existentes y cuántos juegos tiene cada uno.
- Crear un sistema nuevo: nombre visible, nombre corto, y **el comando de lanzamiento del
  emulador**.
- Ver si un sistema tiene la cabecera mal formada (error de eje VÁLIDO).

**Restricción dura:** la ruta del comando de lanzamiento **debe ser absoluta**. Es una regla del
contrato y hoy se viola en silencio: el síntoma aparece recién en el gabinete, cuando el juego no
arranca. El campo debe validar esto en el momento, con un mensaje que diga por qué.

Se usa poco —solo al sumar una plataforma— pero cuando se usa, se usa mal. Merece guía.

### 5.2 Lista de juegos

La pantalla de inicio. Responde una sola pregunta: *¿qué me falta?*

Debe permitir:
- Ver los juegos con su **grado de completitud de un vistazo** — el usuario tiene que barrer la
  lista y detectar los agujeros sin entrar a cada ficha.
- Distinguir tres estados, no dos: **listo**, **incompleto** (faltan cosas), **con errores**
  (algo está mal formado). Ver sección 3.
- Buscar por nombre, filtrar por sistema y por estado.
- Agregar un juego nuevo.

**Estado vacío:** primera vez, cero juegos. Única pantalla de bienvenida del sistema.

### 5.3 Alta de un juego — la bifurcación

Al crear un juego se parte del archivo de ROM, y ahí el flujo se abre en dos:

- **El sistema lo reconoce.** Solo pasa en arcade. La identidad (título, año, desarrollador,
  editor, género, cantidad de jugadores) se completa sola desde el catálogo. El usuario
  confirma. Camino feliz y rápido.
- **El sistema no lo reconoce.** Todo lo que no es arcade, y también arcade cuando el catálogo
  no está disponible en esa máquina. El usuario **declara la identidad a mano**: mismos campos,
  escritos por él.

Los campos que vienen del catálogo **se pueden editar**, pero cambiarlos debe costar un gesto
deliberado. Pisar sin querer un dato confirmado es peor que dejarlo mal: nadie vuelve a revisar
un campo que ya venía lleno.

**Arcade también se puede dar de alta por fuera de COINDOOR**, desde la terminal. La ficha de
un juego que llegó por ese camino se ve igual que cualquier otra; el usuario no tiene por qué
saber por dónde entró.

El diseño debe dejar claro **de dónde vino la identidad**, porque no valen lo mismo: una la
confirmó un catálogo autoritativo, la otra la escribió una persona.

El segundo caso no es marginal ni provisional: para todo lo que no sea arcade —MS-DOS, PC,
NES, PSX— **COINDOOR es la única fuente de esos datos**. Nadie los va a corregir después.
Es la pantalla donde más caro sale un error, y el diseño debería tratarla en consecuencia:
confirmación deliberada, no un formulario que se pasa de largo con Tab.

Lo que **nunca** escribe el usuario es el identificador interno del juego: sale del archivo
o la carpeta en disco, siempre, en todas las plataformas.

### 5.4 Ficha del juego

El corazón de la aplicación. Aquí se pasa el 95% del tiempo.

Formulario **dividido en secciones**, sin orden impuesto — no es un wizard. El usuario salta a lo
que tiene a mano.

**Secciones y contenido esperado:**

| Sección | Contenido | Cómo se carga |
|---|---|---|
| Identidad | Título, año, desarrollador, editor, género, jugadores, **formato** | Catálogo o a mano (§5.3) |
| Imágenes | Carátula, marquesina, póster | Subir o sugerir |
| Video | Video de gameplay | Subir o sugerir |
| Sinopsis | Texto descriptivo del juego | Escribir o sugerir |
| Reseña | Nota global + categorías | Formulario estructurado (§5.4.1) |
| Trucos | Agrupados por tipo | Editor de grupos (§5.4.2) |
| Presentación | **Dos** colores de acento | Selector de color |
| Manual | Uno o **varios** PDF | Subir → el sistema procesa (§5.6) |

**Ninguna imagen es obligatoria por separado.** Hay una cadena de reemplazo:
carátula → póster → marquesina → genérico. Un arcade no tiene caja y se apoya en la
marquesina. El diseño no debe marcar "falta la carátula" como si fuera un agujero si hay
póster: la pantalla del gabinete nunca queda vacía.

**El formato sí es obligatorio** (Arcade, GD-ROM, cartucho…). Alimenta un badge visible
en la ficha del gabinete y se conoce siempre.

#### 5.4.1 Reseña — no es un texto

Es una **nota global de 0 a 100** más hasta seis categorías, cada una de 0 a 100:
originalidad, gráficos, adicción, sonido, dificultad, animación.

Dos niveles de "sin dato" que el diseño tiene que distinguir:

- **No hay reseña.** El bloque entero dice "Sin Información". Ninguna categoría se ve.
- **Hay reseña pero faltan categorías.** Pasa seguido: reseñas parciales, con tres
  categorías cargadas y tres vacías. Las que faltan muestran `"-"`; las demás, normal.

O sea: el formulario debe permitir dejar categorías vacías **sin** que eso cuente como
reseña incompleta. Vacío es un valor legítimo, no un pendiente.

#### 5.4.2 Trucos — grupos libres

No es una lista plana ni un texto. Son **grupos que el usuario nombra**, y dentro de
cada uno, pares de *nombre* + *cómo se hace*:

```
Combos          → "Ataque hacia atrás"  ·  [←] [←] + [ATAQUE]
Códigos         → "9 créditos"          ·  mantener [←] + [↓] y pulsar [A] + [C] + [START]
Secretos        → "Pociones de magia"   ·  golpear a los ladrones azules en las fases de bonus
Dos jugadores   → …
```

Los nombres de grupo **no salen de una lista cerrada**: el usuario crea los que necesite.
El diseño necesita: agregar/renombrar/ordenar grupos, y agregar/ordenar entradas dentro
de cada grupo.

Los `input` llevan símbolos de dirección y botones (`←`, `↓`, `↘`, `[ATAQUE]`). Vale la
pena pensar cómo se escriben sin pelearse con el teclado.

Cada campo tiene tres estados que el diseño debe distinguir:

| Estado | Qué significa |
|---|---|
| Vacío | Nadie lo cargó. Si el contrato lo requiere, se ve como pendiente. |
| Cargado a mano | El usuario lo subió o lo escribió. **Protegido: nada lo pisa.** |
| Cargado por sugerencia | Vino de una fuente externa. La procedencia debe ser visible, discreta. |

Por cada campo: cargar a mano, pedir sugerencias (§5.5), ver **preview real** (la imagen o el
video, no el nombre del archivo), reemplazar, borrar.

En la ficha completa:
- **Indicador permanente** de qué falta y qué está mal, siempre visible, separando los dos ejes.
- Botón de **marcar como listo**: si faltan campos requeridos, la acción falla y muestra
  exactamente cuáles. Es el punto de mayor fricción del sistema — diseñalo bien.

**Nota:** los nombres de archivo del contrato distinguen mayúsculas de minúsculas, y un nombre
mal capitalizado hace que el gabinete simplemente no muestre la imagen, sin avisar. El usuario
nunca debería escribir un nombre de archivo a mano: al subir, el sistema lo nombra.

### 5.5 Sugerencias (sobre un campo)

El diferencial del producto. Botón por campo — *"buscar más carátulas"* — siempre **a pedido del
usuario**. Nunca automático, nunca en segundo plano.

Requisitos:
- **Lo que el usuario ya tiene se muestra junto a las sugerencias**, como un candidato más. Es
  una comparación, no una lista de resultados. Quedarse con lo propio es el **default**, no una
  acción que haya que buscar.
- Se elige **una** opción. Sin selección múltiple.
- Reemplazar algo cargado a mano **exige confirmación explícita**.
- Las opciones se ven a tamaño suficiente para decidir. Cinco carátulas parecidas en miniaturas
  de 60px no se pueden comparar.

Estados a diseñar — los tres ocurren seguido:
- **Buscando.** Sale a internet: tarda segundos, a veces muchos.
- **Sin resultados.** Frecuente en juegos oscuros. Debe ofrecer salida: reintentar, ajustar la
  búsqueda, o cargar a mano.
- **Error de la fuente externa.** Problema temporal y ajeno; el mensaje debe dejarlo claro para
  que el usuario reintente en vez de abandonar.

### 5.6 Manual — subida con procesamiento

Distinto del resto: el usuario sube un PDF y el sistema **genera las páginas como imágenes** para
que el gabinete las muestre. No es una subida instantánea.

**Un juego puede tener varios manuales** — el original, la traducción, el mapa desplegable —
y en el gabinete se muestran como pestañas. El diseño tiene que soportar la lista, no un
único archivo: agregar, nombrar y ordenar.

- Los PDF son pesados y el procesado tarda. Progreso visible, cancelable.
- Un manual subido pero **sin procesar** es un estado intermedio real, y es un faltante distinto
  de "no hay manual". El diseño debe distinguirlos: uno se resuelve con un botón, el otro
  requiere conseguir el archivo.
- Al terminar, el usuario debería poder ver las páginas generadas y confirmar que salieron bien.

### 5.7 Exportar — el bundle del juego

COINDOOR guarda todo en su propio almacenamiento. El export empaqueta **un juego** en un
archivo `.zip` instalable en cualquier ATTRACT
([ADR-0003](../../spec/decisions/0003-bundle-por-juego.md)).

Eso cambia el peso de la acción: el bundle **no es solo para vos**. Es compartible, y el
trabajo de cargar un juego —lo más caro del sistema— se hace una vez y lo usa cualquiera.
El diseño debería tratarlo como un producto terminado, no como un botón de guardar.

- **Se exporta de a un juego**, desde su propia ficha. Coherente con todo el resto.
- Antes de empaquetar, COINDOOR verifica contra el contrato y **muestra qué va a quedar
  afuera**. Un juego incompleto se puede exportar igual: no es un error (§3).

**La pantalla es, sobre todo, una decisión de qué incluir.** Dos cosas pesadas y
opcionales, cada una con su interruptor y **su peso a la vista**:

| Incluir | Por qué dudarlo |
|---|---|
| Los archivos del juego | Un cartucho de NES pesa KB; un disco de PSX o un romset con CHD, varios GB |
| El video de gameplay | En `goldnaxe` son 53 MB de los 63 MB del bundle |

El diseño tiene que mostrar **el peso total actualizándose** al marcar y desmarcar. Sin
eso el usuario no puede tomar la decisión, que es el único motivo por el que la pantalla
existe.

**El corte no es por sistema.** Un romset de MAME con CHD pesa lo mismo que un PSX. No
decidas por el usuario según la plataforma: mostrale el número y que elija.

- Un juego puede ser **varios archivos** (`.bin` + `.cue`, multi-disco) o una carpeta
  entera (MS-DOS). Van todos o ninguno; medio juego no sirve. Para el usuario es **una
  sola cosa**: se incluye "el juego", no se eligen archivos sueltos.
- Un bundle sin los archivos del juego **es legítimo y frecuente**: el receptor suele
  tener sus propias ROMs. El texto no debe sugerir que el bundle está incompleto.
- **La revista no viaja de ninguna forma**, ni el archivo ni la referencia. Lo que COINDOOR
  guarda es una pista para conseguirla más adelante, no un asset del juego. No aparece en
  la pantalla de export: no hay decisión que tomar.

**El juego debe pertenecer a una colección ya configurada.** La configuración del sistema
—en particular la ruta del emulador— es propia de cada máquina y no viaja en el bundle. Si
falta, el export tiene que fallar con ese motivo exacto, no con un error genérico.

## 6. Restricciones de diseño

- **Sin dependencia de conexión permanente.** Solo las sugerencias salen a internet. Cargar,
  editar y exportar funcionan offline. No bloquees la interfaz por falta de red.
- **Archivos pesados.** Videos y manuales de decenas de MB: progreso visible y cancelación.
- **Contexto de uso:** escritorio, sesiones largas, teclado y mouse. No es mobile-first. Si hay
  atajos para navegar entre juegos y campos, se van a usar.
- **El contrato con ATTRACT es externo y no negociable.** COINDOOR se adapta. Si el diseño
  necesita un campo que el contrato no acepta, no va.

## 7. Fuera de alcance

Que no aparezcan en el diseño:

- Login, usuarios, roles, permisos, compartir.
- Carga masiva, importación de carpetas, operaciones en lote.
- Reproducir o navegar la colección como lo hace el gabinete — COINDOOR prepara, no exhibe.
- **Escanear o digitalizar revistas.** Vincular un juego con una revista sí está dentro;
  producir el escaneo es otro subsistema.
- Historial de versiones, papelera, deshacer entre sesiones.
- Sugerencias automáticas o en segundo plano.
- Estadísticas, dashboards, reportes.

## 8. Pendiente de definición

1. **Qué significa COMPLETO, exactamente.** El contrato de ATTRACT solo marca dos campos
   obligatorios (título y formato); todo lo demás es opcional y tiene texto de reemplazo. La
   vara real es el único juego cargado entero de la colección. Sin una definición explícita,
   el indicador de completitud de §5.4 no tiene contra qué medir.
2. **Si la identidad de los juegos no-arcade la escribe una persona o la propone una IA.**
   En los dos casos hay confirmación humana antes de marcar el juego como listo, pero la
   pantalla no se diseña igual: proponer y confirmar no es lo mismo que escribir en blanco.
   Afecta §5.3.
3. **Fuentes externas concretas** de las sugerencias — define qué campos tienen botón de sugerir
   y cuáles no.
4. **Aviso de contrato desactualizado** — COINDOOR valida contra una copia del contrato de
   ATTRACT que puede quedar vieja ([ADR-0001](../../spec/decisions/0001-contrato-coindoor-attract.md)).
   Hay que diseñar cómo se avisa sin volverse ruido: qué ve el usuario y con cuánta urgencia.
