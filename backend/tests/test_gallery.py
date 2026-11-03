from __future__ import annotations

import json
import shutil
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
from backend.lib.providers.base import Candidato, Consulta, ProviderResult, ProviderTrace
from backend.lib.providers.launchbox.cliente import LaunchboxSearchResult
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


def test_la_galeria_no_ofrece_urls_que_responden_403(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    vieja = "https://www.mobygames.com/images/covers/l/123869-prince-of-persia-dos-front-cover.jpg"
    cdn = "https://cdn.mobygames.com/covers/4008841-prince-of-persia-dos-front-cover.jpg"
    monkeypatch.setattr(
        "backend.lib.providers.referencia.images._search_ddg_images",
        lambda _query: [{"image": vieja}, {"image": cdn}],
    )

    candidatos = GalleryService(settings).candidatos("final-fight", source="ImageSearch")

    assert {c["url"] for c in candidatos} == {cdn}


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="necesita ffmpeg en el host")
def test_el_buscador_se_puede_pedir_de_a_un_casillero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    claves: list[str] = []

    def buscar(_self: object, consulta: Consulta) -> ProviderResult:
        claves.append(consulta.key)
        return ProviderResult((), ProviderTrace("Image Search", "scrape", "ok"))

    monkeypatch.setattr(
        "backend.lib.providers.referencia.images.ImageSearchProvider.buscar", buscar,
    )
    servicio = GalleryService(settings)

    servicio.candidatos("final-fight", source="ImageSearch", clave="logo")
    assert claves == ["logo"]

    claves.clear()
    servicio.candidatos("final-fight", source="ImageSearch")
    assert len(claves) == 5


def test_launchbox_da_a_la_galeria_todas_sus_categorias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    pedidas: list[bool] = []

    def fetch(_id: str, _slug: str, *, todas: bool = False) -> list[object]:
        pedidas.append(todas)
        return []

    resultado = LaunchboxSearchResult("1", "x", "Arcade", "X", "u")
    monkeypatch.setattr(
        "backend.services.gallery.launchbox_search_game", lambda *_a, **_k: resultado,
    )
    monkeypatch.setattr("backend.services.gallery.launchbox_fetch_images", fetch)

    GalleryService(settings).candidatos("final-fight", source="Launchbox")

    assert pedidas == [True]


def test_mobygames_suma_portadas_y_capturas_a_la_galeria(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(tmp_path)
    trace = ProviderTrace("MobyGames", "scrape", "ok")

    def candidato(url: str, clase: str = "aplicable") -> Candidato:
        return Candidato(
            id=url, key="caratula", kind="media", nombre=url, fuente="MobyGames",
            clase=clase, media_url=url, trace=trace,
        )

    class Falso:
        def buscar(self, consulta: Consulta) -> ProviderResult:
            if consulta.key == "caratula":
                return ProviderResult((
                    candidato("https://cdn.mobygames.com/covers/1.jpg"),
                    candidato("https://www.mobygames.com/images/covers/2.jpg"),
                    candidato("https://cdn.mobygames.com/referencia.jpg", "referencia"),
                ), trace)
            return ProviderResult((candidato("https://cdn.mobygames.com/shots/3.jpg"),), trace)

    monkeypatch.setattr("backend.services.gallery.proveedor_mobygames", lambda _s: Falso())

    candidatos = GalleryService(settings).candidatos("final-fight", source="MobyGames")

    assert [c["url"] for c in candidatos] == [
        "https://cdn.mobygames.com/covers/1.jpg",
        "https://cdn.mobygames.com/shots/3.jpg",
    ]
    assert {c["source"] for c in candidatos} == {"MobyGames"}


def test_sin_navegador_la_galeria_no_tiene_mobygames_y_sigue(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    assert GalleryService(settings).candidatos("final-fight", source="MobyGames") == []


def test_guardar_un_gif_lo_deja_como_png(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    gif = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
        b"!\xf9\x04\x01\x00\x00\x00\x00"
        b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )

    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport(), cuerpo=gif)
        GalleryService(settings).guardar(
            "final-fight",
            [GuardarGaleriaItem(url="https://mya.test/1.gif", source="MyAbandonware")],
        )

    imagen = GamesStore(settings.games_dir).get("final-fight").gallery[0]
    assert imagen.file == "g001.png"
    guardada = settings.media_dir / "mame" / "final-fight" / "_gallery" / "g001.png"
    assert guardada.read_bytes().startswith(b"\x89PNG")


_CUADRO_GIF = (
    b"!\xf9\x04\x00\x0a\x00\x00\x00"
    b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00"
)
_GIF_ANIMADO = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
    + _CUADRO_GIF + _CUADRO_GIF + b";"
)


def test_un_jpeg_declarado_como_gif_no_queda_con_extension_gif() -> None:
    from backend.lib.media import sin_gif

    jpeg = bytes.fromhex("ffd8ffe000104a46494600010100000100")
    assert sin_gif(jpeg, ".gif") == (jpeg, ".jpg")
    assert sin_gif(jpeg, ".jpeg") == (jpeg, ".jpeg")


def test_guardar_un_gif_animado_no_lo_guarda_y_avisa(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport(), cuerpo=_GIF_ANIMADO)
        resultado = GalleryService(settings).guardar(
            "final-fight",
            [GuardarGaleriaItem(url="https://sitio.test/1.gif", source="ImageSearch")],
        )

    assert GamesStore(settings.games_dir).get("final-fight").gallery == []
    assert len(resultado["fallidas"]) == 1


def test_aplicar_un_gif_animado_no_cae_a_la_miniatura(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.api.errors import BadRequest
    from backend.services import fields as modulo
    from backend.services.fields import FieldsService

    settings = _settings(tmp_path)
    candidato = {
        "kind": "media",
        "clase": "aplicable",
        "mediaUrl": "https://sitio.test/1.gif",
        "previewUrl": "https://sitio.test/mini.jpg",
    }
    monkeypatch.setattr(modulo, "cached_candidate", lambda *_a, **_k: candidato)
    pedidas: list[str] = []

    def get(url: str, **_k: object) -> httpx.Response:
        pedidas.append(url)
        return httpx.Response(200, content=_GIF_ANIMADO, headers={"content-type": "image/gif"})

    monkeypatch.setattr(modulo.httpx, "get", get)
    with pytest.raises(BadRequest, match="GIF animado"):
        FieldsService(settings).apply_suggestion("final-fight", "captura", "x")
    assert pedidas == ["https://sitio.test/1.gif"]


def test_candidatos_incluyen_las_capturas_de_myabandonware(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    consultas: list[Consulta] = []
    trace = ProviderTrace("MyAbandonware", "scrape", "ok")

    def buscar(_self: object, consulta: Consulta) -> ProviderResult:
        consultas.append(consulta)
        captura = Candidato(
            id="myabandonware:https://mya.test/1.png",
            key="captura",
            kind="media",
            nombre="Captura 1 de DOS (MyAbandonware)",
            fuente="MyAbandonware",
            clase="aplicable",
            media_url="https://mya.test/1.png",
            preview_url="https://mya.test/1-mini.png",
            origen_url="https://mya.test/juego",
            trace=trace,
        )
        return ProviderResult((captura,), trace)

    with pytest.MonkeyPatch.context() as mp:
        _parchear(mp, _transport())
        mp.setattr("backend.services.gallery.MyAbandonwareProvider.buscar", buscar)
        candidatos = GalleryService(settings).candidatos("final-fight", source="MyAbandonware")

    assert [(c["url"], c["previewUrl"], c["source"]) for c in candidatos] == [
        ("https://mya.test/1.png", "https://mya.test/1-mini.png", "MyAbandonware")
    ]
    assert (consultas[0].key, consultas[0].year) == ("captura", "1989")
