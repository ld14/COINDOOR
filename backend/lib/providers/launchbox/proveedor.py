"""Proveedor Launchbox: sugiere imágenes desde Games Database.

Scraping de ``gamesdb.launchbox-app.com`` (server-rendered). No hay API
pública. Busca el juego por título + plataforma, luego extrae imágenes
categorizadas de la página de imágenes.

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
    fetch_images,
    search_game,
)

log = logging.getLogger(__name__)

_TIMEOUT = 15.0


class LaunchboxImageProvider:
    """Busca imágenes de juegos en Launchbox Games Database."""

    nombre = "Launchbox"
    tipo: Literal["api", "scrape"] = "scrape"
    campos: frozenset[str] = frozenset({
        "caratula", "marquesina", "poster", "logo", "captura",
    })
    timeout = _TIMEOUT
    limite = Limite(por_segundo=0.5, por_dia=None, espera_min=0.0)

    def buscar(self, consulta: Consulta) -> ProviderResult:
        trace = ProviderTrace(self.nombre, self.tipo, "sin resultados")

        if consulta.key not in self.campos or not consulta.title:
            log.info("Launchbox: skipped key=%s title=%s", consulta.key, bool(consulta.title))
            return ProviderResult((), trace)

        # 1. Buscar juego por título + plataforma
        log.info("Launchbox: searching title=%s system=%s", consulta.title, consulta.system)
        result = search_game(consulta.title, consulta.system)
        if result is None:
            log.info("Launchbox: no match for '%s' on '%s'", consulta.title, consulta.system)
            return ProviderResult((), trace)

        log.info("Launchbox: found %s-%s (%s)", result.game_id, result.slug, result.title)

        # 2. Obtener imágenes
        images = fetch_images(result.game_id, result.slug)
        if not images:
            log.info("Launchbox: no mapped images for %s-%s", result.game_id, result.slug)
            return ProviderResult((), trace)

        log.info("Launchbox: %d images found for key=%s", len(images), consulta.key)

        # 3. Filtrar por el campo solicitado y crear candidatos
        candidates = []
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
            kind="referencia",
            nombre=f"Ver galería de {result.title} en Launchbox",
            fuente=self.nombre,
            clase="referencia",
            origen_url=f"https://gamesdb.launchbox-app.com/games/images/{result.game_id}-{result.slug}",
            trace=trace,
        )
        return ProviderResult((ref,), trace)
