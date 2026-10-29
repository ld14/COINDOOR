# 020 · Scrapling y MobyGames — Tareas

## Antes de tocar código

- [x] Verificar el flujo de búsqueda: URL, forma de los resultados y cómo se distingue la
      plataforma. Verificado el 2026-10-28 con Pac-Man; queda en el plan §Lo verificado.
- [x] Resolver a mano 5 juegos MS-DOS de la colección con la regla del plan (paso 5). Hecho
      cuando: cada uno da la ficha correcta, o la regla se ajusta y se anota por qué. Los
      cinco dieron la ficha correcta sin ajustar la regla.
  - [x] *Monkey Island* (1990): MobyGames lo titula "The Secret of Monkey Island". Está en
    la primera página, debajo de la séptima fila; el nivel 2 de la regla lo elige por el año.
  - [x] *Out Run* (1986): nivel 1 por el AKA "Out Run"; única fila exacta con DOS (1989).
  - [x] *Teenage Mutant Ninja Turtles* (1990): dos filas exactas con DOS; desempata el año
    de DOS (1990 contra 1992).
  - [x] *Mission: Impossible* (1991): nivel 1; una sola fila exacta con DOS (1991).
  - [x] *Guy Spy* (1992): la ficha tiene un espacio de más y no tiene el subtítulo. Nivel 2;
    la única fila con "guy", "spy" y DOS es *Guy Spy and the Crystals of Armageddon*, con
    DOS (1992).
- [x] Definir el catálogo de plataformas con las que existen hoy (MS-DOS y arcade) y las
      entradas de Launchbox. Hecho cuando: MS-DOS resuelve una ficha real de MobyGames
      (nombre "DOS", confirmado), y arcade declara `"mobygames": null`. Quedó en el plan,
      paso 6b.
- [x] Confirmar contra `ReviewValue` y `fielddefs.json` qué claves acepta `review` y si la
      nota sola es válida. `score` es opcional y `cats` arranca vacío; la escala es de 0 a 100
      (`CONVENCION` nota 3).
- [x] Guardar la ficha de Maniac Mansion como fixture de tests. Está en
      `backend/tests/fixtures/mobygames/maniac-mansion.html`; lo que muestra quedó en el plan
      §Lo verificado.
- [x] Guardar la página de specs de Maniac Mansion (`/game/714/maniac-mansion/specs/`).
      Hecho cuando: se sabe si DOS tiene su propio bloque de jugadores y soporte, y queda la
      tabla de soportes del parser (paso 4); si no lo tiene, `players` y `format` salen de la
      lista de MobyGames. DOS tiene su bloque; está en `maniac-mansion-specs.html`.
- [x] Guardar como fixtures las búsquedas de Monkey Island, TMNT y Guy Spy, antes de
      programar el cliente. Hecho cuando: están en `backend/tests/fixtures/mobygames/` y
      cubren los dos niveles de la regla y el desempate por año.
- [x] Aceptar o rechazar [`ADR-0024`](../../decisions/0024-scrapling-y-mobygames-para-pc-dos.md).
      Aceptado el 2026-10-28; la conclusión está en `tech-stack.md` §Límites duros.

## Implementación

- [x] Extraer `politica.py` de `http.py`. Hecho cuando: los tests actuales de `http.py` pasan
      sin cambios.
- [x] `pyproject.toml` y `scripts/install-deps.sh`. Hecho cuando: un `uv sync` limpio más el
      script dejan el navegador listo en WSL. Verificado el 2026-10-29 en WSL: `chromium-1248`
      en `~/.cache/ms-playwright` y `scrapling` 0.5 importable.
- [x] `plataformas.json` y su cargador, con un test que falla si una fila omite un sitio
      declarado (sin equivalencia se escribe `null`).
- [x] Migrar Launchbox al catálogo. Hecho cuando: `_SYSTEM_TO_LAUNCHBOX` no existe y los tests
      de Launchbox pasan sin cambios.
- [x] `scraping.py` con escalado de HTTP a navegador. Hecho cuando: cancelar corta antes del
      siguiente pedido y de cada espera, y dos peticiones al mismo sitio quedan separadas por
      3 s. El navegador es de un solo uso (abre, baja la página y cierra), así que cancelar no
      deja ninguno vivo; lo más que espera es el `timeout` de esa página. Con tests y dobles;
      falta probarlo contra el sitio real en WSL (tarea de cierre).
- [ ] `mobygames/parser.py`. Hecho cuando: de las fixtures de Maniac Mansion saca los siete
      campos para DOS (año 1988 y editor Lucasfilm Games, no los de Apple II; 1 jugador y
      formato `Diskette`) y la nota de críticos (82), y da lo mismo con la ficha bajada por
      `ScrapingClient`. Hecho: `parse_ficha` y `parse_specs` contra las fixtures (9 tests).
      Comparado el 2026-10-29 contra la ficha y las specs reales bajadas por `ScrapingClient`
      en WSL: salen los mismos datos que de las fixtures. Falta el parser de la búsqueda.
- [x] `mobygames/cliente.py` con memo de ficha. Hecho cuando: con el título de 3 juegos reales
      devuelve la ficha correcta, con un título inexistente devuelve vacío, y una segunda
      consulta del mismo juego no baja la página. Hecho con las fixtures (12 tests): TMNT y
      Guy Spy se resuelven, Monkey Island 1990 no (ver plan); el memo y el salto por
      `originUrl` funcionan. Contra el sitio real (2026-10-29, WSL): la búsqueda baja y trae las
      12 filas, y la ficha y las specs ya se habían comparado; la prueba de 3 juegos seguidos no
      terminó en 28 min por el desafío de Cloudflare (ver plan, riesgo "Alta más lenta").
      Con el arreglo (sin `network_idle`, timeout 60 s, perfil persistente): Guy Spy, TMNT y
      Monkey Island dan la ficha correcta, en 198 s, 18 s y 21 s.
- [x] `mobygames/proveedor.py` y las cadenas nuevas en `registro.py`.
- [x] Sacar la IA de las sugerencias de identidad (`registro.py` y `suggest_identity_batch`).
      Hecho cuando: un test recorre las claves de identidad y ninguna cadena incluye
      `ia_primary` ni `ia_backup`, y la sugerencia en bloque no devuelve candidatos `ia-batch`.
- [x] Precarga de MS-DOS en `services/msdos.py`: MobyGames → Launchbox → IA por campo vacío.
      Hecho cuando: con un MobyGames falso que trae `developer` y no `players`, `developer`
      queda de MobyGames, `players` de la IA, y la procedencia lo dice. El género de
      MobyGames queda traducido. Con una ficha elegida por año aproximado, ni el año ni el
      formato salen de MobyGames.
- [x] Reseña parcial en `apply_rich_suggestion`. Hecho cuando: un test aplica un candidato con
      solo `score` sobre una reseña con seis categorías y las seis siguen.
- [x] Sin Chromium el proveedor no se construye. Hecho cuando: un test lo simula y la app arranca.
- [x] Tests sin red para parser, cliente y proveedor.
- [x] Arreglo de Cloudflare con opciones de Scrapling: `network_idle=False`, timeout de 60 s y
      perfil persistente en `games/navegador`. Hecho cuando: tres consultas reales seguidas
      terminan (antes no terminaban en 28 min). Medido el 2026-10-29: 198 s, 18 s y 21 s.
- [x] Precalentamiento al arrancar ([`ADR-0025`](../../decisions/0025-precalentar-mobygames-al-arrancar.md)).
      Hecho cuando: los tests de gate, marca, fallo y cancelación pasan, y al levantar la app
      real el servidor responde enseguida mientras el log muestra "MobyGames precalentado".
      Verificado el 2026-10-29 en WSL con un directorio de datos temporal: el servidor
      respondió a los 12 s de lanzarlo, con el desafío todavía en curso, y el log mostró
      "MobyGames precalentado en 171 s" con la marca creada.

## Cierre

- [ ] Comparar sobre 3 juegos MS-DOS la identidad de MobyGames contra la actual de la IA.
      Hecho cuando: se anota cuál acertó más y cuántos campos tuvo que completar la IA en la
      precarga.
- [ ] `ruff`, `mypy` y `pytest` en verde.
- [ ] Marcar la feature como hecha en [`roadmap.md`](../../constitution/roadmap.md).
