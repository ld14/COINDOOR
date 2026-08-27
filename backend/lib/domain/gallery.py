"""Etiquetas en español para los tipos de imagen de ArcadeDB.

Mapa estatico y no una llamada a la IA: son ~16 valores conocidos y cerrados, asi
que traducirlos en vivo seria mas lento, no determinista y gastaria cuota para
siempre devolver lo mismo. Los textos libres de la precarga (sinopsis, trucos) si
pasan por el traductor, porque ahi el contenido es abierto.
"""

from __future__ import annotations

# Tipos observados en las respuestas de ``query_mame_media``. Un tipo que no este
# aca no se pierde: cae a su nombre crudo (ver ``label_para``).
ETIQUETAS: dict[str, str] = {
    "artwork_preview": "Ilustración",
    "boss": "Jefe final",
    "cabinet": "Gabinete",
    "cpanel": "Panel de control",
    "decal": "Calcomanía",
    "end": "Final",
    "flyer": "Folleto",
    "gameover": "Fin del juego",
    "howto": "Cómo se juega",
    "ingame": "En juego",
    "logo": "Logo",
    "marquee": "Marquesina",
    "pcb": "Placa PCB",
    "score": "Puntajes",
    "select": "Selección",
    "title": "Pantalla de título",
}


def label_para(tipo: str) -> str:
    """Etiqueta en español del tipo, o el tipo crudo si es uno nuevo.

    Devolver el nombre crudo y no ``""`` es a proposito: si ArcadeDB agrega un tipo,
    la imagen se guarda igual y se ve con etiqueta en ingles, en vez de aparecer sin
    titulo o desaparecer de la galeria.
    """
    return ETIQUETAS.get(tipo, tipo)
