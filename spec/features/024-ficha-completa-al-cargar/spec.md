# 024 · Ficha completa al cargar

**Estado:** implementada

## Qué hace

Al dar de alta un juego, el sistema llena solo la mayor parte de la ficha, en cualquier
sistema, y el usuario ajusta sobre eso. Tres partes:

1. **Completar:** después de la precarga de la fuente del sistema, cada campo vacío de
   identidad, textos, "Cómo se juega", reseña, trucos e imágenes recibe el mejor candidato de
   su cadena de "Sugerir". El color de acento sale de la carátula.
2. **Criterio de imágenes:** el sistema decide qué imagen va en cada casillero (carátula,
   marquesina, póster, logo, captura) y deja el casillero vacío si ninguna encaja.
3. **Todas las imágenes:** la galería y "Sugerir" muestran todo lo que las fuentes tienen, sin
   un número máximo.

Las fichas ya creadas se completan con un botón "Completar lo que falta".

## Por qué

La precarga deja la mayoría de las secciones vacías y en sistemas que no son arcade ni MS-DOS
no hace nada: el usuario abre un modal por campo para aceptar casi siempre el primer candidato.
Y la galería de *Prince of Persia* mostraba 10 imágenes por búsqueda y 8 capturas cuando las
fuentes tienen muchas más. Pedido del dueño del producto el 2026-10-31. Decisión y
alternativas en [`ADR-0028`](../../decisions/0028-la-precarga-completa-toda-la-ficha.md).

## Criterios de aceptación

- [x] Dado un juego con título y campos vacíos, cuando corre el completado, entonces identidad,
      sinopsis, "Cómo se juega", reseña, trucos e imágenes reciben el primer candidato aplicable
      de su cadena, con la misma procedencia que al aplicarlo a mano.
- [x] Dado un sistema que no es arcade ni MS-DOS, cuando se crea un juego, entonces también se
      completa la ficha.
- [x] Dado un campo con valor, cuando corre el completado, entonces no cambia, tampoco si se
      llenó con el job ya en marcha.
- [x] Dado que falla una fuente o un candidato no se puede bajar, cuando corre el completado,
      entonces se prueba el siguiente y el job termina bien.
- [x] Dado un job cancelado, cuando llega al próximo campo, entonces no escribe nada más.
- [x] Dado un juego sin título, cuando corre el completado, entonces termina con `sin-titulo`
      sin salir a la red.
- [x] Dado un resultado del buscador, cuando se elige para un casillero, entonces solo entra si
      sus proporciones encajan y su título nombra al juego y nada más que vocabulario genérico
      (ni secuela, ni mod, ni otra plataforma, ni otro año); logo y póster además tienen que
      decir que lo son.
- [x] Dado que ningún resultado del buscador encaja, cuando se completa, entonces el casillero
      queda vacío y no se usa una imagen dudosa.
- [x] Dada una imagen de una fuente que publica el tipo (ArcadeDB, Launchbox, MobyGames), cuando
      se completa, entonces se usa sin juzgar su forma.
- [x] Dada una ficha con carátula y sin póster, cuando termina el completado, entonces el póster
      usa la carátula.
- [x] Dada una ficha con carátula y sin color de acento, cuando termina el completado, entonces
      quedan sugeridos el acento y el acento secundario.
- [x] Dada una búsqueda de imágenes, cuando hay más páginas de resultados, entonces se recorren
      hasta el final, y si una falla se conserva lo ya traído.
- [x] Dado un juego con más de 8 capturas o de 3 portadas, cuando se piden candidatos, entonces
      aparecen todas; la precarga pide solo la primera portada.
- [x] Dada la galería abierta, cuando una fuente responde, entonces sus imágenes aparecen sin
      esperar a las otras.
- [x] Dadas muchas opciones para un casillero, cuando se muestran, entonces ocupan tres filas con
      desplazamiento horizontal, y "Usar la mía" queda a la vista sin desplazarse (agregado el
      2026-10-31).
- [x] Dada la pantalla de alta, cuando se llega al paso final, entonces la casilla de completar
      está tildada en todos los sistemas.
- [x] Dada una ficha ya creada, cuando se aprieta "Completar lo que falta", entonces corre el
      mismo job, con su progreso.

## Fuera de alcance

- Bajar el video: [`ADR-0020`](../../decisions/0020-descarga-de-video-youtube.md) dice que nada
  se descarga solo.
- Manuales, revistas y galería: los elige el usuario.
- Reemplazar o mejorar lo que ya está cargado: eso sigue siendo "Sugerir".
- Mirar el contenido de las imágenes con un modelo de visión (ADR-0028, alternativa C).
- Sumar AbandonSocios: es otra decisión, todavía abierta.
