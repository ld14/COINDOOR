from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from types import TracebackType
from typing import Any, cast

import pytest

from backend.config import Settings
from backend.lib.providers import mobygames as _pkg  # noqa: F401
from backend.lib.providers.base import Consulta
from backend.lib.providers.mobygames import cliente
from backend.lib.providers.mobygames.proveedor import MobyGamesProvider
from backend.lib.providers.registro import providers_for
from backend.lib.providers.scraping import ScrapingClient, navegador_disponible, pagina_desde_html
from backend.store.juegos import GamesStore

FIXTURES = Path(__file__).parent / "fixtures" / "mobygames"


class _Cliente:
    abiertos = 0

    def __init__(self) -> None:
        self.pedidas: list[str] = []

    def __enter__(self) -> _Cliente:
        type(self).abiertos += 1
        return self

    def __exit__(
        self,
        _t: type[BaseException] | None,
        _e: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        return None

    def get_page(self, url: str, **_k: Any) -> Any:
        self.pedidas.append(url)
        if "/search/" in url:
            archivo = "busqueda-guy-spy.html"
        elif url.endswith("/specs/"):
            archivo = "maniac-mansion-specs.html"
        else:
            archivo = "maniac-mansion.html"
        return pagina_desde_html((FIXTURES / archivo).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def memo_limpio() -> Iterator[None]:
    cliente.olvidar()
    _Cliente.abiertos = 0
    yield
    cliente.olvidar()


def _provider(tmp_path: Path, fake: _Cliente | None = None) -> MobyGamesProvider:
    fake = fake or _Cliente()
    return MobyGamesProvider(
        GamesStore(tmp_path / "juegos"),
        lambda: cast("ScrapingClient", fake),
        timeout=60,
        pace=3.0,
    )


def _buscar(provider: MobyGamesProvider, key: str, system: str = "msdos") -> Any:
    return provider.buscar(Consulta("guy-spy", key, "Guy Spy", system, "1992"))


def test_msdos_sugiere_cada_campo_de_identidad_con_los_datos_de_dos(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    esperado = {
        "title": "Maniac Mansion",
        "year": "1988",
        "developer": "Lucasfilm Games",
        "publisher": "Lucasfilm Games",
        "genre": "Adventure",
        "players": "1",
        "format": "Diskette",
    }
    for key, valor in esperado.items():
        resultado = _buscar(provider, key)
        assert [c.value for c in resultado.candidatos] == [valor], key
        candidato = resultado.candidatos[0]
        assert candidato.kind == "identity" and candidato.clase == "aplicable"
        assert candidato.fuente == "MobyGames"
        assert candidato.origen_url == "https://www.mobygames.com/game/714/maniac-mansion/"
        assert candidato.generado_por_ia is False


def test_la_nota_de_criticos_es_un_candidato_de_resena_con_solo_score(tmp_path: Path) -> None:
    resultado = _buscar(_provider(tmp_path), "review")
    candidato = resultado.candidatos[0]
    assert candidato.kind == "text"
    assert json.loads(candidato.value or "") == {"score": 82}


def test_la_sinopsis_es_texto(tmp_path: Path) -> None:
    candidato = _buscar(_provider(tmp_path), "sinopsis").candidatos[0]
    assert candidato.kind == "text"
    assert (candidato.value or "").startswith("The Edison mansion")


def test_arcade_no_se_consulta(tmp_path: Path) -> None:
    fake = _Cliente()
    resultado = _buscar(_provider(tmp_path, fake), "developer", system="arcade")
    assert resultado.candidatos == ()
    assert resultado.trace.estado == "plataforma sin equivalencia"
    assert _Cliente.abiertos == 0 and fake.pedidas == []


def test_una_clave_que_no_responde_no_abre_el_navegador(tmp_path: Path) -> None:
    resultado = _buscar(_provider(tmp_path), "marquesina")
    assert resultado.candidatos == ()
    assert _Cliente.abiertos == 0


def test_la_segunda_clave_del_mismo_juego_no_baja_otra_vez_las_paginas(tmp_path: Path) -> None:
    fake = _Cliente()
    provider = _provider(tmp_path, fake)
    _buscar(provider, "developer")
    _buscar(provider, "publisher")
    assert len(fake.pedidas) == 3  # búsqueda, ficha y specs, una sola vez


def test_registro_construye_mobygames_solo_con_navegador(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)

    monkeypatch.setattr("backend.lib.providers.registro.navegador_disponible", lambda: False)
    sin = [p.nombre for p in providers_for("developer", settings)]
    assert "MobyGames" not in sin  # la app arranca y la cadena sigue de largo

    monkeypatch.setattr("backend.lib.providers.registro.navegador_disponible", lambda: True)
    con = [p.nombre for p in providers_for("developer", settings)]
    # MobyGames es el último recurso (ADR-0027).
    assert con == ["ArcadeDB", "MyAbandonware", "Launchbox", "MobyGames"]


def test_con_el_enlace_de_otra_fuente_no_busca(tmp_path: Path) -> None:
    fake = _Cliente()
    provider = MobyGamesProvider(
        GamesStore(tmp_path / "juegos"),
        lambda: cast("ScrapingClient", fake),
        timeout=60,
        pace=3.0,
        enlace=lambda _consulta: "https://www.mobygames.com/game/714/maniac-mansion/",
    )
    resultado = _buscar(provider, "developer")
    assert [c.value for c in resultado.candidatos] == ["Lucasfilm Games"]
    assert not [url for url in fake.pedidas if "/search/" in url]


def test_si_el_enlace_falla_busca_como_siempre(tmp_path: Path) -> None:
    def enlace(_consulta: Consulta) -> str | None:
        raise RuntimeError("myabandonware caído")

    fake = _Cliente()
    provider = MobyGamesProvider(
        GamesStore(tmp_path / "juegos"),
        lambda: cast("ScrapingClient", fake),
        timeout=60,
        pace=3.0,
        enlace=enlace,
    )
    assert _buscar(provider, "developer").candidatos
    assert [url for url in fake.pedidas if "/search/" in url]


def test_navegador_disponible_busca_chromium_en_la_ruta_de_playwright(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    assert navegador_disponible() is False
    (tmp_path / "ffmpeg-1013").mkdir()
    assert navegador_disponible() is False
    (tmp_path / "chromium-1248").mkdir()
    assert navegador_disponible() is True
