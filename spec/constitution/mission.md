# Misión

## Qué construimos

Una interfaz visual para preparar la metadata completa de cada juego de una
colección arcade, que después ATTRACT ensambla en la librería que Pegasus muestra
en el gabinete.

## Para quién

El dueño de la instalación arcade. Uno solo, trabajando en su propia máquina, sobre
su propia colección. No hay equipo, no hay clientes, no hay multiusuario.

## Qué problema resuelve

Un juego se ve bien en el gabinete cuando tiene video, carátula, marquesina, logo,
sinopsis, manual y trucos. Juntar todo eso es trabajo manual, archivo por archivo,
repartido entre cinco comandos de terminal y ocho documentos.

Dos consecuencias medidas en ATTRACT:

1. **Nadie sabe qué falta.** No existe forma de verificar "ya cargué todo": el hueco
   aparece recién cuando el juego se ve roto en el gabinete.
2. **Lo que más enriquece la ficha vive en internet, y el gabinete es offline por
   diseño.** ATTRACT deliberadamente no descarga nada. Alguien tiene que traer ese
   material desde afuera, y hoy ese alguien es una persona con un navegador abierto.

COINDOOR es la mitad conectada del sistema: busca, propone, arma y verifica. ATTRACT
valida y ensambla. El gabinete nunca se conecta.

## Cómo sabemos que funciona

- Un juego cargado entero desde COINDOOR pasa `attract doctor` sin errores y queda al
  nivel de `goldnaxe`, hoy el único juego completo de la colección y la vara de COMPLETO.
- Cargar un juego completo no obliga a abrir una terminal en ningún momento.
- Mirando la lista de juegos se ve qué falta, sin entrar a cada ficha.
- Un juego incompleto se puede dejar a medias y retomar semanas después.

## Qué NO somos

- **No somos el frontend del gabinete.** Eso es Pegasus. COINDOOR prepara, no exhibe.
- **No somos ATTRACT ni lo reemplazamos.** ATTRACT es la autoridad sobre qué es válido
  y qué está completo; COINDOOR se adapta a su contrato ([`ADR-0001`](../decisions/0001-contrato-coindoor-attract.md)).
- **No producimos contenido propio.** No generamos arte ni escaneamos revistas: lo traemos
  de fuentes externas o lo carga el usuario.
- **Con las revistas solo sugerimos.** La IA dice en qué publicaciones de la época pudo
  haber notas sobre el juego y guardamos esa referencia. Conseguir la revista y
  digitalizarla es otro subsistema.
- **No hacemos carga masiva.** Un juego por vez, a mano, con sugerencias a pedido. Una
  colección se arma una vez y se cuida para siempre; la velocidad no es el problema, la
  completitud sí.
- **No decidimos nada automáticamente.** Toda sugerencia la acepta una persona. Una
  sinopsis inventada o una carátula del juego equivocado quedan permanentes en el
  gabinete.
