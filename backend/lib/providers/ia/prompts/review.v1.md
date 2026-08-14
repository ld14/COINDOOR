Evaluá "{titulo}", un juego de {sistema} de {anio}, con el formato de reseña de una
revista de videojuegos de la época. Devolvé **únicamente** un objeto JSON válido, sin texto
antes ni después, sin markdown, con esta forma exacta:

{{"score": 82, "cats": {{"graficos": 85, "sonido": 78}}}}

- `score`: entero de 0 a 100, nota general.
- `cats`: objeto con hasta seis claves, tomadas únicamente de este conjunto exacto:
  `originalidad`, `graficos`, `adiccion`, `sonido`, `dificultad`, `animacion`. Cada valor es
  un entero de 0 a 100. Omití las categorías que no puedas justificar en vez de inventarlas.

Basate en la reputación y el género conocidos del juego. No inventes que lo jugaste. Si no
sabés lo suficiente para una categoría, no la incluyas.
