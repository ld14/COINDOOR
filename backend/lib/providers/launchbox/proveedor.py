"""Proveedor Launchbox: sugiere identidad e imágenes desde Games Database.

Scraping de ``gamesdb.launchbox-app.com`` (server-rendered). No hay API
pública. Busca el juego por título, plataforma y año con la regla común de
``coincidencia``; la identidad sale de la página del juego y las imágenes,
categorizadas, de su página de imágenes.

Rate limit: 0.5 s entre requests, sin límite diario.
"""

from __future__ import annotations

import logging
from typing import Literal

from backend.lib.providers.base import (
    Candidato,
    Consulta,
    Limite,
    ProviderResult,
    ProviderTrace,
)
from backend.lib.providers.launchbox.cliente import (
    LaunchboxFicha,
    LaunchboxSearchResult,
    fetch_details,
    fetch_images,
    search_game,
)

log = logging.getLogger(__name__)

_TIMEOUT = 15.0
_IDENTIDAD = frozenset({"year", "developer", "publisher", "genre", "players"})
_ETIQUETAS = {
    "year": "Año",
    "developer": "Desarrollador",
    "publisher": "Editor",
    "genre": "Género (en inglés)",
    "players": "Jugadores",
}


def jugadores(max_players: str) -> str:
    """'1' queda '1'; un máximo de N jugadores, '1-N' (la forma de la ficha)."""
    if not max_players.isdigit():
        return ""
    return max_players if max_players == "1" else f"1-{max_players}"


def valor_identidad(
    key: str,
    ficha: LaunchboxFicha | None,
    result: LaunchboxSearchResult,
) -> str:
    """El valor de un campo de identidad en Launchbox, o vacío si no lo tiene."""
    if key == "year":
        return (ficha.year if ficha else "") or result.year
    if ficha is None:
        return ""
    if key == "developer":
        return next(iter(ficha.developers), "")
    if key == "publisher":
        return next(iter(ficha.publishers), "")
    if key == "genre":
        return ", ".join(ficha.genres)
    if key == "players":
        return jugadores(ficha.max_players)
    return ""


class LaunchboxImageProvider:
    """Busca identidad e imágenes de juegos en Launchbox Games Database."""

    nombre = "Launchbox"
    tipo: Literal["api", "scrape"] = "scrape"
    campos: frozenset[str] = frozenset({
        "caratula", "marquesina", "poster", "logo", "captura",
        *_IDENTIDAD,
    })
    timeout = _TIMEOUT
    limite = Limite(por_segundo=0.5, por_dia=None, espera_min=0.0)

    def buscar(self, consulta: Consulta) -> ProviderResult:
        trace = ProviderTrace(self.nombre, self.tipo, "sin resultados")

        if not consulta.title or consulta.key not in self.campos:
            return ProviderResult((), trace)

        # 1. Buscar juego por título, plataforma y año
        log.info("Launchbox: searching title=%s system=%s", consulta.title, consulta.system)
        result = search_game(consulta.title, consulta.system, anio=consulta.year)
        if result is None:
            log.info("Launchbox: no match for '%s' on '%s'", consulta.title, consulta.system)
            return ProviderResult((), trace)

        log.info("Launchbox: found %s-%s (%s)", result.game_id, result.slug, result.title)

        # 2. Identidad: de la página del juego (el año, si falta, de la búsqueda)
        if consulta.key in _IDENTIDAD:
            ficha = fetch_details(result.game_id, result.slug)
            valor = valor_identidad(consulta.key, ficha, result)
            if not valor:
                return ProviderResult((), trace)
            trace = ProviderTrace(self.nombre, self.tipo, "ok")
            candidato = Candidato(
                id=f"launchbox:{result.game_id}:{consulta.key}",
                key=consulta.key,
                kind="identity",
                nombre=f"{_ETIQUETAS[consulta.key]} (Launchbox)",
                fuente=self.nombre,
                clase="aplicable",
                value=valor,
                origen_url=ficha.url if ficha else result.detail_url,
                trace=trace,
            )
            return ProviderResult((candidato,), trace)

        # 3. Imágenes: de la página de imágenes del juego
        images = fetch_images(result.game_id, result.slug)
        if not images:
            log.info("Launchbox: no mapped images for %s-%s", result.game_id, result.slug)
            return ProviderResult((), trace)

        log.info("Launchbox: %d images found for key=%s", len(images), consulta.key)

        # 4. Filtrar por el campo solicitado y crear candidatos
        candidates: list[Candidato] = []
        for img in images:
            if img.field_key != consulta.key:
                continue
            candidates.append(Candidato(
                id=f"launchbox:{result.game_id}:{consulta.key}:{len(candidates)}",
                key=consulta.key,
                kind="media",
                nombre=f"{img.label} (Launchbox)",
                fuente=self.nombre,
                clase="aplicable",
                media_url=img.media_url,
                preview_url=img.preview_url,
                origen_url=img.game_url,
                trace=trace,
            ))

        if candidates:
            trace = ProviderTrace(self.nombre, self.tipo, "ok")
            return ProviderResult(tuple(candidates), trace)

        # No hay imágenes para este campo específico, pero el juego existe.
        # Ofrecer link a la galería como referencia.
        trace = ProviderTrace(self.nombre, self.tipo, "ok")
        ref = Candidato(
            id=f"launchbox:{result.game_id}:{consulta.key}:ref",
            key=consulta.key,
            kind="media",
            nombre=f"Ver galería de {result.title} en Launchbox",
            fuente=self.nombre,
            clase="referencia",
            origen_url=f"https://gamesdb.launchbox-app.com/games/images/{result.game_id}-{result.slug}",
            trace=trace,
        )
        return ProviderResult((ref,), trace)
