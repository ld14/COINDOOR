"""Cliente de myabandonware.com: encuentra la página de un juego y la lee, por HTTP común.

El sitio no tiene Cloudflare. Su ``robots.txt`` prohíbe la búsqueda (``/search/``), las
descargas y los manuales: el juego se encuentra en el ``sitemap``, que lista una página por
juego, y solo se bajan esas páginas y sus capturas (ADR-0027).

1. Índice: los slugs del ``sitemap``, guardados en disco y renovados cada 30 días.
2. Candidatas: los slugs que son el título buscado y, aparte, los que lo contienen.
3. Elegir: solo una página de la plataforma cuyo título o nombre alternativo es el buscado; si
   hay varias, desempata el año, con la regla común de ``coincidencia``. Que el slug contenga
   el título no alcanza: sin un buscador, son todos los juegos con esa palabra ("Doom": 56).
"""

from __future__ import annotations

import contextlib
import gzip
import logging
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from backend.lib.providers import coincidencia
from backend.lib.providers.base import Limite
from backend.lib.providers.myabandonware.parser import BASE, Ficha, parse_ficha, parse_sitemap
from backend.lib.providers.politica import ProviderHttpError, ProviderNotFound
from backend.lib.providers.scraping import pagina_desde_html
from backend.store.archivo import escribir_binario

log = logging.getLogger(__name__)

SITEMAP = f"{BASE}/sitemap.xml.gz"
LIMITE = Limite(espera_min=1.0)
TIMEOUT = 30.0
# Páginas que se leen, a lo sumo, para encontrar un juego. "Civilization" lo encuentra en la
# cuarta: Sid Meier's Civilization, con "Civilization" como nombre alternativo.
MAX_PAGINAS = 5
_DIAS_INDICE = 30
_ARCHIVO_INDICE = "juegos.txt"


class Http(Protocol):
    def get_text(self, url: str) -> str: ...

    def get_bytes(self, url: str) -> bytes: ...


_lock = threading.Lock()
_indices: dict[Path, tuple[str, ...]] = {}
_fichas: dict[str, Ficha | None] = {}
_busquedas: dict[tuple[str, str, str], Ficha | None] = {}


def olvidar() -> None:
    with _lock:
        _indices.clear()
        _fichas.clear()
        _busquedas.clear()


def indice(http: Http, carpeta: Path) -> tuple[str, ...]:
    """Los slugs de juego del ``sitemap``: el guardado si tiene menos de 30 días y, si no, uno
    recién bajado. Si bajarlo falla y hay uno guardado, sigue con ese."""
    archivo = carpeta / _ARCHIVO_INDICE
    vigente = _vigente(archivo)
    with _lock:
        guardado = _indices.get(archivo)
    if guardado is not None and vigente:
        return guardado
    if vigente:
        slugs = _leer(archivo)
    else:
        try:
            slugs = _bajar_indice(http)
        except ProviderHttpError:
            if not archivo.exists():
                raise
            log.warning("myabandonware: no se pudo renovar el índice; sigue el guardado")
            slugs = _leer(archivo)
        else:
            if slugs:
                escribir_binario(archivo, "\n".join(slugs).encode("utf-8"))
            elif archivo.exists():
                log.warning("myabandonware: el sitemap no trajo juegos; sigue el índice guardado")
                slugs = _leer(archivo)
    with _lock:
        _indices[archivo] = slugs
    return slugs


def _vigente(archivo: Path) -> bool:
    return archivo.exists() and time.time() - archivo.stat().st_mtime < _DIAS_INDICE * 86400


def _leer(archivo: Path) -> tuple[str, ...]:
    return tuple(archivo.read_text(encoding="utf-8").split())


def _bajar_indice(http: Http) -> tuple[str, ...]:
    crudo = http.get_bytes(SITEMAP)
    with contextlib.suppress(OSError):  # si ya vino descomprimido, queda como está
        crudo = gzip.decompress(crudo)
    return parse_sitemap(crudo.decode("utf-8", errors="replace"))


def candidatas(slugs: Sequence[str], titulo: str) -> tuple[list[str], list[str]]:
    """Los slugs iguales al título y, aparte, los que lo contienen, en el orden en que conviene
    leerlos: primero los que terminan en el título (*Sid Meier's Civilization*), y entre ellos
    los de menos palabras de más."""
    buscadas = coincidencia.normalizar(titulo).split()
    if not buscadas:
        return [], []
    exactas: list[str] = []
    contienen: list[tuple[bool, int, str]] = []
    for slug in slugs:
        palabras = slug.split("-")[:-1]  # el último tramo es el id del sitio
        if palabras == buscadas:
            exactas.append(slug)
        elif set(buscadas) <= set(palabras):
            termina = palabras[-len(buscadas) :] == buscadas
            contienen.append((not termina, len(palabras) - len(buscadas), slug))
    return exactas, [slug for *_, slug in sorted(contienen)]


def buscar(
    http: Http,
    carpeta: Path,
    titulo: str,
    anio: str | None,
    plataforma: str,
) -> Ficha | None:
    """La página del juego en esa plataforma ("DOS"), o ``None`` si no hay una sin ambigüedad.

    Lee primero las páginas cuyo slug es el título; si ninguna es de la plataforma, las que lo
    contienen, buscando el título entre sus nombres alternativos. La búsqueda y cada página
    quedan en memoria mientras corre el proceso.
    """
    clave = (coincidencia.normalizar(titulo), anio or "", plataforma.lower())
    with _lock:
        if clave in _busquedas:
            return _busquedas[clave]
    exactas, contienen = candidatas(indice(http, carpeta), titulo)
    leidas = exactas[:MAX_PAGINAS]
    fichas = _las_del_juego(http, leidas, titulo, plataforma)
    if not fichas:
        fichas = _las_del_juego(http, contienen[: MAX_PAGINAS - len(leidas)], titulo, plataforma)
    elegida = coincidencia.elegir(
        fichas,
        titulo,
        anio,
        titulos_de=lambda f: (f.title, *f.alias),
        principal_de=lambda f: f.title,
        anio_de=lambda f: coincidencia.anio_entero(f.year),
    )
    with _lock:
        _busquedas[clave] = elegida
    return elegida


def _las_del_juego(
    http: Http,
    slugs: Sequence[str],
    titulo: str,
    plataforma: str,
) -> list[Ficha]:
    """Las páginas de esos slugs que son de la plataforma buscada y tienen el título o un nombre
    alternativo igual al buscado."""
    buscado = coincidencia.normalizar(titulo)
    fichas: list[Ficha] = []
    for slug in slugs:
        ficha = _ficha(http, slug)
        if ficha is None or ficha.plataforma.lower() != plataforma.lower():
            continue
        if buscado in {coincidencia.normalizar(t) for t in (ficha.title, *ficha.alias)}:
            fichas.append(ficha)
    return fichas


def _ficha(http: Http, slug: str) -> Ficha | None:
    """La página de un juego. Una que ya no existe (404: el índice guardado quedó viejo) es
    ``None``; cualquier otro error sube, para que nada quede en memoria."""
    url = f"{BASE}/game/{slug}"
    with _lock:
        if url in _fichas:
            return _fichas[url]
    try:
        html = http.get_text(url)
    except ProviderNotFound:
        ficha = None
    else:
        ficha = parse_ficha(pagina_desde_html(html, url=url), url)
    with _lock:
        _fichas[url] = ficha
    return ficha
