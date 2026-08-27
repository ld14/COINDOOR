Traducí al español rioplatense neutro cada string del array JSON de abajo. Vienen de la
ficha de "{titulo}", un juego arcade, y son de tres tipos: trucos de jugabilidad, géneros
y descripciones técnicas del gabinete.

Reglas:

- Devolvé un array JSON con exactamente la misma cantidad de elementos y en el mismo orden.
- Traducí solo el texto. No agregues, no resumas, no expliques, no numeres.
- Conservá en inglés los nombres propios (juegos, empresas, personajes) y los términos
  técnicos de MAME y de hardware arcade que no tienen equivalente usado en español:
  joystick, trackball, spinner, DIP switch, romset, sprite.
- Traducí las cantidades y direcciones: "4-way" → "4 direcciones", "Horizontal" →
  "Horizontal", "Vertical" → "Vertical".
- Si un string ya está en español, devolvelo igual.

Devolvé únicamente el array JSON, sin encabezados y sin markdown.

ARRAY ORIGINAL:
{textos}
