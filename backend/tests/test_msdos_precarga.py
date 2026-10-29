from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from backend.api.schemas import CreateGame, Identity, NewSystem
from backend.config import Settings
from backend.lib.jobs.registro import JobState
from backend.lib.providers.mobygames.cliente import FichaCompleta
from backend.lib.providers.mobygames.parser import Ficha, Specs
from backend.services.msdos import MsdosPrecargaService
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

URL = "https://www.mobygames.com/game/714/maniac-mansion/"


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


class _Preparado:
    def __init__(self, ia: dict[str, str]) -> None:
        self.ia = ia
        self.campos_pedidos_a_ia: list[str] | None = None


def _correr(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    moby: FichaCompleta | None,
    ia: dict[str, str],
    launchbox_year: str = "",
) -> tuple[dict[str, Any], _Preparado]:
    preparado = _Preparado(ia)

    class _LaunchboxFalso:
        year = launchbox_year
        game_id = "1"
        slug = "maniac"

    monkeypatch.setattr(
        "backend.services.msdos.search_game",
        lambda *_a, **_k: _LaunchboxFalso() if launchbox_year else None,
    )
    monkeypatch.setattr("backend.services.msdos.fetch_images", lambda *_a, **_k: [])
    monkeypatch.setattr(MsdosPrecargaService, "_fetch_mobygames", lambda *_a, **_k: moby)
    monkeypatch.setattr("backend.services.msdos.traductor_configurado", lambda *_a, **_k: None)

    def fetch_ia(_self: Any, _id: str, _t: str, _s: str, _job: Any, campos: list[str]) -> Any:
        preparado.campos_pedidos_a_ia = list(campos)
        return preparado.ia

    monkeypatch.setattr(MsdosPrecargaService, "_fetch_ia_data", fetch_ia)
    resultado = MsdosPrecargaService(settings)._execute(
        "maniac-mansion", JobState(job_id="t"), force=False
    )
    return resultado, preparado


def test_cada_campo_sale_de_su_fuente_y_la_procedencia_lo_dice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # MobyGames trae developer y no players: developer es suyo, players de la IA.
    settings = _settings(tmp_path)
    resultado, prep = _correr(
        settings, monkeypatch, _ficha(players=""),
        {"developer": "Otro", "players": "1", "sinopsis": "Una casa embrujada."},
    )

    assert resultado["estado"] == "ok"
    game = GamesStore(settings.games_dir).get("maniac-mansion")
    assert game.identity.developer == "Lucasfilm Games"
    assert game.identity.players == "1"
    assert game.identity.year == "1988"
    assert game.identity.format == "Diskette"
    assert game.provenance["developer"].source == "MobyGames"
    assert game.provenance["developer"].originUrl == URL
    assert game.provenance["developer"].sourceType == "scrape"
    assert game.provenance["players"].source == "IA"
    assert game.provenance["players"].originUrl is None
    # La IA solo recibió lo que MobyGames no tenía.
    assert prep.campos_pedidos_a_ia == ["players", "sinopsis"]


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
    assert prep.campos_pedidos_a_ia == ["sinopsis"]


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
    monkeypatch.setattr(MsdosPrecargaService, "_fetch_mobygames", lambda *_a, **_k: _ficha())
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
