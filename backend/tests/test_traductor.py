from __future__ import annotations

import json
from typing import Any

from backend.lib.providers.ia.traductor import Traductor


class ClienteFalso:
    """Cliente que devuelve respuestas guionadas y anota los prompts recibidos."""

    def __init__(self, *respuestas: Any) -> None:
        self.respuestas = list(respuestas)
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


def _traductor(*respuestas: Any) -> tuple[Traductor, ClienteFalso]:
    cliente = ClienteFalso(*respuestas)
    return Traductor(lambda: cliente, "modelo-test"), cliente


def test_lote_devuelve_las_traducciones_en_orden() -> None:
    traductor, cliente = _traductor(json.dumps(["uno", "dos", "tres"]))
    assert traductor.lote(["one", "two", "three"], titulo="X") == ["uno", "dos", "tres"]
    assert '"one"' in cliente.prompts[0]


def test_lote_con_largo_distinto_se_descarta_entero() -> None:
    # Traducir la mitad y dejar la otra en ingles seria peor que no traducir.
    traductor, _ = _traductor(json.dumps(["uno", "dos"]))
    assert traductor.lote(["one", "two", "three"], titulo="X") == ["one", "two", "three"]


def test_lote_ante_json_roto_o_error_deja_el_original() -> None:
    traductor, _ = _traductor("no soy json")
    assert traductor.lote(["one"], titulo="X") == ["one"]

    traductor, _ = _traductor(RuntimeError("modelo caido"))
    assert traductor.lote(["one"], titulo="X") == ["one"]


def test_lote_repone_elementos_vacios_sin_tirar_el_resto() -> None:
    traductor, _ = _traductor(json.dumps(["uno", "   ", "tres"]))
    assert traductor.lote(["one", "two", "three"], titulo="X") == ["uno", "two", "tres"]


def test_lote_vacio_no_llama_al_modelo() -> None:
    traductor, cliente = _traductor()
    assert traductor.lote([], titulo="X") == []
    assert cliente.prompts == []


def test_sinopsis_pasa_titulo_limite_y_texto_al_prompt() -> None:
    traductor, cliente = _traductor("Una sinopsis en español.")
    salida = traductor.sinopsis(
        "An English synopsis.", titulo="Super Pang", sistema="mame", anio="1990", max_length=700
    )
    assert salida == "Una sinopsis en español."
    prompt = cliente.prompts[0]
    assert "Super Pang" in prompt
    assert "700" in prompt
    assert "An English synopsis." in prompt


def test_sinopsis_ante_error_o_respuesta_vacia_deja_el_ingles() -> None:
    traductor, _ = _traductor(RuntimeError("timeout"))
    assert traductor.sinopsis("English.", titulo="X", sistema="mame", anio="", max_length=700) == "English."  # noqa: E501

    traductor, _ = _traductor("   ")
    assert traductor.sinopsis("English.", titulo="X", sistema="mame", anio="", max_length=700) == "English."  # noqa: E501


def test_sinopsis_vacia_no_llama_al_modelo() -> None:
    traductor, cliente = _traductor()
    assert traductor.sinopsis("", titulo="X", sistema="mame", anio="", max_length=700) == ""
    assert cliente.prompts == []


def test_cada_llamada_pide_un_cliente_nuevo() -> None:
    """El ProviderHttpClient real es de un solo uso: cierra su httpx.Client al
    salir del ``with`` y no lo reabre. Reusar la instancia rompia la segunda
    llamada con "Cannot send a request, as the client has been closed"."""

    class ClienteUnSoloUso:
        def __init__(self, respuesta: str) -> None:
            self.respuesta = respuesta
            self.usado = False

        def complete(self, prompt: str) -> str:
            if self.usado:
                raise RuntimeError("Cannot send a request, as the client has been closed.")
            self.usado = True
            return self.respuesta

    creados: list[ClienteUnSoloUso] = []

    def fabrica() -> ClienteUnSoloUso:
        cliente = ClienteUnSoloUso(json.dumps(["uno"]) if not creados else "Sinopsis en español.")
        creados.append(cliente)
        return cliente

    traductor = Traductor(fabrica, "modelo-test")
    assert traductor.lote(["one"], titulo="X") == ["uno"]
    assert traductor.sinopsis(
        "English.", titulo="X", sistema="mame", anio="1990", max_length=700
    ) == "Sinopsis en español."
    assert len(creados) == 2
