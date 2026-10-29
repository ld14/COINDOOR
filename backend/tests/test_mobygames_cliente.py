from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from backend.lib.providers.mobygames import cliente
from backend.lib.providers.mobygames.cliente import buscar_ficha, elegir, normalizar
from backend.lib.providers.mobygames.parser import parse_busqueda
from backend.lib.providers.scraping import pagina_desde_html

if TYPE_CHECKING:
    from backend.lib.providers.mobygames.parser import Fila
    from backend.lib.providers.scraping import ScrapingClient

FIXTURES = Path(__file__).parent / "fixtures" / "mobygames"


def _filas(nombre: str) -> tuple[Fila, ...]:
    html = (FIXTURES / nombre).read_text(encoding="utf-8")
    return parse_busqueda(pagina_desde_html(html))


def test_normaliza_puntuacion_y_espacios() -> None:
    assert normalizar("Guy Spy ") == "guy spy"
    assert normalizar("Mission: Impossible") == "mission impossible"
    assert normalizar("Monkey Island 1 & 2") == "monkey island 1 2"
    assert normalizar("Island :  VGA") == "island vga"


def test_lee_las_filas_de_juego_con_alias_y_anio_por_plataforma() -> None:
    filas = _filas("busqueda-tmnt.html")
    assert len(filas) == 12
    primera = filas[0]
    assert primera.id == "6932"
    assert primera.title == "Teenage Mutant Ninja Turtles"
    assert primera.url == "https://www.mobygames.com/game/6932/teenage-mutant-ninja-turtles/"
    assert primera.plataformas["dos"] == "1990"
    assert primera.plataformas["arcade"] == "1989"
    assert "Gekikame Ninja Den" in primera.alias
    assert filas[1].plataformas["dos"] == "1992"


def test_la_busqueda_general_descarta_las_filas_que_no_son_juegos() -> None:
    filas = _filas("busqueda-monkey-island-todo.html")
    assert len(filas) == 11  # la fila 2 es el grupo "Monkey Island series"
    assert all("series" not in f.title.lower() for f in filas)


def test_tmnt_nivel_1_desempata_por_el_anio_de_dos() -> None:
    filas = _filas("busqueda-tmnt.html")
    elegida = elegir(filas, "Teenage Mutant Ninja Turtles", "1990", "DOS")
    assert elegida is not None and elegida.id == "6932"
    otra = elegir(filas, "Teenage Mutant Ninja Turtles", "1992", "DOS")
    assert otra is not None and otra.id == "7470"


def test_tmnt_con_un_anio_que_no_separa_no_elige() -> None:
    filas = _filas("busqueda-tmnt.html")
    assert elegir(filas, "Teenage Mutant Ninja Turtles", "1975", "DOS") is None


def test_guy_spy_nivel_2_exige_el_anio_de_dos() -> None:
    filas = _filas("busqueda-guy-spy.html")
    elegida = elegir(filas, "Guy Spy ", "1992", "DOS")
    assert elegida is not None and elegida.id == "6716"
    assert elegir(filas, "Guy Spy", None, "DOS") is None  # sin año, el nivel 2 no elige
    assert elegir(filas, "Guy Spy", "1980", "DOS") is None


def test_el_nivel_2_compara_palabras_enteras() -> None:
    filas = _filas("busqueda-guy-spy.html")
    # "Spycraft: The Great Game" tiene DOS 1996 pero no la palabra "spy" suelta
    assert elegir(filas, "Spy", "1996", "DOS") is None


def test_una_plataforma_sin_filas_no_elige() -> None:
    filas = _filas("busqueda-guy-spy.html")
    assert elegir(filas, "Guy Spy", "1992", "Atari 2600") is None


def test_monkey_island_1990_se_resuelve_con_la_tolerancia_del_nivel_2() -> None:
    # MobyGames lista DOS (1992) para "The Secret of Monkey Island" y la ficha dice 1990:
    # 2 años. Las otras filas con DOS son de 1997 y 1999, así que queda una sola.
    filas = _filas("busqueda-monkey-island.html")
    elegida = elegir(filas, "Monkey Island", "1990", "DOS")
    assert elegida is not None and elegida.id == "141074"
    assert elegir(filas, "Monkey Island", "1992", "DOS") == elegida


def test_la_tolerancia_de_2_anios_es_solo_del_nivel_2() -> None:
    # Nivel 1 (título exacto): TMNT 1975 está a 15 años de las dos filas, no elige;
    # y a 2 años de una fila exacta tampoco (solo ±1).
    filas = _filas("busqueda-tmnt.html")
    assert elegir(filas, "Teenage Mutant Ninja Turtles", "1994", "DOS") is None
    # Nivel 2: a 3 años ya no resuelve.
    guy = _filas("busqueda-guy-spy.html")
    assert elegir(guy, "Guy Spy", "1995", "DOS") is None
    assert elegir(guy, "Guy Spy", "1994", "DOS") is not None


class _Cliente:
    def __init__(self, paginas: dict[str, str]) -> None:
        self.paginas = paginas
        self.pedidas: list[str] = []

    def get_page(self, url: str, **_k: Any) -> Any:
        self.pedidas.append(url)
        for fin, archivo in self.paginas.items():
            if url.endswith(fin):
                return pagina_desde_html((FIXTURES / archivo).read_text(encoding="utf-8"))
        raise AssertionError(f"pedido inesperado: {url}")


def _como_cliente(fake: _Cliente) -> ScrapingClient:
    return cast("ScrapingClient", fake)


@pytest.fixture(autouse=True)
def memo_limpio() -> Iterator[None]:
    cliente.olvidar()
    yield
    cliente.olvidar()


def test_buscar_ficha_baja_busqueda_ficha_y_specs_y_usa_el_memo() -> None:
    fake = _Cliente(
        {
            "type=game": "busqueda-guy-spy.html",
            "/guy-spy-and-the-crystals-of-armageddon/": "maniac-mansion.html",
            "/specs/": "maniac-mansion-specs.html",
        }
    )
    primera = buscar_ficha(_como_cliente(fake), "Guy Spy", "1992", "DOS")
    assert primera is not None
    assert fake.pedidas[0].endswith("/search/?q=Guy+Spy&type=game")
    assert len(fake.pedidas) == 3
    segunda = buscar_ficha(_como_cliente(fake), "guy spy", "1992", "DOS")
    assert segunda is primera
    assert len(fake.pedidas) == 3  # el memo evitó volver a bajar


def test_buscar_ficha_sin_resultado_claro_no_baja_la_ficha() -> None:
    fake = _Cliente({"type=game": "busqueda-guy-spy.html"})
    assert buscar_ficha(_como_cliente(fake), "Titulo Inexistente", "1992", "DOS") is None
    assert len(fake.pedidas) == 1


def test_con_el_enlace_de_procedencia_se_salta_la_busqueda() -> None:
    fake = _Cliente(
        {
            "/maniac-mansion/": "maniac-mansion.html",
            "/specs/": "maniac-mansion-specs.html",
        }
    )
    resultado = buscar_ficha(
        _como_cliente(fake),
        "Maniac Mansion",
        "1988",
        "DOS",
        ficha_url="https://www.mobygames.com/game/714/maniac-mansion/",
    )
    assert resultado is not None and resultado.ficha.year == "1988"
    assert all("/search/" not in u for u in fake.pedidas)


def test_sugerir_con_la_url_de_la_procedencia_reusa_la_ficha_de_la_precarga() -> None:
    # La precarga busca por título; "Sugerir" llega después con la URL que quedó en la
    # procedencia. Es la misma ficha: no se vuelve a bajar.
    fake = _Cliente(
        {
            "type=game": "busqueda-guy-spy.html",
            "/guy-spy-and-the-crystals-of-armageddon/": "maniac-mansion.html",
            "/specs/": "maniac-mansion-specs.html",
        }
    )
    por_titulo = buscar_ficha(_como_cliente(fake), "Guy Spy", "1992", "DOS")
    assert por_titulo is not None and len(fake.pedidas) == 3
    por_url = buscar_ficha(
        _como_cliente(fake),
        "Guy Spy",
        None,
        "DOS",
        ficha_url="https://www.mobygames.com/game/6716/guy-spy-and-the-crystals-of-armageddon/",
    )
    assert por_url is por_titulo
    assert len(fake.pedidas) == 3


def test_una_busqueda_sin_resultado_tampoco_se_repite() -> None:
    fake = _Cliente({"type=game": "busqueda-guy-spy.html"})
    assert buscar_ficha(_como_cliente(fake), "Titulo Inexistente", "1992", "DOS") is None
    assert buscar_ficha(_como_cliente(fake), "Titulo Inexistente", "1992", "DOS") is None
    assert len(fake.pedidas) == 1


def test_sin_año_y_con_dos_ediciones_del_mismo_titulo_no_elige() -> None:
    filas = _filas("busqueda-tmnt.html")
    assert elegir(filas, "Teenage Mutant Ninja Turtles", None, "DOS") is None
