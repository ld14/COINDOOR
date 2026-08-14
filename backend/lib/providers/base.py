from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol

CandidateKind = Literal["identity", "media", "text"]
CandidateClass = Literal["aplicable", "referencia"]


@dataclass(frozen=True)
class Consulta:
    game_id: str
    key: str
    title: str
    system: str
    year: str | None = None


@dataclass(frozen=True)
class Limite:
    por_segundo: float | None = None
    por_dia: int | None = None
    espera_min: float = 0.0


@dataclass(frozen=True)
class ProcessedUrl:
    url: str
    status: int | None
    datos_obtenidos: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderTrace:
    nombre: str
    tipo: Literal["api", "scrape"]
    estado: str
    urls_procesadas: tuple[ProcessedUrl, ...] = ()
    datos_obtenidos: tuple[str, ...] = ()


@dataclass(frozen=True)
class Candidato:
    id: str
    key: str
    kind: CandidateKind
    nombre: str
    fuente: str
    clase: CandidateClass
    value: str | None = None
    preview_url: str | None = None
    media_url: str | None = None
    origen_url: str | None = None
    trace: ProviderTrace | None = None
    generado_por_ia: bool = False
    meta: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderResult:
    candidatos: Sequence[Candidato]
    trace: ProviderTrace


class Proveedor(Protocol):
    nombre: str
    tipo: Literal["api", "scrape"]
    campos: frozenset[str]
    timeout: float
    limite: Limite

    def buscar(self, consulta: Consulta) -> ProviderResult: ...
