from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from backend.bundle.gamejson import FORMATOS_FISICOS
from backend.lib.providers.mobygames import parser
from backend.lib.providers.mobygames.parser import parse_ficha, parse_specs
from backend.lib.providers.scraping import pagina_desde_html

if TYPE_CHECKING:
    from backend.lib.providers.scraping import Pagina

FIXTURES = Path(__file__).parent / "fixtures" / "mobygames"


def _pagina(nombre: str) -> Pagina:
    return pagina_desde_html((FIXTURES / nombre).read_text(encoding="utf-8"))


def test_ficha_de_dos_toma_los_datos_de_esa_plataforma() -> None:
    ficha = parse_ficha(_pagina("maniac-mansion.html"), "DOS")
    assert ficha.title == "Maniac Mansion"
    assert ficha.alias == ("MM",)
    assert ficha.year == "1988"  # el de DOS, no 1987 (Apple II) del JSON-LD
    assert ficha.developer == "Lucasfilm Games"
    assert ficha.publisher == "Lucasfilm Games"
    assert ficha.genre == "Adventure"
    assert ficha.score == 82
    assert ficha.url == "https://www.mobygames.com/game/714/maniac-mansion/"
    assert ficha.description.startswith("The Edison mansion has always been")


def test_el_editor_es_el_de_la_plataforma_pedida() -> None:
    page = _pagina("maniac-mansion.html")
    assert parse_ficha(page, "NES").publisher == "Jaleco Ltd."
    assert parse_ficha(page, "Windows").publisher == "Disney Interactive Studios, Inc."


def test_el_anio_cambia_con_la_plataforma() -> None:
    page = _pagina("maniac-mansion.html")
    assert parse_ficha(page, "Apple II").year == "1987"
    assert parse_ficha(page, "NES").year == "1988"
    assert parse_ficha(page, "Linux").year == "2017"


def test_plataforma_sin_fila_da_campos_vacios() -> None:
    ficha = parse_ficha(_pagina("maniac-mansion.html"), "Atari 2600")
    assert ficha.year == ""
    assert ficha.publisher == ""
    assert ficha.title == "Maniac Mansion"


def test_specs_de_dos_trae_jugadores_y_formato() -> None:
    specs = parse_specs(_pagina("maniac-mansion-specs.html"), "DOS")
    assert specs.players == "1"  # "Number of Offline Players" en DOS
    assert specs.formatos == ("Diskette",)  # 3.5" y 5.25" son el mismo formato


def test_specs_de_otras_plataformas_no_se_mezclan() -> None:
    page = _pagina("maniac-mansion-specs.html")
    nes = parse_specs(page, "NES")
    assert nes.players == "1"
    assert nes.formatos == ("Cartucho",)
    linux = parse_specs(page, "Linux")
    assert linux.formatos == ()  # "Download" no tiene equivalente


def test_specs_de_plataforma_ausente_es_vacio() -> None:
    specs = parse_specs(_pagina("maniac-mansion-specs.html"), "Atari 2600")
    assert specs.players == ""
    assert specs.formatos == ()


def test_los_soportes_se_llevan_a_formatos_del_contrato() -> None:
    for _marca, formato in parser._SOPORTES:
        assert formato in FORMATOS_FISICOS
    assert parser._formato('3.5" Floppy Disk') == "Diskette"
    assert parser._formato("Double-sided Disk") == "Diskette"
    assert parser._formato("CD-ROM") == "CD"  # el nombre exacto en MobyGames no se vio
    assert parser._formato("Download") == ""


def test_jugadores_como_rango() -> None:
    assert parser._jugadores(["1 Player", "2 Players"]) == "1-2"
    assert parser._jugadores(["1-4 Players"]) == "1-4"
    assert parser._jugadores([]) == ""
