"""Feature 024: el job que llena los campos vacíos de la ficha (ADR-0028)."""

from __future__ import annotations

import json
import shutil
import subprocess
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Literal

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.api.schemas import CreateGame, Identity, NewSystem
from backend.config import Settings
from backend.lib.jobs.registro import JobState
from backend.lib.media import colores_dominantes
from backend.lib.providers import referencia
from backend.lib.providers.base import Candidato, Consulta, ProviderResult, ProviderTrace
from backend.lib.providers.referencia.images import (
    ImageSearchProvider,
    _search_ddg_images,
    encaja_en,
)
from backend.main import app
from backend.services.completar import CompletarFichaService
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
TRACE = ProviderTrace("fake", "api", "ok")
REVIEW = json.dumps({"score": 80, "cats": {"graficos": 80}})
TRUCOS = json.dumps({"groups": [{"name": "Códigos", "entries": [{"name": "A", "input": "B"}]}]})


def _settings(tmp_path: Path, sistema: str = "snes", **identity: str) -> Settings:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name=sistema, shortName=sistema, launchCmd="/bin/echo"),
    )
    base = {"title": "Prince of Persia", "year": "1989", "developer": "", "publisher": "",
            "genre": "", "players": "", "format": ""}
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId=sistema, romSource="path", romRef="/roms/juego",
            identity=Identity(**{**base, **identity}),
        )
    )
    return settings


def _id(settings: Settings) -> str:
    return next(iter(GamesStore(settings.games_dir).list())).id


def _store(settings: Settings) -> GamesStore:
    return GamesStore(settings.games_dir)


def _texto(key: str, valor: str) -> Candidato:
    return Candidato(
        id=f"{key}:1", key=key, kind="text", nombre=key, fuente="Fake", clase="aplicable",
        value=valor, trace=TRACE,
    )


def _identidad(key: str, valor: str) -> Candidato:
    return Candidato(
        id=f"{key}:1", key=key, kind="identity", nombre=key, fuente="Fake", clase="aplicable",
        value=valor, trace=TRACE,
    )


def _imagen(
    key: str,
    url: str,
    fuente: str = "Launchbox",
    **meta: str,
) -> Candidato:
    return Candidato(
        id=f"{key}:{url}", key=key, kind="media", nombre=key, fuente=fuente, clase="aplicable",
        media_url=url, trace=TRACE, meta=meta,
    )


class _Fuente:
    nombre = "Fake"
    tipo: Literal["api", "scrape"] = "api"
    timeout = 1.0

    def __init__(
        self,
        candidatos: dict[str, Sequence[Candidato]],
        al_buscar: Callable[[str], None] | None = None,
    ) -> None:
        self.candidatos = candidatos
        self.al_buscar = al_buscar
        self.pedidas: list[str] = []

    def buscar(self, consulta: Consulta) -> ProviderResult:
        self.pedidas.append(consulta.key)
        if self.al_buscar is not None:
            self.al_buscar(consulta.key)
        return ProviderResult(tuple(self.candidatos.get(consulta.key, ())), TRACE)


def _con_fuente(monkeypatch: pytest.MonkeyPatch, fuente: _Fuente, rechazadas: frozenset[str] = frozenset()) -> None:  # noqa: E501
    monkeypatch.setattr(
        "backend.lib.providers.orquestador.providers_for", lambda *a, **kw: (fuente,),
    )

    def bajar(url: str, **_kw: Any) -> httpx.Response:
        if url in rechazadas:
            return httpx.Response(403)
        return httpx.Response(200, content=PNG, headers={"content-type": "image/png"})

    monkeypatch.setattr("backend.services.fields.httpx.get", bajar)
    monkeypatch.setattr(
        "backend.services.completar.colores_dominantes", lambda _r: ["#d03030", "#30d030"],
    )


def _correr(settings: Settings, job: JobState | None = None) -> dict[str, object]:
    return CompletarFichaService(settings).run(_id(settings))(job or JobState("job"))


TODO = {
    "developer": [_identidad("developer", "Broderbund")],
    "publisher": [_identidad("publisher", "Broderbund")],
    "genre": [_identidad("genre", "Plataformas")],
    "players": [_identidad("players", "1")],
    "format": [_identidad("format", "Diskette")],
    "sinopsis": [_texto("sinopsis", "Un príncipe.")],
    "caratula": [_imagen("caratula", "https://x/caja.png")],
    "objetivo": [_texto("objetivo", "Rescatar a la princesa.")],
    "primerosPasos": [_texto("primerosPasos", "Correr.")],
    "reglasEsenciales": [_texto("reglasEsenciales", "Una hora.")],
    "modo": [_texto("modo", "1 jugador")],
    "review": [_texto("review", REVIEW)],
    "cheats": [_texto("cheats", TRUCOS)],
}


def test_llena_todos_los_campos_vacios_como_sugerencia(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _con_fuente(monkeypatch, _Fuente(TODO))

    resultado = _correr(settings)

    game = _store(settings).get(_id(settings))
    assert resultado["estado"] == "ok"
    assert game.identity.developer == "Broderbund"
    assert game.provenance["developer"].source == "Fake"
    assert game.texts["sinopsis"].status == "suggested"
    assert game.texts["objetivo"].value == "Rescatar a la princesa."
    assert game.review.score == 80
    assert game.review.status == "suggested"
    assert game.cheats.groups[0].name == "Códigos"
    assert game.images["caratula"].source == "Launchbox"


def test_en_un_sistema_sin_precarga_igual_completa(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path, sistema="snes")
    monkeypatch.setattr(
        "backend.services.completar.MsdosPrecargaService",
        lambda *_a: pytest.fail("snes no tiene precarga"),
    )
    monkeypatch.setattr(
        "backend.services.completar.ArcadeDbPrecargaService",
        lambda *_a: pytest.fail("snes no tiene precarga"),
    )
    _con_fuente(monkeypatch, _Fuente(TODO))

    _correr(settings)

    assert _store(settings).get(_id(settings)).texts["sinopsis"].value == "Un príncipe."


def test_no_pisa_lo_que_ya_estaba_cargado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path, developer="Jordan Mechner")
    _store(settings).set_text_field(_id(settings), "sinopsis", "La mía.")
    fuente = _Fuente(TODO)
    _con_fuente(monkeypatch, fuente)

    _correr(settings)

    game = _store(settings).get(_id(settings))
    assert game.identity.developer == "Jordan Mechner"
    assert game.texts["sinopsis"].value == "La mía."
    assert game.texts["sinopsis"].status == "manual"
    assert "developer" not in fuente.pedidas
    assert "sinopsis" not in fuente.pedidas


def test_no_pisa_lo_que_el_usuario_escribe_con_el_job_en_marcha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)

    def escribir(key: str) -> None:
        if key == "objetivo":
            _store(settings).set_text_field(_id(settings), "objetivo", "Lo escribí yo.")

    _con_fuente(monkeypatch, _Fuente(TODO, escribir))

    _correr(settings)

    game = _store(settings).get(_id(settings))
    assert game.texts["objetivo"].value == "Lo escribí yo."
    # Lo que escribió el usuario no se perdió con los campos que vinieron después.
    assert game.texts["primerosPasos"].value == "Correr."


def test_conserva_lo_que_trajo_la_precarga_de_la_fuente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path, sistema="msdos")

    class _Precarga:
        def __init__(self, _settings: Settings) -> None:
            pass

        def run(self, game_id: str) -> Callable[[JobState], dict[str, object]]:
            def job_fn(_job: JobState) -> dict[str, object]:
                store = _store(settings)
                game = store.get(game_id)
                data = game.model_dump()
                data["identity"]["genre"] = "Acción"
                store.save(type(game).model_validate(data))
                return {"estado": "ok"}

            return job_fn

    monkeypatch.setattr("backend.services.completar.MsdosPrecargaService", _Precarga)
    _con_fuente(monkeypatch, _Fuente({"sinopsis": TODO["sinopsis"]}))

    _correr(settings)

    game = _store(settings).get(_id(settings))
    assert game.identity.genre == "Acción"
    assert game.texts["sinopsis"].value == "Un príncipe."


def test_si_la_precarga_falla_completa_igual(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path, sistema="msdos")

    class _Rota:
        def __init__(self, _settings: Settings) -> None:
            pass

        def run(self, _game_id: str) -> Callable[[JobState], dict[str, object]]:
            def job_fn(_job: JobState) -> dict[str, object]:
                raise RuntimeError("caída")

            return job_fn

    monkeypatch.setattr("backend.services.completar.MsdosPrecargaService", _Rota)
    _con_fuente(monkeypatch, _Fuente(TODO))

    assert _correr(settings)["estado"] == "ok"
    assert _store(settings).get(_id(settings)).texts["sinopsis"].value == "Un príncipe."


def test_si_una_imagen_no_baja_prueba_la_siguiente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    caja = {"caratula": [
        _imagen("caratula", "https://x/rota.png"),
        _imagen("caratula", "https://x/buena.png", fuente="MobyGames"),
    ]}
    _con_fuente(monkeypatch, _Fuente(caja), frozenset({"https://x/rota.png"}))

    resultado = _correr(settings)

    assert _store(settings).get(_id(settings)).images["caratula"].source == "MobyGames"
    assert "caratula" in resultado["escritos"]  # type: ignore[operator]


def test_si_una_fuente_explota_el_job_sigue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)

    def romper(key: str) -> None:
        if key == "sinopsis":
            raise RuntimeError("sitio caído")

    _con_fuente(monkeypatch, _Fuente(TODO, romper))

    _correr(settings)

    game = _store(settings).get(_id(settings))
    assert game.texts.get("sinopsis") is None or not game.texts["sinopsis"].value
    assert game.review.score == 80


def test_cancelado_no_escribe_mas(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(tmp_path)
    cancelar = threading.Event()

    def cortar(key: str) -> None:
        if key == "publisher":
            cancelar.set()

    _con_fuente(monkeypatch, _Fuente(TODO, cortar))

    resultado = _correr(settings, JobState("job", cancel_event=cancelar))

    game = _store(settings).get(_id(settings))
    assert resultado["estado"] == "cancelado"
    assert game.identity.developer == "Broderbund"
    assert game.identity.publisher == ""
    assert not game.texts.get("sinopsis")


def test_el_endpoint_lanza_el_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(tmp_path)
    monkeypatch.setattr("backend.api.games.get_settings", lambda: settings)
    lanzados: list[object] = []
    monkeypatch.setattr(
        "backend.api.games.submit",
        lambda fn: lanzados.append(fn) or JobState("job-1"),
    )

    cliente = TestClient(app, headers={"host": "127.0.0.1:8765"})
    respuesta = cliente.post(f"/api/games/{_id(settings)}/completar")

    assert respuesta.status_code == 200
    assert respuesta.json()["jobId"] == "job-1"
    assert len(lanzados) == 1


def test_sin_titulo_no_sale_a_la_red(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(tmp_path, title="")
    fuente = _Fuente(TODO)
    _con_fuente(monkeypatch, fuente)

    assert _correr(settings)["estado"] == "sin-titulo"
    assert fuente.pedidas == []


def _buscador(key: str, url: str, ancho: int, alto: int, titulo: str) -> Candidato:
    return _imagen(
        key, url, fuente=ImageSearchProvider.nombre,
        ancho=str(ancho), alto=str(alto), titulo=titulo,
    )


def test_del_buscador_toma_la_primera_que_encaja(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    marquesinas = {"marquesina": [
        _buscador("marquesina", "https://x/caja.png", 660, 800, "Prince of Persia"),
        _buscador("marquesina", "https://x/ancha.png", 1200, 300, "Prince of Persia marquee"),
    ]}
    _con_fuente(monkeypatch, _Fuente(marquesinas))

    _correr(settings)

    assert _store(settings).get(_id(settings)).images["marquesina"].url.endswith(  # type: ignore[union-attr]
        "marquesina.png",
    )


def test_si_ninguna_encaja_el_casillero_queda_vacio(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    cajas = {"marquesina": [
        _buscador("marquesina", "https://x/caja.png", 660, 800, "Prince of Persia"),
    ]}
    _con_fuente(monkeypatch, _Fuente(cajas))

    resultado = _correr(settings)

    imagen = _store(settings).get(_id(settings)).images.get("marquesina")
    assert imagen is None or not imagen.url
    assert "marquesina" in resultado["sinDato"]  # type: ignore[operator]


def test_lo_que_publica_una_fuente_no_se_juzga_por_su_forma(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    _con_fuente(monkeypatch, _Fuente({"marquesina": [_imagen("marquesina", "https://x/m.png")]}))

    _correr(settings)

    assert _store(settings).get(_id(settings)).images["marquesina"].source == "Launchbox"


@pytest.mark.parametrize(
    ("key", "url", "ancho", "alto", "titulo", "esperado"),
    [
        ("caratula", "https://m/1-front-cover.jpg", 660, 800, "Prince of Persia - MobyGames", True),
        ("caratula", "https://m/1.jpg", 1200, 300, "Prince of Persia box", False),
        ("caratula", "https://m/1.jpg", 618, 800, "Prince Of Persia 1989 Manual", False),
        ("caratula", "https://m/1-back-cover.jpg", 660, 800, "Prince of Persia", False),
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia Review - IGN", False),
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia: The Sands of Time", False),
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia (2008) Box", False),
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia (1990) Box Shot", True),
        ("caratula", "https://m/2019/05/1.jpg", 660, 800, "Prince of Persia box", True),
        ("caratula", "https://m/1.jpg", 660, 800, "Wing Commander box", False),
        ("caratula", "https://m/background.jpg", 660, 800, "Prince of Persia box", True),
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia cover or packaging material - MobyGames", True),  # noqa: E501
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia 2: The Shadow", False),
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia (Amiga, 1990)", False),
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia (MS-DOS, 1990)", True),
        ("caratula", "https://m/1.jpg", 660, 800, "Prince of Persia (1990) Cheats & Tricks", False),
        ("logo", "https://m/logo.png", 800, 274, "Prince of Persia III & Standoff", False),
        ("logo", "https://m/1.jpg", 800, 300, "Una marca sin el juego logo", False),
        ("marquesina", "https://m/1.jpg", 1200, 300, "Prince of Persia banner", True),
        ("logo", "https://m/1.png", 800, 300, "Prince of Persia logo", True),
        ("logo", "https://m/1.png", 800, 300, "Prince of Persia title", False),
        ("poster", "https://m/1.jpg", 600, 900, "Prince of Persia poster", True),
        ("poster", "https://m/1.jpg", 600, 900, "Prince of Persia box", False),
        ("captura", "https://m/1.jpg", 640, 400, "Prince of Persia gameplay", True),
        ("captura", "https://m/1.jpg", 400, 640, "Prince of Persia gameplay", False),
    ],
)
def test_criterio_del_buscador(
    key: str, url: str, ancho: int, alto: int, titulo: str, esperado: bool,
) -> None:
    meta = {"ancho": str(ancho), "alto": str(alto), "titulo": titulo}
    assert encaja_en(key, url, meta, "Prince of Persia", "1989", "msdos") is esperado


def test_acepta_el_nombre_del_sistema_del_juego() -> None:
    meta = {"ancho": "640", "alto": "400", "titulo": "Screenshot of Prince of Persia (SNES, 1992)"}
    assert encaja_en("captura", "https://m/1.jpg", meta, "Prince of Persia", "1992", "snes")
    assert not encaja_en("captura", "https://m/1.jpg", meta, "Prince of Persia", "1992", "msdos")


def test_sin_medidas_no_encaja() -> None:
    meta = {"ancho": "", "alto": "", "titulo": "Prince of Persia box"}
    assert not encaja_en("caratula", "https://m/1.jpg", meta, "Prince of Persia", "1989", "msdos")


def test_el_poster_toma_la_caratula(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(tmp_path)
    _con_fuente(monkeypatch, _Fuente({"caratula": [_imagen("caratula", "https://x/c.png")]}))

    resultado = _correr(settings)

    game = _store(settings).get(_id(settings))
    assert game.images["poster"].url == game.images["caratula"].url
    assert game.images["poster"].source == "Launchbox"
    assert "poster" in resultado["escritos"]  # type: ignore[operator]
    assert "poster" not in resultado["sinDato"]  # type: ignore[operator]


def test_el_acento_sale_de_la_caratula(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(tmp_path)
    _con_fuente(monkeypatch, _Fuente({"caratula": [_imagen("caratula", "https://x/c.png")]}))

    _correr(settings)

    game = _store(settings).get(_id(settings))
    assert game.accent == "suggested"
    assert game.accentValue == "#d03030"
    assert game.accent2Value == "#30d030"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="necesita ffmpeg en el host")
def test_colores_dominantes_prefiere_el_color_al_negro(tmp_path: Path) -> None:
    ruta = tmp_path / "caja.png"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=16x16", "-f", "lavfi",
         "-i", "color=red:s=4x4", "-filter_complex", "overlay", "-frames:v", "1", str(ruta)],
        check=True,
    )

    colores = colores_dominantes(ruta)

    assert colores[0] == "#f01010"  # el negro ocupa casi toda la imagen


def _paginas(respuestas: list[httpx.Response], monkeypatch: pytest.MonkeyPatch) -> list[str]:
    pedidas: list[str] = []
    restantes = list(respuestas)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, text='vqd="1-2"')
        pedidas.append(str(request.url))
        return restantes.pop(0)

    cliente = httpx.Client

    monkeypatch.setattr(
        referencia.images.httpx,
        "Client",
        lambda **kw: cliente(transport=httpx.MockTransport(handler), **kw),
    )
    monkeypatch.setattr(referencia.images.time, "sleep", lambda _s: None)
    return pedidas


def test_la_busqueda_recorre_todas_las_paginas(monkeypatch: pytest.MonkeyPatch) -> None:
    pedidas = _paginas(
        [
            httpx.Response(200, json={"results": [{"image": "a"}], "next": "i.js?s=100"}),
            httpx.Response(200, json={"results": [{"image": "b"}], "next": "i.js?s=200"}),
            httpx.Response(200, json={"results": [{"image": "c"}]}),
        ],
        monkeypatch,
    )

    assert [r["image"] for r in _search_ddg_images("pop")] == ["a", "b", "c"]
    assert "vqd=1-2" in pedidas[2]


def test_si_una_pagina_falla_conserva_lo_ya_traido(monkeypatch: pytest.MonkeyPatch) -> None:
    _paginas(
        [
            httpx.Response(200, json={"results": [{"image": "a"}], "next": "i.js?s=100"}),
            httpx.Response(429),
        ],
        monkeypatch,
    )

    assert [r["image"] for r in _search_ddg_images("pop")] == ["a"]


def test_una_pagina_sin_nada_nuevo_termina_la_busqueda(monkeypatch: pytest.MonkeyPatch) -> None:
    pedidas = _paginas(
        [
            httpx.Response(200, json={"results": [{"image": "a"}], "next": "i.js?s=100"}),
            httpx.Response(200, json={"results": [{"image": "a"}], "next": "i.js?s=100"}),
        ],
        monkeypatch,
    )

    assert [r["image"] for r in _search_ddg_images("pop")] == ["a"]
    assert len(pedidas) == 2


def test_el_buscador_no_tiene_tope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.lib.providers.referencia.images._search_ddg_images",
        lambda _q: [
            {"image": f"https://archive.org/{i}.jpg", "width": "600", "height": "800", "title": "t"}
            for i in range(30)
        ],
    )

    resultado = ImageSearchProvider().buscar(
        Consulta("pop", "caratula", "Prince of Persia", "msdos", "1989"),
    )

    assert len(resultado.candidatos) == 30
    assert resultado.candidatos[0].meta == {"ancho": "600", "alto": "800", "titulo": "t"}
