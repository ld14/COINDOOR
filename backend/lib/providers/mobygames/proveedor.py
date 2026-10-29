"""Proveedor MobyGames: sugiere identidad, sinopsis y nota de críticos para PC/DOS.

No sabe de navegadores: recibe una fábrica de ``ScrapingClient``. Su gate es el catálogo de
plataformas: un sistema sin equivalencia en MobyGames (arcade incluido) no se consulta.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Literal

from backend.lib.domain.plataformas import nombre_en
from backend.lib.providers.base import (
    Candidato,
    Consulta,
    Limite,
    ProviderResult,
    ProviderTrace,
)
from backend.lib.providers.mobygames.cliente import FichaCompleta, buscar_ficha
from backend.lib.providers.scraping import ScrapingClient
from backend.store.juegos import GamesStore

log = logging.getLogger(__name__)

_URL_FICHA = "mobygames.com/game/"


class MobyGamesProvider:
    nombre = "MobyGames"
    tipo: Literal["api", "scrape"] = "scrape"
    campos: frozenset[str] = frozenset(
        {
            "title", "year", "developer", "publisher", "genre", "players", "format",
            "sinopsis", "review",
        }
    )

    def __init__(
        self,
        games: GamesStore,
        client_factory: Callable[[], ScrapingClient],
        *,
        timeout: float,
        pace: float,
    ) -> None:
        self.games = games
        self._client_factory = client_factory
        self.timeout = timeout
        self.limite = Limite(espera_min=pace)

    def buscar(self, consulta: Consulta) -> ProviderResult:
        trace = ProviderTrace(self.nombre, self.tipo, "sin resultados")
        if consulta.key not in self.campos:
            return ProviderResult((), trace)
        plataforma = nombre_en(consulta.system, "mobygames")
        if plataforma is None:
            sin_equivalencia = ProviderTrace(self.nombre, self.tipo, "plataforma sin equivalencia")
            return ProviderResult((), sin_equivalencia)

        with self._client_factory() as client:
            completa = buscar_ficha(
                client,
                consulta.title,
                consulta.year,
                plataforma,
                ficha_url=self._url_conocida(consulta.game_id),
            )
        if completa is None:
            return ProviderResult((), trace)
        candidatos = self._mapear(consulta.key, completa)
        if candidatos:
            trace = ProviderTrace(self.nombre, self.tipo, "ok")
        return ProviderResult(candidatos, trace)

    def _url_conocida(self, game_id: str) -> str | None:
        """El enlace de MobyGames que la procedencia ya guardó, si lo hay."""
        try:
            game = self.games.get(game_id)
        except Exception:  # la ficha puede no existir todavía (alta en curso)
            return None
        for procedencia in game.provenance.values():
            url = procedencia.originUrl or ""
            if _URL_FICHA in url:
                return url
        return None

    def _mapear(self, key: str, completa: FichaCompleta) -> list[Candidato]:
        ficha, specs = completa.ficha, completa.specs
        origen = ficha.url or None

        def candidato(
            sufijo: str,
            valor: str,
            kind: Literal["identity", "text"],
            etiqueta: str,
        ) -> Candidato:
            return Candidato(
                id=f"mobygames:{ficha.url}:{sufijo}",
                key=key,
                kind=kind,
                nombre=f"{etiqueta} (MobyGames)",
                fuente=self.nombre,
                clase="aplicable",
                value=valor,
                origen_url=origen,
                trace=ProviderTrace(self.nombre, self.tipo, "ok"),
            )

        if key == "title" and ficha.title:
            return [candidato("title", ficha.title, "identity", "Título")]
        if key == "year" and ficha.year:
            return [candidato("year", ficha.year, "identity", "Año")]
        if key == "developer" and ficha.developer:
            return [candidato("developer", ficha.developer, "identity", "Desarrollador")]
        if key == "publisher" and ficha.publisher:
            return [candidato("publisher", ficha.publisher, "identity", "Editor")]
        if key == "genre" and ficha.genre:
            return [candidato("genre", ficha.genre, "identity", "Género (en inglés)")]
        if key == "players" and specs.players:
            return [candidato("players", specs.players, "identity", "Jugadores")]
        if key == "format":
            return [
                candidato(f"format:{formato}", formato, "identity", "Formato")
                for formato in specs.formatos
            ]
        if key == "sinopsis" and ficha.description:
            return [candidato("sinopsis", ficha.description, "text", "Sinopsis (en inglés)")]
        if key == "review" and ficha.score is not None:
            # Solo la nota: las seis categorías ya cargadas se conservan al aplicarla.
            valor = json.dumps({"score": ficha.score})
            return [candidato("review", valor, "text", "Nota de críticos")]
        return []
