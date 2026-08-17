from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

from backend.config import Settings

log = logging.getLogger(__name__)

_SEARCH_HEADERS = {
    "User-Agent": "COINDOOR/0.1 (+local research)",
}

_HTTP_TIMEOUT = 5.0

_TRUSTED_DOMAINS = frozenset({
    "archive.org",
    "retrocdn.net",
    "mobygames.com",
    "pcgamingwiki.com",
    "worldofpectrum.com",
    "retromagazines.com",
    "gamebase64.com",
    "atariage.com",
    "nesdev.org",
    "tcrf.net",
    "hiddenpalace.org",
    "romhacking.net",
    "gamemanuals.com",
    "manualslib.com",
    "eurogamer.net",
    "gamespot.com",
    "ign.com",
    "3djuegos.com",
    "meristation.com",
    "vandal.com",
    "hobbyconsolas.com",
})


@dataclass(frozen=True)
class ManualResult:
    title: str
    url: str
    source: str


def search_manuals(game_title: str, system: str, settings: Settings) -> list[ManualResult]:
    results: list[ManualResult] = []

    try:
        results = _search_archive(game_title)
    except Exception:
        log.warning("Archive.org failed for '%s'", game_title, exc_info=True)

    if not results:
        try:
            results = _search_archive_browse(game_title)
        except Exception:
            log.warning("Archive.org browse failed for '%s'", game_title, exc_info=True)

    if not results:
        try:
            results = _search_duckduckgo(game_title, system)
        except Exception:
            log.warning("DuckDuckGo failed for '%s'", game_title, exc_info=True)

    if not results:
        results = _fallback_links(game_title, system)

    return results[:10]


def _search_archive(game_title: str) -> list[ManualResult]:
    params = {
        "q": f'({game_title}) AND mediatype:texts AND format:"PDF"',
        "fl[]": "identifier,title",
        "sort[]": "downloads desc",
        "rows": "10",
        "output": "json",
    }
    with httpx.Client(timeout=_HTTP_TIMEOUT, headers=_SEARCH_HEADERS) as client:
        resp = client.get("https://archive.org/advancedsearch.php", params=params)
        resp.raise_for_status()

    results: list[ManualResult] = []
    for doc in resp.json().get("response", {}).get("docs", []):
        identifier = doc.get("identifier", "")
        title = doc.get("title", "Manual")
        url = f"https://archive.org/download/{identifier}"
        results.append(ManualResult(title=title, url=url, source="archive.org"))
    return results


def _search_archive_browse(game_title: str) -> list[ManualResult]:
    encoded = game_title.replace(" ", "%20")
    url = f"https://archive.org/search?query={encoded}&and[]=mediatype%3Atexts&and[]=format%3A%22PDF%22"
    with httpx.Client(timeout=_HTTP_TIMEOUT, headers=_SEARCH_HEADERS) as client:
        resp = client.get(url)
        resp.raise_for_status()

    results: list[ManualResult] = []
    for match in re.finditer(r'/details/([^"?]+)', resp.text):
        identifier = match.group(1)
        if identifier and identifier not in {r.url.split("/download/")[-1] for r in results if "/download/" in r.url}:
            results.append(ManualResult(
                title=f"{game_title} — {identifier}",
                url=f"https://archive.org/download/{identifier}",
                source="archive.org",
            ))
    return results[:10]


def _search_duckduckgo(game_title: str, system: str) -> list[ManualResult]:
    query = f'site:archive.org "{game_title}" {system} manual PDF'
    with httpx.Client(timeout=_HTTP_TIMEOUT, headers=_SEARCH_HEADERS) as client:
        resp = client.post("https://html.duckduckgo.com/html/", data={"q": query})
        resp.raise_for_status()

    results: list[ManualResult] = []
    for match in re.finditer(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text):
        href = match.group(1)
        title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        domain = _domain(href)
        if _is_trusted(domain):
            results.append(ManualResult(title=title, url=href, source=domain))
    return results


def _fallback_links(game_title: str, system: str) -> list[ManualResult]:
    encoded = game_title.replace(" ", "+")
    sys_encoded = system.replace(" ", "+")
    return [
        ManualResult(
            title=f"Archive.org: {game_title} ({system}) — manuales PDF",
            url=f"https://archive.org/search?query={encoded}+{sys_encoded}+manual&and[]=mediatype%3Atexts&and[]=format%3A%22PDF%22",
            source="archive.org",
        ),
        ManualResult(
            title=f"Archive.org: {game_title} — instrucciones",
            url=f"https://archive.org/search?query={encoded}+instructions&and[]=mediatype%3Atexts",
            source="archive.org",
        ),
        ManualResult(
            title=f"Retro CDN: {game_title}",
            url="https://retrocdn.net",
            source="retrocdn.net",
        ),
        ManualResult(
            title=f"Game Manuals: {game_title}",
            url="https://www.gamemanuals.com",
            source="gamemanuals.com",
        ),
    ]


def _is_trusted(domain: str) -> bool:
    d = domain.lower()
    return any(trusted in d for trusted in _TRUSTED_DOMAINS)


def _domain(url: str) -> str:
    match = re.search(r"https?://([^/]+)", url)
    return match.group(1) if match else url
