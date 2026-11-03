"""Cliente HTTP para Launchbox Games Database (scraping HTML).

No hay API pública. Se scraping ``gamesdb.launchbox-app.com`` que es
server-rendered (Blazor). Cuatro pasos:

1. Buscar: ``/games/results/{query}?platform={platform}``
2. Elegir el juego entre las tarjetas de esa plataforma con la regla común de
   ``coincidencia`` (título exacto, año), la misma que MobyGames. Sin tarjeta exacta, la
   página de cada candidata dice su año, sus nombres alternativos y si es un DLC.
3. Ficha: ``/games/details/{id}-{slug}`` → desarrolladores, editores, géneros, jugadores y año.
4. Imágenes: ``/games/images/{id}-{slug}`` → extraer URLs de imágenes.

Rate limit conservador: 0.5 s entre requests. Cloudflare puede bloquear.
"""

from __future__ import annotations

import html as html_lib
import logging
import re
import threading
import time
from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx

from backend.lib.domain.plataformas import plataforma
from backend.lib.providers import coincidencia
from backend.lib.providers.scraping import pagina_desde_html

log = logging.getLogger(__name__)

_BASE = "https://gamesdb.launchbox-app.com"
_IMG_CDN = "https://images.launchbox-app.com"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}
_TIMEOUT = 15.0

# ── Categorías Launchbox → COINDOOR field keys ─────────────────────────
# Cada categoría de Launchbox se mapea a un campo de fielddefs.
# Se usa substring match (case-insensitive) contra data-title.
CATEGORY_MAP: dict[str, tuple[str, str]] = {
    # field_key, label display
    "box - front": ("caratula", "Carátula"),
    "box - 3d": ("caratula", "Carátula 3D"),
    "box - front - reconstructed": ("caratula", "Carátula Reconstruida"),
    "cart - front": ("caratula", "Cartucho"),
    "fanart - box - front": ("caratula", "Fanart Carátula"),
    "arcade - marquee": ("marquesina", "Marquesina"),
    "banner": ("marquesina", "Banner"),
    "poster": ("poster", "Póster"),
    "advertisement flyer - front": ("poster", "Flyer"),
    "clear logo": ("logo", "Logo"),
    "screenshot - gameplay": ("captura", "Captura Gameplay"),
    "screenshot - game title": ("captura", "Captura Título"),
    "screenshot - game select": ("captura", "Captura Selección"),
    "screenshot - game over": ("captura", "Captura Game Over"),
    "screenshot - high scores": ("captura", "Captura High Scores"),
    "arcade - cabinet": ("captura", "Gabinete Arcade"),
    "arcade - control panel": ("captura", "Panel Control"),
}


@dataclass(frozen=True)
class LaunchboxImage:
    """Una imagen encontrada en Launchbox Games Database."""

    media_url: str
    preview_url: str
    category: str
    field_key: str
    label: str
    game_url: str


@dataclass
class LaunchboxSearchResult:
    """Resultado de búsqueda: ID, slug, plataforma y URL de detalle."""

    game_id: str
    slug: str
    platform: str
    title: str
    detail_url: str
    year: str = ""
    alternos: tuple[str, ...] = ()


@dataclass(frozen=True)
class LaunchboxFicha:
    """Los datos de identidad de la página de un juego."""

    url: str
    developers: tuple[str, ...]
    publishers: tuple[str, ...]
    genres: tuple[str, ...]
    max_players: str
    year: str
    alternos: tuple[str, ...] = ()
    tipo: str = ""


def search_game(
    title: str,
    system: str,
    http: httpx.Client | None = None,
    anio: str | None = None,
) -> LaunchboxSearchResult | None:
    """Busca un juego en Launchbox por título, plataforma y, si se sabe, año.

    Intenta primero con el título completo, y si no encuentra nada,
    prueba con un título simplificado (sin sufijos comunes).
    """
    should_close = http is None
    if http is None:
        http = httpx.Client(timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True)
    try:
        # 1. Intento con título completo
        result = _search_and_parse(title, system, http, anio)
        if result is not None:
            return result

        # 2. Fallback: título simplificado (quitar sufijos comunes)
        simplified = _simplify_title(title)
        if simplified != title:
            log.info("Launchbox: retrying with simplified title '%s'", simplified)
            result = _search_and_parse(simplified, system, http, anio)
            if result is not None:
                return result

        return None
    finally:
        if should_close:
            http.close()


def _search_and_parse(
    title: str,
    system: str,
    http: httpx.Client,
    anio: str | None = None,
) -> LaunchboxSearchResult | None:
    """Una sola intento de búsqueda y parse."""
    query = _build_search_query(title, system)
    url = f"{_BASE}/games/results/{query}"
    try:
        resp = http.get(url)
        resp.raise_for_status()
    except Exception:
        log.warning("Launchbox search failed for '%s' (url=%s)", title, url, exc_info=True)
        return None

    tarjetas = _con_su_pagina(_tarjetas_de(resp.text, system), title, http)
    parsed = _elegir(tarjetas, title, anio)
    if parsed is None:
        log.info(
            "Launchbox: parse found no match for '%s' on '%s' (status=%d)",
            title, system, resp.status_code,
        )
    else:
        log.info(
            "Launchbox: parsed game %s-%s (%s) on %s",
            parsed.game_id, parsed.slug, parsed.title, parsed.platform,
        )
    return parsed


# Sufijos comunes que Launchbox no usa en sus títulos
_SUFFIXES_TO_STRIP = [
    " arcade game",
    " arcade",
    " game",
]


def _simplify_title(title: str) -> str:
    """Quita sufijos comunes del título para mejorar el match en Launchbox."""
    result = title
    for suffix in _SUFFIXES_TO_STRIP:
        if result.lower().endswith(suffix):
            result = result[: -len(suffix)].strip()
            break
    return result


_fichas: dict[str, LaunchboxFicha] = {}
_fichas_lock = threading.Lock()


def olvidar() -> None:
    with _fichas_lock:
        _fichas.clear()


def fetch_details(
    game_id: str,
    slug: str,
    http: httpx.Client | None = None,
) -> LaunchboxFicha | None:
    """La identidad de la página del juego; queda en memoria mientras corre el proceso."""
    with _fichas_lock:
        guardada = _fichas.get(game_id)
    if guardada is not None:
        return guardada
    url = f"{_BASE}/games/details/{game_id}-{slug}"
    should_close = http is None
    if http is None:
        http = httpx.Client(timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True)
    try:
        resp = http.get(url)
        resp.raise_for_status()
    except Exception:
        log.warning("Launchbox details fetch failed for %s-%s", game_id, slug, exc_info=True)
        return None
    finally:
        if should_close:
            http.close()
    ficha = _parse_details(resp.text, url)
    with _fichas_lock:
        _fichas[game_id] = ficha
    return ficha


def fetch_images(
    game_id: str,
    slug: str,
    http: httpx.Client | None = None,
    *,
    todas: bool = False,
) -> list[LaunchboxImage]:
    """Las imágenes de un juego que van en un casillero o, con ``todas``, las de cualquier
    categoría: contratapas, discos o fanart no van en un casillero, pero sí en la galería."""
    url = f"{_BASE}/games/images/{game_id}-{slug}"

    should_close = http is None
    if http is None:
        http = httpx.Client(timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True)
    try:
        resp = http.get(url)
        resp.raise_for_status()
    except Exception:
        log.warning("Launchbox images fetch failed for %s-%s", game_id, slug, exc_info=True)
        return []
    finally:
        if should_close:
            http.close()

    return _parse_images_page(resp.text, game_id, slug, todas=todas)


# ── Parsing helpers ────────────────────────────────────────────────────

def _build_search_query(title: str, system: str) -> str:
    """Construye la query URL para la búsqueda en Launchbox.

    Launchbox acepta ``query?platform=Arcade`` como filtro.
    Mapea nombres de sistema COINDOOR a nombres de plataforma Launchbox.
    """
    clean_title = re.sub(r"[^a-zA-Z0-9\s\-]", "", title).strip()
    words = clean_title.split()
    encoded = quote_plus("+".join(words))
    fila = plataforma(system)
    # Fuera del catálogo el sistema va tal cual; en el catálogo sin equivalencia, sin filtro.
    launchbox_platform = system if fila is None else fila.sitios["launchbox"]
    platform = quote_plus(launchbox_platform) if launchbox_platform else ""
    if platform:
        return f"{encoded}?platform={platform}"
    return encoded


def _parse_search_results(
    html: str,
    expected_title: str,
    expected_system: str,
    anio: str | None = None,
) -> LaunchboxSearchResult | None:
    """Elige el juego entre las tarjetas de la plataforma, con la regla común.

    La lista viene en orden alfabético: el primer título que *contiene* el buscado puede ser
    otro juego ("4D Prince of Persia" antes que "Prince of Persia"). Por eso no se mira la
    posición sino el título y el año, como en MobyGames.
    """
    return _elegir(_tarjetas_de(html, expected_system), expected_title, anio)


# Entre dos páginas de juego que hay que bajar de verdad; las que están en memoria no esperan.
_PAUSA_ENTRE_PAGINAS = 0.5


def _tarjetas_de(html: str, system: str) -> list[LaunchboxSearchResult]:
    expected_sys_lower = system.lower().strip()
    return [
        t
        for t in _parse_cards(html)
        # Evita que "Nintendo Entertainment System" matchee "Super Nintendo Entertainment System"
        if not expected_sys_lower or _platform_match(expected_sys_lower, t.platform.lower())
    ]


def _elegir(
    tarjetas: list[LaunchboxSearchResult],
    title: str,
    anio: str | None,
) -> LaunchboxSearchResult | None:
    buscado = coincidencia.anio_entero(anio)

    def titulos(t: LaunchboxSearchResult) -> tuple[str, ...]:
        # Un remake declara el nombre del original ("Space Quest" en el de 1991): el alias solo
        # vale con el año de la ficha. Con el título real alcanza, como en MobyGames.
        propio = coincidencia.anio_entero(t.year)
        if buscado is None or (
            propio is not None and abs(propio - buscado) <= coincidencia.TOLERANCIA_EXACTO
        ):
            return (t.title, *t.alternos)
        return (t.title,)

    return coincidencia.elegir(
        tarjetas,
        title,
        anio,
        titulos_de=titulos,
        principal_de=lambda t: t.title,
        anio_de=lambda t: coincidencia.anio_entero(t.year),
    )


def _contienen(
    tarjetas: list[LaunchboxSearchResult],
    title: str,
) -> list[LaunchboxSearchResult]:
    """Las tarjetas con todas las palabras del título, si ninguna es exacta."""
    buscado = coincidencia.normalizar(title)
    if not buscado or any(coincidencia.normalizar(t.title) == buscado for t in tarjetas):
        return []
    palabras = set(buscado.split())
    return [t for t in tarjetas if palabras <= set(coincidencia.normalizar(t.title).split())]


def _con_su_pagina(
    tarjetas: list[LaunchboxSearchResult],
    title: str,
    http: httpx.Client,
) -> list[LaunchboxSearchResult]:
    """Sin tarjeta exacta, completa las candidatas con la página de cada juego.

    Se hace antes de elegir: la lista no siempre trae el año ("Sid Meier's Civilization") y una
    tarjeta con año ganaría a la correcta sin él. La página da también los nombres alternativos
    ("Wing Commander" en *The 3-D Space Combat Simulator*) y si es un DLC (*The Secret
    Missions*), que el título y el año no separan. Una página fallida corta: si el sitio
    bloquea, seguir pidiendo no ayuda.
    """
    dlc: set[str] = set()
    for tarjeta in _contienen(tarjetas, title):
        with _fichas_lock:
            en_memoria = tarjeta.game_id in _fichas
        ficha = fetch_details(tarjeta.game_id, tarjeta.slug, http)
        if ficha is None:
            break
        tarjeta.year = tarjeta.year or ficha.year
        tarjeta.alternos = ficha.alternos
        if ficha.tipo.casefold() == "dlc":
            dlc.add(tarjeta.game_id)
        if not en_memoria:
            time.sleep(_PAUSA_ENTRE_PAGINAS)
    return [t for t in tarjetas if t.game_id not in dlc]


def _parse_cards(html: str) -> list[LaunchboxSearchResult]:
    """Todas las tarjetas del HTML de búsqueda, en orden.

    Patrón: ``<a href="/games/details/{id}-{slug}">`` con
    ``<p>{Platform}</p>`` y ``<h3>{Title}</h3>`` dentro de la card.
    """
    card_re = re.compile(
        r'<a\s+class="list-item[^"]*"\s+href="/games/details/(\d+)-([a-z0-9\-]+)">'
        r'(.*?)</a>',
        re.DOTALL | re.IGNORECASE,
    )
    tarjetas: list[LaunchboxSearchResult] = []
    for match in card_re.finditer(html):
        gid, slug, card_html = match.groups()

        title_match = re.search(r"<h3[^>]*>([^<]+)</h3>", card_html)
        platform_match = re.search(r"<p[^>]*>([^<]+)</p>", card_html)
        if not title_match or not platform_match:
            continue

        # Extraer año de <div class="releaseDate"> → <h5>
        year_match = re.search(
            r'class="releaseDate".*?<h5[^>]*>(\d{4})</h5>',
            card_html,
            re.DOTALL,
        )
        tarjetas.append(LaunchboxSearchResult(
            game_id=gid,
            slug=slug,
            platform=_unescape_html(platform_match.group(1)).strip(),
            title=_unescape_html(title_match.group(1)).strip(),
            detail_url=f"{_BASE}/games/details/{gid}-{slug}",
            year=year_match.group(1) if year_match else "",
        ))
    return tarjetas


# Etiqueta de la página del juego → campo de ``LaunchboxFicha``.
_ETIQUETAS_FICHA = {
    "developers": "developers",
    "developer": "developers",
    "publishers": "publishers",
    "publisher": "publishers",
    "genre": "genres",
    "genres": "genres",
    "max players": "max_players",
    "release date": "year",
    "alternate names": "alternos",
    "game type": "tipo",
}


def _parse_details(html: str, url: str) -> LaunchboxFicha:
    """Pares ``dt``/``dd`` de la página del juego. Los valores son enlaces y cada uno aparece
    dos veces en el texto: se toman una vez, en orden. Los nombres alternativos son una lista
    sin enlaces."""
    page = pagina_desde_html(html, url=url)
    valores: dict[str, list[str]] = {}
    for dt in page.css("dt"):
        campo = _ETIQUETAS_FICHA.get(" ".join(str(dt.get_all_text()).split()).lower())
        dd = dt.xpath("following-sibling::dd[1]")
        if campo is None or not dd or campo in valores:
            continue
        piezas = dd[0].css("a") or dd[0].css("li")
        textos = [" ".join(str(p.get_all_text()).split()) for p in piezas]
        if not any(textos):
            textos = [" ".join(str(dd[0].get_all_text()).split())]
        unicos: list[str] = []
        for texto in textos:
            if texto and texto not in unicos and "no information" not in texto.lower():
                unicos.append(texto)
        valores[campo] = unicos
    anio = re.search(r"\b(\d{4})\b", " ".join(valores.get("year", [])))
    return LaunchboxFicha(
        url=url,
        developers=tuple(valores.get("developers", [])),
        publishers=tuple(valores.get("publishers", [])),
        genres=tuple(valores.get("genres", [])),
        max_players=next(iter(valores.get("max_players", [])), ""),
        year=anio.group(1) if anio else "",
        alternos=tuple(valores.get("alternos", [])),
        tipo=next(iter(valores.get("tipo", [])), ""),
    )


def _parse_images_page(
    html: str,
    game_id: str,
    slug: str,
    *,
    todas: bool = False,
) -> list[LaunchboxImage]:
    """Extrae imágenes del HTML de la página de imágenes.

    Cada imagen tiene:
    - ``href="https://images.launchbox-app.com/{uuid}.{ext}"`` (full size)
    - ``data-title="Game Name - Category (Region)"``
    - ``src="https://images.launchbox-app.com/{uuid_thumb}.{ext}"`` (thumbnail)
    """
    images: list[LaunchboxImage] = []
    seen_urls: set[str] = set()

    # Patrón: cada <a> con data-title y href a images.launchbox-app.com
    image_re = re.compile(
        r'<a\s[^>]*href="(https://images\.launchbox-app\.com/[^"]+)"'
        r'[^>]*data-title="([^"]+)"'
        r'[^>]*>',
        re.DOTALL | re.IGNORECASE,
    )

    # Thumbnail pattern dentro del mismo <a>
    thumb_re = re.compile(
        r'<img\s+class="imageCard"[^>]+src="(https://images\.launchbox-app\.com/[^"]+)"',
        re.IGNORECASE,
    )

    for match in image_re.finditer(html):
        full_url, data_title = match.group(1), match.group(2)

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # Extraer categoría del data-title
        # Formato: "Game Name - Category (Region)" o "Game Name - Category"
        category, label = _extract_category(data_title)
        if category is None and not todas:
            continue

        # Buscar thumbnail en el contexto cercano
        # Miramos los 2000 chars después del match
        search_start = match.end()
        search_end = min(search_start + 2000, len(html))
        chunk = html[search_start:search_end]
        thumb_match = thumb_re.search(chunk)
        preview_url = thumb_match.group(1) if thumb_match else full_url

        images.append(LaunchboxImage(
            media_url=full_url,
            preview_url=preview_url,
            category=category or "",
            field_key=CATEGORY_MAP[category][0] if category else "",
            label=label if category else _categoria_sin_mapear(data_title),
            game_url=f"{_BASE}/games/images/{game_id}-{slug}",
        ))

    return images


def _platform_match(expected: str, card: str) -> bool:
    """Check if the expected platform matches the card platform.

    Uses exact match after normalization. Avoids false positives where
    "Nintendo Entertainment System" matches "Super Nintendo Entertainment System".
    """
    if expected == card:
        return True
    # Handle common aliases: "nes" == "nintendo entertainment system"
    _ALIASES: dict[str, set[str]] = {
        "arcade": {"arcade"},
        "mame": {"arcade"},
        "msdos": {"ms-dos"},
        "ms-dos": {"msdos"},
        "nes": {"nintendo entertainment system"},
        "nintendo entertainment system": {"nes"},
        "snes": {"super nintendo entertainment system"},
        "super nintendo entertainment system": {"snes"},
        "genesis": {"sega genesis", "mega drive"},
        "mega drive": {"sega genesis", "genesis"},
        "game boy": {"nintendo game boy"},
        "nintendo game boy": {"game boy"},
        "game boy advance": {"nintendo game boy advance"},
        "nintendo game boy advance": {"game boy advance"},
        "game boy color": {"nintendo game boy color"},
        "nintendo game boy color": {"game boy color"},
    }
    aliases = _ALIASES.get(expected, set())
    return card in aliases


def _extract_category(data_title: str) -> tuple[str | None, str]:
    """Extrae la categoría de un data-title de Launchbox.

    Formato: "Game Name - Category (Region)" o "Game Name - Category"
    Retorna (category_key, label) o (None, "") si no matchea.
    """
    # Quitar el nombre del juego (todo antes del primer " - ")
    parts = data_title.split(" - ", 1)
    if len(parts) < 2:
        return None, ""

    remainder = parts[1].strip()

    # Quitar región entre paréntesis al final
    remainder_clean = re.sub(r"\s*\([^)]*\)\s*$", "", remainder).strip().lower()

    for cat_key, (_, label) in CATEGORY_MAP.items():
        if cat_key in remainder_clean:
            return cat_key, label

    return None, ""


def _categoria_sin_mapear(data_title: str) -> str:
    """"Prince of Persia - Box - Back Image (Europe)" da "Box - Back (Europe)"."""
    resto = data_title.split(" - ", 1)[-1]
    return re.sub(r"\s+Image\b", "", _unescape_html(resto)).strip()


def _unescape_html(text: str) -> str:
    """Decodifica entidades HTML. Launchbox escribe el apóstrofo como ``&#x27;``: con una
    lista a mano, "Sid Meier's Civilization" quedaba "Sid Meier&#x27;s Civilization"."""
    return html_lib.unescape(text)
