from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from urllib.parse import quote_plus

import httpx

from backend.api.schemas import MagazineAppearance
from backend.config import Settings
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.client import OpenAiCompatibleClient
from backend.store.cuotas import QuotasStore

log = logging.getLogger(__name__)

_SEARCH_HEADERS = {
    "User-Agent": "COINDOOR/0.1 (+local research)",
}

_HTTP_TIMEOUT = 5.0
_ARCHIVE_TIMEOUT = 3.0

_TRUSTED_DOMAINS = frozenset({
    "archive.org",
    "retrocdn.net",
    "mobygames.com",
    "pcgamingwiki.com",
    "worldofpectrum.com",
    "retromagazines.com",
    "igitalpress.com",
    "thegamersroom.com",
    "gaming alexandria.com",
    "intellivisionaries.com",
    "computermagcollection.com",
    "magazinesfromspace.com",
    "retro-mag.com",
    "digitalgame museum.org",
    "gamebase64.com",
    "sector7.com.rs",
    "zabetha.com",
    "rgoad.fr",
    "planeta sinclair.com",
    "sinclair.org.uk",
    "cpcwiki.eu",
    "amstrad.es",
    "msx.org",
    "zx-spectrum .info",
    "6502.org",
    "atariage.com",
    "nesdev.org",
    "sm64.org",
    "tcrf.net",
    "cutstuff.net",
    "doorgame s.com",
    "romhacking.net",
    "hiddenpalace.org",
    "vgmuseum.com",
    "digital foundry.com",
    "eurogamer.net",
    "rockpapershotgun.com",
    "pcgamer.com",
    "gamespot.com",
    "ign.com",
    "eurogamer.es",
    "3djuegos.com",
    "meri station.com",
    "vandal.com",
    "hobbyconsolas.com",
    "levelup.com",
    "gamedeveloper.com",
})


@dataclass(frozen=True)
class MagazineSearchResult:
    title: str
    url: str
    source: str
    magazine: str
    appearance: MagazineAppearance | None = None
    links: dict[str, str] = field(default_factory=dict)


@dataclass
class _SearchState:
    seen_urls: set[str] = field(default_factory=set)
    results: list[MagazineSearchResult] = field(default_factory=list)
    magazines_found: set[str] = field(default_factory=set)


def search_magazines(game_title: str, system: str, settings: Settings) -> list[MagazineSearchResult]:
    log.info("Iniciando búsqueda de revistas para '%s' (%s)", game_title, system)
    state = _SearchState()

    try:
        _phase1_ai_identify(game_title, system, state, settings)
    except Exception:
        log.warning("AI identification failed", exc_info=True)

    log.info("Fase 1 completa: %d apariciones identificadas por IA", len([r for r in state.results if r.appearance]))

    try:
        _phase2_digitized(game_title, state)
    except Exception:
        log.warning("Phase 2 failed (archive.org timeout)", exc_info=True)

    log.info("Fase 2 completa: %d resultados totales", len(state.results))

    if not state.results:
        try:
            _phase3_direct(game_title, state)
        except Exception:
            log.warning("Phase 3 failed", exc_info=True)

        log.info("Fase 3 completa: %d resultados totales", len(state.results))

    if not state.results:
        state.results = _fallback_links(game_title, system)
        log.info("Usando links de fallback: %d links", len(state.results))

    log.info("Búsqueda finalizada: %d resultados para '%s'", len(state.results), game_title)
    return state.results


def _phase1_ai_identify(game_title: str, system: str, state: _SearchState, settings: Settings) -> None:
    """Use AI to identify which magazine issues contain the game."""
    if not settings.ai_primary_base_url or not settings.ai_primary_api_key:
        log.info("No AI config, skipping magazine identification")
        return

    log.info("Fase 1: consultando IA para identificar revistas de '%s'...", game_title)
    prompt = f"""Eres un historiador de videojuegos con conocimiento profundo de la prensa especializada iberoamericana. Identifica en qué revistas de videojuegos apareció el juego "{game_title}" para la plataforma {system}.

CATÁLOGO COMPLETO DE REVISTAS DE REFERENCIA:

=== ESPAÑA - 80s ORDENADORES (8 bits) ===
- MicroHobby (1984-1992, ZX Spectrum, semanal/quincenal/mensual)
- Micromanía (1985-2024, todos los ordenadores, la más longeva)
- Input Sinclair (1983-1987, Sinclair)
- Tu Micro (1984-, informática general)
- MSX Magazine (España, MSX)
- Amstrad Semanal (España, Amstrad CPC)
- Amstrad User / Amstrad-Sinclair Ocio (España, Amstrad)
- Club Commodore (España, Commodore 64)
- Load'N'Run (España, carga de juegos)
- Carga y Juega (España, carga de juegos)
- Spectrum Magazine (España, ZX Spectrum)
- Software en Acción (España, 8/16 bits)

=== ESPAÑA - 90s PRIMERA MITAD (consolas 16 bits) ===
- Hobby Consolas (1991-presente, TODAS las plataformas, la más vendida de España)
- Super Juegos / Superjuegos (1992-2001, análisis detallados 16/32 bits)
- Nintendo Acción (1992-2001, oficial Nintendo: NES, SNES, Game Boy, N64)
- Todo Sega (1992-, dedicada a Sega: Genesis, Master System, Saturn)
- Mega Consolas / Mega Consolas Clásicas (1990-1998, Sega focused)
- Game (1993-2001, generalista multiplataforma)
- Game Fan (1994-1998, consolas)
- Consola Clásica (1993-1997, retro y clásicos)
- Videomanía / Videomanias (1990-1995, temprana)
- Gametro (1992-1996)
- Loco Journal (1995-2000)
- Press Start (1996-2000)
- ClickJuegos (1998-2003)
- Zona Nintendo (2000-2006, especializada Nintendo)
- Todo Nintendo (España, Nintendo)
- Nintendomanía (España, Nintendo)
- Sonic (revista, España, Sega)
- Play (revista, España)

=== ESPAÑA - 90s PC ===
- PC Juegos / PC Juego (1990-1999)
- PC Manía / PCManía (1992-2005)
- OK Computer (1995-2000, PC general)
- Computermagazine (1988-1996)
- CD Mega / Mega PC (1993-1997, PC con CD)
- Informática CD (1993-1998)
- PC Games (1991-1999)
- PC Users (España)
- GameReport (España)

=== ESPAÑA - ERA PLAYStation (finales 90s) ===
- PlayManía (1999-2022, PlayStation focused, la más vendida de PS)
- PlanetStation (1998-, PlayStation guías y trucos)
- PlayStation Magazine / Revista Oficial PlayStation (Grupo Zeta)
- Loading (1999-)
- DualPixel (España)

=== ESPAÑA - 2000s ===
- Edge (España, 2006-2009, edición local de UK)
- GamesTM (España, 2012-, edición local de UK)
- Marca Player (2008-, Unidad Editorial)
- Retro Gamer (España, retrogaming)
- NGamer (España, Nintendo)
- GameLive PC (España, PC)
- ScreenFun (España)
- Top Games (España)
- Pocket Boy (España)
- Games World (España)
- Dreamplanet (España, Dreamcast)
- Revista Oficial Dreamcast (España)
- Revista Oficial PlayStation 2 (España)
- Revista Oficial Xbox (España)
- Revista Oficial Xbox 360 (España)
- HobbyGames (2002-2010, juegos de mesa y videojuegos)
- MeriStation (1999-2012, también web)
- Vandal (1997-presente, también web)
- 3DJuegos (1996-presente, también web)

=== LATINOAMÉRICA - MÉXICO ===
- Club Nintendo México (1991-2019, oficial Nintendo, la más longeva de Latam)
- EGM en español (2002-2008, multiconsola, licencia de Ziff Davis)
- Atomix (1999-2009 impreso, multiconsola, una de las primeras de Latam)
- Video Tips (México, videojuegos)
- GamePro en español (México, ediciones internacionales)
- Nintendo World (México, oficial Nintendo)
- Megaconsolas (México)
- Xbox World (México)
- PlayStation World (México)

=== LATINOAMÉRICA - ARGENTINA ===
- Next Level (1997-2001, consolas, antecedente de Loaded)
- Xtreme PC (1997-, PC)
- Loaded / Malditos Nerds (2004-presente, multiconsola, muy popular)
- Irrompibles (Argentina)
- Nuke (Argentina, manga/anime y videojuegos)
- Play & Share (Argentina)

=== BRASIL (portugués pero mercado hispanohablante lo conoce) ===
- Ação Games (1991-2002, pionera en Brasil)
- Videogame (1991-1996, Editora Sigla)
- Supergame (1991-1994, Sega focused)
- SuperGamePower (1994-2005, fusión Sega+Nintendo)
- GamePower (1993-1994, Nintendo focused)
- ProGames (Brasil, locadoras)
- Gamers (Brasil, Editora Escala)
- Nintendo World (Brasil, oficial Nintendo)
- PSWorld (Brasil, oficial PlayStation)
- Xbox (Brasil, oficial Xbox)

=== INTERNACIONALES (ediciones en español o relevantes) ===
- Electronic Gaming Monthly / EGM (1988-, USA, ediciones internacionales)
- GamePro (1989-2015, USA, ediciones internacionales incluida España)
- Official PlayStation Magazine (1997-2017, UK, ediciones en español)
- Official Xbox Magazine (2001-2015, UK, ediciones en español)
- Computer and Video Games / CVG (1981-2004, UK)
- GamesTM (2002-2017, UK)
- Retro Gamer (2005-presente, UK, retrogaming global)
- Nintendo Power (1988-2012, USA, oficial Nintendo)

=== REVISTAS RETRO ACTUALES (las más importantes) ===
- Retro Gamer España (2011-presente, Axel Springer, retrogaming)
- Pixels / Hecho con Pixels (2024-presente, José Luis Sanz, retro 80s/90s)
- Microhobby (relanzamiento 2026, Hecho con Pixels, formato sábana, retro)
- Micromanía (relanzamiento 2026, Hecho con Pixels, formato sábana, retro)
- Loading (2da era, Game Press, actualidad + retro)
- Retro Gamer UK (2004-presente, Future, la más longeva de retro)
- Retro Gamer Deutschland (2012-presente, alemán)
- Retro Gamer Italia (2025-presente, italiano)
- Old School Gamer Magazine (2017-, USA, retro)
- RETRO Fusion (Norteamérica, sindicación de Retro Gamer UK)
- Retro (Alemania, 2006-presente, retro)
- Return (Alemania, 2009-presente, retro)
- VideoGamer RETRO (Francia, 2020-presente, retro)
- Retro Gamer Collection (Francia, 2020-presente, retro)
- Retro (Polonia, 2024-presente, retro)
- Replay (Argentina, 2016-presente, retro, investigación histórica)

=== REVISTAS ACTUALES CON SECCIONES RETRO ===
- Hobby Consolas (sección "Retro Hobby")
- Edge (contenido retro)
- PC Gamer (contenido retro)

ESTRUCTURA DE RESPUESTA - JSON array:
[
  {{
    "magazineName": "Nombre exacto de la revista (ej: 'Hobby Consolas', 'Micromanía', 'Club Nintendo México')",
    "country": "país de origen (ej: 'España', 'México', 'Argentina', 'Brasil', 'UK', 'USA')",
    "language": "español|portugués|inglés",
    "issueNumber": "número de issue (string, vacío si se desconoce)",
    "date": "fecha aproximada de publicación (ej: '1993', '1993-06', 'Q2 1993', 'primera mitad 1994')",
    "contentType": "review|preview|articulo|entrevista|guia|noticia|trucos",
    "appearanceType": "portada|preview|review|articulo|guia|entrevista|noticia|trucos"
  }}
]

REGLAS:
1. Piensa en TODAS las revistas que cubrieron esa plataforma/era/región, no solo las más famosas
2. Un juego de NES puede aparecer en: Nintendo Acción, Hobby Consolas, Mega Consolas, Game Fan, Club Nintendo México, Ação Games, etc.
3. Un juego de SNES puede aparecer en: Super Juegos, Nintendo Acción, Hobby Consolas, Mega Consolas, Club Nintendo México, SuperGamePower, etc.
4. Un juego de Genesis/Mega Drive puede aparecer en: Mega Consolas, Todo Sega, Game Fan, Hobby Consolas, Club Nintendo México, Supergame, etc.
5. Un juego de Game Boy puede aparecer en: Nintendo Acción, Zona Nintendo, Club Nintendo México, etc.
6. Un juego de arcade/MAME puede aparecer en: Micromanía, PC Juegos, Hobby Consolas, etc.
7. Un juego de PlayStation puede aparecer en: PlayManía, PlanetStation, Revista Oficial PlayStation, Club Nintendo México, Loaded, etc.
8. Un juego de N64 puede aparecer en: Nintendo Acción, Zona Nintendo, Club Nintendo México, etc.
9. Los juegos populares suelen tener múltiples apariciones en diferentes revistas de diferentes países
10. Incluye revistas latinas (México, Argentina, Brasil) si el juego fue popular en esa región
11. Incluye revistas de ordenador si el juego tuvo versión PC
12. Responde SOLO el JSON, sin explicaciones ni texto adicional
13. Prioriza las más relevantes por orden cronológico
14. Si no estás seguro de un número de issue específico, deja issueNumber vacío pero incluye la revista
15. NO inventes revistas que no existieron. Solo usa las del catálogo o revistas reales que conozcas"""

    try:
        quotas = QuotasStore(settings.quotas_path)
        http = ProviderHttpClient(
            provider="ia",
            limite=type("L", (), {"por_segundo": None, "por_dia": None, "espera_min": 1.0})(),
            quotas=quotas,
            timeout=30.0,
        )
        client = OpenAiCompatibleClient(
            settings.ai_primary_base_url,
            settings.ai_primary_api_key,
            settings.ai_primary_model,
            http,
        )
        log.info("IA: enviando prompt a %s...", settings.ai_primary_model)
        with client.http:
            content = client.complete(prompt)
        log.info("IA: respuesta recibida (%d chars)", len(content))

        appearances = json.loads(content)
        if not isinstance(appearances, list):
            log.warning("IA: respuesta no es un array")
            return

        count = 0
        for item in appearances:
            if not isinstance(item, dict) or "magazineName" not in item:
                continue
            appearance = MagazineAppearance(
                id=str(uuid.uuid4()),
                magazineName=item.get("magazineName", ""),
                country=item.get("country", ""),
                language=item.get("language", ""),
                issueNumber=item.get("issueNumber", ""),
                volume=item.get("volume"),
                date=item.get("date", ""),
                platform=system,
                contentType=item.get("contentType", ""),
                source="ai_identification",
                appearanceType=item.get("appearanceType", "no_determinado"),
            )
            _add_result(state, f"{game_title} en {appearance.magazineName}", "", "ai", appearance.magazineName, appearance)
            count += 1
        log.info("IA: %d apariciones identificadas", count)
    except json.JSONDecodeError:
        log.warning("IA: respuesta no es JSON válido", exc_info=True)
    except Exception:
        log.warning("AI magazine identification failed", exc_info=True)


def _phase2_digitized(game_title: str, state: _SearchState) -> None:
    magazines = list(state.magazines_found)
    if not magazines:
        log.info("Fase 2: sin revistas conocidas para buscar digitalizaciones")
        return
    log.info("Fase 2: buscando digitalizaciones de %d revistas en archive.org...", len(magazines))
    for magazine in magazines:
        try:
            _search_archive_org(game_title, magazine, state)
        except httpx.ConnectTimeout:
            log.warning("Fase 2: timeout conectando a archive.org para '%s'", magazine)
        except Exception:
            log.warning("Fase 2: error buscando '%s' en archive.org", magazine, exc_info=True)


def _search_archive_org(game_title: str, magazine: str, state: _SearchState) -> None:
    params = {
        "q": f'({magazine}) AND mediatype:texts AND (subject:"videojuegos" OR subject:"games")',
        "fl[]": "identifier,title,creator",
        "sort[]": "downloads desc",
        "rows": "25",
        "output": "json",
    }
    log.info("Archive.org: buscando '%s'...", magazine)
    with httpx.Client(timeout=_ARCHIVE_TIMEOUT, headers=_SEARCH_HEADERS) as client:
        resp = client.get("https://archive.org/advancedsearch.php", params=params)
        resp.raise_for_status()

    docs = resp.json().get("response", {}).get("docs", [])
    log.info("Archive.org: %d resultados para '%s'", len(docs), magazine)
    for doc in docs:
        identifier = doc.get("identifier", "")
        title = doc.get("title", "Revista")
        _add_result(state, title, f"https://archive.org/download/{identifier}", "archive.org", magazine)


def _phase3_direct(game_title: str, state: _SearchState) -> None:
    queries = [
        f'site:archive.org "{game_title}" revista videojuegos',
        f'site:retrocdn.net "{game_title}"',
        f'"{game_title}" revista digitalizada filetype:pdf site:archive.org',
        f'"{game_title}" "Hobby Consolas" OR "Super Juegos" OR "Nintendo Acción"',
        f'"{game_title}" "Micromanía" OR "PC Juegos" OR "PC Manía"',
        f'"{game_title}" "Mega Consolas" OR "Game Fan" OR "Videomanía"',
        f'"{game_title}" "Retro Gamer" OR "Pixels" OR "Old School Gamer"',
        f'"{game_title}" "PlayManía" OR "PlanetStation" OR "Loading"',
        f'"{game_title}" "Club Nintendo" OR "Atomix" OR "Loaded"',
    ]
    for query in queries:
        try:
            with httpx.Client(timeout=_HTTP_TIMEOUT, headers=_SEARCH_HEADERS) as client:
                resp = client.post("https://html.duckduckgo.com/html/", data={"q": query})
                resp.raise_for_status()

            for match in re.finditer(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text):
                href = match.group(1)
                title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                domain = _domain(href)

                if not _is_trusted(domain):
                    continue

                magazine = _extract_magazine_name(title, domain)
                _add_result(state, title, href, domain, magazine or domain)
        except Exception:
            log.warning("Phase 3 failed for '%s'", query, exc_info=True)


def _fallback_links(game_title: str, system: str) -> list[MagazineSearchResult]:
    encoded = game_title.replace(" ", "+")
    sys_encoded = system.replace(" ", "+")
    return [
        MagazineSearchResult(
            title=f"Archive.org: {game_title} ({system}) — revistas",
            url=f"https://archive.org/search?query={encoded}+{sys_encoded}+magazine&and[]=mediatype%3Atexts",
            source="archive.org",
            magazine="Archive.org",
        ),
        MagazineSearchResult(
            title=f"Archive.org: {game_title} — digitalizadas",
            url=f"https://archive.org/search?query={encoded}&and[]=mediatype%3Atexts&and[]=format%3A%22PDF%22",
            source="archive.org",
            magazine="Archive.org",
        ),
        MagazineSearchResult(
            title=f"Retro CDN: {game_title}",
            url="https://retrocdn.net",
            source="retrocdn.net",
            magazine="Retro CDN",
        ),
    ]


def _add_result(
    state: _SearchState,
    title: str,
    url: str,
    source: str,
    magazine: str,
    appearance: MagazineAppearance | None = None,
) -> None:
    if url:
        key = url.rstrip("/").lower()
        if key in state.seen_urls:
            return
        state.seen_urls.add(key)
    state.magazines_found.add(magazine)
    state.results.append(MagazineSearchResult(
        title=title,
        url=url,
        source=source,
        magazine=magazine or source,
        appearance=appearance,
    ))


def _is_trusted(domain: str) -> bool:
    d = domain.lower()
    return any(trusted in d for trusted in _TRUSTED_DOMAINS)


def _domain(url: str) -> str:
    match = re.search(r"https?://([^/]+)", url)
    return match.group(1) if match else url


def _extract_magazine_name(title: str, source: str) -> str:
    known = [
        # España - 80s ordenadores
        "MicroHobby", "Micromanía", "Input Sinclair", "Tu Micro", "MSX Magazine",
        "Amstrad Semanal", "Amstrad User", "Amstrad-Sinclair Ocio", "Club Commodore",
        "Load'N'Run", "Carga y Juega", "Spectrum Magazine", "Software en Acción",
        # España - 90s consolas
        "Hobby Consolas", "Super Juegos", "Superjuegos", "Nintendo Acción",
        "Todo Sega", "Mega Consolas", "Mega Consolas Clásicas", "Game", "Game Fan",
        "Consola Clásica", "Videomanía", "Videomanias", "Gametro", "Loco Journal",
        "Press Start", "ClickJuegos", "Zona Nintendo", "Todo Nintendo",
        "Nintendomanía", "Nintendomanias", "Sonic", "Play",
        # España - 90s PC
        "PC Juegos", "PC Juego", "PC Manía", "PCManía", "PCMania", "OK Computer",
        "Computermagazine", "CD Mega", "Mega PC", "Informática CD", "PC Games",
        "PC Users", "GameReport",
        # España - PlayStation
        "PlayManía", "PlayMania", "PlanetStation", "PlayStation Magazine",
        "Revista Oficial PlayStation", "Loading", "DualPixel",
        # España - 2000s
        "Edge", "GamesTM", "GTM", "Marca Player", "Retro Gamer", "NGamer",
        "GameLive PC", "ScreenFun", "Top Games", "Pocket Boy", "Games World",
        "Dreamplanet", "HobbyGames", "MeriStation", "Vandal", "3DJuegos",
        # México
        "Club Nintendo", "EGM", "Atomix", "Video Tips", "Megaconsolas",
        "Nintendo World", "Xbox World", "PlayStation World",
        # Argentina
        "Next Level", "Xtreme PC", "Loaded", "Malditos Nerds", "Irrompibles",
        "Nuke", "Play & Share", "Replay",
        # Brasil
        "Ação Games", "Acao Games", "Videogame", "Supergame", "SuperGamePower",
        "GamePower", "ProGames", "Gamers", "PSWorld",
        # Internacionales
        "Electronic Gaming Monthly", "GamePro", "Official PlayStation Magazine",
        "Official Xbox Magazine", "Computer and Video Games", "CVG", "Nintendo Power",
        # Retro actuales
        "Pixels", "Hecho con Pixels", "Old School Gamer", "RETRO Fusion",
        "Retro", "Return", "VideoGamer RETRO", "Retro Gamer Collection",
    ]
    text = f"{title} {source}".lower()
    for name in known:
        if name.lower() in text:
            return name
    return ""


def build_magazine_links(appearance: MagazineAppearance) -> dict[str, str]:
    """Build multiple direct links to the magazine (archive.org, retrocdn, official)."""
    magazine = appearance.magazineName
    issue = appearance.issueNumber
    date = appearance.date

    links: dict[str, str] = {}

    # Retro CDN: link directo a la categoría de la revista
    retrocdn_slug = magazine.replace(" ", "_").replace(".", "")
    retrocdn_url = f"https://retrocdn.net/Category:{retrocdn_slug}_scans"
    links["retroCdn"] = retrocdn_url

    # Archive.org: búsqueda específica de la revista
    query_parts = [magazine]
    if issue:
        query_parts.append(f"issue {issue}")
    if date:
        query_parts.append(date)
    archive_url = f"https://archive.org/search?query={quote_plus(' '.join(query_parts))}&and[]=mediatype%3Atexts"
    links["archiveOrg"] = archive_url

    return links
