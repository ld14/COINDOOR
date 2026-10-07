from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any

from backend.bundle.gamejson import validate_accent
from backend.lib.domain.guia import (
    acciones_de,
    controles_de,
    lineas,
    multijugador_de,
    perifericos_desde,
    texto_guia,
)


def build_datajson(
    game: Mapping[str, Any],
    incluir: Collection[str],
    galeria: Collection[Mapping[str, str]] = (),
) -> dict[str, Any]:
    data: dict[str, Any] = {}

    accent = str(game.get("accentValue", ""))
    if validate_accent(accent):
        data["accent"] = accent

    accent2 = str(game.get("accent2Value", ""))
    if accent2.strip() and validate_accent(accent2) and "accent2" in incluir:
        data["accent2"] = accent2

    # review es la unica excepcion a "se omite lo vacio o deseleccionado": null
    # tiene significado propio ("no hay resena"), a diferencia de una clave ausente.
    data["review"] = _review(game, incluir)

    if "cheats" in incluir:
        cheats = _cheats(game)
        if cheats:
            data["cheats"] = cheats

    if "manual" in incluir:
        manual = _manual(game)
        if manual:
            data["manual"] = manual

    # La galeria la arma el staging, que es quien sabe que archivos copio de verdad:
    # declarar una imagen que no viaja deja un hueco del otro lado (ADR-0016).
    if "galeria" in incluir and galeria:
        data["gallery"] = [
            {"file": img["file"], "label": img["label"]} for img in galeria
        ]

    if "objetivo" in incluir:
        guia = build_guia(game, incluir)
        if guia:
            data["guia"] = guia

    return data


def build_guia(game: Mapping[str, Any], incluir: Collection[str] = ("objetivo",)) -> dict[str, Any]:
    """Bloque ``guia`` de ADR-0037 (ATTRACT). Vacio si no hay ``objetivo``.

    ``doctor`` rechaza una ``guia`` sin ``objetivo``. Los textos opcionales
    (``primerosPasos``, ``reglasEsenciales``, ``modo``) viajan solo si se eligieron en
    ``incluir``; ``acciones`` y ``perifericos`` son datos de ArcadeDB y acompañan al
    bloque. Nada de aca nombra un boton fisico ni una tecla de salida (los resuelve
    ATTRACT). ``fuentes`` no se emite: no se guarda la fecha de consulta y ``fecha`` es
    obligatoria.

    El ``objetivo`` es el texto ``texts.objetivo`` (feature 017), nunca la sinopsis.
    ``revision`` es ``revisado`` solo si todos los textos que viajan los escribio o
    guardo una persona (``manual``).
    """
    objetivo = texto_guia(game, "objetivo")
    if objetivo is None:
        return {}

    guia: dict[str, Any] = {"objetivo": objetivo[0]}
    revisados = [objetivo[1]]

    acciones = acciones_de(game)
    if acciones:
        guia["acciones"] = acciones

    for clave in ("primerosPasos", "reglasEsenciales"):
        campo = texto_guia(game, clave) if clave in incluir else None
        items = lineas(campo[0]) if campo else []
        if items:
            guia[clave] = items
            revisados.append(campo[1])  # type: ignore[index]

    multijugador, modo_manual = multijugador_de(game, incluir)
    if multijugador:
        guia["multijugador"] = multijugador
    if modo_manual is not None:
        revisados.append(modo_manual)

    perifericos = perifericos_desde(controles_de(game))
    if perifericos:
        guia["perifericos"] = perifericos

    guia["revision"] = "revisado" if all(revisados) else "borrador"
    return guia


def _review(game: Mapping[str, Any], incluir: Collection[str]) -> dict[str, Any] | None:
    review = game.get("review", {})
    if not isinstance(review, Mapping):
        return None
    if review.get("status") == "empty" or "review" not in incluir:
        return None
    return {"score": review.get("score"), "cats": dict(review.get("cats") or {})}


def _cheats(game: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    cheats = game.get("cheats", {})
    if not isinstance(cheats, Mapping) or cheats.get("status") == "empty":
        return {}
    groups = cheats.get("groups", [])
    if not isinstance(groups, list):
        return {}
    return {
        str(group["name"]): [
            {"name": str(entry["name"]), "input": str(entry["input"])}
            for entry in group.get("entries", [])
        ]
        for group in groups
        if isinstance(group, Mapping)
    }


def _manual(game: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Genera la lista manual[] para data.json.

    COINDOOR entrega el PDF crudo en media/_manual/, sin paginas rasterizadas.
    pages va ausente: rasterizar es paso de ATTRACT (attract rasterize).
    """
    manuals = game.get("manuals", [])
    if not isinstance(manuals, list):
        return []
    result: list[dict[str, Any]] = []
    for manual in manuals:
        if not isinstance(manual, Mapping) or manual.get("status") != "processed":
            continue
        pages = int(manual.get("pages", 0) or 0)
        if pages <= 0:
            continue
        result.append(
            {
                "file": manual.get("fileName", "manual.pdf"),
            }
        )
    return result
