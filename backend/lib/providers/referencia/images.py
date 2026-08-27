from __future__ import annotations

import logging
import re
from typing import Literal
from urllib.parse import urlencode

import httpx

from backend.lib.providers.base import Candidato, Consulta, Limite, ProviderResult, ProviderTrace

log = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

_TIMEOUT = 10.0

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
        formatted_queries = [
            q.format(title=consulta.title, system=consulta.system)
            for q in queries
        ]

        images = []
        seen_urls = set()

        for query in formatted_queries:
            if len(images) >= 10:
                break
            try:
                for result in _search_ddg_images(query):
                    url = result.get("image", "")
                    if url and url not in seen_urls and _is_trusted_url(url):
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
                kind="referencia",
                nombre=f"Buscar imágenes de \"{consulta.title}\" en DuckDuckGo",
                fuente=self.nombre,
                clase="referencia",
                origen_url=search_url,
                trace=trace,
            )
            return ProviderResult((candidate,), trace)

        trace = ProviderTrace(self.nombre, self.tipo, "ok")
        candidates = []
        for i, img in enumerate(images[:10]):
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
            ))

        return ProviderResult(candidates, trace)


def _search_ddg_images(query: str) -> list[dict[str, str]]:
    """Search DuckDuckGo Images and return image results."""
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
            return []

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
        return data.get("results", [])


def _is_trusted_url(url: str) -> bool:
    """Check if URL is from a trusted domain."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in _TRUSTED_DOMAINS)


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    match = re.search(r"https?://([^/]+)", url)
    return match.group(1) if match else url
