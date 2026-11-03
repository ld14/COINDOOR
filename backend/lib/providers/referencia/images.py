from __future__ import annotations

import logging
import re
import threading
import time
from collections.abc import Mapping
from typing import Literal
from urllib.parse import urlencode, urlparse

import httpx

from backend.lib.providers.base import Candidato, Consulta, Limite, ProviderResult, ProviderTrace
from backend.lib.providers.coincidencia import TOLERANCIA_EXACTO, anio_entero, normalizar

log = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

_TIMEOUT = 10.0
# Entre páginas de una búsqueda: este proveedor no pasa por `Politica`.
_PAUSA_ENTRE_PAGINAS = 1.0

_IMAGE_SEARCH_QUERIES = {
    "caratula": ["{title} {system} cover art", "{title} box art", "{title} cartridge"],
    "marquesina": ["{title} arcade marquee", "{title} arcade flyer", "{title} cabinet art"],
    "poster": ["{title} game poster", "{title} promotional art", "{title} flyer"],
    "logo": ["{title} game logo", "{title} title screen", "{title} logo"],
    "captura": ["{title} {system} screenshot", "{title} gameplay", "{title} ingame"],
}

_TRUSTED_DOMAINS = frozenset({
    "mobygames.com",
    "pcgamingwiki.com",
    "archive.org",
    "vgmuseum.com",
    "worldofpectrum.com",
    "strategywiki.org",
    "gamespot.com",
    "ign.com",
    "giantbomb.com",
    "wikimedia.org",
    "wikipedia.org",
    "retromags.com",
    "thevideogameartgallery.com",
    "adb.arcadeitalia.net",
    "flyers.arcade-museum.com",
    "flyers.arcadeotaku.com",
    "launchbox-android.com",
    "launchbox-app.com",
    "screenscraper.fr",
    "emumovies.com",
})

# Proporción ancho/alto que tolera cada casillero: las cajas reales no miden 3:4 exacto. Más
# angosto o más ancho que esto es otra cosa (ADR-0028).
_PROPORCIONES: dict[str, tuple[float, float]] = {
    "caratula": (0.6, 1.05),
    "poster": (0.55, 0.85),
    "marquesina": (2.5, 8.0),
    "logo": (1.2, 8.0),
    "captura": (1.2, 1.8),
}
# El buscador trae esto mezclado con las portadas: tienen la misma forma.
_NO_ES_LA_IMAGEN = re.compile(
    r"\b(manuals?|reviews?|guides?|walkthrough|back|wallpapers?)\b", re.IGNORECASE,
)
# Logo y póster no se distinguen de otra imagen por su forma: tienen que decir que lo son.
_TIENE_QUE_DECIR: dict[str, tuple[str, ...]] = {
    "logo": ("logo",),
    "poster": ("poster", "flyer", "advert", "promo"),
}
# Lo que un título puede tener además del nombre del juego. Cualquier otra palabra lo vuelve otro
# juego o una imagen de otra plataforma: "Wing Commander III & Standoff", "(Amiga, 1990)". Salió
# de los títulos reales de tres juegos (feature 024).
_PALABRAS_GENERICAS = frozenset({
    "a", "ad", "ads", "advert", "advertisement", "advertising", "and", "art", "banner", "box",
    "boxart", "clear", "cover", "covers", "dos", "for", "front", "game", "gameplay", "ibm",
    "image", "images", "ingame", "logo", "logos", "magazine", "magazines", "marquee", "material",
    "ms", "of", "official", "or", "packaging", "pc", "png", "poster", "promo", "promotional",
    "screen", "screenshot", "screenshots", "shot", "the", "title", "transparent", "video",
})


class ImageSearchProvider:
    """Busca imágenes de referencia en DuckDuckGo Images. Devuelve URLs de imágenes
    de fuentes confiables para que el usuario elija cuál cargar."""

    nombre = "Image Search"
    tipo: Literal["api", "scrape"] = "scrape"
    campos = frozenset({"caratula", "marquesina", "poster", "logo", "captura"})
    timeout = _TIMEOUT
    limite = Limite(por_segundo=1.0, por_dia=None, espera_min=0.5)

    def buscar(self, consulta: Consulta) -> ProviderResult:
        if consulta.key not in self.campos or not consulta.title:
            return ProviderResult((), ProviderTrace(self.nombre, self.tipo, "sin resultados"))

        queries = _IMAGE_SEARCH_QUERIES.get(consulta.key, ["{title} {system} game"])
        # Con el año, el buscador favorece la edición de la ficha: sin él, "Prince of Persia"
        # trae las portadas de Sands of Time o The Lost Crown (feature 022).
        titulo = f"{consulta.title} {consulta.year}" if consulta.year else consulta.title
        formatted_queries = [
            q.format(title=titulo, system=consulta.system)
            for q in queries
        ]

        images: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for query in formatted_queries:
            try:
                for result in _search_ddg_images(query):
                    url = result.get("image", "")
                    if url and url not in seen_urls and _is_trusted_url(url) and not _es_gif(url):
                        seen_urls.add(url)
                        images.append(result)
            except Exception:
                log.warning("Image search failed for '%s'", query, exc_info=True)

        if not images:
            search_url = (
                f"https://duckduckgo.com/?q={urlencode({'q': formatted_queries[0]})}"
                "&iar=images&iax=images&ia=images"
            )
            trace = ProviderTrace(self.nombre, self.tipo, "sin resultados")
            candidate = Candidato(
                id=f"image-search:{consulta.game_id}:{consulta.key}",
                key=consulta.key,
                kind="media",
                nombre=f"Buscar imágenes de \"{consulta.title}\" en DuckDuckGo",
                fuente=self.nombre,
                clase="referencia",
                origen_url=search_url,
                trace=trace,
            )
            return ProviderResult((candidate,), trace)

        trace = ProviderTrace(self.nombre, self.tipo, "ok")
        candidates = []
        for i, img in enumerate(images):
            candidates.append(Candidato(
                id=f"image-search:{consulta.game_id}:{consulta.key}:{i}",
                key=consulta.key,
                kind="media",
                nombre=f"Imagen {i+1}: {_extract_domain(img.get('image', ''))}",
                fuente=self.nombre,
                clase="aplicable",
                media_url=img.get("image", ""),
                preview_url=img.get("thumbnail", img.get("image", "")),
                origen_url=img.get("link", ""),
                trace=trace,
                meta={
                    "ancho": str(img.get("width", "")),
                    "alto": str(img.get("height", "")),
                    "titulo": img.get("title", ""),
                },
            ))

        return ProviderResult(candidates, trace)


def encaja_en(
    key: str,
    url: str,
    meta: Mapping[str, str],
    titulo: str,
    anio: str | None,
    sistema: str,
) -> bool:
    """Si un resultado del buscador sirve para el casillero ``key`` (ADR-0028).

    El buscador no sabe qué le pidieron: "arcade marquee" devuelve cajas. Ante la duda dice que
    no, porque un casillero vacío se ve y una imagen de otro juego queda en el gabinete.
    """
    proporcion = _proporcion(meta)
    limites = _PROPORCIONES.get(key)
    if proporcion is None or limites is None or not limites[0] <= proporcion <= limites[1]:
        return False
    titulo_resultado = meta.get("titulo", "")
    texto = f"{titulo_resultado} {url}".casefold()
    if _NO_ES_LA_IMAGEN.search(texto):
        return False
    pedidas = _TIENE_QUE_DECIR.get(key)
    if pedidas and not any(palabra in texto for palabra in pedidas):
        return False
    return _nombra_solo_al_juego(titulo_resultado, titulo, anio, sistema)


def _proporcion(meta: Mapping[str, str]) -> float | None:
    ancho, alto = meta.get("ancho", ""), meta.get("alto", "")
    if not (ancho.isdigit() and alto.isdigit()) or int(alto) == 0:
        return None
    return int(ancho) / int(alto)


def _nombra_solo_al_juego(
    titulo_resultado: str, titulo: str, anio: str | None, sistema: str,
) -> bool:
    """El título del resultado nombra este juego y nada más: ni una secuela, ni un mod, ni otra
    plataforma u otra época. Lo que sigue a " - " es el sitio. La URL no cuenta: trae años que
    son la fecha de la nota."""
    cabeza = normalizar(re.split(r"\s[-|–—]\s", titulo_resultado)[0])
    buscado = normalizar(titulo)
    if not buscado or buscado not in cabeza:
        return False
    genericas = _PALABRAS_GENERICAS | set(normalizar(sistema).split())
    anios = []
    for palabra in cabeza.replace(buscado, " ", 1).split():
        if re.fullmatch(r"(?:19|20)\d{2}", palabra):
            anios.append(int(palabra))
        elif palabra not in genericas:
            return False
    esperado = anio_entero(anio)
    if esperado is None or not anios:
        return True
    return any(abs(a - esperado) <= TOLERANCIA_EXACTO for a in anios)


def _es_gif(url: str) -> bool:
    """Un GIF del buscador no se ofrece: muchos son animados, y esos no entran a la ficha."""
    return urlparse(url).path.lower().endswith(".gif")


_busquedas: dict[str, list[dict[str, str]]] = {}
_busquedas_lock = threading.Lock()


def olvidar() -> None:
    with _busquedas_lock:
        _busquedas.clear()


def _search_ddg_images(query: str) -> list[dict[str, str]]:
    """Los resultados de una búsqueda, de memoria si ya se hizo entera mientras corre el proceso.

    Una búsqueda son minutos sumando los casilleros: sin esto, reabrir la galería o pasar de
    Imágenes a la galería los repetiría. Una búsqueda que cortó a la mitad no se guarda.
    """
    with _busquedas_lock:
        guardada = _busquedas.get(query)
    if guardada is not None:
        return guardada
    resultados, completa = _paginas_ddg(query)
    if completa and resultados:
        with _busquedas_lock:
            _busquedas[query] = resultados
    return resultados


def _paginas_ddg(query: str) -> tuple[list[dict[str, str]], bool]:
    """Todos los resultados de una búsqueda de DuckDuckGo Images, página por página, y si
    llegó al final.

    Termina cuando el buscador no da otra página, unas cinco en la práctica. Si una falla se
    conserva lo ya traído.
    """
    with httpx.Client(timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True) as client:
        resp = client.get(
            "https://duckduckgo.com/",
            params={"q": query, "iar": "images", "iax": "images", "ia": "images"},
        )
        resp.raise_for_status()

        vqd_match = re.search(r'vqd="([^"]+)"', resp.text)
        if not vqd_match:
            vqd_match = re.search(r'vqd=([0-9\-]+)', resp.text)

        if not vqd_match:
            return [], False

        vqd = vqd_match.group(1)

        api_resp = client.get(
            "https://duckduckgo.com/i.js",
            params={
                "l": "us-en",
                "o": "json",
                "q": query,
                "vqd": vqd,
                "f": ",,,,,",
                "p": "1",
            },
        )
        api_resp.raise_for_status()

        data = api_resp.json()
        resultados: list[dict[str, str]] = data.get("results", [])
        vistas = {r.get("image") for r in resultados}
        while siguiente := data.get("next"):
            time.sleep(_PAUSA_ENTRE_PAGINAS)
            try:
                api_resp = client.get(f"https://duckduckgo.com/{siguiente}&vqd={vqd}")
                api_resp.raise_for_status()
                data = api_resp.json()
            except (httpx.HTTPError, ValueError):
                log.warning("Image search cortó en una página de '%s'", query, exc_info=True)
                return resultados, False
            nuevos = [r for r in data.get("results", []) if r.get("image") not in vistas]
            if not nuevos:
                break
            vistas.update(r.get("image") for r in nuevos)
            resultados.extend(nuevos)
        return resultados, True


def _is_trusted_url(url: str) -> bool:
    """Check if URL is from a trusted domain."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in _TRUSTED_DOMAINS)


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    match = re.search(r"https?://([^/]+)", url)
    return match.group(1) if match else url
