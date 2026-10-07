from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

# Vocabulario cerrado del bloque `guia` de ATTRACT (ADR-0037): coincide con el
# `<control type>` de `mame -listxml`, mas mouse/keyboard.
MODOS = ("individual", "cooperativo", "versus")
PERIFERICOS = ("joy", "trackball", "dial", "paddle", "lightgun", "mouse", "keyboard")

# Palabra clave que aparece en el control que publica ArcadeDB -> periferico de ATTRACT.
# `spinner` es lo que MAME llama `dial`.
_CLAVES_PERIFERICO = (
    ("trackball", "trackball"),
    ("dial", "dial"),
    ("spinner", "dial"),
    ("paddle", "paddle"),
    ("lightgun", "lightgun"),
    ("light gun", "lightgun"),
    ("joystick", "joy"),
    ("joy", "joy"),
    ("mouse", "mouse"),
    ("keyboard", "keyboard"),
)
_VINETA = re.compile(r"^\s*(?:[-*•–]|\d+[.)])\s*")

# Textos libres del bloque `guia`: los que una persona escribe o una IA sugiere.
TEXTOS_GUIA = ("objetivo", "primerosPasos", "reglasEsenciales", "modo")
# Un texto que aun lleva este prefijo es un placeholder: nunca debe llegar al paquete.
_EJEMPLO = re.compile(r"^\s*(?:[-*•–]|\d+[.)])?\s*ejemplo\s*:", re.IGNORECASE | re.MULTILINE)
_LARGO_MIN_NOMBRE = 3


def perifericos_desde(controles: str) -> list[str]:
    """Perifericos del vocabulario de ATTRACT que nombra `controles`, sin repetir.

    Lo que no se reconoce se omite: un periferico inventado no cruza con `-listxml`.
    """
    texto = controles.lower()
    encontrados: list[str] = []
    for clave, periferico in _CLAVES_PERIFERICO:
        if clave in texto and periferico not in encontrados:
            encontrados.append(periferico)
    return encontrados


def lineas(texto: str) -> list[str]:
    """Items de un texto de varias lineas (uno por linea), sin vinetas ni vacios."""
    items = (_VINETA.sub("", linea).strip() for linea in str(texto).splitlines())
    return [item for item in items if item]


def modo_desde_ficha(jugadores: str, nplayers: str) -> str:
    """`individual` solo cuando es un hecho: un jugador, o ArcadeDB dice por turnos (`alt`).

    Un juego simultaneo (`sim`) puede ser cooperativo o versus y de ahi no se deduce.
    """
    if jugadores.strip() == "1" or "alt" in nplayers.lower():
        return "individual"
    return ""


def es_placeholder(texto: str) -> bool:
    """¿Alguna linea del texto sigue empezando con «EJEMPLO:»?"""
    return _EJEMPLO.search(texto) is not None


def _normalizar(valor: str) -> str:
    return "".join(c for c in valor.casefold() if c.isalnum())


def nombres_internos(game: Mapping[str, Any]) -> list[str]:
    """Nombres con los que COINDOOR identifica el juego por dentro (romset, id, carpeta).

    Se descartan los que coinciden con el titulo comercial: si el romset se llama igual
    que el juego (`xevious`), nombrarlo en el texto es correcto y no es un sintoma.
    """
    identity = game.get("identity", {})
    titulo = _normalizar(str(identity.get("title", ""))) if isinstance(identity, Mapping) else ""
    rom_ref = str(game.get("romRef") or "").replace("\\", "/")
    ruta = Path(rom_ref) if rom_ref else None
    candidatos = [str(game.get("id", "")), str(game.get("dirName", ""))]
    if ruta is not None:
        es_archivo_rom = ruta.suffix.lower() in (".zip", ".7z", ".chd")
        candidatos.append(ruta.stem if es_archivo_rom else ruta.name)
    nombres: list[str] = []
    for candidato in candidatos:
        nombre = candidato.strip()
        if len(nombre) < _LARGO_MIN_NOMBRE or _normalizar(nombre) == titulo:
            continue
        if nombre.casefold() not in (existente.casefold() for existente in nombres):
            nombres.append(nombre)
    return nombres


def nombre_interno_en(texto: str, game: Mapping[str, Any]) -> str | None:
    """El nombre interno del juego que aparece tal cual en `texto`, sin distinguir mayusculas."""
    for nombre in nombres_internos(game):
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(nombre)}(?![A-Za-z0-9])", texto, re.IGNORECASE):
            return nombre
    return None


def _crudo(game: Mapping[str, Any], clave: str) -> tuple[str, bool] | None:
    texts = game.get("texts", {})
    campo = texts.get(clave) if isinstance(texts, Mapping) else None
    if not isinstance(campo, Mapping) or campo.get("status") == "empty":
        return None
    valor = str(campo.get("value", "")).strip()
    if not valor:
        return None
    return valor, campo.get("status") == "manual"


def problema_texto(game: Mapping[str, Any], clave: str) -> str | None:
    """Por que un texto cargado no puede viajar en la guia, o ``None`` si esta bien."""
    crudo = _crudo(game, clave)
    if crudo is None:
        return None
    if es_placeholder(crudo[0]):
        return "Todavía tiene un texto de ejemplo («EJEMPLO:»): reemplazalo por el real"
    if clave == "objetivo":
        nombre = nombre_interno_en(crudo[0], game)
        if nombre:
            return f"Menciona el nombre interno «{nombre}» en vez del título del juego: corregilo"
    return None


def texto_guia(game: Mapping[str, Any], clave: str) -> tuple[str, bool] | None:
    """(valor, escrito a mano) de ``texts.<clave>``, o ``None`` si no hay texto util.

    Un texto con placeholder o con el nombre interno del juego cuenta como ausente: es lo
    unico que garantiza que no llegue al paquete, venga de donde venga la llamada.
    """
    if problema_texto(game, clave) is not None:
        return None
    return _crudo(game, clave)


def acciones_de(game: Mapping[str, Any]) -> list[dict[str, str]]:
    cabinet = game.get("cabinet", {})
    botones = cabinet.get("button_list", []) if isinstance(cabinet, Mapping) else []
    if not isinstance(botones, list):
        return []
    acciones: list[dict[str, str]] = []
    for boton in botones:
        if not isinstance(boton, Mapping):
            continue
        control = str(boton.get("control", "")).strip()
        action = str(boton.get("action", "")).strip()
        if not control or not action:
            continue
        accion = {"control": control, "action": action}
        color = str(boton.get("color", "")).strip()
        if color:
            accion["color"] = color
        acciones.append(accion)
    return acciones


def controles_de(game: Mapping[str, Any]) -> str:
    cabinet = game.get("cabinet", {})
    return str(cabinet.get("controls", "")) if isinstance(cabinet, Mapping) else ""


def _jugadores_y_nplayers(game: Mapping[str, Any]) -> tuple[str, str]:
    identity = game.get("identity", {})
    players = str(identity.get("players", "")).strip() if isinstance(identity, Mapping) else ""
    cabinet = game.get("cabinet", {})
    nplayers = str(cabinet.get("nplayers", "")) if isinstance(cabinet, Mapping) else ""
    return players, nplayers


def multijugador_de(
    game: Mapping[str, Any],
    incluir: Collection[str],
) -> tuple[dict[str, Any], bool | None]:
    """``multijugador`` y, si el modo salio de un texto, si lo escribio una persona."""
    players, nplayers = _jugadores_y_nplayers(game)
    resultado: dict[str, Any] = {}
    # Un "1-2" no es un entero limpio: mejor omitir `jugadores` que afirmar un 1 falso.
    if players.isdigit() and int(players) >= 1:
        resultado["jugadores"] = int(players)

    modo_manual: bool | None = None
    elegido = texto_guia(game, "modo") if "modo" in incluir else None
    if elegido and elegido[0].lower() in MODOS:
        resultado["modo"] = elegido[0].lower()
        modo_manual = elegido[1]
    elif derivado := modo_desde_ficha(players, nplayers):
        resultado["modo"] = derivado
    return resultado, modo_manual


def guia_checklist(game: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Que tiene y que le falta a la guia «Como se juega» de esta ficha, y por que.

    Mismas reglas que el export (se apoya en las mismas funciones), para que la lista
    que ve la persona no pueda diferir de lo que viaja. ``estado`` es ``ok`` o ``falta``;
    ``requerido`` marca lo sin lo cual ATTRACT rechaza el bloque.
    """
    todo = ("objetivo", "primerosPasos", "reglasEsenciales", "modo")
    items: list[dict[str, Any]] = []

    def sumar(key: str, label: str, ok: bool, detalle: str, requerido: bool = False) -> None:
        items.append({
            "key": key, "label": label, "estado": "ok" if ok else "falta",
            "detalle": detalle, "requerido": requerido,
        })

    def origen(clave: str) -> tuple[bool, str]:
        problema = problema_texto(game, clave)
        if problema:
            return False, problema
        campo = texto_guia(game, clave)
        if campo is None:
            return False, ""
        return True, "escrito a mano" if campo[1] else "sugerido, sin revisar"

    ok, detalle = origen("objetivo")
    sumar("objetivo", "Objetivo", ok, detalle or "Sin objetivo la guía no se exporta", True)
    listas = (("primerosPasos", "Primeros pasos"), ("reglasEsenciales", "Reglas esenciales"))
    for clave, label in listas:
        ok, detalle = origen(clave)
        campo = texto_guia(game, clave)
        cantidad = len(lineas(campo[0])) if campo else 0
        sumar(clave, label, ok, f"{cantidad} ítem(s), {detalle}" if ok else detalle or "Escribilo o usá Sugerir")  # noqa: E501

    players, nplayers = _jugadores_y_nplayers(game)
    multijugador, _ = multijugador_de(game, todo)
    jugadores = multijugador.get("jugadores")
    sumar("jugadores", "Cantidad de jugadores", jugadores is not None,
          f"{jugadores}" if jugadores else f"Cargá un número entero en Identidad (hoy: «{players}»)" if players else "Falta en Identidad")  # noqa: E501
    modo = multijugador.get("modo")
    elegido = texto_guia(game, "modo")
    if modo and elegido and elegido[0].lower() == modo:
        sumar("modo", "Modo multijugador", True, f"{modo}, {'elegido a mano' if elegido[1] else 'sugerido, sin revisar'}")  # noqa: E501
    elif modo:
        motivo = "un jugador" if players == "1" else "por turnos según ArcadeDB"
        sumar("modo", "Modo multijugador", True, f"{modo}, deducido ({motivo})")
    elif "sim" in nplayers.lower():
        sumar("modo", "Modo multijugador", False, "Juego simultáneo: elegí cooperativo o versus")
    else:
        sumar("modo", "Modo multijugador", False, "Sin dato de ArcadeDB: elegilo a mano")

    controles = controles_de(game)
    perifericos = perifericos_desde(controles)
    sumar("perifericos", "Periféricos", bool(perifericos),
          ", ".join(perifericos) if perifericos else
          f"Control no reconocido: «{controles}»" if controles.strip() else "ArcadeDB no publicó el control de este juego")  # noqa: E501
    acciones = acciones_de(game)
    sumar("acciones", "Acciones de los botones", bool(acciones),
          f"{len(acciones)} acción(es)" if acciones else "ArcadeDB no publica botones con acción para este juego")  # noqa: E501
    return items
