"""Trucos = una búsqueda web + el modelo que ya está configurado (ADR-0019).

El reparto de tareas es el punto: el modelo deja de tener que **recordar** los
trucos —donde se midió que falla, devolviendo vacíos o códigos inventados— y pasa
a **estructurar** lo que trajo el buscador, que es donde sí es bueno.

Si la búsqueda no trae evidencia, no hay candidato. Un modelo sin evidencia
inventa, y ese es justamente el fallo que este proveedor viene a cerrar.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.lib.providers.base import (
    Candidato,
    Consulta,
    Limite,
    ProcessedUrl,
    ProviderResult,
    ProviderTrace,
)
from backend.lib.providers.http import ProviderHttpClient, ProviderHttpError
from backend.lib.providers.ia.client import ModelResponseError, OpenAiCompatibleClient
from backend.lib.providers.ia.generador import PROMPT_VERSION, _validate_shape

PROMPT_PATH = Path(__file__).parent / "prompts" / f"cheats-web.{PROMPT_VERSION}.md"
CAMPOS = frozenset({"cheats"})

# Presupuesto de evidencia. No es una precaución: `gpt-oss-120b` en el tier
# gratuito de Groq tiene 8.000 TPM y cuenta `prompt + max_tokens` contra ese
# techo, así que pasarle las páginas enteras devuelve 429. Recortar cuesta
# cobertura —un truco que estaba en el párrafo cortado se pierde— y es el precio.
_EVIDENCIA_TOTAL = 10_000
# El buscador devuelve por relevancia, y el presupuesto se reparte por orden de
# llegada: el tope por resultado es alto a propósito para que la primera página
# —la buena— entre lo más entera posible, y a las de abajo les toque el resto. Con
# un tope bajo, una página del juego equivocado se lleva la misma tajada que la
# fuente principal.
_EVIDENCIA_POR_RESULTADO = 5_000
_MAX_TOKENS = 3_000
_MAX_RESULTADOS = 5


@dataclass(frozen=True)
class ResultadoWeb:
    titulo: str
    url: str
    texto: str


@dataclass(frozen=True)
class Busqueda:
    query: str
    resultados: tuple[ResultadoWeb, ...]


class TavilyClient:
    """Búsqueda en Tavily. Una consulta básica = un crédito de los 1.000 mensuales."""

    def __init__(self, base_url: str, api_key: str, http: ProviderHttpClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.http = http

    def buscar(self, query: str) -> Busqueda:
        body: dict[str, object] = {
            "query": query,
            # "basic" cuesta 1 crédito; "advanced" cuesta 2 y no compensa para
            # páginas de trucos, que son texto plano sin nada que razonar.
            "search_depth": "basic",
            "max_results": _MAX_RESULTADOS,
            # El texto completo de la página, no el resumen: los trucos viven en
            # listas largas que el snippet corta. No cuesta créditos extra.
            "include_raw_content": "text",
        }
        with self.http:
            response = self.http.post_json(
                f"{self.base_url}/search",
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return Busqueda(query, _resultados_de(response.json))


class TrucosWebGenerador:
    """Solo sirve `cheats`. El resto de los campos siguen con `IaGenerador`."""

    tipo: Literal["api", "scrape"] = "api"
    campos = CAMPOS
    # Una búsqueda más una llamada al modelo, en serie.
    timeout = 60.0
    limite = Limite(por_segundo=None, por_dia=None, espera_min=1.0)
    nombre = "Búsqueda web + IA"

    def __init__(
        self,
        buscador: TavilyClient,
        modelos: Sequence[OpenAiCompatibleClient],
    ) -> None:
        self.buscador = buscador
        # En orden: primario y respaldo. Cada cliente se usa una sola vez por
        # `buscar` — su ProviderHttpClient queda cerrado después.
        self.modelos = tuple(modelos)

    def buscar(self, consulta: Consulta) -> ProviderResult:
        if consulta.key not in self.campos:
            return ProviderResult((), self._trace("sin resultados"))
        busqueda = self.buscador.buscar(_query(consulta))
        evidencia, usados = _evidencia(busqueda.resultados)
        if not evidencia:
            # "Buscó y no encontró" es una respuesta, no un fallo: si acá se
            # devolviera un estado distinto de "ok", el modal lo contaría como
            # fuente caída y mostraría "error de la fuente externa".
            return ProviderResult(
                (),
                self._trace("ok", busqueda, (), motivo="la búsqueda no devolvió páginas con texto"),
            )
        prompt = PROMPT_PATH.read_text(encoding="utf-8").format(
            titulo=consulta.title,
            sistema=consulta.system,
            anio=consulta.year or "año desconocido",
            texto=evidencia,
        )
        ultimo_error = ""
        for cliente in self.modelos:
            try:
                contenido = cliente.complete(prompt, max_tokens=_MAX_TOKENS)
                value = _validate_shape(consulta.key, _extraer_objeto_json(contenido))
            except (ModelResponseError, ProviderHttpError) as exc:
                # Pasar al respaldo no es un reintento propio: es la misma cadena
                # primario→respaldo que ya usan la precarga y el pegado de texto.
                ultimo_error = f"{cliente.model}: {exc}"
                continue
            if not json.loads(value).get("groups"):
                return ProviderResult(
                    (),
                    self._trace(
                        "ok",
                        busqueda,
                        usados,
                        motivo="las páginas encontradas no traían trucos de esta versión",
                    ),
                )
            trace = self._trace("ok", busqueda, usados)
            candidato = Candidato(
                id=f"trucos-web:{cliente.model}:{consulta.key}",
                key=consulta.key,
                kind="text",
                nombre=f"{consulta.key} buscado en la web",
                fuente=self.nombre,
                clase="aplicable",
                value=value,
                generado_por_ia=True,
                meta={
                    "prompt_version": PROMPT_VERSION,
                    "modelo": cliente.model,
                    "busqueda": busqueda.query,
                },
                trace=trace,
            )
            return ProviderResult((candidato,), trace)
        motivo = ultimo_error or "sin modelo de IA configurado"
        return ProviderResult(
            (),
            self._trace(f"se buscó, pero no se pudo estructurar: {motivo}", busqueda, usados),
        )

    def _trace(
        self,
        estado: str,
        busqueda: Busqueda | None = None,
        usados: Sequence[ResultadoWeb] = (),
        *,
        motivo: str = "",
    ) -> ProviderTrace:
        """`estado` distingue respondió de falló; `motivo` explica un "ok" sin
        candidatos, que no es lo mismo que una fuente caída."""
        return ProviderTrace(
            self.nombre,
            self.tipo,
            estado,
            urls_procesadas=tuple(
                ProcessedUrl(r.url, None, (r.titulo,) if r.titulo else ()) for r in usados
            ),
            datos_obtenidos=((f"búsqueda: {busqueda.query}",) if busqueda else ())
            + ((motivo,) if motivo else ())
            + tuple(r.titulo for r in usados if r.titulo),
        )


def _query(consulta: Consulta) -> str:
    """Una sola búsqueda por sugerencia: son créditos contados.

    Va en inglés y sin el paréntesis del nombre del sistema. Los dos detalles se
    midieron: "trucos" sesga hacia páginas en castellano, que para juegos retro
    casi no existen, y un sistema llamado "MAME (máquinas arcade)" mete cuatro
    palabras de ruido en la consulta. El prompt pide la respuesta en castellano
    igual —traducir es barato, encontrar no—.
    """
    plataforma = consulta.system.split("(")[0].strip() or consulta.system
    partes = [consulta.title]
    if consulta.year:
        partes.append(consulta.year)
    partes.extend([plataforma, "cheats codes"])
    return " ".join(partes)


def _resultados_de(payload: object) -> tuple[ResultadoWeb, ...]:
    if not isinstance(payload, dict):
        return ()
    crudos = payload.get("results")
    if not isinstance(crudos, list):
        return ()
    resultados: list[ResultadoWeb] = []
    for crudo in crudos:
        if not isinstance(crudo, dict):
            continue
        url = crudo.get("url")
        if not isinstance(url, str) or not url:
            continue
        # `raw_content` es la página entera; `content` el snippet. El primero que
        # tenga algo: sin texto, el resultado no aporta nada al modelo.
        texto = ""
        for campo in ("raw_content", "content"):
            valor = crudo.get(campo)
            if isinstance(valor, str) and valor.strip():
                texto = valor
                break
        titulo = crudo.get("title")
        resultados.append(
            ResultadoWeb(titulo if isinstance(titulo, str) else "", url, texto),
        )
    return tuple(resultados)


def _evidencia(
    resultados: Sequence[ResultadoWeb],
) -> tuple[str, tuple[ResultadoWeb, ...]]:
    """Texto para el prompt, dentro del presupuesto, y qué resultados entraron."""
    bloques: list[str] = []
    usados: list[ResultadoWeb] = []
    restante = _EVIDENCIA_TOTAL
    for resultado in resultados:
        if restante <= 0:
            break
        cuerpo = " ".join(resultado.texto.split())[: min(_EVIDENCIA_POR_RESULTADO, restante)]
        if not cuerpo:
            continue
        # La URL va en el bloque para que el modelo pueda descartar por sitio
        # cuando el texto no diga de qué plataforma habla.
        bloques.append(f"### {resultado.titulo or resultado.url}\n{resultado.url}\n{cuerpo}")
        usados.append(resultado)
        restante -= len(cuerpo)
    return "\n\n".join(bloques), tuple(usados)


def _extraer_objeto_json(texto: str) -> str:
    """Primer objeto JSON con `groups`, buscando desde la izquierda.

    No se reusa `_extract_response` de `client.py`: aquel usa `rfind("{")`, o sea
    la *última* llave de apertura, que en `{"groups":[{…}]}` es la del objeto
    anidado. Cuando al texto le falta el comienzo hay que escanear desde la
    primera llave, no desde la última.
    """
    decoder = json.JSONDecoder()
    inicio = texto.find("{")
    while inicio != -1:
        try:
            objeto, _fin = decoder.raw_decode(texto, inicio)
        except json.JSONDecodeError:
            objeto = None
        if isinstance(objeto, dict) and "groups" in objeto:
            return json.dumps(objeto, ensure_ascii=False)
        inicio = texto.find("{", inicio + 1)
    raise ModelResponseError("la respuesta no trae un objeto JSON con 'groups'")
