from __future__ import annotations

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
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        choices = response.json.get("choices") if isinstance(response.json, dict) else None
        if not isinstance(choices, list) or not choices:
            raise ModelResponseError("respuesta del modelo sin 'choices'")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ModelResponseError("respuesta del modelo sin contenido")
        return content.strip()
