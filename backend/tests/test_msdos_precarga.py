from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from backend.api.schemas import CreateGame, Identity, NewSystem
from backend.config import Settings
from backend.lib.jobs.registro import JobState
from backend.lib.providers.launchbox.cliente import LaunchboxFicha, LaunchboxImage
from backend.lib.providers.mobygames.cliente import FichaCompleta, Imagen
from backend.lib.providers.mobygames.parser import Ficha, Specs
from backend.lib.providers.myabandonware.parser import Captura
from backend.lib.providers.myabandonware.parser import Ficha as FichaMyAbandonware
from backend.services.msdos import MsdosPrecargaService
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

URL = "https://www.mobygames.com/game/714/maniac-mansion/"
MYA_URL = "https://www.myabandonware.com/game/maniac-mansion-x1"


def _settings(tmp_path: Path, **identity: str) -> Settings:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="msdos", shortName="msdos", launchCmd="/bin/echo"),
    )
    base = {"title": "Maniac Mansion", "year": "", "developer": "", "publisher": "",
            "genre": "", "players": "", "format": ""}
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="msdos",
            romSource="path",
            romRef="/roms/maniac",
            identity=Identity(**{**base, **identity}),
        )
    )
    return settings


def _ficha(*, players: str = "", formatos: tuple[str, ...] = ("Diskette",)) -> FichaCompleta:
    return FichaCompleta(
        Ficha(
            url=URL, title="Maniac Mansion", alias=(), year="1988",
            developer="Lucasfilm Games", publisher="Lucasfilm Games", genre="Adventure",
            description="", score=82,
        ),
        Specs(players=players, formatos=formatos),
    )


def _mya(**campos: Any) -> FichaMyAbandonware:
    base: dict[str, Any] = {
        "url": MYA_URL,
        "title": "Maniac Mansion",
        "alias": (),
        "year": "1988",
        "plataforma": "DOS",
        "developer": "Lucasfilm Games LLC",
        "publisher": "Lucasfilm Games LLC",
        "genre": "Adventure",
        "description": "",
        "capturas": (),
        "mobygames_url": URL,
    }
    base.update(campos)
    return FichaMyAbandonware(**base)


class _Preparado:
    def __init__(self, ia: dict[str, str]) -> None:
        self.ia = ia
        self.campos_pedidos_a_ia: list[str] | None = None
        self.anio_launchbox: str | None = None
        self.mobygames: list[dict[str, Any]] = []


LB_URL = "https://gamesdb.launchbox-app.com/games/details/1-maniac"


def _imagen_launchbox(categoria: str) -> LaunchboxImage:
    campo = "caratula" if categoria.startswith("box") else "captura"
    return LaunchboxImage(
        f"https://lb/{campo}.png", f"https://lb/{campo}-mini.png", categoria, campo, categoria,
        LB_URL,
    )


@pytest.fixture()
def bajadas(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    urls: list[str] = []

    def bajar(_self: Any, _game_id: str, key: str, url: str) -> str:
        urls.append(url)
        return f"/media/msdos/maniac-mansion/{key}.png"

    monkeypatch.setattr(MsdosPrecargaService, "_download_media", bajar)
    return urls


def _correr(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    moby: FichaCompleta | None,
    ia: dict[str, str],
    launchbox_year: str = "",
    launchbox_ficha: LaunchboxFicha | None = None,
    portadas: tuple[Imagen, ...] = (),
    mya: FichaMyAbandonware | None = None,
    launchbox_images: tuple[LaunchboxImage, ...] = (),
) -> tuple[dict[str, Any], _Preparado]:
    preparado = _Preparado(ia)

    class _LaunchboxFalso:
        year = launchbox_year
        game_id = "1"
        slug = "maniac"

    hay_launchbox = bool(launchbox_year or launchbox_ficha)

    def search_game(*_a: Any, **k: Any) -> Any:
        preparado.anio_launchbox = k.get("anio")
        return _LaunchboxFalso() if hay_launchbox else None

    def fetch_mobygames(_self: Any, _game: Any, anio: str, _job: Any, **k: Any) -> Any:
        preparado.mobygames.append({"anio": anio, **k})
        return moby, (portadas if k.get("con_portadas", True) else ())

    monkeypatch.setattr(MsdosPrecargaService, "_fetch_myabandonware", lambda *_a, **_k: mya)
    monkeypatch.setattr("backend.services.msdos.search_game", search_game)
    monkeypatch.setattr(
        "backend.services.msdos.fetch_details", lambda *_a, **_k: launchbox_ficha
    )
    monkeypatch.setattr(
        "backend.services.msdos.fetch_images", lambda *_a, **_k: list(launchbox_images)
    )
    monkeypatch.setattr(MsdosPrecargaService, "_fetch_mobygames", fetch_mobygames)
    monkeypatch.setattr("backend.services.msdos.traductor_configurado", lambda *_a, **_k: None)

    def fetch_ia(_self: Any, _id: str, _t: str, _s: str, _job: Any, campos: list[str]) -> Any:
        preparado.campos_pedidos_a_ia = list(campos)
        return preparado.ia

    monkeypatch.setattr(MsdosPrecargaService, "_fetch_ia_data", fetch_ia)
    resultado = MsdosPrecargaService(settings)._execute(
        "maniac-mansion", JobState(job_id="t"), force=False
    )
    return resultado, preparado


def _launchbox(**campos: Any) -> LaunchboxFicha:
    base: dict[str, Any] = {
        "url": LB_URL,
        "developers": ("Lucasfilm Games",),
        "publishers": ("Lucasfilm Games", "Erbe"),
        "genres": ("Adventure",),
        "max_players": "1",
        "year": "1988",
    }
    base.update(campos)
    return LaunchboxFicha(**base)


# ── ADR-0027: myabandonware → Launchbox → IA → MobyGames ────────────────────


def test_cada_campo_sale_de_su_fuente_y_la_procedencia_lo_dice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # myabandonware: año, editor y género (no tiene desarrollador); Launchbox: desarrollador y
    # jugadores; la IA, solo la sinopsis; MobyGames, el formato.
    settings = _settings(tmp_path)
    resultado, prep = _correr(
        settings, monkeypatch, _ficha(players="4"),
        {"developer": "Otro", "sinopsis": "Una casa embrujada."},
        launchbox_ficha=_launchbox(max_players="2"),
        mya=_mya(developer=""),
    )

    assert resultado["estado"] == "ok"
    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.year == "1988"
    assert game.identity.publisher == "Lucasfilm Games LLC"
    assert game.identity.genre == "Adventure"
    for key in ("year", "publisher", "genre"):
        assert game.provenance[key].source == "MyAbandonware", key
        assert game.provenance[key].originUrl == MYA_URL, key
        assert game.provenance[key].sourceType == "scrape", key
    assert game.identity.developer == "Lucasfilm Games"
    assert game.provenance["developer"].source == "Launchbox"
    assert game.identity.players == "1-2"
    assert game.provenance["players"].source == "Launchbox"
    assert game.identity.format == "Diskette"
    assert game.provenance["format"].source == "MobyGames"
    assert game.provenance["format"].originUrl == URL
    assert prep.campos_pedidos_a_ia == ["sinopsis"]


def test_la_ia_va_antes_que_mobygames(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(tmp_path)
    _, prep = _correr(
        settings, monkeypatch, _ficha(players="1"),
        {"developer": "Otro", "publisher": "Otro", "genre": "Aventura", "players": "2",
         "sinopsis": "x"},
    )

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.developer == "Otro"
    assert game.provenance["developer"].source == "IA"
    assert game.identity.players == "2"
    assert game.provenance["players"].source == "IA"
    # MobyGames completa lo que la IA no da: el año y el formato.
    assert game.identity.year == "1988"
    assert game.provenance["year"].source == "MobyGames"
    assert game.identity.format == "Diskette"
    assert prep.campos_pedidos_a_ia == ["developer", "publisher", "genre", "players", "sinopsis"]


def test_mobygames_no_se_abre_si_no_falta_nada_que_tenga(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bajadas: list[str]
) -> None:
    settings = _settings(tmp_path, format="Diskette")
    _, prep = _correr(
        settings, monkeypatch, _ficha(), {"sinopsis": "x"},
        launchbox_ficha=_launchbox(), mya=_mya(),
        launchbox_images=(_imagen_launchbox("box - front"),),
    )
    assert prep.mobygames == []


def test_mobygames_va_directo_a_la_ficha_que_enlaza_myabandonware(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _, prep = _correr(settings, monkeypatch, _ficha(), {"sinopsis": "x"}, mya=_mya())
    assert prep.mobygames[0]["enlace"] == URL


def test_launchbox_busca_con_el_año_de_myabandonware(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _, prep = _correr(
        settings, monkeypatch, None, {}, launchbox_ficha=_launchbox(), mya=_mya(year="1987")
    )
    assert prep.anio_launchbox == "1987"


def test_el_genero_de_myabandonware_se_traduce_y_la_fuente_lo_dice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class TraductorFalso:
        def lote(self, textos: list[str], *, titulo: str) -> list[str]:
            return ["Aventura" for _ in textos]

    settings = _settings(tmp_path)
    monkeypatch.setattr(MsdosPrecargaService, "_fetch_myabandonware", lambda *_a, **_k: _mya())
    monkeypatch.setattr("backend.services.msdos.search_game", lambda *_a, **_k: None)
    monkeypatch.setattr("backend.services.msdos.fetch_images", lambda *_a, **_k: [])
    monkeypatch.setattr(MsdosPrecargaService, "_fetch_mobygames", lambda *_a, **_k: (None, ()))
    monkeypatch.setattr(MsdosPrecargaService, "_fetch_ia_data", lambda *_a, **_k: {})
    monkeypatch.setattr(
        "backend.services.msdos.traductor_configurado", lambda *_a, **_k: TraductorFalso()
    )
    MsdosPrecargaService(settings)._execute("maniac-mansion", JobState(job_id="t"), force=False)

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.genre == "Aventura"
    assert game.provenance["genre"].source == "MyAbandonware · traducido por IA"


def test_la_captura_es_la_de_launchbox_y_si_no_la_de_myabandonware(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bajadas: list[str]
) -> None:
    # Launchbox dice cuál captura es de juego; la primera de myabandonware puede ser el título.
    mya = _mya(capturas=(Captura("https://mya/maniac_1.gif", "https://mya/thumbs/maniac_1.png"),))
    settings = _settings(tmp_path)
    _correr(
        settings, monkeypatch, None, {}, launchbox_ficha=_launchbox(), mya=mya,
        launchbox_images=(_imagen_launchbox("screenshot - gameplay"),),
    )
    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.images["captura"].source == "Launchbox"

    otro = _settings(tmp_path / "otro")
    resultado, _ = _correr(otro, monkeypatch, None, {}, launchbox_ficha=_launchbox(), mya=mya)
    game = GamesStore(otro.games_dir).get("maniac-mansion")
    assert game.images["captura"].source == "MyAbandonware"
    assert "https://mya/maniac_1.gif" in bajadas
    assert "captura" in resultado["escritos"]


# ── Lo que sigue igual: MobyGames, Launchbox y la IA ────────────────────────


def test_sin_mobygames_el_año_es_de_launchbox_y_la_ia_completa_el_resto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _, prep = _correr(
        settings, monkeypatch, None,
        {"developer": "Lucasfilm", "publisher": "Lucasfilm", "genre": "Aventura",
         "players": "1", "sinopsis": "x"},
        launchbox_year="1990",
    )

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.year == "1990"
    assert game.provenance["year"].source == "Launchbox"
    assert game.identity.developer == "Lucasfilm"
    assert game.provenance["developer"].source == "IA"
    assert game.identity.format == ""  # la IA no propone el formato
    assert prep.campos_pedidos_a_ia == ["developer", "publisher", "genre", "players", "sinopsis"]


def test_un_campo_ya_cargado_no_se_pisa_ni_se_le_pide_a_la_ia(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path, developer="Mío", players="2")
    resultado, prep = _correr(settings, monkeypatch, _ficha(players="1"), {"sinopsis": "x"})

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.developer == "Mío"
    assert game.identity.players == "2"
    assert {"developer", "players"} <= set(resultado["omitidos"])
    # La IA, que va antes que MobyGames, recibe solo lo que falta.
    assert prep.campos_pedidos_a_ia == ["publisher", "genre", "sinopsis"]


def test_con_dos_soportes_no_se_escribe_el_formato(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _correr(settings, monkeypatch, _ficha(formatos=("Diskette", "CD")), {})
    assert GamesStore(settings.games_dir).get("maniac-mansion").identity.format == ""


def test_el_genero_de_mobygames_se_traduce_y_la_fuente_lo_dice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)

    class TraductorFalso:
        def lote(self, textos: list[str], *, titulo: str) -> list[str]:
            return [f"[es] {t}" for t in textos]

    _correr(settings, monkeypatch, _ficha(), {})
    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.genre == "Adventure"  # sin IA queda en inglés
    assert game.provenance["genre"].source == "MobyGames"

    settings2 = _settings(tmp_path / "otro")
    monkeypatch.setattr(
        "backend.services.msdos.traductor_configurado", lambda *_a, **_k: TraductorFalso()
    )
    preparado = _Preparado({})
    monkeypatch.setattr("backend.services.msdos.search_game", lambda *_a, **_k: None)
    monkeypatch.setattr("backend.services.msdos.fetch_images", lambda *_a, **_k: [])
    monkeypatch.setattr("backend.services.msdos.fetch_details", lambda *_a, **_k: None)
    monkeypatch.setattr(
        MsdosPrecargaService, "_fetch_mobygames", lambda *_a, **_k: (_ficha(), ())
    )
    monkeypatch.setattr(
        MsdosPrecargaService, "_fetch_ia_data", lambda *_a, **_k: preparado.ia
    )
    MsdosPrecargaService(settings2)._execute("maniac-mansion", JobState(job_id="t"), force=False)
    game2 = GamesStore(settings2.games_dir).get("maniac-mansion")
    assert game2.identity.genre == "[es] Adventure"
    assert game2.provenance["genre"].source == "MobyGames · traducido por IA"


def test_ficha_elegida_por_año_aproximado_no_aporta_año_ni_formato(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Se buscó con el año de Launchbox (1990) y MobyGames dio una ficha de DOS 1988: año y
    # soporte son de otra edición. El año sigue la cadena y lo da Launchbox.
    settings = _settings(tmp_path)
    _correr(settings, monkeypatch, _ficha(), {}, launchbox_year="1990")

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.year == "1990"
    assert game.provenance["year"].source == "Launchbox"
    assert game.identity.format == ""
    assert game.identity.developer == "Lucasfilm Games"  # los datos del juego sí
    assert game.provenance["developer"].source == "MobyGames"


def test_ficha_ya_fechada_con_otro_año_tampoco_recibe_el_formato(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path, year="1990")
    _correr(settings, monkeypatch, _ficha(), {})

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.year == "1990"
    assert game.identity.format == ""


def test_con_el_mismo_año_si_aporta_el_formato(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path, year="1988")
    _correr(settings, monkeypatch, _ficha(), {})

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.format == "Diskette"
    assert game.provenance["format"].source == "MobyGames"


def test_sin_mobygames_la_identidad_sale_de_la_pagina_de_launchbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _, prep = _correr(
        settings, monkeypatch, None, {"sinopsis": "x"},
        launchbox_year="1988", launchbox_ficha=_launchbox(),
    )

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.developer == "Lucasfilm Games"
    assert game.identity.publisher == "Lucasfilm Games"
    assert game.identity.genre == "Adventure"
    assert game.identity.players == "1"
    assert game.identity.year == "1988"
    for key in ("developer", "publisher", "genre", "players", "year"):
        assert game.provenance[key].source == "Launchbox", key
    assert game.provenance["developer"].originUrl == LB_URL
    assert prep.campos_pedidos_a_ia == ["sinopsis"]  # la IA no hizo falta para la identidad


def test_launchbox_va_antes_que_mobygames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    _, prep = _correr(
        settings, monkeypatch, _ficha(players="4"), {"players": "9"},
        launchbox_ficha=_launchbox(max_players="2"),
    )

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.players == "1-2"
    assert game.provenance["players"].source == "Launchbox"
    assert game.identity.developer == "Lucasfilm Games"
    assert game.provenance["developer"].source == "Launchbox"
    assert prep.campos_pedidos_a_ia == ["sinopsis"]


def test_launchbox_busca_con_el_año_de_la_ficha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path, year="1988")
    _, prep = _correr(settings, monkeypatch, None, {}, launchbox_ficha=_launchbox())
    assert prep.anio_launchbox == "1988"


def test_sin_caratula_en_launchbox_es_la_portada_de_mobygames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bajadas: list[str]
) -> None:
    portada = Imagen("https://cdn/grande.jpg", "https://cdn/chica.webp", "Portada frontal", "o")
    settings = _settings(tmp_path)
    resultado, prep = _correr(settings, monkeypatch, _ficha(), {}, portadas=(portada,))

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert bajadas == ["https://cdn/grande.jpg"]
    assert game.images["caratula"].source == "MobyGames"
    assert "caratula" in resultado["escritos"]
    assert prep.mobygames[0]["con_portadas"] is True


def test_con_caratula_en_launchbox_mobygames_no_baja_portadas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bajadas: list[str]
) -> None:
    portada = Imagen("https://cdn/grande.jpg", "https://cdn/chica.webp", "Portada frontal", "o")
    settings = _settings(tmp_path)
    _, prep = _correr(
        settings, monkeypatch, _ficha(), {}, portadas=(portada,),
        launchbox_ficha=_launchbox(), launchbox_images=(_imagen_launchbox("box - front"),),
    )

    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.images["caratula"].source == "Launchbox"
    assert "https://cdn/grande.jpg" not in bajadas
    assert prep.mobygames[0]["con_portadas"] is False  # MobyGames se abrió por el formato
