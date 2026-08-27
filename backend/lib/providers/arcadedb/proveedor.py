"""Proveedor ArcadeDB: sugiere campos para juegos arcade desde adb.arcadeitalia.net.

El romset se deriva de ``Path(game.romRef).stem.lower()``, igual que hace
``IdentityActualProvider`` con el GamesStore. ``Consulta`` no se toca.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from backend.config import Settings
from backend.lib.providers.arcadedb.cliente import ArcadeGame, fetch
from backend.lib.providers.base import (
    CandidateClass,
    CandidateKind,
    Candidato,
    Consulta,
    Limite,
    ProviderResult,
    ProviderTrace,
)
from backend.lib.providers.http import ProviderHttpClient
from backend.store.juegos import GamesStore

log = logging.getLogger(__name__)

# Mapeo ArcadeDB → fielddefs: campo de ArcadeDB → (key, kind, clase, label).
_MAPPING_IDENTITY: dict[str, tuple[str, CandidateKind, CandidateClass, str]] = {
    "short_title": ("title", "identity", "aplicable", "Título ( ArcadeDB)"),
    "title": ("title", "identity", "referencia", "Título completo"),
    "year": ("year", "identity", "aplicable", "Año"),
    "manufacturer": ("developer", "identity", "aplicable", "Desarrollador"),
    "manufacturer_publisher": ("publisher", "identity", "aplicable", "Editor"),
    "genre": ("genre", "identity", "aplicable", "Género"),
    "players": ("players", "identity", "aplicable", "Jugadores"),
}

_MAPPING_TEXT: dict[str, tuple[str, CandidateKind, CandidateClass, str]] = {
    "sinopsis": ("sinopsis", "text", "aplicable", "Sinopsis"),
    "cheats": ("cheats", "text", "aplicable", "Trucos"),
}

_MAPPING_IMAGE: dict[str, tuple[str, CandidateKind, CandidateClass, str]] = {
    "flyer": ("caratula", "media", "aplicable", "Carátula"),
    "flyer_poster": ("poster", "media", "aplicable", "Póster"),
    "marquee": ("marquesina", "media", "aplicable", "Marquesina"),
    "screen1": ("captura", "media", "aplicable", "Captura de pantalla"),
}

_MAPPING_VIDEO: dict[str, tuple[str, CandidateKind, CandidateClass, str]] = {
    "video": ("video", "media", "aplicable", "Video de gameplay"),
}

_MappingTuple = tuple[str, CandidateKind, CandidateClass, str]
_ValorFn = Callable[[ArcadeGame, str], str]


class ArcadeDbProvider:
    nombre = "ArcadeDB"
    tipo: Literal["api", "scrape"] = "api"
    campos: frozenset[str] = frozenset({
        "title", "year", "developer", "publisher", "genre", "players",
        "sinopsis", "cheats",
        "caratula", "poster", "marquesina", "captura",
        "video",
    })
    timeout = 10.0
    limite = Limite()

    def __init__(self, settings: Settings, http: ProviderHttpClient) -> None:
        self.games = GamesStore(settings.games_dir)
        self.http = http

    def buscar(self, consulta: Consulta) -> ProviderResult:
        trace = ProviderTrace(self.nombre, self.tipo, "sin resultados")

        # Gate por sistema: solo arcade.
        if "arcade" not in consulta.system.lower():
            return ProviderResult((), trace)

        # Derivar romset de romRef.
        game = self.games.get(consulta.game_id)
        romset = Path(game.romRef).stem.lower() if game.romRef else ""
        if not romset:
            return ProviderResult((), trace)

        # Fetch con memo.
        arcade_game = fetch(romset, self.http)
        if arcade_game is None:
            return ProviderResult((), trace)

        return self._mapear(consulta.key, arcade_game, trace)

    def _mapear(
        self,
        key: str,
        game: ArcadeGame,
        trace: ProviderTrace,
    ) -> ProviderResult:
        candidatos: list[Candidato] = []

        # Identity
        self._agregar_candidatos(
            candidatos, key, game, _MAPPING_IDENTITY, trace, self._valor_identity,
        )
        # Manufacturer → publisher (segundo candidato)
        if key == "publisher":
            self._agregar_candidato(
                candidatos, key, game,
                "manufacturer_publisher", _MAPPING_IDENTITY, trace,
            )
        # Text
        self._agregar_candidatos(
            candidatos, key, game, _MAPPING_TEXT, trace, self._valor_text,
        )
        # Images
        self._agregar_candidatos(
            candidatos, key, game, _MAPPING_IMAGE, trace, self._valor_image,
        )
        # Video
        self._agregar_candidatos(
            candidatos, key, game, _MAPPING_VIDEO, trace, self._valor_video,
        )

        return ProviderResult(tuple(candidatos), trace)

    def _agregar_candidatos(
        self,
        candidatos: list[Candidato],
        key: str,
        game: ArcadeGame,
        mapping: dict[str, _MappingTuple],
        trace: ProviderTrace,
        valor_fn: _ValorFn,
    ) -> None:
        for arcade_key, (field_key, kind, clase, label) in mapping.items():
            if key != field_key:
                continue
            value = valor_fn(game, arcade_key)
            if not value:
                continue
            candidatos.append(Candidato(
                id=f"arcadedb:{game.romset}:{arcade_key}",
                key=field_key,
                kind=kind,
                nombre=f"{label} (ArcadeDB)",
                fuente=self.nombre,
                clase=clase,
                value=value,
                origen_url=game.origen_url,
                trace=trace,
            ))

    def _agregar_candidato(
        self,
        candidatos: list[Candidato],
        key: str,
        game: ArcadeGame,
        arcade_key: str,
        mapping: dict[str, _MappingTuple],
        trace: ProviderTrace,
    ) -> None:
        if arcade_key not in mapping:
            return
        field_key, kind, clase, label = mapping[arcade_key]
        if key != field_key:
            return
        value = self._valor_identity(game, arcade_key)
        if not value:
            return
        candidatos.append(Candidato(
            id=f"arcadedb:{game.romset}:{arcade_key}",
            key=field_key,
            kind=kind,
            nombre=f"{label} (ArcadeDB)",
            fuente=self.nombre,
            clase=clase,
            value=value,
            origen_url=game.origen_url,
            trace=trace,
        ))

    @staticmethod
    def _valor_identity(game: ArcadeGame, arcade_key: str) -> str:
        if arcade_key == "short_title":
            return game.short_title
        if arcade_key == "title":
            return game.title
        if arcade_key == "year":
            return game.year
        if arcade_key == "manufacturer":
            return game.manufacturer
        if arcade_key == "manufacturer_publisher":
            return game.manufacturer
        if arcade_key == "genre":
            return game.genre
        if arcade_key == "players":
            return game.players
        return ""

    @staticmethod
    def _valor_text(game: ArcadeGame, arcade_key: str) -> str:
        if arcade_key == "sinopsis":
            return game.history.sinopsis
        if arcade_key == "cheats":
            return "\n\n".join(game.history.tips) if game.history.tips else ""
        return ""

    @staticmethod
    def _valor_image(game: ArcadeGame, arcade_key: str) -> str:
        if arcade_key == "flyer":
            return game.image("flyer")
        if arcade_key == "flyer_poster":
            return game.image("flyer")
        if arcade_key == "marquee":
            return game.image("marquee")
        if arcade_key == "screen1":
            return game.image("screen1")
        return ""

    @staticmethod
    def _valor_video(game: ArcadeGame, arcade_key: str) -> str:
        if arcade_key == "video":
            return game.video_url
        return ""
