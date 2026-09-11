# 010 · Descubrimiento de ROMs sin ficha — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

El escaneo es un `iterdir()` de dos niveles sobre `settings.games_dir`, sincrónico y
sin caché: la carpeta es local, el volumen es de decenas de entradas y la latencia no
es un problema de este producto (`tech-stack.md` §Convenciones). No hay job, no hay
índice nuevo, no hay estado persistido — un candidato es una lectura del disco, no una
entidad.

Qué cuenta como "ya tiene metadata" se resuelve contra el `GamesStore`, que ya indexa
todos los `game.json` al construirse: una carpeta con `game.json` adentro y cualquier
entrada cuyo `safe_id` derivado ya sea un id de ficha quedan afuera. Reusar el índice
en vez de releer el disco mantiene una sola definición de "juego existente".

El endpoint es sincrónico como `magazines/search` y `gallery/candidates`. El frontend
lo consume con React Query y lo invalida junto con `games` al crear una ficha, así el
candidato desaparece solo.

Deliberadamente **no** toca el disco ni el store: seleccionar un candidato solo llena
estado local del formulario. Toda la escritura sigue pasando por `POST /api/games`,
que ya valida.

## Implementación

1. `backend/lib/domain/descubrimiento.py` — puro: `titulo_propuesto(nombre)` (limpia
   `(World)`, `[!]`, separadores, y capitaliza solo si el nombre no trae mayúsculas
   propias) y `EXTENSIONES_IGNORADAS`.
2. `backend/api/schemas.py` — `RomCandidate` (`id`, `systemId`, `name`, `title`,
   `path`, `kind`, `file_format`, `tratamiento`, `sizeBytes`).
3. `backend/services/descubrimiento.py` — `DescubrimientoService.candidatos(system_id)`:
   recorre `games_dir/*/`, filtra lo que ya tiene ficha, ordena por título.
4. `backend/api/roms.py` — `scan_router` con `GET /api/roms/candidates`, registrado en
   `backend/main.py`.
5. `frontend/src/lib/api/roms.ts` — `listRomCandidates(systemId?)` y el tipo
   `RomCandidate`.
6. `frontend/src/hooks/useRomCandidates.ts` — query `['rom-candidates', systemId]`.
7. `frontend/src/pages/NuevoJuego.tsx` — panel `INSTALADOS SIN FICHA` con filtro de
   texto; al elegir, setea sistema, origen, ruta, formato, tratamiento y título.
8. `frontend/src/hooks/useGameMutations.ts` — invalidar `rom-candidates` en
   `createGame`.
9. `backend/api/schemas.py` — `StoredGame.dirName`: la carpeta donde vive el
   `game.json`. Campo aditivo, vacío cae a `safe_id(id)` — las fichas anteriores no
   necesitan migración por `version`.
10. `backend/store/juegos.py` — `dir_de(game)` centraliza la carpeta; `_path`,
    `create` y `_mover_a_sistema` la usan en vez de derivarla del id.
11. `backend/services/games.py` — `_dir_name()` decide dónde va la ficha según a
    dónde apunte el `romRef`, y `_adoptar_rom_suelta()` mueve una ROM suelta de la
    raíz del sistema a la carpeta de su ficha.
12. `backend/services/roms.py` — la ROM subida va a `store.dir_de(game)`.
13. `backend/bundle/staging.py` — `_es_interno()` excluye el `game.json` de COINDOOR
    y sus temporales del `.zip` del juego: la carpeta que se comprime ahora los
    contiene.

## Decisiones

- **`GET /api/roms/candidates` en un router propio dentro de `api/roms.py`** — el
  router existente tiene prefijo `/api/games` y el descubrimiento no cuelga de un
  juego, porque justamente todavía no existe.
- **"Ya tiene metadata" es estructural: la carpeta contiene un `game.json`** — la
  ficha pasa a guardarse dentro de la carpeta del propio juego, así el vínculo deja de
  depender de ningún nombre y sobrevive a renombrarla.
  Ver [`ADR 0017`](../../decisions/0017-ficha-en-la-carpeta-del-juego.md).
- **El match por `romRef` queda como fallback para las fichas anteriores al 0017** — el id
  sale del título y el del candidato del nombre en disco, y esos dos no coinciden en
  cuanto el título limpia algo: `Indiana Jones … (1992)` daba ficha `…-atlantis` y
  candidato `…-atlantis-1992`, así que el candidato seguía a la vista después del
  alta. Un `romRef` que apunta afuera de `games/juegos/` simplemente no matchea con
  ningún candidato, que es lo correcto.
- **Del `romRef` se compara solo el último segmento, normalizado con `safe_id`, y
  dentro de la misma carpeta de sistema** — `./dev.sh` corre el backend en WSL y
  guarda `/mnt/d/…`; el mismo repo abierto desde Windows lee `D:\…`. Comparar rutas
  enteras haría reaparecer el juego al cambiar de entorno. Acotarlo al sistema evita
  que una ficha tape una ROM homónima de otra plataforma.
- **Archivo → `copiar`, carpeta → `descomprimir`** — es la lectura literal de las dos
  opciones del alta: un romset viaja entero, un juego ya suelto se instala tal cual.
- **Título propuesto por heurística de nombre, sin IA ni catálogo** — es una
  conveniencia de tipeo; la identidad real la pone la precarga, que ya existe y ya
  pisa campos vacíos.
- **Sin caché ni watcher del filesystem** — el escaneo cuesta un `iterdir()` y la
  alternativa introduce estado que puede quedar viejo.

## Riesgos

- **Una carpeta de sistema con miles de ROMs** hace la lista inmanejable. Se mitiga
  con el filtro de texto y el orden alfabético; si aparece de verdad, se pagina.
- **Nombres de archivo con caracteres que `safe_id` colapsa** pueden dar dos
  candidatos con el mismo id derivado. El segundo se crea igual, pero pisa la ficha
  del primero: es el mismo comportamiento que ya tiene el alta manual y no se cambia
  acá.
