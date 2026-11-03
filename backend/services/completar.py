"""Completa los campos vacíos de una ficha (ADR-0028).

Corre la precarga de la fuente del sistema, si tiene, y después pasa por cada campo vacío con la
misma cadena de "Sugerir", aplicando el mejor candidato con el mismo camino que un clic en el
modal: la procedencia y las reglas de cada campo no se repiten acá. Nada de lo que escribe queda
confirmado. Si un campo no tiene candidato o no se puede bajar, queda vacío y el job sigue.

``GamesStore`` guarda su índice al crearse y cada servicio tiene el suyo: acá se crean de nuevo
en cada paso, porque un store viejo escribiría la ficha sin lo que trajeron la precarga, el paso
anterior o el usuario, que puede estar editando mientras corre el job.

El video queda afuera: nada se descarga solo (ADR-0020).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from typing import Any, cast

from backend.api.schemas import FieldProvenance, StoredGame
from backend.config import Settings
from backend.lib.domain.arcade import soporta_arcadedb
from backend.lib.domain.fielddefs import identity_keys, image_keys
from backend.lib.jobs.registro import JobState
from backend.lib.media import colores_dominantes
from backend.lib.providers.orquestador import SuggestionsService
from backend.lib.providers.referencia.images import ImageSearchProvider, encaja_en
from backend.services.arcadedb import ArcadeDbPrecargaService
from backend.services.fields import FieldsService
from backend.services.msdos import MsdosPrecargaService, soporta_msdos
from backend.store.archivo import media_path
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

log = logging.getLogger(__name__)

_IDENTIDAD = ("year", "developer", "publisher", "genre", "players", "format")
_IMAGENES = ("caratula", "poster", "marquesina", "logo", "captura")
_GUIA = ("objetivo", "primerosPasos", "reglasEsenciales", "modo")
# La identidad va primero: el año ayuda a elegir la edición, y la guía la usa para reconocer el
# juego.
_ORDEN = (
    *_IDENTIDAD,
    "sinopsis",
    *_IMAGENES,
    *_GUIA,
    "review",
    "cheats",
)
# Hasta acá llega el progreso con la precarga de la fuente; el resto es de los campos.
_PROGRESO_PRECARGA = 30


class CompletarFichaService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, game_id: str) -> Callable[[JobState], dict[str, object]]:
        def job_fn(job: JobState) -> dict[str, object]:
            return self._execute(game_id, job)

        return job_fn

    def _juego(self, game_id: str) -> StoredGame:
        return GamesStore(self.settings.games_dir).get(game_id)

    def _execute(self, game_id: str, job: JobState) -> dict[str, object]:
        game = self._juego(game_id)
        if not game.identity.title and not soporta_arcadedb(game.systemId):
            return {"estado": "sin-titulo", "escritos": [], "sinDato": []}

        estado = self._precargar_fuente(game, job)
        job.progress = _PROGRESO_PRECARGA
        # ArcadeDB saca el título del romset: recién acá se sabe si hay con qué buscar.
        if not self._juego(game_id).identity.title:
            return {"estado": "sin-titulo", "escritos": [], "sinDato": []}

        escritos: list[str] = []
        sin_dato: list[str] = []
        for i, key in enumerate(_ORDEN):
            if job.cancel_event.is_set():
                return {"estado": "cancelado", "escritos": escritos, "sinDato": sin_dato}
            job.progress = _PROGRESO_PRECARGA + int(i / len(_ORDEN) * 65)
            if not self._vacio(game_id, key):
                continue
            (escritos if self._llenar(game_id, key, job) else sin_dato).append(key)

        self._poster_de_la_caratula(game_id, escritos, sin_dato)
        self._acento(game_id, escritos)
        return {**estado, "escritos": escritos, "sinDato": sin_dato}

    def _precargar_fuente(self, game: StoredGame, job: JobState) -> dict[str, object]:
        """La precarga del sistema, si tiene. Con un estado propio: su progreso va de 0 a 100 y
        no tiene que mover la barra del job. Si falla, los campos se completan igual."""
        servicio: MsdosPrecargaService | ArcadeDbPrecargaService
        if soporta_msdos(game.systemId):
            servicio = MsdosPrecargaService(self.settings)
        elif soporta_arcadedb(game.systemId):
            servicio = ArcadeDbPrecargaService(self.settings)
        else:
            return {"estado": "ok"}
        parcial = replace(job, progress=0)
        try:
            resultado = servicio.run(game.id)(parcial)
        except Exception:
            log.warning("La precarga de %s falló; se sigue con el resto", game.id, exc_info=True)
            return {"estado": "ok"}
        if resultado.get("estado") in ("no-encontrado", "sin-romset"):
            return {"estado": resultado["estado"], "romset": resultado.get("romset", "")}
        return {"estado": "ok"}

    def _vacio(self, game_id: str, key: str) -> bool:
        """Se mira justo antes de escribir: el usuario puede estar editando la ficha."""
        game = self._juego(game_id)
        if key in identity_keys():
            return not getattr(game.identity, key)
        if key in image_keys():
            imagen = game.images.get(key)
            return imagen is None or not imagen.url
        if key == "review":
            return game.review.status == "empty"
        if key == "cheats":
            return game.cheats.status == "empty"
        texto = game.texts.get(key)
        return texto is None or not texto.value

    def _llenar(self, game_id: str, key: str, job: JobState) -> bool:
        try:
            payload = SuggestionsService(self.settings).suggest(
                game_id, key, job.cancel_event, sin_memo=True,
            )
        except Exception:
            log.warning("No se pudo buscar %s para %s", key, game_id, exc_info=True)
            return False
        for candidato in self._elegibles(key, payload, self._juego(game_id)):
            if job.cancel_event.is_set() or not self._vacio(game_id, key):
                return False
            try:
                FieldsService(self.settings).apply_suggestion(
                    game_id, key, str(candidato["id"]),
                )
            except Exception:
                # Lo habitual es una imagen que el sitio no deja bajar: sigue la próxima.
                log.warning("No se pudo aplicar %s a %s", key, game_id, exc_info=True)
                continue
            return True
        return False

    def _elegibles(
        self, key: str, payload: Mapping[str, object], game: StoredGame,
    ) -> Iterable[Mapping[str, Any]]:
        """Los candidatos aplicables, en el orden de la cadena. Las fuentes de imágenes publican
        el tipo de cada una; las del buscador hay que juzgarlas."""
        candidatos = cast("list[Mapping[str, Any]]", payload.get("candidatos", []))
        sistema = SystemsStore(self.settings.systems_path).get(game.systemId).name
        for candidato in candidatos:
            if candidato.get("clase") != "aplicable":
                continue
            del_buscador = candidato.get("fuente") == ImageSearchProvider.nombre
            if del_buscador and not encaja_en(
                key,
                str(candidato.get("mediaUrl") or ""),
                candidato.get("meta") or {},
                game.identity.title,
                game.identity.year or None,
                sistema,
            ):
                continue
            yield candidato

    def _poster_de_la_caratula(
        self, game_id: str, escritos: list[str], sin_dato: list[str],
    ) -> None:
        """El póster es obligatorio y rara vez se encuentra uno aparte: la carátula sirve, como
        el ``flyer`` de ArcadeDB, que también alimenta a los dos."""
        game = self._juego(game_id)
        caratula = game.images.get("caratula")
        if caratula is None or not caratula.url or not self._vacio(game_id, "poster"):
            return
        origen = game.provenance.get("caratula")
        procedencia = FieldProvenance(
            source=caratula.source or "",
            originUrl=origen.originUrl if origen else None,
        )
        GamesStore(self.settings.games_dir).apply_media_suggestion(
            game_id, "poster", caratula.url, procedencia,
        )
        escritos.append("poster")
        if "poster" in sin_dato:
            sin_dato.remove("poster")

    def _acento(self, game_id: str, escritos: list[str]) -> None:
        game = self._juego(game_id)
        if game.accent != "empty":
            return
        url = next(
            (img.url for key in _IMAGENES if (img := game.images.get(key)) and img.url),
            None,
        )
        ruta = media_path(self.settings.media_dir, url) if url else None
        if ruta is None or not ruta.exists():
            return
        try:
            colores = colores_dominantes(ruta)
        except Exception:
            log.warning("No se pudo sacar el color de %s", game_id, exc_info=True)
            return
        if colores:
            GamesStore(self.settings.games_dir).apply_accent_suggestion(
                game_id, colores[0], "".join(colores[1:2]),
            )
            escritos.append("accent")
