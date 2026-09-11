---
id: 0017
title: El `game.json` vive en la carpeta del propio juego, no en una carpeta hermana derivada del título
status: accepted
date: 2026-09-08
supersedes: null
superseded-by: null
tags: [data, backend, storage]
---

# 0017 — El `game.json` vive en la carpeta del propio juego

## Contexto

ADR-0008 fijó un `game.json` por juego con su media al lado, y el store derivó la
ruta del id: `juegos/<safe_id(systemId)>/<safe_id(id)>/game.json`. El id, a su vez,
sale del **título**.

La feature [010](../features/010-descubrimiento-roms/spec.md) descubre juegos ya
instalados leyendo `juegos/<sistema>/`. Ahí quedó a la vista que el juego en disco y
su ficha son dos carpetas hermanas sin ningún vínculo estructural:

```text
juegos/ms-dos/
├── Indiana Jones and the Fate of Atlantis (1992)/   ← el juego
└── indiana-jones-and-the-fate-of-atlantis/          ← su ficha
    └── game.json
```

Los nombres difieren porque el título limpia el `(1992)` y el nombre en disco no. El
único vínculo entre las dos carpetas es el `romRef`, o sea **un nombre**, y de ahí
salieron dos problemas concretos:

1. El juego ya documentado seguía apareciendo como candidato, porque comparar ids
   derivados no encontraba la correspondencia.
2. Cualquier criterio de reemplazo hereda la fragilidad: renombrar la carpeta rompe
   el vínculo.

Se descartó apoyarse en el filesystem: el mismo directorio en NTFS reporta
`st_ino` distinto según se lea desde Windows o desde WSL —`…958285` contra
`…958287`, con `st_dev` sin relación—, y este proyecto usa los dos (`./dev.sh`
levanta el backend en WSL).

## Decisión

**El `game.json` se guarda dentro de la carpeta del propio juego.** El nombre de esa
carpeta deja de derivarse del id y pasa a ser un dato de la ficha: `StoredGame.dirName`.

- **Alta desde una carpeta descubierta** — `dirName` es el nombre real en disco y el
  `game.json` se escribe adentro. Renombrar la carpeta se lleva la ficha con ella.
- **Alta desde una ROM suelta** (`sf2.zip` en la raíz del sistema) — no hay carpeta
  donde escribir, así que se adopta: se crea `<sistema>/<safe_id(id)>/`, el archivo se
  **mueve** ahí adentro y el `romRef` se actualiza. Es exactamente el layout que ya
  produce `Subir ROM` hoy.
- **Alta con una ruta fuera de `juegos/`** (un ROM en otro disco) — `dirName` es
  `safe_id(id)`, el comportamiento de siempre.
- **Fichas anteriores** — `dirName` vacío cae a `safe_id(id)`, que es el nombre que ya
  tienen en disco. Campo aditivo con default seguro: no necesita migración por
  `version`.

"Este juego ya tiene metadata" pasa a ser un hecho estructural —*la carpeta contiene
un `game.json`*— y no un dato derivado que puede quedar desincronizado.

## Alternativas descartadas

**Un archivo marcador (`.metadata`) en la carpeta del juego.** Funciona para carpetas
y no para ROMs sueltas: un `sf2.zip` es un archivo, no hay adentro dónde escribir, y
un sidecar `sf2.zip.metadata` ensucia la carpeta del sistema. Además queda viejo: si
se borra la ficha, el marcador sobrevive y el juego no vuelve a ofrecerse nunca.

**Huella por contenido** (hash del archivo; para carpetas, cantidad de archivos y
bytes totales). Sobrevive al renombre, pero se rompe al tocar un archivo adentro de la
carpeta, y obliga a recorrer árboles de cientos de MB en cada escaneo. Cachearlo
reintroduce el estado desincronizado que se quiere evitar.

**Identificador del filesystem** (`st_ino`). Descartado por medición: no es estable
entre WSL y Windows sobre el mismo NTFS, que es el escenario de este proyecto.

**Dejar el match por último tramo del `romRef`.** Resuelve el caso observado y no
cuesta nada, pero sigue atado a un nombre: renombrar la carpeta hace reaparecer el
juego. Se conserva **como fallback** para las fichas anteriores a este ADR, no como
criterio principal.

## Consecuencias

- El id del juego sigue saliendo del título y sigue siendo la clave del índice y de
  las rutas de `media/`. Este ADR solo cambia dónde se escribe el `game.json`.
- Un alta desde una ROM suelta **mueve un archivo del usuario**. Es la única escritura
  destructiva del descubrimiento y queda acotada a esa operación explícita.
- Dos juegos del mismo sistema con el mismo `dirName` se pisan, igual que hoy se pisan
  dos con el mismo id. No se agrega desambiguación.
- `dirName` es interno: no viaja al bundle, como toda procedencia (ADR-0002).
- Si alguien mueve una carpeta a otro sistema por fuera de COINDOOR, la ficha viaja
  con ella pero su `systemId` queda viejo. El índice la sigue encontrando; corregir el
  sistema es una edición normal de la ficha.
