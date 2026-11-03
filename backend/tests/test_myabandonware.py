"""Feature 023: myabandonware como primera fuente de PC/DOS (ADR-0027)."""

from __future__ import annotations

import gzip
import os
import time
from pathlib import Path
from types import TracebackType

import httpx
import pytest

from backend.config import Settings
from backend.lib.domain.plataformas import nombre_en
from backend.lib.providers.base import Consulta, Limite
from backend.lib.providers.http import ProviderHttpClient, ProviderHttpError, ProviderNotFound
from backend.lib.providers.myabandonware import cliente
from backend.lib.providers.myabandonware.parser import Ficha, parse_ficha, parse_sitemap
from backend.lib.providers.myabandonware.proveedor import MyAbandonwareProvider
from backend.lib.providers.registro import providers_for
from backend.lib.providers.scraping import pagina_desde_html
from backend.store.cuotas import QuotasStore

FIXTURES = Path(__file__).parent / "fixtures" / "myabandonware"
# El índice de verdad: el conftest lo reemplaza por uno vacío para que ningún test salga a la red.
_INDICE = cliente.indice
_PROHIBIDAS = ("/search/", "/download/", "/manual/")


class _Http:
    """Sirve las páginas guardadas; una página que no está guardada es un 404."""

    def __init__(self, sitemap: bytes | None = None) -> None:
        self.pedidas: list[str] = []
        self.sitemap = sitemap if sitemap is not None else (FIXTURES / "sitemap.xml").read_bytes()

    def __enter__(self) -> _Http:
        return self

    def __exit__(
        self,
        _t: type[BaseException] | None,
        _e: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        return None

    def get_text(self, url: str) -> str:
        self.pedidas.append(url)
        archivo = FIXTURES / f"{url.rsplit('/', 1)[-1]}.html"
        if not archivo.exists():
            raise ProviderNotFound("sin resultados", status_code=404)
        return archivo.read_text(encoding="utf-8")

    def get_bytes(self, url: str) -> bytes:
        self.pedidas.append(url)
        return self.sitemap


class _Caido(_Http):
    def get_bytes(self, url: str) -> bytes:
        raise ProviderHttpError("fallo pasajero", retry_exhausted=True)


@pytest.fixture()
def indice_real(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cliente, "indice", _INDICE)


def _ficha(slug: str) -> Ficha:
    url = f"https://www.myabandonware.com/game/{slug}"
    html = (FIXTURES / f"{slug}.html").read_text(encoding="utf-8")
    return parse_ficha(pagina_desde_html(html, url=url), url)


def _paginas(http: _Http) -> list[str]:
    return [url.rsplit("/", 1)[-1] for url in http.pedidas if "/game/" in url]


# ── Parser ──────────────────────────────────────────────────────────────────


def test_lee_la_pagina_de_prince_of_persia() -> None:
    ficha = _ficha("prince-of-persia-pd")
    assert ficha.title == "Prince of Persia"
    assert "Jordan Mechner's Prince of Persia" in ficha.alias
    assert ficha.year == "1990"
    assert ficha.plataforma == "DOS"
    assert ficha.developer == ""  # la página no lo tiene
    assert ficha.publisher == "Brøderbund Software, Inc."
    assert ficha.genre == "Action"
    assert ficha.description.startswith("Prince of Persia was released in 1989 on the Apple II")
    # Termina antes de la firma y de las notas del sitio.
    assert "Review By" not in ficha.description
    assert "popot.org" not in ficha.description
    assert ficha.mobygames_url == "https://www.mobygames.com/game/196/prince-of-persia/"


def test_solo_lee_las_capturas_de_la_plataforma_de_la_pagina() -> None:
    capturas = _ficha("prince-of-persia-pd").capturas
    assert len(capturas) == 22  # las de Mac, Amiga… van en otras pestañas
    assert all("/prince-of-persia-pd/" in c.url for c in capturas)
    assert capturas[0].url == (
        "https://www.myabandonware.com/media/screenshots/p/prince-of-persia-pd/prince-of-persia_1.gif"
    )
    assert capturas[0].miniatura.endswith("/thumbs/prince-of-persia_1.png")


def test_el_editor_es_el_primero_que_lo_publico() -> None:
    # La tabla los ordena por nombre (Hasbro primero); el JSON-LD, por lanzamiento.
    ficha = _ficha("sid-meier-s-civilization-1nj")
    assert ficha.publisher == "MicroProse Software, Inc."
    assert ficha.developer == "MPS Labs"
    assert "Civilization" in ficha.alias
    assert ficha.mobygames_url == "https://www.mobygames.com/game/585/sid-meiers-civilization/"


def test_el_sitemap_da_los_slugs_de_juego() -> None:
    slugs = parse_sitemap((FIXTURES / "sitemap.xml").read_text(encoding="utf-8"))
    assert len(slugs) == 107
    assert {"prince-of-persia-pd", "sid-meier-s-civilization-1nj"} <= set(slugs)
    assert all("/" not in slug for slug in slugs)


# ── Elegir el juego ─────────────────────────────────────────────────────────


def test_candidatas_primero_el_titulo_y_despues_las_que_lo_contienen() -> None:
    slugs = parse_sitemap((FIXTURES / "sitemap.xml").read_text(encoding="utf-8"))
    exactas, contienen = cliente.candidatas(slugs, "Civilization")
    assert exactas == ["civilization-td6"]
    assert contienen[:3] == [
        "advanced-civilization-249",
        "dawn-of-civilization-l0b",
        "sid-meier-s-civilization-1nj",
    ]


def test_prince_of_persia_elige_la_pagina_de_dos(tmp_path: Path, indice_real: None) -> None:
    http = _Http()
    ficha = cliente.buscar(http, tmp_path, "Prince of Persia", "1990", "DOS")
    assert ficha is not None and ficha.url.endswith("/prince-of-persia-pd")
    # Solo las dos páginas con ese título: la de J2ME (2008) queda afuera por plataforma.
    assert set(_paginas(http)) == {"prince-of-persia-pd", "prince-of-persia-w2a"}


def test_civilization_la_encuentra_por_su_nombre_alternativo(
    tmp_path: Path, indice_real: None
) -> None:
    http = _Http()
    ficha = cliente.buscar(http, tmp_path, "Civilization", "1991", "DOS")
    assert ficha is not None and ficha.title == "Sid Meier's Civilization"
    assert "civilization-td6" in _paginas(http)  # la de N-Gage tiene el título, no la plataforma
    assert len(_paginas(http)) <= cliente.MAX_PAGINAS


def test_un_titulo_que_solo_esta_contenido_no_elige_ninguno(
    tmp_path: Path, indice_real: None
) -> None:
    # "Doom" está contenido en 56 slugs y ninguno es el de DOS.
    http = _Http()
    assert cliente.buscar(http, tmp_path, "Doom", "1993", "DOS") is None
    assert len(_paginas(http)) <= cliente.MAX_PAGINAS


def test_guy_spy_no_se_elige_porque_su_pagina_no_tiene_el_nombre_corto(
    tmp_path: Path, indice_real: None
) -> None:
    # Se llama "Guy Spy and the Crystals of Armageddon", sin nombres alternativos: lo busca
    # Launchbox, que tiene buscador (ADR-0027, alternativa D).
    assert cliente.buscar(_Http(), tmp_path, "Guy Spy", "1992", "DOS") is None


def test_dos_paginas_de_dos_con_el_mismo_titulo_las_desempata_el_año(
    tmp_path: Path, indice_real: None
) -> None:
    ficha = cliente.buscar(_Http(), tmp_path, "Teenage Mutant Ninja Turtles", "1989", "DOS")
    assert ficha is not None and ficha.year == "1990"  # la de 1992 queda a más de un año
    assert cliente.buscar(_Http(), tmp_path, "Teenage Mutant Ninja Turtles", None, "DOS") is None


def test_la_busqueda_queda_en_memoria(tmp_path: Path, indice_real: None) -> None:
    cliente.buscar(_Http(), tmp_path, "Prince of Persia", "1990", "DOS")
    otra = _Http()
    assert cliente.buscar(otra, tmp_path, "Prince of Persia", "1990", "DOS") is not None
    assert otra.pedidas == []


def test_nunca_pide_la_busqueda_las_descargas_ni_los_manuales(
    tmp_path: Path, indice_real: None
) -> None:
    http = _Http()
    for titulo in ("Prince of Persia", "Civilization", "Doom", "Guy Spy"):
        cliente.buscar(http, tmp_path, titulo, None, "DOS")
    assert http.pedidas
    assert not [url for url in http.pedidas if any(p in url for p in _PROHIBIDAS)]


# ── Índice ──────────────────────────────────────────────────────────────────


def _indice_guardado(carpeta: Path, *, dias: int) -> None:
    archivo = carpeta / "juegos.txt"
    archivo.write_text("viejo-1\n", encoding="utf-8")
    cuando = time.time() - dias * 86400
    os.utime(archivo, (cuando, cuando))


def test_el_indice_se_baja_comprimido_una_vez_y_queda_en_disco(
    tmp_path: Path, indice_real: None
) -> None:
    http = _Http(sitemap=gzip.compress((FIXTURES / "sitemap.xml").read_bytes()))
    slugs = cliente.indice(http, tmp_path)
    assert "prince-of-persia-pd" in slugs
    assert http.pedidas == [cliente.SITEMAP]
    cliente.olvidar()
    otra = _Http()
    assert cliente.indice(otra, tmp_path) == slugs
    assert otra.pedidas == []


def test_un_indice_de_hace_mas_de_30_dias_se_renueva(tmp_path: Path, indice_real: None) -> None:
    _indice_guardado(tmp_path, dias=31)
    http = _Http()
    slugs = cliente.indice(http, tmp_path)
    assert "viejo-1" not in slugs
    assert http.pedidas == [cliente.SITEMAP]


def test_si_no_se_puede_renovar_sigue_el_indice_guardado(
    tmp_path: Path, indice_real: None
) -> None:
    _indice_guardado(tmp_path, dias=31)
    assert cliente.indice(_Caido(), tmp_path) == ("viejo-1",)


def test_sin_indice_guardado_el_error_sube(tmp_path: Path, indice_real: None) -> None:
    with pytest.raises(ProviderHttpError):
        cliente.indice(_Caido(), tmp_path)


# ── Proveedor ───────────────────────────────────────────────────────────────


def _consulta(key: str, titulo: str = "Prince of Persia", system: str = "msdos") -> Consulta:
    anio = "1990" if titulo == "Prince of Persia" else "1991"
    return Consulta("juego", key, titulo, system, anio)


def test_el_proveedor_ofrece_la_identidad_la_sinopsis_y_las_capturas(
    tmp_path: Path, indice_real: None
) -> None:
    provider = MyAbandonwareProvider(_Http, tmp_path)

    editor = provider.buscar(_consulta("publisher"))
    assert [c.value for c in editor.candidatos] == ["Brøderbund Software, Inc."]
    assert editor.candidatos[0].fuente == "MyAbandonware"
    assert editor.candidatos[0].kind == "identity" and editor.candidatos[0].clase == "aplicable"
    assert (editor.candidatos[0].origen_url or "").endswith("/prince-of-persia-pd")
    assert editor.trace.estado == "ok"

    genero = provider.buscar(_consulta("genre")).candidatos[0]
    assert genero.nombre == "Género (en inglés) (MyAbandonware)"

    sinopsis = provider.buscar(_consulta("sinopsis")).candidatos[0]
    assert sinopsis.kind == "text"
    assert sinopsis.nombre == "Sinopsis (en inglés) (MyAbandonware)"

    capturas = provider.buscar(_consulta("captura")).candidatos
    assert len(capturas) == 22
    assert capturas[0].kind == "media"
    assert (capturas[0].media_url or "").endswith("/prince-of-persia_1.gif")
    assert (capturas[0].preview_url or "").endswith("/thumbs/prince-of-persia_1.png")

    # La página no tiene desarrollador: sin candidato, para que siga Launchbox.
    assert provider.buscar(_consulta("developer")).candidatos == ()


def test_no_ofrece_jugadores_formato_ni_caratula() -> None:
    # `playMode` dice "SinglePlayer" en todos los juegos, el formato no está y no hay cajas.
    assert not {"players", "format", "caratula"} & MyAbandonwareProvider.campos


def test_un_sistema_sin_equivalencia_no_se_consulta(tmp_path: Path) -> None:
    http = _Http()
    resultado = MyAbandonwareProvider(lambda: http, tmp_path).buscar(
        _consulta("developer", "Golden Axe", "arcade")
    )
    assert resultado.trace.estado == "plataforma sin equivalencia"
    assert http.pedidas == []


def test_solo_ms_dos_tiene_equivalencia() -> None:
    assert nombre_en("msdos", "myabandonware") == "DOS"
    assert nombre_en("arcade", "myabandonware") is None


def test_da_el_enlace_a_la_ficha_de_mobygames(tmp_path: Path, indice_real: None) -> None:
    provider = MyAbandonwareProvider(_Http, tmp_path)
    enlace = provider.enlace_mobygames(_consulta("format", "Civilization"))
    assert enlace == "https://www.mobygames.com/game/585/sid-meiers-civilization/"


def test_sin_red_no_hay_enlace_y_no_rompe(tmp_path: Path, indice_real: None) -> None:
    provider = MyAbandonwareProvider(_Caido, tmp_path)
    assert provider.enlace_mobygames(_consulta("format")) is None


# ── Cadenas (ADR-0027) ──────────────────────────────────────────────────────


def test_las_cadenas_de_adr_0027(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backend.lib.providers.registro.navegador_disponible", lambda: True)
    settings = Settings(
        data_dir=tmp_path / "data",
        ai_primary_base_url="https://ia.test/v1",
        ai_primary_api_key="k",
        ai_primary_model="m1",
        ai_backup_base_url="https://ia.test/v1",
        ai_backup_api_key="k",
        ai_backup_model="m2",
    )
    settings.data_dir.mkdir(parents=True)

    def nombres(key: str) -> list[str]:
        return [p.nombre for p in providers_for(key, settings)]

    for key in ("year", "developer", "publisher", "genre"):
        assert nombres(key) == ["ArcadeDB", "MyAbandonware", "Launchbox", "MobyGames"], key
    assert nombres("title") == ["ArcadeDB", "MyAbandonware", "MobyGames"]
    assert nombres("players") == ["ArcadeDB", "Launchbox", "MobyGames"]
    assert nombres("format") == ["ArcadeDB", "MobyGames"]
    assert nombres("caratula") == ["ArcadeDB", "Launchbox", "MobyGames", "Image Search"]
    assert nombres("captura") == [
        "ArcadeDB", "MyAbandonware", "Launchbox", "MobyGames", "Image Search",
    ]
    assert nombres("sinopsis") == ["ArcadeDB", "MyAbandonware", "IA · m1", "IA · m2", "MobyGames"]
    # La reseña vuelve a ser solo de la IA; video, guía y trucos no cambian.
    assert nombres("review") == ["IA · m1", "IA · m2"]
    assert nombres("video") == ["ArcadeDB", "YouTube"]
    assert nombres("objetivo") == ["IA · m1", "IA · m2"]
    assert nombres("cheats") == ["ArcadeDB"]  # sin buscador configurado


# ── HTTP común con la política de http.py ───────────────────────────────────


def test_http_lee_texto_y_bytes_con_la_misma_politica(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/ya-no-esta":
            return httpx.Response(404, text="<html>no</html>")
        return httpx.Response(200, content="<html>Brøderbund</html>".encode())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("Test", Limite(), quotas, timeout=1, client=client)
    with http:
        assert http.get_text("https://example.test/pagina") == "<html>Brøderbund</html>"
        assert http.get_bytes("https://example.test/pagina") == "<html>Brøderbund</html>".encode()
        with pytest.raises(ProviderNotFound):
            http.get_text("https://example.test/ya-no-esta")
