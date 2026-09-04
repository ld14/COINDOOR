"""Cliente HTTP para Launchbox Games Database (scraping HTML).

No hay API pública. Se scraping ``gamesdb.launchbox-app.com`` que es
server-rendered (Blazor). Tres pasos:

1. Buscar: ``/games/results/{query}?platform={platform}``
2. Extraer el ID y slug del primer resultado que matchee por título + plataforma.
3. Imágenes: ``/games/images/{id}-{slug}`` → extraer URLs de imágenes.

Rate limit conservador: 0.5 s entre requests. Cloudflare puede bloquear.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx

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


def search_game(
    title: str,
    system: str,
    http: httpx.Client | None = None,
) -> LaunchboxSearchResult | None:
    """Busca un juego en Launchbox por título y plataforma.

    Intenta primero con el título completo, y si no encuentra nada,
    prueba con un título simplificado (sin sufijos comunes).
    """
    should_close = http is None
    if http is None:
        http = httpx.Client(timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True)
    try:
        # 1. Intento con título completo
        result = _search_and_parse(title, system, http)
        if result is not None:
            return result

        # 2. Fallback: título simplificado (quitar sufijos comunes)
        simplified = _simplify_title(title)
        if simplified != title:
            log.info("Launchbox: retrying with simplified title '%s'", simplified)
            result = _search_and_parse(simplified, system, http)
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

    parsed = _parse_search_results(resp.text, title, system)
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


def fetch_images(
    game_id: str,
    slug: str,
    http: httpx.Client | None = None,
) -> list[LaunchboxImage]:
    """Obtiene todas las imágenes de un juego desde su página de imágenes."""
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

    return _parse_images_page(resp.text, game_id, slug)


# ── Parsing helpers ────────────────────────────────────────────────────

def _build_search_query(title: str, system: str) -> str:
    """Construye la query URL para la búsqueda en Launchbox.

    Launchbox acepta ``query?platform=Arcade`` como filtro.
    Mapea nombres de sistema COINDOOR a nombres de plataforma Launchbox.
    """
    clean_title = re.sub(r"[^a-zA-Z0-9\s\-]", "", title).strip()
    words = clean_title.split()
    encoded = quote_plus("+".join(words))
    launchbox_platform = _SYSTEM_TO_LAUNCHBOX.get(system.lower(), system)
    platform = quote_plus(launchbox_platform) if launchbox_platform else ""
    if platform:
        return f"{encoded}?platform={platform}"
    return encoded


# Mapeo de sistemas COINDOOR → nombres de plataforma Launchbox
_SYSTEM_TO_LAUNCHBOX: dict[str, str] = {
    "arcade": "Arcade",
    "mame": "Arcade",
    "msdos": "MS-DOS",
    "ms-dos": "MS-DOS",
    "nes": "Nintendo Entertainment System",
    "snes": "Super Nintendo Entertainment System",
    "genesis": "Sega Genesis",
    "mega drive": "Sega Mega Drive",
    "game boy": "Nintendo Game Boy",
    "game boy advance": "Nintendo Game Boy Advance",
    "game boy color": "Nintendo Game Boy Color",
}


def _parse_search_results(
    html: str,
    expected_title: str,
    expected_system: str,
) -> LaunchboxSearchResult | None:
    """Extrae resultados del HTML de búsqueda.

    Patrón: ``<a href="/games/details/{id}-{slug}">`` con
    ``<p>{Platform}</p>`` y ``<h3>{Title}</h3>`` dentro de la card.
    """
    card_re = re.compile(
        r'<a\s+class="list-item[^"]*"\s+href="/games/details/(\d+)-([a-z0-9\-]+)">'
        r'(.*?)</a>',
        re.DOTALL | re.IGNORECASE,
    )

    expected_lower = expected_title.lower().strip()
    expected_sys_lower = expected_system.lower().strip()

    for match in card_re.finditer(html):
        gid, slug, card_html = match.groups()

        # Extraer título de <h3>
        title_match = re.search(r"<h3[^>]*>([^<]+)</h3>", card_html)
        if not title_match:
            continue
        card_title = _unescape_html(title_match.group(1)).strip()

        # Extraer plataforma de <p>
        platform_match = re.search(r"<p[^>]*>([^<]+)</p>", card_html)
        if not platform_match:
            continue
        card_platform = _unescape_html(platform_match.group(1)).strip()

        # Match por plataforma: exacto o normalizado
        # Evita que "Nintendo Entertainment System" matchee "Super Nintendo Entertainment System"
        card_sys_lower = card_platform.lower().strip()
        if expected_sys_lower and not _platform_match(expected_sys_lower, card_sys_lower):
            continue

        # Match por título: substring
        if expected_lower not in card_title.lower():
            continue

        # Extraer año de <div class="releaseDate"> → <h5>
        year = ""
        year_match = re.search(
            r'class="releaseDate".*?<h5[^>]*>(\d{4})</h5>',
            card_html,
            re.DOTALL,
        )
        if year_match:
            year = year_match.group(1)

        return LaunchboxSearchResult(
            game_id=gid,
            slug=slug,
            platform=card_platform,
            title=card_title,
            detail_url=f"{_BASE}/games/details/{gid}-{slug}",
            year=year,
        )

    return None


def _parse_images_page(
    html: str,
    game_id: str,
    slug: str,
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
        if category is None:
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
            category=category,
            field_key=CATEGORY_MAP[category][0],
            label=label,
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


def _unescape_html(text: str) -> str:
    """Decodifica entidades HTML básicas."""
    return (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#x2B;", "+")
        .replace("&#39;", "'")
    )
