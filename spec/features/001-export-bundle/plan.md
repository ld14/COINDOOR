# 001 · Export a bundle — Plan

## Enfoque

Tres etapas, en este orden y sin saltos: **preparar → verificar → comprimir**.

La clave es que se comprime **último**. COINDOOR arma un árbol de staging idéntico a lo que
ATTRACT espera encontrar, lo somete a `attract doctor`, y solo si pasa lo mete en el `.zip`.
Comprimir primero y verificar después obligaría a descomprimir para validar, y dejaría
bundles inválidos circulando.

El bundle **no inventa un formato paralelo**. `media/` y `data.json` viajan tal como van a
quedar instalados; se copian, no se traducen. `bundle.json` solo lleva lo que necesita
interpretación: qué colección, qué identidad y cómo tratar cada artefacto.

## Estructura del bundle

```
goldnaxe.coindoor.zip
├── bundle.json                  ← el manifiesto
├── media/                       ← se copia tal cual a <sistema>/media/<set>/
│   ├── boxFront.jpg  marquee.jpeg  poster.jpg  video.mp4
│   ├── data.json                ← accent, accent2, review, cheats, manual, mags
│   └── _manual/
│       ├── manual.pdf
│       └── p001.png … p026.png
├── _synopsis.json               ← va a <sistema>/_synopsis/<set>.json
└── juego/                       ← OPCIONAL
    └── goldnaxe.zip
```

`media/` va con **los nombres finales del contrato** (`boxFront`, `marquee`, `poster`,
`logo`, `screenshot`, `video`), no con los de la UI. La traducción ocurre acá y en ningún
otro lado; el usuario nunca escribe un nombre de archivo.

## `bundle.json`

```json
{
  "bundle": 1,
  "generado": "2026-08-11T14:32:00Z",
  "contrato": "<versión del contrato de ATTRACT usada al armar>",

  "coleccion": "Arcade",
  "set": "goldnaxe",

  "identidad": {
    "origen": "mame",
    "campos": {
      "title": "Golden Axe",
      "developer": "Sega",
      "publisher": "Sega",
      "genre": "Beat 'em up",
      "release": "1989",
      "players": 2,
      "x-formato": "Arcade"
    }
  },

  "artefactos": [
    { "archivo": "juego/goldnaxe.zip", "destino": "goldnaxe.zip", "tratamiento": "copiar" }
  ],

  "incluye": ["marquee", "video", "review", "cheats", "manual", "juego"],
  "verificado": { "por": "attract doctor", "contrato": "<versión>", "ok": true }
}
```

- **`identidad.origen`** — `mame`: al instalar se consulta `mame -listxml <set>` y manda su
  respuesta; si MAME no está, se cae a `campos`. `declarada`: nunca se consulta.
  Editar **cualquier** campo de identidad mueve el juego entero a `declarada`.
- **`artefactos[].tratamiento`** — `copiar` (romset de MAME: descomprimirlo lo rompe) o
  `descomprimir` (carpeta de MS-DOS: dejar el zip lo deja sin lanzar). Vacío si no se
  incluyó el juego.
- **`incluye[]`** — solo lo **opcional** que el usuario dejó marcado. Lo obligatorio no se
  lista porque no es una elección: identidad, `boxFront`, `poster`, sinopsis y `accent` van
  siempre. Sirve para que quien recibe el bundle sepa qué falta a propósito y qué falta
  porque nadie lo cargó.
- **`verificado`** — si pasó `attract doctor` y con qué contrato. Sin esto, un bundle
  verificado y uno sin verificar se ven iguales.
- **No lleva el bloque `game:` escrito.** Lleva los campos; ATTRACT lo renderiza con el
  mismo código que `ingest`, y así los dos caminos de alta no pueden divergir
  ([`ADR-0004`](../../decisions/0004-coindoor-fuente-identidad-no-mame.md)).

## Implementación

1. **`bundle/seleccion.py`** — resuelve qué entra. Una tabla de datos, no `if`s: por cada
   campo, si es obligatorio, si tiene contenido y cuánto pesa. De ahí salen las tres cosas
   que necesita la pantalla —qué se puede elegir, qué está bloqueado, cuánto suma— y la
   lista que consume el staging. Agregar un campo al contrato es una fila.
2. **`bundle/staging.py`** — arma el árbol en un temporal a partir de esa selección.
   Traduce los nombres de la UI a los del contrato, escribe `data.json` y `_synopsis.json`,
   copia los binarios. Función pura sobre `(Game, selección)`.
3. **`bundle/datajson.py`** — serializa `review`, `cheats`, `accent`/`accent2` y `manual[]`
   a la forma exacta del contrato. Es el único lugar que conoce ese formato. Omite las
   claves sin dato o deseleccionadas en vez de escribir `null`, salvo `review`, donde
   `null` es un valor con significado ("no hay reseña"). **Nunca escribe `mags[]`.**
4. **`bundle/verify.py`** — corre `attract doctor` sobre el staging. Si el binario no está,
   devuelve `no_verificado` en vez de fallar.
5. **`bundle/pack.py`** — comprime el staging. **Sin compresión** (`ZIP_STORED`): `.mp4`,
   `.jpg`, `.png` y los romsets ya vienen comprimidos, así que deflate gasta CPU para nada.
6. **`bundle/manifest.py`** — construye `bundle.json`.
7. **API**:
   ```
   GET  /games/:id/export-options  → { obligatorio: [{key,label,bytes}],
                                       opcional:    [{key,label,bytes,disponible}] }
   POST /export { gameId, incluir: ["video","manual",…] }  → { runId }
   GET  /export/:runId  → { stage, result }
   ```
   El servidor calcula los pesos; el cliente no los estima. Un total mentiroso es peor que
   no mostrarlo, porque la decisión entera se toma mirando ese número.

## Decisiones

- **Lo obligatorio se calcula, no se configura.** La lista bloqueada sale de la misma
  función que decide si un juego es `ready` (`completeness.ts` / su gemela del servidor).
  Dos listas separadas divergirían y aparecería el caso absurdo: un juego listo que no se
  puede exportar completo.
- **Comprimir al final, no al principio** — permite verificar sobre archivos reales, con
  las rutas que ATTRACT va a ver.
- **`ZIP_STORED`** — el bundle es un contenedor, no un compresor. Medido: 53 MB de los
  63 MB de `goldnaxe` son un `.mp4`.
- **`data.json` viaja listo, no se reconstruye al instalar** — es JSON, no sintaxis
  Pegasus; no hay riesgo de divergencia como con el bloque `game:`.
- **Fallar si `doctor` da error** — un bundle inválido que circula es peor que un export
  que no ocurre. Mismo criterio que `ingest`: nunca escritura parcial.
- **Verificación opcional, export no** — si ATTRACT no está en esa máquina, el usuario
  igual necesita su bundle. Se avisa que no se verificó.

## Riesgos

- **El staging de un juego con video son 63 MB de copias temporales.** Hay que limpiarlo
  siempre, incluso si el export falla a la mitad.
- **Un opcional deseleccionado y uno que nunca se cargó llegan iguales al destino.** En los
  dos casos el campo no está. `incluye[]` en el manifiesto es la única forma de distinguir
  "lo dejé afuera a propósito" de "nadie lo cargó"; sin él, quien recibe el bundle no
  sabe si conviene pedir el video o si no existe.
- **El peso mostrado es el del archivo original, el del `.zip` va a ser casi idéntico**
  porque no hay compresión. Si algún día se comprime, el total deja de ser fiable y hay que
  revisar la promesa de la pantalla.
