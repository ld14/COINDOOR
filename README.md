# COINDOOR

Herramienta local para preparar la ficha completa de un juego —identidad, carátula,
marquesina, video, sinopsis, reseña, trucos, guía, manual, galería— y entregarla como un
`.zip` que [ATTRACT](https://github.com/ld14/attract) instala en la librería que Pegasus
muestra en el gabinete.

El gabinete es offline por diseño y ATTRACT no descarga nada. COINDOOR es la mitad
conectada: busca en las fuentes, propone, deja editar, arma el paquete y lo instala.

| Pieza | Qué es |
|---|---|
| **Pegasus** | El frontend del gabinete: lo que ve el jugador |
| **ATTRACT** | CLI en Python que arma y valida la librería que lee Pegasus |
| **COINDOOR** | *Este repo.* Prepara el material de cada juego y produce el bundle |

## Estado

**En uso.** 25 features especificadas, la gran mayoría implementadas, y 29 decisiones de
arquitectura. El detalle de qué está hecho y qué sigue está en el
[roadmap](spec/constitution/roadmap.md).

## Qué hace

1. **Alta:** se elige el sistema y el título, y opcionalmente la ROM.
2. **Precarga:** un trabajo en segundo plano completa todos los campos vacíos con las
   fuentes del sistema. Elige qué imagen va en cada casillero, y si ninguna encaja deja el
   casillero vacío ([ADR-0028](spec/decisions/0028-la-precarga-completa-toda-la-ficha.md)).
3. **Ficha:** cada sección se revisa y se edita, y se guarda sola, sin botón de guardar.
   «Sugerir» trae candidatos de varias fuentes con su procedencia, y lo que propone la IA
   aparece marcado como IA.
4. **Export:** genera el `.zip` del juego, lo verifica con `attract doctor` y lo instala
   en ATTRACT con un botón.

Las pantallas son el listado de juegos (exportados y pendientes), los sistemas, la ficha,
el export y la configuración (la ruta de ATTRACT).

### Fuentes

| Fuente | Para qué | Sistemas |
|---|---|---|
| [ArcadeDB](spec/decisions/0014-arcadedb-fuente-arcade.md) | Identidad, imágenes, video, sinopsis, trucos y manual | Arcade |
| [MyAbandonware](spec/decisions/0027-myabandonware-primera-fuente-de-pc-dos.md) | Identidad, sinopsis y capturas, por HTTP común | MS-DOS (primera fuente) |
| Launchbox | Identidad, carátulas y capturas de la edición, galería | Todos |
| [MobyGames](spec/decisions/0024-scrapling-y-mobygames-para-pc-dos.md) | El dato que ninguna fuente anterior tuvo, por scraping con Scrapling | MS-DOS y consolas |
| IA (API compatible con OpenAI) | Sinopsis, reseña, objetivo y guía; identidad solo como [último recurso](spec/decisions/0026-ia-ultimo-recurso-en-sugerir-identidad.md) | Todos |
| Buscador web (Tavily) + IA | [Trucos](spec/decisions/0019-buscador-mas-modelo-para-trucos.md) con evidencia, no de memoria | Todos |
| DuckDuckGo Images | Imágenes cuando las fuentes no tienen | Todos |
| [YouTube](spec/decisions/0020-descarga-de-video-youtube.md) | Video a pedido con yt-dlp. Si dura más de 10 minutos se [recorta](spec/decisions/0029-recorte-de-videos-largos-de-youtube.md) a los 3 primeros | Todos |

Sistemas configurados: arcade, MS-DOS, NES, SNES, Genesis / Mega Drive, Game Boy, Game Boy
Color y Game Boy Advance
([`plataformas.json`](backend/lib/domain/plataformas.json)). Una fuente caída no rompe la
búsqueda: ese campo queda vacío y el resto sigue.

## Cómo está hecho

| Capa | Qué |
|---|---|
| Backend | Python 3.12, FastAPI, un solo proceso en `127.0.0.1` sin autenticación: el bind y la validación del `Host` la reemplazan ([ADR-0009](spec/decisions/0009-proceso-local-en-loopback.md)) |
| Frontend | Vite + React + TypeScript + TanStack Query, estética «Flyer 80s» ([ADR-0023](spec/decisions/0023-estetica-flyer-reemplaza-dos.md)) |
| Datos | Sin base de datos: un `game.json` por juego, con su media al lado y escritura atómica ([ADR-0008](spec/decisions/0008-persistencia-en-archivos.md)) |
| Trabajos largos | Hilos del propio proceso, cancelables. Sin colas ni workers ([ADR-0010](spec/decisions/0010-jobs-en-proceso.md)) |
| Contrato con ATTRACT | Se consume como dato versionado. El bundle lleva campos, nunca sintaxis de Pegasus ([ADR-0001](spec/decisions/0001-contrato-coindoor-attract.md), [ADR-0003](spec/decisions/0003-bundle-por-juego.md)) |

Un solo usuario y un juego por vez, por diseño: sin carga masiva.

## Requisitos

Python 3.12 · [uv](https://docs.astral.sh/uv/) · Node 22.12+ · ffmpeg · [Deno](https://deno.com) 2.3+
· el Chromium de Scrapling.

`./dev.sh` instala ffmpeg, Deno y Chromium si faltan (`scripts/install-deps.sh`: brew en
macOS, apt en WSL/Linux, winget o choco en Windows con Git Bash). Si no puede, ver
[`docs/troubleshooting.md`](docs/troubleshooting.md).

Opcionales: los binarios `mame` y `attract`. Sin ellos la aplicación funciona, con más
trabajo manual.

## Instalar en otra máquina

```bash
git clone git@github.com:ld14/COINDOOR.git
git clone git@github.com:ld14/attract.git   # al lado: ../attract
cd COINDOOR
./dev.sh                                     # instala lo que falte y levanta todo
```

`./dev.sh` corre `uv sync`, `npm install` y `scripts/install-deps.sh`. La app queda en
`http://127.0.0.1:5173`.

Tres cosas no viajan en el repo, a propósito:

| Qué | Por qué | Cómo llevarlo |
|---|---|---|
| `.env` | Tiene las claves de la IA y del buscador | Crearlo a mano (abajo) o copiarlo |
| `games/` | Las fichas, su media y los exports: pesa GB | Copiar la carpeta entera si se quieren los mismos juegos |
| La ruta de ATTRACT | Depende de cada máquina | Configurarla en la app. Si se copia `games/`, revisarla: `configuracion.json` guarda la ruta de la máquina de origen |

Sin `.env` la app funciona, pero la IA no propone sinopsis, reseña ni trucos. Las
variables llevan el prefijo `COINDOOR_` (ver `backend/config.py`):

```bash
COINDOOR_AI_PRIMARY_BASE_URL=   # IA principal, API compatible con OpenAI
COINDOOR_AI_PRIMARY_API_KEY=
COINDOOR_AI_PRIMARY_MODEL=
COINDOOR_AI_BACKUP_BASE_URL=    # IA de respaldo, mismo formato
COINDOOR_AI_BACKUP_API_KEY=
COINDOOR_AI_BACKUP_MODEL=
COINDOOR_SEARCH_API_KEY=        # Tavily, para trucos
```

Opcionales: `COINDOOR_DATA_DIR` (otra carpeta en vez de `games/`) y
`COINDOOR_SCRAPING_WARMUP=false` (no precalentar MobyGames al arrancar). El puerto es
8765: el backend solo acepta ese `Host` y Vite apunta ahí.

## Comandos

| Comando | Qué hace |
|---|---|
| `./dev.sh` | Instala dependencias y levanta backend (`8765`) y Vite (`5173`) |
| `uv run coindoor` | Levanta el proceso y sirve el build del frontend (antes, `npm run build`) |
| `uv run pytest` | Tests del backend |
| `uv run ruff check .` · `uv run mypy backend/lib` | Lint y tipos |
| `npm run dev` · `npm run build` | Vite con proxy a `8765` · build estático |
| `npm test` · `npm run lint` | Vitest · ESLint |

## Mapa del repo

| Ruta | Qué es |
|---|---|
| [`backend/`](backend/) | API, fuentes (`lib/providers/`), bundle y tests |
| [`frontend/`](frontend/) | La interfaz |
| [`spec/constitution/`](spec/constitution/) | Misión, stack, modelo de datos, límites duros, [glosario](spec/constitution/glosario.md) y roadmap |
| [`spec/decisions/`](spec/decisions/README.md) | Los ADRs: por qué se decidió cada cosa y qué se descartó |
| [`spec/features/`](spec/features/) | Spec, plan y tareas de cada feature |
| [`docs/`](docs/) | Análisis del stack, UX, diseño del frontend e insumos de ATTRACT |

## Cómo se trabaja

Spec Driven Development: primero la spec, después el plan, después las tareas y recién
entonces el código. Ver [`spec/README.md`](spec/README.md). La constitución manda: si una
feature choca con `spec/constitution/`, se replantea la feature. Una decisión con
alternativas descartadas va en un ADR nuevo, y los ADRs aceptados no se editan: se
reemplazan con otro.

## Licencia

`<PENDIENTE>`
