"""Parseo del texto libre que devuelve ArcadeDB. Sin red, sin estado.

El campo ``history`` viene de arcade-history.com y trae la sinopsis seguida de
secciones delimitadas por ``- NOMBRE -``: TECHNICAL, TRIVIA, TIPS AND TRICKS,
STAFF, PORTS, SERIES, CONTRIBUTE. Solo se usan la intro y TIPS AND TRICKS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Encabezado de seccion: una linea que es solo "- NOMBRE EN MAYUSCULAS -".
_SECCION = re.compile(r"^[ \t]*-[ \t]*([A-Z][A-Z '&]+?)[ \t]*-[ \t]*$", re.MULTILINE)

# "Arcade Video game published 37 years ago:" — encabezado sin valor para la sinopsis.
_PUBLICADO = re.compile(r"^.*\bpublished\b.*\bago:\s*$", re.IGNORECASE)

# "Golden Axe (c) 1989 Sega." — se saca de la sinopsis y se guarda como candidato.
_COPYRIGHT = re.compile(r"^.*?\(c\)\s*\d{4}\s*(?P<empresa>.+?)\.?\s*$", re.IGNORECASE)

# Separa trucos: por linea en blanco, o antes de una linea que arranca con "*".
_TIP_SPLIT = re.compile(r"\n[ \t]*\n|\n(?=[ \t]*\*)")

_SECCION_TIPS = "TIPS AND TRICKS"


@dataclass(frozen=True)
class CabinetButtonData:
    control: str
    color: str
    action: str


@dataclass(frozen=True)
class HistoryParts:
    sinopsis: str = ""
    tips: tuple[str, ...] = ()
    copyright_company: str = ""


def parse_history(raw: str, *, max_length: int | None = None) -> HistoryParts:
    """Corta ``history`` en sinopsis y trucos.

    ``max_length`` trunca la sinopsis cortando en el ultimo punto que entre, para
    respetar el limite que declara ``fielddefs.json``.
    """
    if not raw or not raw.strip():
        return HistoryParts()

    texto = raw.replace("\r\n", "\n").replace("\r", "\n")
    secciones = _split_secciones(texto)
    intro, empresa = _limpiar_intro(secciones.pop("", ""))
    return HistoryParts(
        sinopsis=truncar_en_oracion(intro, max_length),
        tips=_split_tips(secciones.get(_SECCION_TIPS, "")),
        copyright_company=empresa,
    )


def parse_buttons(raw: str) -> tuple[CabinetButtonData, ...]:
    """Parsea ``buttons_colors``: ``P1_BUTTON1:Red:Attack;P1_COIN:White:;...``

    Las entradas sin accion (``P1_COIN:White:``) se descartan: son el mapa fisico
    del panel, no controles con significado en el juego.
    """
    botones = []
    for entrada in raw.split(";"):
        partes = entrada.split(":", 2)
        if len(partes) != 3:
            continue
        control, color, accion = (parte.strip() for parte in partes)
        if control and accion:
            botones.append(CabinetButtonData(control, color, accion))
    return tuple(botones)


def _split_secciones(texto: str) -> dict[str, str]:
    """Mapea nombre de seccion a su cuerpo. La intro queda bajo la clave vacia."""
    cortes = list(_SECCION.finditer(texto))
    secciones = {"": texto[: cortes[0].start()] if cortes else texto}
    for i, corte in enumerate(cortes):
        fin = cortes[i + 1].start() if i + 1 < len(cortes) else len(texto)
        secciones[corte.group(1).strip()] = texto[corte.end() : fin]
    return secciones


def _limpiar_intro(intro: str) -> tuple[str, str]:
    """Saca el boilerplate de la intro y devuelve (sinopsis, empresa del copyright)."""
    parrafos: list[str] = []
    empresa = ""
    for parrafo in intro.split("\n\n"):
        limpio = " ".join(parrafo.split())
        if not limpio or _PUBLICADO.match(limpio):
            continue
        copyright_match = _COPYRIGHT.match(limpio)
        if copyright_match and not parrafos:
            empresa = empresa or copyright_match.group("empresa").strip()
            continue
        parrafos.append(limpio)
    return "\n\n".join(parrafos), empresa


def _split_tips(cuerpo: str) -> tuple[str, ...]:
    tips = []
    for bruto in _TIP_SPLIT.split(cuerpo):
        tip = " ".join(bruto.lstrip(" \t*").split())
        if tip:
            tips.append(tip)
    return tuple(tips)


def truncar_en_oracion(texto: str, max_length: int | None) -> str:
    """Recorta al ultimo punto que entre en ``max_length``. Publico: tambien lo usa
    el servicio de precarga para hacer respetar el limite despues de traducir."""
    if max_length is None or len(texto) <= max_length:
        return texto
    recorte = texto[:max_length]
    ultimo_punto = recorte.rfind(".")
    return recorte[: ultimo_punto + 1] if ultimo_punto > 0 else recorte.rstrip()
