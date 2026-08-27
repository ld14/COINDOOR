"""Traduccion al español de los textos que llegan de ArcadeDB.

ArcadeDB (y arcade-history.com detras) publica todo en ingles. La ficha de
COINDOOR es en español, asi que la precarga traduce antes de escribir.

Best-effort por diseño, igual que el resto de la precarga: si la IA no esta
configurada o falla, se devuelve el texto original en ingles. Un texto en ingles
es peor que uno traducido, pero mucho mejor que un campo vacio, y el ``source``
del campo deja constancia de cual de los dos caso paso.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

from backend.lib.providers.ia.client import OpenAiCompatibleClient

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_VERSION = "v1"

log = logging.getLogger(__name__)


class Traductor:
    """Envuelve el cliente OpenAI-compatible con los dos prompts de traduccion.

    Recibe una fabrica y no un cliente porque hace DOS llamadas: el
    ``ProviderHttpClient`` que hay abajo cierra su httpx.Client al salir del
    ``with`` y no lo reabre, asi que reusar la misma instancia hace fallar la
    segunda con "Cannot send a request, as the client has been closed".
    """

    def __init__(self, client_factory: Callable[[], OpenAiCompatibleClient], modelo: str) -> None:
        self._client_factory = client_factory
        self.modelo = modelo

    def sinopsis(self, texto: str, *, titulo: str, sistema: str, anio: str, max_length: int) -> str:
        """Traduce y condensa a la misma spec que la sinopsis generada por IA.

        Recibe el texto completo, no el truncado: el modelo condensa mejor con
        todo el contexto. El limite se hace respetar afuera, en el servicio.
        """
        if not texto.strip():
            return texto
        prompt = _prompt("traduccion-sinopsis").format(
            titulo=titulo,
            sistema=sistema,
            anio=anio or "año desconocido",
            max_length=max_length,
            texto=texto,
        )
        try:
            traducido = self._client_factory().complete(prompt).strip()
        except Exception as exc:  # noqa: BLE001
            log.warning("Traduccion de sinopsis fallo, queda en ingles: %s", exc)
            return texto
        return traducido or texto

    def lote(self, textos: list[str], *, titulo: str) -> list[str]:
        """Traduce N strings cortos en una sola llamada.

        Devuelve siempre una lista del mismo largo que la entrada: si el modelo
        contesta otra cosa, se descarta entera y vuelven los originales. Traducir
        la mitad y dejar la otra en ingles seria peor que no traducir.
        """
        if not textos:
            return []
        prompt = _prompt("traduccion-lote").format(
            titulo=titulo,
            textos=json.dumps(textos, ensure_ascii=False, indent=2),
        )
        try:
            crudo = self._client_factory().complete(prompt)
            traducidos = json.loads(crudo)
        except Exception as exc:  # noqa: BLE001
            log.warning("Traduccion en lote fallo, queda en ingles: %s", exc)
            return list(textos)
        if not isinstance(traducidos, list) or len(traducidos) != len(textos):
            log.warning(
                "Traduccion en lote devolvio %s elementos y se esperaban %s, queda en ingles",
                len(traducidos) if isinstance(traducidos, list) else "algo que no es lista",
                len(textos),
            )
            return list(textos)
        # Un elemento vacio o que no es string se descarta solo, no el lote entero.
        return [
            str(nuevo).strip() or viejo
            for viejo, nuevo in zip(textos, traducidos, strict=True)
        ]


def _prompt(nombre: str) -> str:
    return (PROMPT_DIR / f"{nombre}.{PROMPT_VERSION}.md").read_text(encoding="utf-8")
