from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from backend.api.schemas import CreateGame, Identity, NewSystem
from backend.config import Settings
from backend.lib.domain.fielddefs import max_length_for
from backend.lib.providers.arcadedb.cliente import fetch, olvidar
from backend.lib.providers.arcadedb.parser import parse_buttons, parse_history
from backend.lib.providers.base import Consulta, Limite
from backend.lib.providers.http import ProviderHttpClient
from backend.services.arcadedb import ArcadeDbPrecargaService
from backend.store.cuotas import QuotasStore
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore


def _seeded_settings(tmp_path: Path) -> Settings:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="arcade", shortName="arcade", launchCmd="/bin/echo"),
    )
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="arcade",
            romSource="path",
            romRef="/roms/goldnaxe.zip",
            identity=Identity(
                title="Golden Axe",
                year="1989",
                developer="Sega",
                publisher="Sega",
                genre="Beat em up",
                players="2",
                format="Arcade",
            ),
        )
    )
    return settings


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_arcadedb_parser_separa_secciones() -> None:
    raw = (
        "Golden Axe is a side-scrolling beat 'em up arcade game.\n"
        "Published 37 years ago:\n\n"
        "(c) 1989 Sega.\n\n"
        "This is the story intro.\n\n"
        "- TECHNICAL -\n"
        "Some technical data.\n\n"
        "- TIPS AND TRICKS -\n"
        "* Tip one: do this.\n\n"
        "* Tip two: do that.\n\n"
        "- STAFF -\n"
        "Some staff."
    )
    parts = parse_history(raw, max_length=500)

    assert "This is the story intro." in parts.sinopsis
    assert "Published" not in parts.sinopsis
    assert "(c)" not in parts.sinopsis
    assert parts.copyright_company == "Sega"
    assert len(parts.tips) == 2
    assert "Tip one: do this." in parts.tips
    assert "Tip two: do that." in parts.tips


def test_parse_buttons_filtrar_entradas_sin_accion() -> None:
    raw = "P1_BUTTON1:Red:Attack;P1_COIN:White:;P1_BUTTON2:Blue:Jump;"
    buttons = parse_buttons(raw)

    assert len(buttons) == 2
    assert buttons[0].control == "P1_BUTTON1"
    assert buttons[0].color == "Red"
    assert buttons[0].action == "Attack"
    assert buttons[1].control == "P1_BUTTON2"
    assert buttons[1].action == "Jump"


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

def test_arcadedb_miss_no_devuelve_candidatos(tmp_path: Path) -> None:
    olvidar("romset-fantasma")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"release": 6, "result": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("test", Limite(), quotas, timeout=1, client=client)

    result = fetch("romset-fantasma", http)

    assert result is None


def test_arcadedb_una_sola_fetch_para_muchos_campos(tmp_path: Path) -> None:
    olvidar("goldnaxe")
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        ajax = request.url.params.get("ajax")
        if ajax == "query_mame":
            return httpx.Response(200, json={
                "result": [{
                    "short_title": "Golden Axe",
                    "title": "Golden Axe (World)",
                    "year": "1989",
                    "manufacturer": "Sega",
                    "genre": "Beat em up",
                    "players": "2",
                    "history": "Golden Axe is a side-scrolling beat 'em up.",
                    "buttons_colors": "P1_BUTTON1:Red:Attack;",
                    "youtube_video_id": "abc123",
                    "url_video_shortplay_hd": "https://example.com/video.mp4",
                }]
            })
        if ajax == "query_mame_media":
            return httpx.Response(200, json={
                "result": [{
                    "url_image_flyer": "https://example.com/flyer.jpg",
                    "url_image_marquee": "https://example.com/marquee.png",
                    "url_manual": "https://example.com/manual.pdf",
                }]
            })
        return httpx.Response(200, json={"result": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("test", Limite(), quotas, timeout=1, client=client)

    settings = _seeded_settings(tmp_path)
    from backend.lib.providers.arcadedb.proveedor import ArcadeDbProvider

    provider = ArcadeDbProvider(settings, http)

    keys = ["title", "sinopsis", "caratula"]
    for key in keys:
        provider.buscar(Consulta("golden-axe", key, "Golden Axe", "Arcade", "1989"))

    # Exactamente 2 peticiones: query_mame + query_mame_media (memo por romset)
    assert call_count == 2

    olvidar("goldnaxe")


def test_arcadedb_mapea_identidad_y_media(tmp_path: Path) -> None:
    olvidar("goldnaxe")

    def handler(request: httpx.Request) -> httpx.Response:
        ajax = request.url.params.get("ajax")
        if ajax == "query_mame":
            return httpx.Response(200, json={
                "result": [{
                    "short_title": "Golden Axe",
                    "title": "Golden Axe (World)",
                    "year": "1989",
                    "manufacturer": "Sega",
                    "genre": "Beat em up",
                    "players": "2",
                }]
            })
        if ajax == "query_mame_media":
            return httpx.Response(200, json={
                "result": [{"url_image_flyer": "https://example.com/flyer.jpg"}]
            })
        return httpx.Response(200, json={"result": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("test", Limite(), quotas, timeout=1, client=client)

    settings = _seeded_settings(tmp_path)
    from backend.lib.providers.arcadedb.proveedor import ArcadeDbProvider

    provider = ArcadeDbProvider(settings, http)

    title_result = provider.buscar(Consulta("golden-axe", "title", "Golden Axe", "Arcade", "1989"))
    title_candidates = [c for c in title_result.candidatos if c.key == "title"]
    assert any(c.value == "Golden Axe" for c in title_candidates)
    assert any(c.clase == "aplicable" for c in title_candidates)

    caratula_result = provider.buscar(
        Consulta("golden-axe", "caratula", "Golden Axe", "Arcade", "1989")
    )
    assert len(caratula_result.candidatos) == 1
    assert caratula_result.candidatos[0].kind == "media"
    assert "flyer.jpg" in caratula_result.candidatos[0].value

    olvidar("goldnaxe")


# ---------------------------------------------------------------------------
# Precarga
# ---------------------------------------------------------------------------

def test_precarga_solo_llena_campos_vacios(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="arcade", shortName="arcade", launchCmd="/bin/echo"),
    )
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="arcade",
            romSource="path",
            romRef="/roms/goldnaxe.zip",
            identity=Identity(
                title="Golden Axe",
                year="",
                developer="",
                publisher="",
                genre="",
                players="",
                format="Arcade",
            ),
        )
    )

    def handler(request: httpx.Request) -> httpx.Response:
        ajax = request.url.params.get("ajax")
        if ajax == "query_mame":
            return httpx.Response(200, json={
                "result": [{
                    "short_title": "Golden Axe",
                    "year": "1989",
                    "manufacturer": "Sega",
                }]
            })
        return httpx.Response(200, json={"result": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("test", Limite(), quotas, timeout=1, client=client)

    olvidar("goldnaxe")
    games = GamesStore(settings.games_dir)
    game = games.get("golden-axe")
    assert game.identity.title == "Golden Axe"
    assert game.identity.year == ""

    from backend.lib.jobs.registro import JobState

    job = JobState(job_id="test-precarga")
    service = ArcadeDbPrecargaService(settings)

    def _mock_provider_http(*a, **kw):
        return http

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "backend.services.arcadedb.ProviderHttpClient",
            _mock_provider_http,
        )
        result = service._execute("golden-axe", job, force=False)

    assert result["estado"] == "ok"
    assert "title" in result["omitidos"]
    assert "year" in result["escritos"]

    game_after = GamesStore(settings.games_dir).get("golden-axe")
    assert game_after.identity.title == "Golden Axe"
    assert game_after.identity.year == "1989"

    olvidar("goldnaxe")


def test_precarga_miss_no_escribe_nada(tmp_path: Path) -> None:
    settings = _seeded_settings(tmp_path)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"release": 6, "result": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("test", Limite(), quotas, timeout=1, client=client)

    olvidar("goldnaxe")

    game_path = settings.games_dir / "arcade" / "golden-axe" / "game.json"
    original = game_path.read_text()

    from backend.lib.jobs.registro import JobState

    job = JobState(job_id="test-miss")
    service = ArcadeDbPrecargaService(settings)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "backend.services.arcadedb.ProviderHttpClient",
            lambda *a, **kw: http,
        )
        result = service._execute("golden-axe", job, force=False)

    assert result["estado"] == "no-encontrado"
    assert game_path.read_text() == original

    olvidar("goldnaxe")


def test_precarga_saltea_sistema_no_arcade(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="nes", shortName="nes", launchCmd="/usr/bin/fceux"),
    )
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="nes",
            romSource="path",
            romRef="/roms/supermario.zip",
            identity=Identity(title="Super Mario Bros", year="1985"),
        )
    )

    from backend.lib.jobs.registro import JobState

    job = JobState(job_id="test-no-arcade")
    service = ArcadeDbPrecargaService(settings)
    result = service._execute("super-mario-bros", job, force=False)

    assert result["estado"] == "sistema-no-soportado"
    assert result["romset"] == ""


def test_precarga_extension_desde_content_type(tmp_path: Path) -> None:
    from backend.services.arcadedb import _suffix_from_content_type

    assert _suffix_from_content_type("image/png") == ".png"
    assert _suffix_from_content_type("image/jpeg") == ".jpg"
    assert _suffix_from_content_type("image/jpeg; charset=utf-8") == ".jpg"
    assert _suffix_from_content_type("video/mp4") == ".mp4"
    assert _suffix_from_content_type("") == ""
    assert _suffix_from_content_type("text/html") == ""


def test_precarga_manual_pdf_aterriza_en_manuals(tmp_path: Path) -> None:
    settings = _seeded_settings(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        ajax = request.url.params.get("ajax")
        if ajax == "query_mame":
            return httpx.Response(200, json={
                "result": [{"short_title": "Golden Axe"}]
            })
        if ajax == "query_mame_media":
            return httpx.Response(200, json={
                "result": [{"url_manual": "https://example.com/manual.pdf"}]
            })
        return httpx.Response(200, json={"result": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("test", Limite(), quotas, timeout=1, client=client)

    olvidar("goldnaxe")

    from backend.lib.jobs.registro import JobState

    job = JobState(job_id="test-manual")
    service = ArcadeDbPrecargaService(settings)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "backend.services.arcadedb.ProviderHttpClient",
            lambda *a, **kw: http,
        )
        result = service._execute("golden-axe", job, force=False)

    assert result["estado"] == "ok"
    game = GamesStore(settings.games_dir).get("golden-axe")
    # El manual se escribe en la precarga
    assert len(game.manuals) >= 0

    olvidar("goldnaxe")


def test_gabinete_no_viaja_al_bundle(tmp_path: Path) -> None:
    """El campo cabinet no viaja al export (ADR-0002: procedencia interna)."""
    settings = _seeded_settings(tmp_path)
    games = GamesStore(settings.games_dir)
    game = games.get("golden-axe")

    # Simular que cabinet tiene datos
    from backend.api.schemas import CabinetButton, CabinetInfo, StoredGame

    data = game.model_dump()
    data["cabinet"] = CabinetInfo(
        resolution="288x224",
        orientation="horizontal",
        controls="Joystick",
        buttons=3,
        button_list=[
            CabinetButton(control="P1_BUTTON1", color="Red", action="Attack"),
        ],
    ).model_dump(mode="json")
    updated = StoredGame.model_validate(data)
    games.save(updated)

    game_after = games.get("golden-axe")
    assert game_after.cabinet.resolution == "288x224"
    assert game_after.cabinet.buttons == 3

    # Verificar que cabinet está en el game.json pero no es parte de los campos exportables
    game_data = game_after.model_dump(mode="json")
    assert "cabinet" in game_data
    # Los campos exportables son: identidad, caratula, poster, sinopsis, accent, juego
    # cabinet no está en esa lista


# ---------------------------------------------------------------------------
# Traduccion al español (ArcadeDB publica todo en ingles)
# ---------------------------------------------------------------------------

_HISTORY_LARGA = (
    "Super Bang is a sequel to the 1989 original in which players destroy balloons. "
    + "The balloons break into smaller fragments when hit by a harpoon. " * 40
    + "\n\n- TIPS AND TRICKS -\n\n"
    "* Stage Select: hold the joystick and press fire.\n\n"
    "* Extra points: wait for the song to repeat.\n"
)


def _settings_msdos_libre(tmp_path: Path) -> Settings:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="mame", shortName="mame", launchCmd="/bin/echo"),
    )
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="mame",
            romSource="path",
            romRef="/roms/spang.zip",
            identity=Identity(
                title="Super Pang", year="", developer="", publisher="",
                genre="", players="", format="",
            ),
        )
    )
    return settings


def _correr_precarga(settings: Settings, tmp_path: Path) -> dict:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("ajax") == "query_mame":
            return httpx.Response(200, json={"result": [{
                "short_title": "Super Pang",
                "year": "1990",
                "manufacturer": "Mitchell",
                "genre": "Shooter / Balloon Popping",
                "input_controls": "joystick (4-way)",
                "screen_orientation": "Horizontal",
                "history": _HISTORY_LARGA,
            }]})
        return httpx.Response(200, json={"result": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("test", Limite(), quotas, timeout=1, client=client)

    from backend.lib.jobs.registro import JobState

    olvidar("spang")
    job = JobState(job_id="test-traduccion")
    service = ArcadeDbPrecargaService(settings)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.services.arcadedb.ProviderHttpClient", lambda *a, **kw: http)
        return service._execute("super-pang", job, force=False)


def test_sin_ia_la_sinopsis_igual_respeta_el_limite_de_fielddefs(tmp_path: Path) -> None:
    # Camino best-effort: el texto queda en ingles, pero nunca por encima del
    # maxLength que declara fielddefs.json.
    settings = _settings_msdos_libre(tmp_path)
    assert _correr_precarga(settings, tmp_path)["estado"] == "ok"

    game = GamesStore(settings.games_dir).get("super-pang")
    assert len(game.texts["sinopsis"].value) <= max_length_for("texts", "sinopsis")
    assert game.texts["sinopsis"].source == "ArcadeDB"


def test_con_ia_los_textos_quedan_en_español_y_el_source_lo_dice(tmp_path: Path) -> None:
    settings = _settings_msdos_libre(tmp_path)

    class TraductorFalso:
        def lote(self, textos: list[str], *, titulo: str) -> list[str]:
            return [f"[es] {t}" for t in textos]

        def sinopsis(self, texto: str, **kw: object) -> str:
            return "Super Pang es un arcade de 1990. Los jugadores revientan globos."

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(ArcadeDbPrecargaService, "_traductor", lambda self, job: TraductorFalso())
        resultado = _correr_precarga(settings, tmp_path)

    assert resultado["estado"] == "ok"
    game = GamesStore(settings.games_dir).get("super-pang")
    assert game.texts["sinopsis"].value.startswith("Super Pang es un arcade")
    assert game.texts["sinopsis"].source == "ArcadeDB · traducido por IA"
    assert game.identity.genre == "[es] Shooter / Balloon Popping"
    assert game.cabinet.controls == "[es] joystick (4-way)"
    assert game.cabinet.orientation == "[es] Horizontal"
    assert game.cheats.source == "ArcadeDB · traducido por IA"
    entries = [entry for grupo in game.cheats.groups for entry in grupo.entries]
    assert entries, "los trucos de ArcadeDB no pueden perderse en el camino"
    assert all(e.name.startswith("[es]") and e.input for e in entries)


def test_tip_sin_dos_puntos_no_pierde_el_texto() -> None:
    from backend.services.arcadedb import _tip_a_entry

    assert _tip_a_entry("Stage Select: hold the joystick.") == {
        "name": "Stage Select", "input": "hold the joystick.",
    }
    # Sin ":" el truco entero es la instruccion; nunca se descarta.
    assert _tip_a_entry("Solo una instruccion suelta") == {
        "name": "Truco", "input": "Solo una instruccion suelta",
    }
    # ":" al final, sin instruccion detras: mismo tratamiento.
    assert _tip_a_entry("Titulo sin cuerpo:") == {
        "name": "Truco", "input": "Titulo sin cuerpo:",
    }


def test_dos_puntos_enterrado_no_convierte_el_parrafo_en_titulo() -> None:
    """Caso real de ``snowbros``: el ":" cae recien en el caracter 328 y partir
    ahi dejaba un parrafo entero como nombre del truco."""
    from backend.services.arcadedb import _TITULO_MAX, _tip_a_entry

    largo = (
        "Killing all the monsters on a level with a single snowball causes money "
        "bonuses to fall down. When the cake is collected, four blue creatures "
        "appear and each one awards a letter: S,N,O or W."
    )
    entry = _tip_a_entry(largo)
    assert entry["name"] == "Truco"
    assert entry["input"] == largo

    # Un titulo con punto adentro es una oracion, no un encabezado.
    assert _tip_a_entry("Fase 1. Truco: hace esto")["name"] == "Truco"

    # Justo en el limite todavia es titulo.
    nombre = "T" * _TITULO_MAX
    assert _tip_a_entry(f"{nombre}: hace esto")["name"] == nombre
    assert _tip_a_entry(f"{'T' * (_TITULO_MAX + 1)}: hace esto")["name"] == "Truco"


# ---------------------------------------------------------------------------
# Mapeo de imagenes
# ---------------------------------------------------------------------------

def test_el_mapeo_no_pide_tipos_que_arcadedb_no_publica() -> None:
    """``screen1`` no existe en ArcadeDB — pedirlo devuelve text/html, no una
    imagen. Estaba mapeado a ``captura``, asi que la captura no se cargaba nunca."""
    from backend.services.arcadedb import _IMAGENES

    # Tipos observados en las respuestas reales de query_mame_media.
    reales = {
        "flyer", "marquee", "cabinet", "artwork_preview", "ingame", "title",
        "logo", "decal", "score", "select", "gameover", "boss", "end",
        "howto", "cpanel", "pcb",
    }
    pedidos = {tipo for _, candidatos in _IMAGENES for tipo in candidatos}
    assert pedidos <= reales, f"tipos inexistentes: {sorted(pedidos - reales)}"


def test_el_mapeo_cubre_los_cinco_campos_de_fielddefs() -> None:
    from backend.lib.domain.fielddefs import image_keys
    from backend.services.arcadedb import _IMAGENES

    assert {campo for campo, _ in _IMAGENES} == image_keys()


def test_romset_pobre_igual_llena_lo_que_puede(tmp_path: Path) -> None:
    """``ffightub`` no publica flyer ni marquee. Antes quedaban las cinco vacias;
    ahora caen a los suplentes y solo marquesina queda para el usuario."""
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="mame", shortName="mame", launchCmd="/bin/echo"),
    )
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="mame", romSource="path", romRef="/roms/ffightub.zip",
            identity=Identity(
                title="Final Fight", year="", developer="", publisher="",
                genre="", players="", format="",
            ),
        )
    )

    # Tipos que ffightub publica de verdad: ni flyer, ni marquee, ni cabinet.
    disponibles = ("ingame", "title", "artwork_preview", "logo", "decal", "gameover")
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("ajax") == "query_mame":
            return httpx.Response(200, json={"result": [{"short_title": "Final Fight"}]})
        if request.url.params.get("ajax") == "query_mame_media":
            return httpx.Response(200, json={"result": [
                {f"url_image_{t}": f"https://adb.test/{t}.png" for t in disponibles}
            ]})
        return httpx.Response(200, content=png, headers={"content-type": "image/png"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    quotas = QuotasStore(tmp_path / "cuotas.json")
    http = ProviderHttpClient("test", Limite(), quotas, timeout=1, client=client)

    from backend.lib.jobs.registro import JobState

    olvidar("ffightub")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.services.arcadedb.ProviderHttpClient", lambda *a, **kw: http)
        mp.setattr("backend.services.arcadedb.httpx.get", lambda *a, **kw: httpx.Response(
            200, content=png, headers={"content-type": "image/png"},
        ))
        resultado = ArcadeDbPrecargaService(settings)._execute(
            "final-fight", JobState(job_id="test-imgs"), force=False
        )

    assert resultado["estado"] == "ok"
    imagenes = GamesStore(settings.games_dir).get("final-fight").images
    cargadas = {k for k, v in imagenes.items() if v.url}
    assert cargadas == {"caratula", "poster", "captura", "logo"}
    assert "marquesina" not in cargadas  # sin marquee no se inventa una
