from __future__ import annotations

from typing import Literal
from urllib.parse import urlencode

from backend.lib.providers.base import Candidato, Consulta, Limite, ProviderResult, ProviderTrace

BASE_URL = "https://www.youtube.com/results"


class YoutubeReferenceProvider:
    """No pega ninguna red: arma un link de búsqueda. Siempre `referencia` — el
    usuario mira el video, consigue el archivo y lo carga a mano con el botón
    que ya existe. Nunca falla salvo con título vacío."""

    nombre = "YouTube"
    tipo: Literal["api", "scrape"] = "api"
    campos = frozenset({"video"})
    timeout = 1.0
    limite = Limite()

    def buscar(self, consulta: Consulta) -> ProviderResult:
        if consulta.key not in self.campos or not consulta.title:
            return ProviderResult((), ProviderTrace(self.nombre, self.tipo, "sin resultados"))
        query = " ".join(filter(None, (consulta.title, consulta.system, "gameplay")))
        url = f"{BASE_URL}?{urlencode({'search_query': query})}"
        trace = ProviderTrace(self.nombre, self.tipo, "ok")
        candidate = Candidato(
            id=f"youtube:{consulta.game_id}:{consulta.key}",
            key=consulta.key,
            kind="media",
            nombre=f"Buscar \"{consulta.title}\" en YouTube",
            fuente=self.nombre,
            clase="referencia",
            origen_url=url,
            trace=trace,
        )
        return ProviderResult((candidate,), trace)
