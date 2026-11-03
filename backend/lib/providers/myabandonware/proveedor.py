"""Proveedor myabandonware: identidad, sinopsis y capturas de PC/DOS (ADR-0027).

Baja por HTTP común: recibe una fábrica de ``ProviderHttpClient``. Su gate es el catálogo de
plataformas; hoy solo MS-DOS tiene equivalencia. No da jugadores (``playMode`` no es confiable)
ni formato, y el sitio no tiene carátulas.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from backend.lib.domain.plataformas import nombre_en
from backend.lib.providers.base import Candidato, Consulta, ProviderResult, ProviderTrace
from backend.lib.providers.http import ProviderHttpClient, ProviderHttpError
from backend.lib.providers.myabandonware.cliente import LIMITE, TIMEOUT, buscar
from backend.lib.providers.myabandonware.parser import Ficha

log = logging.getLogger(__name__)

_ETIQUETAS = {
    "title": "Título",
    "year": "Año",
    "developer": "Desarrollador",
    "publisher": "Editor",
    "genre": "Género (en inglés)",
}


class MyAbandonwareProvider:
    nombre = "MyAbandonware"
    tipo: Literal["api", "scrape"] = "scrape"
    campos: frozenset[str] = frozenset({*_ETIQUETAS, "sinopsis", "captura"})
    timeout = TIMEOUT
    limite = LIMITE

    def __init__(self, http_factory: Callable[[], ProviderHttpClient], carpeta: Path) -> None:
        self._http_factory = http_factory
        self.carpeta = carpeta

    def buscar(self, consulta: Consulta) -> ProviderResult:
        trace = ProviderTrace(self.nombre, self.tipo, "sin resultados")
        if not consulta.title or consulta.key not in self.campos:
            return ProviderResult((), trace)
        plataforma = nombre_en(consulta.system, "myabandonware")
        if plataforma is None:
            sin_equivalencia = ProviderTrace(self.nombre, self.tipo, "plataforma sin equivalencia")
            return ProviderResult((), sin_equivalencia)
        ficha = self._ficha(consulta, plataforma)
        if ficha is None:
            return ProviderResult((), trace)
        candidatos = self._mapear(consulta.key, ficha)
        if candidatos:
            trace = ProviderTrace(self.nombre, self.tipo, "ok")
        return ProviderResult(tuple(candidatos), trace)

    def enlace_mobygames(self, consulta: Consulta) -> str | None:
        """La ficha de MobyGames que enlaza la página del juego: MobyGames va directo a ella."""
        plataforma = nombre_en(consulta.system, "myabandonware")
        if plataforma is None or not consulta.title:
            return None
        try:
            ficha = self._ficha(consulta, plataforma)
        except ProviderHttpError:
            log.warning("myabandonware no respondió buscando el enlace a MobyGames", exc_info=True)
            return None
        return ficha.mobygames_url if ficha is not None and ficha.mobygames_url else None

    def _ficha(self, consulta: Consulta, plataforma: str) -> Ficha | None:
        with self._http_factory() as http:
            return buscar(http, self.carpeta, consulta.title, consulta.year, plataforma)

    def _mapear(self, key: str, ficha: Ficha) -> list[Candidato]:
        trace = ProviderTrace(self.nombre, self.tipo, "ok")
        if key == "captura":
            return [
                Candidato(
                    id=f"myabandonware:{captura.url}",
                    key=key,
                    kind="media",
                    nombre=f"Captura {i} de {ficha.plataforma} (MyAbandonware)",
                    fuente=self.nombre,
                    clase="aplicable",
                    media_url=captura.url,
                    preview_url=captura.miniatura,
                    origen_url=ficha.url,
                    trace=trace,
                )
                for i, captura in enumerate(ficha.capturas, start=1)
            ]

        def candidato(
            valor: str,
            kind: Literal["identity", "text"],
            etiqueta: str,
        ) -> list[Candidato]:
            if not valor:
                return []
            return [
                Candidato(
                    id=f"myabandonware:{ficha.url}:{key}",
                    key=key,
                    kind=kind,
                    nombre=f"{etiqueta} (MyAbandonware)",
                    fuente=self.nombre,
                    clase="aplicable",
                    value=valor,
                    origen_url=ficha.url,
                    trace=trace,
                )
            ]

        if key == "sinopsis":
            return candidato(ficha.description, "text", "Sinopsis (en inglés)")
        valores = {
            "title": ficha.title,
            "year": ficha.year,
            "developer": ficha.developer,
            "publisher": ficha.publisher,
            "genre": ficha.genre,
        }
        return candidato(valores.get(key, ""), "identity", _ETIQUETAS.get(key, key))
