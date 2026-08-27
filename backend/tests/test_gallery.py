from __future__ import annotations

import json
import zipfile
from pathlib import Path

import httpx
import pytest

from backend.api.errors import BadRequest, NotFound
from backend.api.schemas import CreateGame, Identity, NewSystem
from backend.bundle.staging import build_staging
from backend.config import Settings
from backend.lib.jobs.registro import JobState
from backend.lib.providers.arcadedb.cliente import olvidar
from backend.services.gallery import GalleryService, GuardarGaleriaItem
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 64

# ffightub publica 8 tipos; su padre ffight suma flyer, marquee y cabinet.
TIPOS_CLON = ("ingame", "title", "artwork_preview", "logo")
TIPOS_PADRE = ("flyer", "marquee", "cabinet")


def _settings(tmp_path: Path) -> Settings:
    settings = Settings(data_dir=tmp_path / "data")
    settings.data_dir.mkdir(parents=True)
    settings.tmp_dir.mkdir(parents=True, exist_ok=True)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="mame", shortName="mame", launchCmd="/bin/echo"),
    )
    GamesStore(settings.games_dir).create(
        CreateGame(
            systemId="mame", romSource="path", romRef="/roms/ffightub.zip",
            identity=Identity(
                title="Final Fight", year="1989", developer="Capcom",
                publisher="Capcom", genre="", players="", format="",
            ),
        )
    )
    return settings


def _transport(*, clon_es_clon: bool = True) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        ajax = request.url.params.get("ajax")
        romset = request.url.params.get("game_name")
        if ajax == "query_mame":
            fila: dict[str, object] = {"short_title": "Final Fight"}
            if romset == "ffightub" and clon_es_clon:
                fila["cloneof"] = "ffight"
            return httpx.Response(200, json={"result": [fila]})
        if ajax == "query_mame_media":
            tipos = TIPOS_CLON if romset == "ffightub" else (*TIPOS_CLON, *TIPOS_PADRE)
            return httpx.Response(200, json={"result": [
                {f"url_image_{t}": f"https://adb.test/{romset}/{t}.php" for t in tipos}
            ]})
        return httpx.Response(200, json={"result": []})

    return httpx.MockTransport(handler)


@pytest.fixture(autouse=True)
def _memo_limpio() -> None:
    for romset in ("ffightub", "ffight"):
        olvidar(romset)


def _parchear(mp: pytest.MonkeyPatch, transport: httpx.MockTransport, cuerpo: bytes = PNG) -> None:
    from backend.lib.providers.http import ProviderHttpClient

    def fabricar(*args: object, **kwargs: object) -> ProviderHttpClient:
        # Uno nuevo por llamada, igual que en produccion: el anterior queda cerrado.
        kwargs.pop("client", None)
        return ProviderHttpClient(*args, client=httpx.Client(transport=transport), **kwargs)  # type: ignore[arg-type]

    mp.setattr("backend.services.gallery.ProviderHttpClient", fabricar)
    mp.setattr(
        "backend.services.gallery.httpx.get",
        lambda *a, **kw: httpx.Response(200, content=cuerpo, headers={"content-type": "image/png"}),
    )
    # Mock ImageSearch and Launchbox to return empty results in tests
    from backend.lib.providers.base import ProviderResult, ProviderTrace

    def _noop_buscar(consulta):
        return ProviderResult((), ProviderTrace("mock", "mock", "sin resultados"))

    mp.setattr("backend.services.gallery.ImageSearchProvider.buscar", _noop_buscar)
    mp.setattr("backend.services.gallery.launchbox_search_game", lambda *a, **kw: None)


# ---------------------------------------------------------------------------
# Candidatos
# ---------------------------------------------------------------------------

def test_candidatos_fusionan_el_romset_padre_y_lo_marcan(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport())
        candidatos = GalleryService(settings).candidatos("final-fight")

    por_tipo = {c["tipo"]: c for c in candidatos}
    assert set(por_tipo) == {*TIPOS_CLON, *TIPOS_PADRE}
    assert all(por_tipo[t]["delPadre"] for t in TIPOS_PADRE)
    assert not any(por_tipo[t]["delPadre"] for t in TIPOS_CLON)
    assert por_tipo["marquee"]["label"] == "Marquesina"
    assert por_tipo["ingame"]["label"] == "En juego"


def test_candidatos_sin_padre_no_marcan_nada(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport(clon_es_clon=False))
        candidatos = GalleryService(settings).candidatos("final-fight")

    assert {c["tipo"] for c in candidatos} == set(TIPOS_CLON)
    assert not any(c["delPadre"] for c in candidatos)


def test_candidatos_de_sistema_no_arcade_es_lista_vacia(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    SystemsStore(settings.systems_path).create(
        NewSystem(name="nes", shortName="nes", launchCmd="/bin/echo"),
    )
    store = GamesStore(settings.games_dir)
    store.create(
        CreateGame(
            systemId="nes", romSource="path", romRef="/roms/mario.zip",
            identity=Identity(
                title="Mario", year="", developer="", publisher="",
                genre="", players="", format="",
            ),
        )
    )
    with pytest.MonkeyPatch.context() as mp:
        from backend.lib.providers.base import ProviderResult, ProviderTrace

        def _noop_buscar(consulta):
            return ProviderResult((), ProviderTrace("mock", "mock", "sin resultados"))

        mp.setattr("backend.services.gallery.ImageSearchProvider.buscar", _noop_buscar)
        mp.setattr("backend.services.gallery.launchbox_search_game", lambda *a, **kw: None)
        candidatos = GalleryService(settings).candidatos("mario")

    assert candidatos == []


# ---------------------------------------------------------------------------
# Guardar
# ---------------------------------------------------------------------------

def test_guardar_numera_gnnn_y_deriva_la_extension_del_contenido(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport(), cuerpo=JPG)
        resultado = GalleryService(settings).guardar(
            "final-fight",
            [GuardarGaleriaItem(tipo="marquee"), GuardarGaleriaItem(tipo="ingame")],
            JobState(job_id="g"),
        )

    assert resultado["guardadas"] == ["marquee-001", "ingame-002"]
    gallery = GamesStore(settings.games_dir).get("final-fight").gallery
    # La URL termina en .php: la extension sale de los magic bytes, no del nombre.
    assert [img.file for img in gallery] == ["g001.jpg", "g002.jpg"]
    assert [img.label for img in gallery] == ["Marquesina", "En juego"]
    assert gallery[0].source == "ArcadeDB (romset padre)"
    assert gallery[1].source == "ArcadeDB"
    for img in gallery:
        assert (settings.media_dir / "mame" / "final-fight" / "_gallery" / img.file).is_file()


def test_guardar_dos_veces_no_recicla_numeros(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    servicio = GalleryService(settings)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport())
        servicio.guardar("final-fight", [GuardarGaleriaItem(tipo="marquee")])
        servicio.guardar("final-fight", [GuardarGaleriaItem(tipo="ingame")])

    gallery = GamesStore(settings.games_dir).get("final-fight").gallery
    assert [img.file for img in gallery] == ["g001.png", "g002.png"]


def test_guardar_rechaza_seleccion_vacia_o_tipo_inexistente(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    servicio = GalleryService(settings)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport())
        with pytest.raises(BadRequest):
            servicio.guardar("final-fight", [])
        resultado = servicio.guardar(
            "final-fight", [GuardarGaleriaItem(tipo="no-existe")]
        )
        assert "no-existe" in resultado["fallidas"]


# ---------------------------------------------------------------------------
# Usar como / eliminar
# ---------------------------------------------------------------------------

def test_usar_como_apunta_el_campo_y_conserva_la_entrada(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    servicio = GalleryService(settings)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport())
        servicio.guardar("final-fight", [GuardarGaleriaItem(tipo="marquee")])

    image_id = GamesStore(settings.games_dir).get("final-fight").gallery[0].id
    game = servicio.usar_como("final-fight", image_id, "marquesina")

    assert game.images["marquesina"].url == "/media/mame/final-fight/_gallery/g001.png"
    # La misma imagen puede alimentar mas de un campo: no se saca del banco.
    assert len(game.gallery) == 1


def test_usar_como_rechaza_un_campo_que_no_es_del_contrato(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    servicio = GalleryService(settings)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport())
        servicio.guardar("final-fight", [GuardarGaleriaItem(tipo="marquee")])
    image_id = GamesStore(settings.games_dir).get("final-fight").gallery[0].id

    with pytest.raises(BadRequest):
        servicio.usar_como("final-fight", image_id, "galeria")
    with pytest.raises(NotFound):
        servicio.usar_como("final-fight", "no-existe", "marquesina")


def test_eliminar_saca_entrada_y_archivo(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    servicio = GalleryService(settings)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport())
        servicio.guardar("final-fight", [GuardarGaleriaItem(tipo="marquee")])

    ruta = settings.media_dir / "mame" / "final-fight" / "_gallery" / "g001.png"
    assert ruta.is_file()
    image_id = GamesStore(settings.games_dir).get("final-fight").gallery[0].id

    game = servicio.eliminar("final-fight", image_id)
    assert game.gallery == []
    assert not ruta.exists()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _con_galeria(tmp_path: Path) -> tuple[Settings, dict]:
    settings = _settings(tmp_path)
    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport())
        GalleryService(settings).guardar(
            "final-fight",
            [GuardarGaleriaItem(tipo="marquee"), GuardarGaleriaItem(tipo="ingame")],
        )
    game = GamesStore(settings.games_dir).get("final-fight").model_dump(mode="json")
    return settings, game


def test_galeria_viaja_en_media_gallery_con_nombres_sueltos(tmp_path: Path) -> None:
    settings, game = _con_galeria(tmp_path)
    staging = build_staging(settings, game, incluir={"galeria"}, system_name="mame")

    assert sorted(p.name for p in (staging.root / "media" / "_gallery").iterdir()) == [
        "g001.png", "g002.png",
    ]
    data = json.loads((staging.root / "data.json").read_text(encoding="utf-8"))
    assert data["gallery"] == [
        {"file": "g001.png", "label": "Marquesina"},
        {"file": "g002.png", "label": "En juego"},
    ]
    # Misma regla que _chk_manual_doc del lado de ATTRACT: nombre suelto, sin rutas.
    for entrada in data["gallery"]:
        assert "/" not in entrada["file"] and "\\" not in entrada["file"]


def test_sin_seleccionarla_no_viaja_ni_la_carpeta_ni_la_clave(tmp_path: Path) -> None:
    settings, game = _con_galeria(tmp_path)
    staging = build_staging(settings, game, incluir=set(), system_name="mame")

    assert not (staging.root / "media" / "_gallery").exists()
    assert "gallery" not in json.loads((staging.root / "data.json").read_text(encoding="utf-8"))


def test_entrada_declarada_sin_archivo_en_disco_no_se_declara(tmp_path: Path) -> None:
    settings, game = _con_galeria(tmp_path)
    (settings.media_dir / "mame" / "final-fight" / "_gallery" / "g001.png").unlink()

    staging = build_staging(settings, game, incluir={"galeria"}, system_name="mame")
    data = json.loads((staging.root / "data.json").read_text(encoding="utf-8"))
    assert [e["file"] for e in data["gallery"]] == ["g002.png"]


def test_galeria_vacia_no_deja_la_clave_colgada(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    game = GamesStore(settings.games_dir).get("final-fight").model_dump(mode="json")
    staging = build_staging(settings, game, incluir={"galeria"}, system_name="mame")

    assert "galeria" not in staging.incluye
    assert "gallery" not in json.loads((staging.root / "data.json").read_text(encoding="utf-8"))


def test_galeria_es_opcional_de_export_y_nunca_bloquea(tmp_path: Path) -> None:
    from backend.bundle.seleccion import compute_seleccion
    from backend.lib.domain.completeness import missing_required

    settings, game = _con_galeria(tmp_path)
    items = {item.key: item for item in compute_seleccion(settings, game)}

    assert items["galeria"].label == "Galería"
    assert items["galeria"].required is False
    assert items["galeria"].disponible is True
    assert items["galeria"].bytes > 0
    # No es un campo de fielddefs: no puede aparecer entre los faltantes.
    assert not any("aler" in falta for falta in missing_required(game))


def test_zip_final_contiene_la_galeria(tmp_path: Path) -> None:
    from backend.bundle.pack import pack_staging

    settings, game = _con_galeria(tmp_path)
    staging = build_staging(settings, game, incluir={"galeria"}, system_name="mame")
    salida = tmp_path / "bundle.zip"
    pack_staging(staging.root, salida)

    with zipfile.ZipFile(salida) as z:
        assert "media/_gallery/g001.png" in z.namelist()
        assert "media/_gallery/g002.png" in z.namelist()
