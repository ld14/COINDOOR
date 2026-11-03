"""Feature 022: todas las fuentes eligen la edición de la ficha (páginas reales guardadas)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest

from backend.lib.providers import coincidencia
from backend.lib.providers.base import Consulta
from backend.lib.providers.launchbox import cliente as lb_cliente
from backend.lib.providers.launchbox.cliente import (
    LaunchboxFicha,
    LaunchboxSearchResult,
    _con_su_pagina,
    _parse_details,
    _parse_images_page,
    _parse_search_results,
    _search_and_parse,
    _tarjetas_de,
    fetch_details,
)
from backend.lib.providers.launchbox.proveedor import LaunchboxImageProvider, jugadores
from backend.lib.providers.mobygames import cliente as mg_cliente
from backend.lib.providers.mobygames.cliente import Imagen, buscar_imagenes
from backend.lib.providers.mobygames.parser import (
    parse_capturas,
    parse_ficha,
    parse_portada_grande,
    parse_portadas,
)
from backend.lib.providers.mobygames.proveedor import MobyGamesProvider
from backend.lib.providers.referencia.images import _search_ddg_images
from backend.lib.providers.scraping import ScrapingClient, pagina_desde_html
from backend.store.juegos import GamesStore

FIXTURES = Path(__file__).parent / "fixtures"
LB = FIXTURES / "launchbox"
MG = FIXTURES / "mobygames"


def _html(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def memorias_limpias() -> Iterator[None]:
    lb_cliente.olvidar()
    mg_cliente.olvidar()
    yield
    lb_cliente.olvidar()
    mg_cliente.olvidar()


# ── La regla común ────────────────────────────────────────────────────────────────


def test_la_regla_comun_prefiere_el_titulo_exacto_a_uno_que_lo_contiene() -> None:
    opciones = [("4D Prince of Persia", None), ("Prince of Persia", 1990)]
    elegida = coincidencia.elegir(
        opciones,
        "Prince of Persia",
        None,
        titulos_de=lambda o: (o[0],),
        principal_de=lambda o: o[0],
        anio_de=lambda o: o[1],
    )
    assert elegida == ("Prince of Persia", 1990)


# ── Launchbox elige con la regla común ───────────────────────────────────────────


def test_launchbox_elige_prince_of_persia_y_no_4d_prince_of_persia() -> None:
    html = _html(LB / "busqueda-prince-of-persia.html")
    for anio in ("1990", None):
        elegido = _parse_search_results(html, "Prince of Persia", "MS-DOS", anio)
        assert elegido is not None, anio
        assert (elegido.game_id, elegido.title, elegido.year) == (
            "13853",
            "Prince of Persia",
            "1990",
        )


def test_launchbox_resuelve_titulos_con_signos() -> None:
    html = _html(LB / "busqueda-prince-of-persia.html")
    elegido = _parse_search_results(
        html, "Prince of Persia 2: The Shadow & The Flame", "MS-DOS", "1993"
    )
    assert elegido is not None and elegido.game_id == "9402"


def test_launchbox_sin_coincidencia_clara_no_elige() -> None:
    html = _html(LB / "busqueda-prince-of-persia.html")
    # "Persia" solo aparece contenido en varios títulos y sin año no se elige ninguno.
    assert _parse_search_results(html, "Persia", "MS-DOS", None) is None


# ── Launchbox: la página del juego ───────────────────────────────────────────────


def test_launchbox_lee_la_identidad_de_la_pagina_del_juego() -> None:
    ficha = _parse_details(_html(LB / "ficha-prince-of-persia.html"), "url")
    assert ficha.developers == ("Brøderbund Software",)
    assert ficha.publishers == ("Brøderbund Software", "Softgold Computerspiele")
    assert ficha.genres == ("Platform", "Action")
    assert ficha.max_players == "1"
    assert ficha.year == "1990"


def test_launchbox_guarda_la_pagina_del_juego_en_memoria() -> None:
    class _Http:
        pedidos = 0

        def get(self, _url: str) -> Any:
            type(self).pedidos += 1

            class _Resp:
                text = _html(LB / "ficha-prince-of-persia.html")

                def raise_for_status(self) -> None:
                    return None

            return _Resp()

    http = cast("Any", _Http())
    assert fetch_details("13853", "prince-of-persia", http) is not None
    assert fetch_details("13853", "prince-of-persia", http) is not None
    assert _Http.pedidos == 1


def test_jugadores_como_en_la_ficha() -> None:
    assert jugadores("1") == "1"
    assert jugadores("4") == "1-4"
    assert jugadores("") == ""


@pytest.fixture()
def launchbox_falso(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    visto: dict[str, Any] = {}
    resultado = LaunchboxSearchResult(
        game_id="13853",
        slug="prince-of-persia",
        platform="MS-DOS",
        title="Prince of Persia",
        detail_url="https://gamesdb.launchbox-app.com/games/details/13853-prince-of-persia",
        year="1990",
    )

    def search_game(title: str, system: str, http: Any = None, anio: Any = None) -> Any:
        visto["anio"] = anio
        return resultado

    ficha = _parse_details(_html(LB / "ficha-prince-of-persia.html"), resultado.detail_url)
    monkeypatch.setattr("backend.lib.providers.launchbox.proveedor.search_game", search_game)
    monkeypatch.setattr(
        "backend.lib.providers.launchbox.proveedor.fetch_details", lambda *_a, **_k: ficha
    )
    return visto


def test_launchbox_sugiere_la_identidad_de_su_pagina(launchbox_falso: dict[str, Any]) -> None:
    provider = LaunchboxImageProvider()
    esperado = {
        "developer": "Brøderbund Software",
        "publisher": "Brøderbund Software",
        "genre": "Platform, Action",
        "players": "1",
        "year": "1990",
    }
    for key, valor in esperado.items():
        resultado = provider.buscar(Consulta("pop", key, "Prince of Persia", "msdos", "1990"))
        assert [c.value for c in resultado.candidatos] == [valor], key
        candidato = resultado.candidatos[0]
        assert candidato.fuente == "Launchbox" and candidato.kind == "identity"
        assert candidato.generado_por_ia is False
    assert launchbox_falso["anio"] == "1990"  # busca con el año de la ficha


def test_launchbox_sin_dato_no_ofrece_candidato(monkeypatch: pytest.MonkeyPatch) -> None:
    resultado = LaunchboxSearchResult("1", "x", "MS-DOS", "X", "u", "")
    monkeypatch.setattr(
        "backend.lib.providers.launchbox.proveedor.search_game", lambda *_a, **_k: resultado
    )
    vacia = LaunchboxFicha("u", (), (), (), "", "")
    monkeypatch.setattr(
        "backend.lib.providers.launchbox.proveedor.fetch_details", lambda *_a, **_k: vacia
    )
    buscado = LaunchboxImageProvider().buscar(Consulta("x", "developer", "X", "msdos", None))
    assert buscado.candidatos == ()


# ── MobyGames: carátulas y capturas de la edición ───────────────────────────────


def test_mobygames_sabe_el_slug_de_la_plataforma() -> None:
    pagina = pagina_desde_html(_html(MG / "prince-of-persia.html"))
    assert parse_ficha(pagina, "DOS").plataforma_slug == "dos"


def test_mobygames_lee_las_portadas_frontales_en_orden() -> None:
    portadas = parse_portadas(pagina_desde_html(_html(MG / "prince-of-persia-covers-dos.html")))
    assert len(portadas) >= 3
    primera = portadas[0]
    assert primera.enlace.endswith("/cover/group-3881/cover-383/")
    assert primera.miniatura.endswith(".webp")
    assert primera.pais == "United States"


def test_mobygames_saca_la_imagen_grande_de_una_portada() -> None:
    grande = parse_portada_grande(pagina_desde_html(_html(MG / "prince-of-persia-cover-383.html")))
    assert grande == "https://cdn.mobygames.com/covers/4008841-prince-of-persia-dos-front-cover.jpg"


def test_mobygames_lee_las_capturas() -> None:
    capturas = parse_capturas(
        pagina_desde_html(_html(MG / "prince-of-persia-screenshots-dos.html"))
    )
    assert len(capturas) == 32
    assert capturas[0].leyenda == "Title Screen"
    assert capturas[0].url.endswith("/screenshots/dos/814/")


class _ClienteMoby:
    def __init__(self) -> None:
        self.pedidas: list[str] = []

    def get_page(self, url: str, **_k: Any) -> Any:
        self.pedidas.append(url)
        if url.endswith("/covers/dos/"):
            archivo = "prince-of-persia-covers-dos.html"
        elif "/cover/" in url:
            archivo = "prince-of-persia-cover-383.html"
        elif url.endswith("/screenshots/dos/"):
            archivo = "prince-of-persia-screenshots-dos.html"
        elif url.endswith("/specs/"):
            archivo = "maniac-mansion-specs.html"
        else:
            archivo = "prince-of-persia.html"
        return pagina_desde_html(_html(MG / archivo))


FICHA_POP = "https://www.mobygames.com/game/196/prince-of-persia/"


def test_buscar_imagenes_da_las_portadas_grandes_de_la_ficha_elegida() -> None:
    fake = _ClienteMoby()
    imagenes = buscar_imagenes(
        cast("ScrapingClient", fake), "Prince of Persia", "1990", "DOS", "caratula",
        ficha_url=FICHA_POP,
    )
    assert len(imagenes) == len(parse_portadas(fake.get_page(f"{FICHA_POP}covers/dos/")))
    assert len(imagenes) > 3  # el tope viejo (feature 024)
    assert imagenes[0].media_url.endswith("prince-of-persia-dos-front-cover.jpg")
    assert imagenes[0].preview_url.endswith(".webp")
    assert imagenes[0].etiqueta == "Portada frontal (United States)"
    antes = len(fake.pedidas)
    buscar_imagenes(
        cast("ScrapingClient", fake), "Prince of Persia", "1990", "DOS", "caratula",
        ficha_url=FICHA_POP,
    )
    assert len(fake.pedidas) == antes  # en memoria


def test_buscar_imagenes_da_capturas_de_la_plataforma() -> None:
    imagenes = buscar_imagenes(
        cast("ScrapingClient", _ClienteMoby()), "Prince of Persia", "1990", "DOS", "captura",
        ficha_url=FICHA_POP,
    )
    assert len(imagenes) > 8  # el tope viejo (feature 024)
    assert imagenes[0].etiqueta == "Title Screen"
    assert imagenes[0].media_url == imagenes[0].preview_url


def test_buscar_imagenes_con_cuantas_no_baja_el_resto_ni_lo_deja_en_memoria() -> None:
    fake = _ClienteMoby()
    primera = buscar_imagenes(
        cast("ScrapingClient", fake), "Prince of Persia", "1990", "DOS", "caratula",
        ficha_url=FICHA_POP, cuantas=1,
    )
    assert len(primera) == 1
    assert sum("/cover/" in url for url in fake.pedidas) == 1
    todas = buscar_imagenes(
        cast("ScrapingClient", fake), "Prince of Persia", "1990", "DOS", "caratula",
        ficha_url=FICHA_POP,
    )
    assert len(todas) > 3


def test_el_proveedor_ofrece_las_portadas_como_media_aplicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    portada = Imagen("https://cdn/grande.jpg", "https://cdn/chica.webp", "Portada frontal", "o")
    monkeypatch.setattr(
        "backend.lib.providers.mobygames.proveedor.buscar_imagenes",
        lambda *_a, **_k: (portada,),
    )

    class _Ctx:
        def __enter__(self) -> _Ctx:
            return self

        def __exit__(self, *_a: Any) -> None:
            return None

    provider = MobyGamesProvider(
        GamesStore(tmp_path / "juegos"),
        lambda: cast("ScrapingClient", _Ctx()),
        timeout=60,
        pace=3.0,
    )
    resultado = provider.buscar(Consulta("pop", "caratula", "Prince of Persia", "msdos", "1990"))
    assert len(resultado.candidatos) == 1
    candidato = resultado.candidatos[0]
    assert candidato.kind == "media" and candidato.clase == "aplicable"
    assert candidato.media_url == "https://cdn/grande.jpg"
    assert candidato.preview_url == "https://cdn/chica.webp"
    assert candidato.nombre == "Portada frontal (MobyGames)"


# ── Image Search busca con el año ────────────────────────────────────────────────


def test_image_search_busca_con_el_año_de_la_ficha(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.lib.providers.referencia.images import ImageSearchProvider

    consultas: list[str] = []

    def buscar_ddg(query: str) -> list[dict[str, str]]:
        consultas.append(query)
        return []

    monkeypatch.setattr("backend.lib.providers.referencia.images._search_ddg_images", buscar_ddg)
    ImageSearchProvider().buscar(Consulta("pop", "caratula", "Prince of Persia", "msdos", "1990"))
    assert consultas and all("Prince of Persia 1990" in q for q in consultas)

    consultas.clear()
    ImageSearchProvider().buscar(Consulta("pop", "caratula", "Prince of Persia", "msdos", None))
    assert consultas and all("None" not in q for q in consultas)


# ── Launchbox: entidades y año que falta en la lista ────────────────────────────


def test_launchbox_decodifica_el_apostrofo() -> None:
    from backend.lib.providers.launchbox.cliente import _unescape_html

    assert _unescape_html("Sid Meier&#x27;s Civilization") == "Sid Meier's Civilization"


def test_launchbox_completa_con_la_pagina_el_año_que_falta_en_la_lista(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # En la búsqueda real "Sid Meier's Civilization" no trae año: sin él, el nivel 2 no
    # podía elegirlo. El año sale de la página del juego.
    def fetch_details(game_id: str, slug: str, _http: Any = None) -> LaunchboxFicha:
        anio = "1991" if game_id == "13599" else ""
        return LaunchboxFicha("u", ("MPS Labs",), ("MicroProse Software",), (), "1", anio)

    monkeypatch.setattr("backend.lib.providers.launchbox.cliente.fetch_details", fetch_details)
    monkeypatch.setattr("backend.lib.providers.launchbox.cliente._PAUSA_ENTRE_PAGINAS", 0)
    elegido = _buscar_en("busqueda-civilization.html", "Civilization", "1991")
    assert elegido is not None
    assert (elegido.game_id, elegido.title) == ("13599", "Sid Meier's Civilization")


def test_launchbox_una_pagina_que_falla_corta_y_elige_con_lo_que_sabe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pedidas: list[str] = []

    def falla(game_id: str, *_a: Any, **_k: Any) -> None:
        pedidas.append(game_id)

    monkeypatch.setattr("backend.lib.providers.launchbox.cliente.fetch_details", falla)
    assert _buscar_en("busqueda-civilization.html", "Civilization", None) is None
    assert len(pedidas) == 1


def test_launchbox_con_todas_trae_tambien_lo_que_no_va_en_un_casillero() -> None:
    html = """
    <a href="https://images.launchbox-app.com/a.jpg" data-title="Juego - Box - Front Image (Europe)">x</a>
    <a href="https://images.launchbox-app.com/b.jpg" data-title="Juego - Box - Back Image (Europe)">x</a>
    <a href="https://images.launchbox-app.com/c.jpg" data-title="Juego - Disc Image">x</a>
    """  # noqa: E501
    assert [i.media_url[-5:] for i in _parse_images_page(html, "1", "j")] == ["a.jpg"]

    todas = _parse_images_page(html, "1", "j", todas=True)
    assert [i.label for i in todas] == ["Carátula", "Box - Back (Europe)", "Disc"]
    assert [i.field_key for i in todas] == ["caratula", "", ""]


def test_una_busqueda_de_imagenes_completa_queda_en_memoria(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas: list[str] = []

    def paginas(query: str) -> tuple[list[dict[str, str]], bool]:
        llamadas.append(query)
        return [{"image": "a"}], query == "entera"

    monkeypatch.setattr("backend.lib.providers.referencia.images._paginas_ddg", paginas)

    assert _search_ddg_images("entera") == _search_ddg_images("entera")
    assert llamadas == ["entera"]

    llamadas.clear()
    _search_ddg_images("cortada")
    _search_ddg_images("cortada")
    assert llamadas == ["cortada", "cortada"]


def test_el_buscador_de_imagenes_no_ofrece_gif() -> None:
    from backend.lib.providers.referencia.images import _es_gif

    assert _es_gif("https://sitio.test/a/Caja.GIF?v=2")
    assert not _es_gif("https://sitio.test/a/caja.png?f=x.gif")


# ── Launchbox: títulos largos (feature 025) ─────────────────────────────────────


def _buscar_en(fixture: str, titulo: str, anio: str | None) -> LaunchboxSearchResult | None:
    html = _html(LB / fixture)

    class _Http:
        def get(self, _url: str) -> Any:
            class _Resp:
                text = html
                status_code = 200

                def raise_for_status(self) -> None:
                    return None

            return _Resp()

    return _search_and_parse(titulo, "msdos", cast("Any", _Http()), anio)


def _paginas_de_wing_commander(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    pedidas: list[str] = []
    juego = _parse_details(_html(LB / "ficha-wing-commander.html"), "u")
    dlc = _parse_details(_html(LB / "ficha-secret-missions.html"), "u")

    def fetch_details(game_id: str, *_a: Any, **_k: Any) -> LaunchboxFicha:
        pedidas.append(game_id)
        if game_id == "3490":
            return juego
        if game_id == "29408":
            return dlc
        return LaunchboxFicha("u", (), (), (), "1", "1990")

    monkeypatch.setattr("backend.lib.providers.launchbox.cliente.fetch_details", fetch_details)
    monkeypatch.setattr("backend.lib.providers.launchbox.cliente._PAUSA_ENTRE_PAGINAS", 0)
    return pedidas


def test_launchbox_lee_nombres_alternativos_y_tipo_de_la_pagina() -> None:
    juego = _parse_details(_html(LB / "ficha-wing-commander.html"), "u")
    assert juego.alternos == ("Wing Commander", "Wing Commander I", "Wing Commander 1")
    assert juego.tipo == "Released"
    dlc = _parse_details(_html(LB / "ficha-secret-missions.html"), "u")
    assert dlc.alternos == ()
    assert dlc.tipo == "DLC"


@pytest.mark.parametrize("anio", ["1990", None])
def test_launchbox_elige_el_juego_por_su_nombre_alternativo(
    monkeypatch: pytest.MonkeyPatch,
    anio: str | None,
) -> None:
    _paginas_de_wing_commander(monkeypatch)
    elegido = _buscar_en("busqueda-wing-commander.html", "Wing Commander", anio)
    assert elegido is not None
    assert (elegido.game_id, elegido.title) == (
        "3490",
        "Wing Commander: The 3-D Space Combat Simulator",
    )


def test_launchbox_no_elige_un_dlc(monkeypatch: pytest.MonkeyPatch) -> None:
    # El juego y el DLC son de 1990: el título y el año no los separan, el tipo sí.
    _paginas_de_wing_commander(monkeypatch)
    tarjetas = _tarjetas_de(_html(LB / "busqueda-wing-commander.html"), "msdos")
    assert any(t.game_id == "29408" for t in tarjetas)
    quedan = _con_su_pagina(tarjetas, "Wing Commander", cast("Any", None))
    assert not any(t.game_id == "29408" for t in quedan)


def test_launchbox_el_nombre_alternativo_solo_vale_con_el_año_de_la_ficha() -> None:
    # Launchbox dice que el remake de 1991 también se llama "Space Quest".
    remake = LaunchboxSearchResult(
        "1", "a", "MS-DOS", "Space Quest 1: Roger Wilco", "u", "1991", ("Space Quest",)
    )
    original = LaunchboxSearchResult("2", "b", "MS-DOS", "Space Quest: Chapter I", "u", "1986")
    elegido = lb_cliente._elegir([remake, original], "Space Quest", "1986")
    assert elegido is not None and elegido.game_id == "2"
    assert lb_cliente._elegir([remake], "Space Quest", "1990") == remake
    assert lb_cliente._elegir([remake, original], "Space Quest", None) == remake


def test_launchbox_no_abre_paginas_si_hay_titulo_exacto(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pedidas = _paginas_de_wing_commander(monkeypatch)
    elegido = _buscar_en("busqueda-wing-commander.html", "Wing Commander Armada", "1994")
    assert elegido is not None and elegido.game_id == "19266"
    assert pedidas == []


def test_launchbox_una_tarjeta_con_año_no_le_gana_a_la_correcta_sin_el(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # "Space Quest": la lista trae año solo en la segunda parte y, sin abrir las páginas, el
    # margen de ±2 se quedaba con ella.
    tarjetas = [
        LaunchboxSearchResult("1", "a", "MS-DOS", "Space Quest: The Sarien Encounter", "u"),
        LaunchboxSearchResult("2", "b", "MS-DOS", "Space Quest: Vohaul's Revenge", "u", "1987"),
    ]
    anios = {"1": "1986", "2": "1987"}
    monkeypatch.setattr(
        "backend.lib.providers.launchbox.cliente.fetch_details",
        lambda game_id, *_a, **_k: LaunchboxFicha("u", (), (), (), "1", anios[game_id]),
    )
    monkeypatch.setattr("backend.lib.providers.launchbox.cliente._PAUSA_ENTRE_PAGINAS", 0)
    completas = _con_su_pagina(tarjetas, "Space Quest", cast("Any", None))
    elegido = lb_cliente._elegir(completas, "Space Quest", "1986")
    assert elegido is not None and elegido.game_id == "1"


def test_launchbox_la_pagina_en_memoria_no_espera(monkeypatch: pytest.MonkeyPatch) -> None:
    esperas: list[float] = []
    ficha = LaunchboxFicha("u", (), (), (), "1", "1986")
    monkeypatch.setattr("backend.lib.providers.launchbox.cliente.time.sleep", esperas.append)
    monkeypatch.setitem(lb_cliente._fichas, "1", ficha)
    monkeypatch.setattr(
        "backend.lib.providers.launchbox.cliente.fetch_details",
        lambda *_a, **_k: ficha,
    )
    tarjetas = [
        LaunchboxSearchResult("1", "a", "MS-DOS", "Space Quest: Uno", "u"),
        LaunchboxSearchResult("2", "b", "MS-DOS", "Space Quest: Dos", "u"),
    ]
    _con_su_pagina(tarjetas, "Space Quest", cast("Any", None))
    assert esperas == [lb_cliente._PAUSA_ENTRE_PAGINAS]


def test_la_regla_comun_no_elige_una_secuela_numerada() -> None:
    def elegir(opciones: list[tuple[str, int]], titulo: str) -> tuple[str, int] | None:
        return coincidencia.elegir(
            opciones,
            titulo,
            "1981",
            titulos_de=lambda o: (o[0],),
            principal_de=lambda o: o[0],
            anio_de=lambda o: o[1],
        )

    assert elegir([("Ultima II: The Revenge", 1982)], "Ultima") is None
    assert elegir([("Keen 3: Die", 1982)], "Keen") is None
    primero = ("Ultima I: The First Age", 1982)
    assert elegir([primero], "Ultima") == primero
    segundo = ("Ultima II: The Revenge", 1982)
    assert elegir([segundo], "Ultima II") == segundo
