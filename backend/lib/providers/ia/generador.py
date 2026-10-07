from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.lib.domain.guia import MODOS, lineas
from backend.lib.providers.base import Candidato, Consulta, Limite, ProviderResult, ProviderTrace
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.client import ModelResponseError, OpenAiCompatibleClient

log = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_VERSION = "v1"
CAMPOS = frozenset(
    {"sinopsis", "objetivo", "primerosPasos", "reglasEsenciales", "modo", "review", "cheats", "identidad"}  # noqa: E501
)
_OBJETIVO_MAX = 600
_OBJETIVO_DESCONOCIDO = "DESCONOCIDO"
_ITEMS_MAX = 5
_ITEM_LARGO_MAX = 200

# MSDOS/DOS/Windows se tratan como PC: mismo criterio que
# backend/services/msdos.py:_MSDOS_MARKERS, duplicado acá para no crear un
# import circular (msdos.py ya importa de este módulo).
_PC_MARKERS = ("msdos", "ms-dos", "dos", "pc", "windows")


def _es_pc(system: str) -> bool:
    nombre = system.lower()
    return any(marker in nombre for marker in _PC_MARKERS)


@dataclass(frozen=True)
class AiModelConfig:
    base_url: str
    api_key: str
    model: str


class IaGenerador:
    tipo: Literal["api", "scrape"] = "api"
    campos = CAMPOS
    timeout = 45.0
    limite = Limite(por_segundo=None, por_dia=None, espera_min=1.0)

    def __init__(self, config: AiModelConfig, http: ProviderHttpClient) -> None:
        self.config = config
        self.nombre = f"IA · {config.model}"
        self.client = OpenAiCompatibleClient(config.base_url, config.api_key, config.model, http)

    def buscar(self, consulta: Consulta) -> ProviderResult:
        if consulta.key not in self.campos:
            return ProviderResult((), ProviderTrace(self.nombre, self.tipo, "sin resultados"))
        prompt = _load_prompt(consulta.key, consulta.system).format(
            titulo=consulta.title,
            sistema=consulta.system,
            anio=consulta.year or "año desconocido",
            contexto=consulta.contexto,
        )
        try:
            content = self.client.complete(prompt)
            if consulta.key == "identidad":
                value = _validate_identity_json(content)
            else:
                value = _validate_shape(consulta.key, content)
        except ModelResponseError as exc:
            log.warning("%s rechazó %s de %r: %s", self.nombre, consulta.key, consulta.title, exc)
            return ProviderResult(
                (),
                ProviderTrace(self.nombre, self.tipo, f"respuesta inválida: {exc}"),
            )
        trace = ProviderTrace(self.nombre, self.tipo, "ok")
        kind: Literal["identity", "media", "text"] = (
            "identity" if consulta.key == "identidad" else "text"
        )
        candidate = Candidato(
            id=f"ia:{self.config.model}:{consulta.key}",
            key=consulta.key,
            kind=kind,
            nombre=f"{consulta.key} generado por IA",
            fuente=self.nombre,
            clase="aplicable",
            value=value,
            generado_por_ia=True,
            meta={"prompt_version": PROMPT_VERSION, "modelo": self.config.model},
            trace=trace,
        )
        return ProviderResult((candidate,), trace)


def _load_prompt(key: str, system: str) -> str:
    if key == "cheats" and _es_pc(system):
        return (PROMPT_DIR / f"cheats-pc.{PROMPT_VERSION}.md").read_text(encoding="utf-8")
    return (PROMPT_DIR / f"{key}.{PROMPT_VERSION}.md").read_text(encoding="utf-8")


def _validate_shape(key: str, content: str) -> str:
    if key == "sinopsis":
        return content
    if key == "objetivo":
        return _validate_objetivo(content)
    if key in ("primerosPasos", "reglasEsenciales"):
        return _validate_lineas(content)
    if key == "modo":
        return _validate_modo(content)
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ModelResponseError(f"JSON inválido: {exc}") from exc
    if key == "review" and (not isinstance(data, dict) or "cats" not in data):
        raise ModelResponseError("reseña sin 'cats'")
    if key == "cheats" and (not isinstance(data, dict) or not isinstance(data.get("groups"), list)):
        raise ModelResponseError("trucos sin 'groups'")
    return json.dumps(data, ensure_ascii=False)


def _validate_objetivo(content: str) -> str:
    texto = content.strip()
    if not texto or texto.upper().rstrip(".") == _OBJETIVO_DESCONOCIDO:
        raise ModelResponseError("el modelo no conoce el juego")
    if len(texto) > _OBJETIVO_MAX:
        raise ModelResponseError(
            f"objetivo de {len(texto)} caracteres (máximo {_OBJETIVO_MAX}): {texto[:80]!r}..."
        )
    return texto


def _validate_lineas(content: str) -> str:
    texto = content.strip()
    if not texto or texto.upper().rstrip(".") == _OBJETIVO_DESCONOCIDO:
        raise ModelResponseError("el modelo no conoce el juego")
    items = lineas(texto)
    if not items:
        raise ModelResponseError("sin líneas útiles")
    if len(items) > _ITEMS_MAX:
        raise ModelResponseError(f"{len(items)} líneas (máximo {_ITEMS_MAX})")
    largo = next((item for item in items if len(item) > _ITEM_LARGO_MAX), None)
    if largo is not None:
        raise ModelResponseError(f"una línea de {len(largo)} caracteres: {largo[:60]!r}...")
    return "\n".join(items)


def _validate_modo(content: str) -> str:
    texto = content.strip().lower().rstrip(".")
    if texto == _OBJETIVO_DESCONOCIDO.lower():
        raise ModelResponseError("el modelo no conoce el juego")
    if texto not in MODOS:
        raise ModelResponseError(f"modo fuera de vocabulario: {texto[:40]!r}")
    return texto


def _validate_identity_json(content: str) -> str:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ModelResponseError(f"JSON inválido: {exc}") from exc
    if not isinstance(data, dict):
        raise ModelResponseError("identidad no es un objeto")
    return json.dumps(data, ensure_ascii=False)
