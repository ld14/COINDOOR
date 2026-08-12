---
id: 0008
title: Guardar cada juego como un archivo JSON en vez de usar una base de datos
status: accepted
date: 2026-08-11
supersedes: null
superseded-by: null
tags: [backend, data]
---

# 0008 — Guardar cada juego como un archivo JSON en vez de usar una base de datos

## Contexto

`tech-stack.md` anota SQLite como «el default razonable — un usuario, una máquina», sin
decidirlo. Mirando qué hay que guardar de verdad, el default merece revisarse:

| Qué se guarda | Forma natural |
|---|---|
| Los 7 campos de identidad | Plana |
| Estado y procedencia por campo | Diccionario de campos |
| `review` — `score` + `cats` **parciales** | Anidada |
| `cheats` — grupos de **nombre libre** con entradas ordenadas | Anidada, sin esquema fijo |
| `manuales[]` — N por juego, cada uno con su estado | Lista |
| Imágenes, video, PDF y páginas rasterizadas | **Archivos**, decenas de MB |

O sea: **el dominio ya es documental**, y la parte pesada ya vive en el filesystem. Un
esquema relacional guardaría la mitad del payload como columnas JSON igual.

Escala real, de `mission.md` y ADR-0006: **un usuario, una máquina, ~200 juegos, sin
concurrencia y sin carga masiva**. Y la misión dice que «una colección se arma una vez y
se cuida para siempre»: los datos son irreemplazables aunque sean pocos.

## Decisión

**No hay base de datos. Cada juego es una carpeta con un `game.json` y su media adentro.**

```
~/.coindoor/
  juegos/<set>/
    game.json          ← el documento entero del juego
    boxFront.jpg  poster.jpg  video.mp4  thumb.jpg
    _manual/manual.pdf  p001.png … pNNN.png
  sistemas.json        ← son cuatro; no justifican un archivo cada uno
  cuotas.json          ← contador diario por proveedor
```

La carpeta se llama como el **`set`**, la identidad física que sale del archivo real en
disco (`CONVENCION` §1.2). La clave del almacenamiento y la del contrato pasan a ser la
misma cosa, y desaparece el `gameId` sintético.

Tres reglas que hacen que esto sea seguro y no solo simple:

1. **Toda escritura es atómica.** Serializar a `game.json.tmp`, `fsync`, y `os.replace()`.
   El rename es atómico en POSIX y en Windows: o queda el archivo anterior o el nuevo,
   nunca uno a medias. **Esto no es opcional**: es lo único que separa «simple» de
   «frágil».
2. **Toda lectura valida** contra el modelo Pydantic y falla nombrando el archivo. El
   formato invita a editarlo a mano y hay que asumir que va a pasar.
3. **La migración es un campo `version`** y una función que lleva el documento a la forma
   actual al leerlo. Las funciones de migración se agregan, nunca se editan, y cada salto
   de versión tiene un test con un documento real de esa versión como fixture.

`status` (`ready` / `incomplete` / `error`) **no se guarda**: se calcula al leer.

## Alternativas consideradas

### A. SQLite con `sqlite3` de stdlib

- A favor: cero dependencias igual. Transacciones reales. Filtrar y paginar sin leer toda
  la colección. Un solo archivo que se copia.
- En contra: hay un esquema que mantener y SQL que escribir, y **la mitad del payload
  termina como columnas JSON igual** porque el modelo es documental, no relacional.
- **Descartada porque:** paga el coste de un esquema sin cobrar su beneficio. Las
  garantías que aporta —transacciones, consultas— resuelven problemas que a 200 juegos,
  un usuario y sin concurrencia no existen. Y su modo de fallo es peor: una migración mal
  hecha toca la colección entera, mientras que acá toca un juego.
  **Sigue en pie si la colección crece a varios miles de juegos**, que es el límite
  honesto de esta decisión.

### B. SQLite + SQLAlchemy + Alembic

- A favor: migraciones con herramienta, modelos tipados que mypy verifica.
- En contra: dos dependencias grandes para ~8 tablas, de las cuales la mitad son
  documentos.
- **Descartada porque:** es la alternativa A con más ceremonia encima. El argumento a
  favor era la evolución del esquema, pero sin esquema no hay nada que evolucionar: el
  contrato de ATTRACT crece agregando claves, y una clave nueva en un JSON no es una
  migración.

### C. Una base documental embebida (TinyDB, LiteDB y similares)

- A favor: API de consulta sobre documentos, sin SQL.
- En contra: una capa entre el código y unos archivos JSON que ya sabemos leer con
  `json.load`.
- **Descartada porque:** agrega una API que aprender y una dependencia que mantener, y no
  quita ninguno de los tres problemas reales (escritura atómica, validación al leer,
  migración por versión). Los tres hay que resolverlos igual.

### D. Un solo archivo con toda la colección

- A favor: una sola lectura, una sola escritura, coherencia trivial.
- En contra: cada guardado reescribe la colección entera, y un archivo corrupto se lleva
  todo.
- **Descartada porque:** concentra el riesgo justo donde no hay que concentrarlo. Con un
  archivo por juego, el peor caso es perder un juego; con uno solo, es perder la
  colección. Además rompe la propiedad más útil de esta decisión: copiar la carpeta de un
  juego lo copia entero, media incluida.

## Consecuencias

**Positivas**

- **Copiar la carpeta de un juego copia el juego entero.** Mover, respaldar o compartir
  trabajo en curso deja de necesitar la aplicación.
- **`game.json` queda casi idéntico al `data.json` del contrato.** `review`, `cheats`,
  `accent` y `accent2` ya tienen la forma que espera ATTRACT, así que exportar deja de
  ser una traducción y pasa a ser una proyección: quitar lo interno (procedencia,
  revista) y renombrar los archivos.
- Agregar un campo al contrato es una clave más, no un cambio de esquema.
- Todo el proyecto se lee sin abrir una base de datos: el contrato es un archivo, la
  política es un archivo, y cada juego es un archivo. Misma cultura que ATTRACT.

**Coste asumido**

- **Sin transacciones entre archivos.** No hay operación que abarque dos juegos, así que
  hoy no duele; si apareciera, esta decisión se revisa.
- **Listar exige un índice en memoria**, construido al arrancar y actualizado después de
  cada escritura exitosa. A 200 juegos son milisegundos; a decenas de miles, no.
- **El almacenamiento pasa a ser código nuestro.** Lo que SQLite garantizaba, acá se
  testea: escritura atómica y migración por salto de versión son tests obligatorios.
- Un `game.json` editado a mano puede quedar inválido. Se mitiga validando al leer, no se
  elimina.

**Qué habría que revisar si esto se replantea**

- Si la colección pasa de unos pocos miles de juegos, el índice en memoria y el escaneo
  al arrancar dejan de ser gratis: vuelve la alternativa A.
- Si aparece una operación que tiene que abarcar varios juegos de forma atómica.
- Si dejara de haber un solo proceso —hoy el `threading.Lock` por juego alcanza porque no
  hay dos procesos escribiendo.

## Referencias

- `spec/constitution/tech-stack.md` §Modelo de datos, §Límites duros.
- `spec/constitution/mission.md` — un usuario, una máquina, sin carga masiva.
- ATTRACT `library/arcade/media/goldnaxe/data.json` — la forma a la que converge `game.json`.
- ATTRACT `docs/CONVENCION.md` §1.2 — de dónde sale el nombre de la carpeta.
- [`ADR-0002`](0002-procedencia-interna.md) — la procedencia vive dentro del campo y no se exporta.
- [`ADR-0007`](0007-fastapi-como-framework-backend.md) — los modelos Pydantic que validan al leer.
