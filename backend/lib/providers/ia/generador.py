from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.lib.providers.base import Candidato, Consulta, Limite, ProviderResult, ProviderTrace
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.ia.client import ModelResponseError, OpenAiCompatibleClient

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_VERSION = "v1"
CAMPOS = frozenset({"sinopsis", "review", "cheats"})


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
        prompt = _load_prompt(consulta.key).format(
            titulo=consulta.title,
            sistema=consulta.system,
            anio=consulta.year or "año desconocido",
        )
        try:
            content = self.client.complete(prompt)
            value = _validate_shape(consulta.key, content)
        except ModelResponseError as exc:
            return ProviderResult(
                (),
                ProviderTrace(self.nombre, self.tipo, f"respuesta inválida: {exc}"),
            )
        trace = ProviderTrace(self.nombre, self.tipo, "ok")
        candidate = Candidato(
            id=f"ia:{self.config.model}:{consulta.key}",
            key=consulta.key,
            kind="text",
            nombre=f"{consulta.key} generado por IA",
            fuente=self.nombre,
            clase="aplicable",
            value=value,
            generado_por_ia=True,
            meta={"prompt_version": PROMPT_VERSION, "modelo": self.config.model},
            trace=trace,
        )
        return ProviderResult((candidate,), trace)


def _load_prompt(key: str) -> str:
    return (PROMPT_DIR / f"{key}.{PROMPT_VERSION}.md").read_text(encoding="utf-8")


def _validate_shape(key: str, content: str) -> str:
    if key == "sinopsis":
        return content
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ModelResponseError(f"JSON inválido: {exc}") from exc
    if key == "review" and (not isinstance(data, dict) or "cats" not in data):
        raise ModelResponseError("reseña sin 'cats'")
    if key == "cheats" and (not isinstance(data, dict) or not isinstance(data.get("groups"), list)):
        raise ModelResponseError("trucos sin 'groups'")
    return json.dumps(data, ensure_ascii=False)
