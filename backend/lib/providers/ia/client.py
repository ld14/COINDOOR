from __future__ import annotations

import json
import re

from backend.lib.providers.http import ProviderHttpClient


class ModelResponseError(Exception):
    pass


class OpenAiCompatibleClient:
    """Cliente mínimo para cualquier API que hable el esquema chat/completions
    de OpenAI (Groq, OpenRouter, Together, Ollama local, etc). Sin reintentos
    propios: los aporta ProviderHttpClient."""

    def __init__(self, base_url: str, api_key: str, model: str, http: ProviderHttpClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.http = http

    def complete(self, prompt: str) -> str:
        with self.http:
            response = self.http.post_json(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2048,
                    "reasoning_effort": "low",
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        choices = response.json.get("choices") if isinstance(response.json, dict) else None
        if not isinstance(choices, list) or not choices:
            raise ModelResponseError("respuesta del modelo sin 'choices'")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            raise ModelResponseError("respuesta sin mensaje")
        content = message.get("content") or ""
        reasoning = message.get("reasoning") or ""
        combined = content or reasoning
        if not combined.strip():
            raise ModelResponseError("respuesta del modelo sin contenido")
        return _extract_response(combined)


def _extract_response(content: str) -> str:
    """Extract the actual response from model output that may contain thinking,
    markdown code blocks, or preamble text."""
    content = _strip_thinking_tags(content)
    content = _strip_markdown_blocks(content)
    try:
        json.loads(content)
        return content.strip()
    except (json.JSONDecodeError, ValueError):
        pass
    start = content.rfind("{")
    end = content.rfind("}")
    if start != -1 and end > start:
        candidate = content[start : end + 1]
        try:
            json.loads(candidate)
            return candidate.strip()
        except (json.JSONDecodeError, ValueError):
            pass
    return content.strip()


def _strip_thinking_tags(content: str) -> str:
    """Remove <think>...</think> tags that some models embed in content."""
    content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL).strip()
    if "<think>" in content:
        content = content.rsplit("<think>", 1)[-1].strip()
    return content


def _strip_markdown_blocks(content: str) -> str:
    """Remove ```json...``` or ```...``` wrappers."""
    content = re.sub(r"```(?:json)?\s*\n?", "", content)
    content = re.sub(r"\n?```\s*$", "", content)
    return content.strip()
