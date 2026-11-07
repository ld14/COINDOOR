# Primeros pasos

<!-- GUÍA: docs/ es para el usuario final. Nada de decisiones técnicas ni
razonamiento de arquitectura: eso vive en spec/. -->

## Requisitos previos

- Python 3.12, [uv](https://docs.astral.sh/uv/) y Node 22.12 o más nuevo.
- Una copia de [ATTRACT](https://github.com/ld14/attract) al lado de esta carpeta
  (`../attract`), para instalar los juegos en el gabinete.
- Opcional: las claves de la IA y de Tavily en un archivo `.env`. Sin ellas la aplicación
  funciona, pero no propone sinopsis, reseña ni trucos. La lista de variables está en el
  [README](../../README.md#instalar-en-otra-máquina).

ffmpeg, Deno y el navegador que usa la búsqueda en MobyGames se instalan solos la primera
vez.

## Instalación

```bash
git clone git@github.com:ld14/COINDOOR.git
git clone git@github.com:ld14/attract.git
cd COINDOOR
./dev.sh
```

Abrí `http://127.0.0.1:5173`. Para cortar, `Ctrl+C` en la terminal.

Si algo falla al instalar, buscá el mensaje en [Problemas comunes](../troubleshooting.md).

## Tu primer juego

1. **Configurá ATTRACT.** En **Configuración**, escribí la **Ruta de ATTRACT**, probala
   con **Probar** y guardá.
2. **Creá el sistema** si no existe, con **+ Nuevo sistema**: arcade, msdos, nes y los
   demás.
3. **Da de alta el juego.** En **Alta de un juego**, elegí el sistema y el archivo. Si el
   juego ya está en la carpeta del sistema, aparece en **Instalados** y el formulario se
   completa solo. Dejá marcado **Completar la ficha al crear** y tocá **Crear ficha y
   empezar a cargar →**.
4. **Esperá la precarga.** La aplicación busca en las fuentes y llena lo que encuentra.
   Puede tardar unos minutos: no hace falta quedarse mirando.
5. **Revisá la ficha.** Cada sección se guarda sola mientras editás. **Sugerir** trae más
   opciones de varias fuentes, y lo que propone la IA aparece marcado. Para el video,
   pegá una URL de YouTube: si dura más de 10 minutos, se bajan los 3 primeros.
6. **Marcala como lista.** Si falta algo obligatorio, **Para exportar falta:** lo
   enumera. Cuando dice **✓ Los obligatorios están completos.**, tocá **Marcar como
   listo**.
7. **Exportá e instalá.** En **Exportar un juego**, elegí qué incluir y exportá. Cuando
   ATTRACT verifica el paquete, tocá **Cargar en ATTRACT**.

## Siguientes pasos

- [Problemas comunes](../troubleshooting.md): los errores que ya aparecieron y cómo se
  resuelven.
- [Referencia de la API](../api-reference.md), si querés automatizar algo.
