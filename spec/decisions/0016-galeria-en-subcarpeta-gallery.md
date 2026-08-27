---
id: 0016
title: La galería vive en `media/_gallery/` y se declara en `data.json`, fuera de los assets del contrato
status: accepted
date: 2026-08-25
supersedes: null
superseded-by: null
tags: [data, backend]
---

# 0016 — La galería vive en `media/_gallery/` y se declara en `data.json`

## Contexto

ArcadeDB publica entre 8 y 16 tipos de imagen por romset (`flyer`, `marquee`,
`cabinet`, `cpanel`, `pcb`, `decal`, `artwork_preview`, `ingame`, `title`, `boss`,
`end`, `gameover`, `score`, `select`, `howto`, `logo`). El contrato de ATTRACT tiene
**seis assets fijos** —`boxFront`, `poster`, `marquee`, `logo`, `screenshot`,
`video`— así que la precarga elige uno por casillero y descarta todo lo demás.

Se quiere conservar el resto como banco de imágenes por juego, y que ese banco viaje
en el bundle. ATTRACT lo consumirá en una etapa posterior; hoy no lo lee.

Hay tres restricciones verificadas contra `../attract`:

1. `media/<juego>/` es plano y Pegasus lo auto-descubre por nombre de asset
   (`CONVENCION.md` §1.3). Meter archivos sueltos ahí los expone a ese
   auto-descubrimiento.
2. Ya existe una excepción documentada: `_manual/`, una subcarpeta con guión bajo
   declarada desde `data.json` (`_chk_manual_doc`, `doctor.py:250`). `_magazines/`
   usa la misma marca a otra altura del árbol.
3. `chk_data_contrato` valida **sólo la forma de las claves que conoce** —"TODOS los
   campos son opcionales… lo que se valida es la forma de lo que SÍ está"— y no hay
   ningún chequeo de archivo inesperado. Una clave nueva y una subcarpeta nueva pasan
   `attract doctor` hoy, sin cambiar nada del otro lado.

## Decisión

Los archivos de galería van a `media/<juego>/_gallery/`, numerados `g001`, `g002`…,
y se declaran en `data.json` bajo la clave `gallery`, como lista de objetos
`{file, label}` donde `file` es un **nombre suelto sin separadores**.

La galería **no** es un campo de `fielddefs.json → images[]`.

```
media/<juego>/
  boxFront.png  poster.png  marquee.png  logo.png  screenshot.png  video.mp4
  data.json
  _gallery/
    g001.png
    g002.png
```

```json
"gallery": [
  {"file": "g001.png", "label": "Panel de control"},
  {"file": "g002.png", "label": "Placa PCB"}
]
```

## Alternativas consideradas

### Inventar assets del contrato: `gallery01.png`, `gallery02.png` en `media/` plano

- A favor: no agrega subcarpetas; Pegasus los auto-descubriría sin cambios.
- En contra: son assets que el contrato no declara.
- **Descartada porque:** `CONVENCION.md` §2.1 enumera los assets soportados y
  `gallery*` no está. Un asset inventado acá contamina bundles que se instalan en
  otras máquinas, que es exactamente lo que prohíbe la regla "no inventes campos del
  contrato". Además el número de imágenes es variable (8 a 16) y no hay forma de
  declarar cardinalidad variable en un esquema de assets fijos.

### `gallery/` sin guión bajo

- A favor: es el nombre literal, más legible.
- En contra: se aparta de la marca que ya usan `_manual/` y `_magazines/`.
- **Descartada porque:** el guión bajo es el marcador establecido para "subcarpeta
  de assets, no un asset", y ordena alfabéticamente aparte. Sin él la carpeta queda
  al mismo nivel que los seis assets reales, expuesta al auto-descubrimiento de
  `media/<juego>/<asset>.<ext>`.

### Lista de nombres pelados, como `magazine.json → pages[]`

- A favor: la forma más simple de validar del lado de ATTRACT.
- En contra: pierde de qué tipo era cada imagen.
- **Descartada porque:** `cpanel`, `pcb` y `cabinet` son información real que
  ArcadeDB provee y que el gabinete puede mostrar como título de cada imagen. Una
  vez descartada en el export no se recupera. `manual[]` ya sienta el precedente de
  objetos con `label` para el caso de varios documentos.

### Sumar `galeria` a `fielddefs.json → images[]`

- A favor: la UI la trataría igual que a los otros cinco campos, sin código nuevo.
- En contra: rompe tres consumidores de ese array.
- **Descartada porque:** `images[]` gobierna la completitud
  (`missing_required`), el mapeo a assets (`contract_asset`, que exige
  `contractAsset`) y la copia al staging (`_copy_assets`, que asume un `MediaField`
  con una sola `url`). La galería es una lista sin asset del contrato: no tiene
  `contractAsset` que declarar y rompería `_copy_assets` en la primera corrida.

### Guardarla sólo en COINDOOR, sin llevarla al bundle

- A favor: cero superficie de contrato, cero trabajo pendiente en ATTRACT.
- En contra: el material queda encerrado en la máquina que lo preparó.
- **Descartada porque:** el propósito del bundle es transportar todo el material
  preparado, y definir la estructura ahora cuesta lo mismo que definirla después
  pero evita re-exportar todos los juegos cuando ATTRACT la soporte.

## Consecuencias

**Positivas**

- El material que hoy se descarta queda conservado y viaja con el juego.
- La estructura queda fijada antes de que ATTRACT la implemente, así que los bundles
  que se generen desde ahora ya son válidos cuando el otro lado la lea.
- Cero cambios en `../attract` para que el bundle siga pasando `attract doctor`.

**Coste asumido**

- `media/<juego>/` deja de ser estrictamente plano. Es la segunda excepción, después
  de `_manual/`, y sigue la misma marca.
- ATTRACT ignora `gallery` hasta que la implemente: durante ese lapso los bytes
  viajan sin que nadie los muestre.
- COINDOOR sostiene el mapa de tipo de ArcadeDB a etiqueta en español. Si ArcadeDB
  agrega un tipo nuevo, cae a su nombre crudo hasta que se lo agregue.

**Qué habría que revisar si esto se replantea**

- Que ATTRACT publique un `contract.json` propio que declare assets de cardinalidad
  variable: ahí la galería podría dejar de ser un dato rico y pasar a ser un asset.
- Que `chk_data_contrato` empiece a rechazar claves desconocidas: hoy no lo hace y
  toda esta decisión se apoya en eso.

## Referencias

- `../attract/docs/CONVENCION.md` §1.3 (layout de media), §2.1 (assets soportados)
- `../attract/src/attract/doctor.py:250` `_chk_manual_doc` — precedente de `_manual/`
- `../attract/src/attract/doctor.py:294` `chk_data_contrato` — claves opcionales
- [ADR-0001](0001-contrato-coindoor-attract.md) — el contrato se consume como dato
- [ADR-0003](0003-bundle-por-juego.md) — el bundle transporta campos, no sintaxis
- [ADR-0011](0011-fielddefs-json-compartido.md) — qué gobierna `fielddefs.json`
- Feature [009-galeria](../features/009-galeria/spec.md)
