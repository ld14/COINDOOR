"""Banco de imagenes por juego, aparte de los cinco campos del contrato.

Tres fuentes de imágenes:
- ArcadeDB: publica entre 8 y 16 tipos por romset (flyer, marquee, cpanel, etc.)
- ImageSearch: imágenes de DuckDuckGo de fuentes confiables
- Launchbox: imágenes categorizadas de Games Database

La galeria conserva todas: se listan, se eligen y se guardan en
``media/<sistema>/<juego>/_gallery/``.

Los archivos viajan al bundle en ``media/_gallery/`` y se declaran en
``data.json → gallery[]``. Ver ADR-0016 para por que una subcarpeta con guion bajo
y no assets nuevos del contrato.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from backend.api.errors import BadRequest, NotFound
from backend.api.schemas import GalleryImage
from backend.config import Settings
from backend.lib.domain.arcade import soporta_arcadedb
from backend.lib.domain.fielddefs import image_keys
from backend.lib.domain.gallery import label_para
from backend.lib.jobs.registro import JobState
from backend.lib.media import ext_por_magic
from backend.lib.providers.arcadedb.cliente import fetch_con_padre
from backend.lib.providers.base import Consulta, Limite
from backend.lib.providers.http import ProviderHttpClient
from backend.lib.providers.launchbox.cliente import (
    fetch_images as launchbox_fetch_images,
)
from backend.lib.providers.launchbox.cliente import (
    search_game as launchbox_search_game,
)
from backend.lib.providers.referencia.images import ImageSearchProvider
from backend.store.archivo import escribir_binario, safe_id
from backend.store.cuotas import QuotasStore
from backend.store.juegos import GamesStore
from backend.store.sistemas import SystemsStore

log = logging.getLogger(__name__)


class GuardarGaleriaItem(BaseModel):
    """Elemento a guardar en la galería.

    Puede ser un tipo de ArcadeDB (ej: ``flyer``) o una URL de otra fuente.
    """

    tipo: str | None = None
    url: str | None = None
    source: str = "ArcadeDB"


_SOURCE_ARCADEDB = "ArcadeDB"
_SOURCE_ARCADEDB_PADRE = "ArcadeDB (romset padre)"
_SOURCE_IMAGESEARCH = "ImageSearch"
_SOURCE_LAUNCHBOX = "Launchbox"
_LIMITE = Limite()
_SUBCARPETA = "_gallery"


class GalleryService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.games = GamesStore(settings.games_dir)
        self.systems = SystemsStore(settings.systems_path)

    # -- candidatos ---------------------------------------------------------

    def candidatos(
        self, game_id: str, *, source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Imágenes disponibles de las tres fuentes: ArcadeDB, ImageSearch, Launchbox.

        Si se pasa ``source``, solo consulta esa fuente (para reintentos individuales).
        Sincrono: fetch memoizado (ArcadeDB) + requests a DDG y Launchbox.
        Un romset desconocido no devuelve error, solo no muestra ArcadeDB.
        """
        game = self.games.get(game_id)
        system = self.systems.get(game.systemId)
        ya_guardados_urls = {img.url for img in game.gallery}

        candidatos: list[dict[str, Any]] = []

        # 1. ArcadeDB (solo para sistemas arcade)
        arcade_ok = source is None or source == "ArcadeDB"
        if arcade_ok and soporta_arcadedb(game.systemId) and game.romRef:
            romset = Path(game.romRef).stem.lower()
            if romset:
                try:
                    candidatos.extend(
                        self._candidatos_arcadedb(game_id, romset, ya_guardados_urls)
                    )
                except Exception:
                    log.warning("Gallery: ArcadeDB failed for %s", game_id, exc_info=True)

        # 2. ImageSearch (todos los sistemas)
        if (source is None or source == "ImageSearch") and game.identity.title:
            try:
                candidatos.extend(
                    self._candidatos_imagesearch(
                        game_id, game.identity.title, system.name, ya_guardados_urls,
                    )
                )
            except Exception:
                log.warning("Gallery: ImageSearch failed for %s", game_id, exc_info=True)

        # 3. Launchbox (todos los sistemas)
        if (source is None or source == "Launchbox") and game.identity.title:
            try:
                candidatos.extend(
                    self._candidatos_launchbox(
                        game_id, game.identity.title, system.name, ya_guardados_urls,
                    )
                )
            except Exception:
                log.warning("Gallery: Launchbox failed for %s", game_id, exc_info=True)

        return candidatos

    def _candidatos_arcadedb(
        self, game_id: str, romset: str, ya_guardados_urls: set[str],
    ) -> list[dict[str, Any]]:
        juego, del_padre = fetch_con_padre(romset, self._http_factory())
        if juego is None:
            return []

        ya_guardados_tipos = {
            img.tipo for img in self.games.get(game_id).gallery
            if img.source in (_SOURCE_ARCADEDB, _SOURCE_ARCADEDB_PADRE)
        }
        return [
            {
                "id": f"arcadedb:{tipo}",
                "tipo": tipo,
                "label": label_para(tipo),
                "url": url,
                "delPadre": tipo in del_padre,
                "yaGuardada": tipo in ya_guardados_tipos,
                "source": _SOURCE_ARCADEDB_PADRE if tipo in del_padre else _SOURCE_ARCADEDB,
            }
            for tipo, url in sorted(juego.images.items(), key=lambda par: label_para(par[0]))
        ]

    def _candidatos_imagesearch(
        self, game_id: str, title: str, system: str, ya_guardados_urls: set[str],
    ) -> list[dict[str, Any]]:
        provider = ImageSearchProvider()
        candidatos: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        # Consultar los campos más útiles para la galería
        for key in ("caratula", "captura", "marquesina"):
            consulta = Consulta(game_id, key, title, system, None)
            result = provider.buscar(consulta)
            for _i, c in enumerate(result.candidatos):
                if c.kind != "media" or not c.media_url:
                    continue
                if c.media_url in seen_urls or c.media_url in ya_guardados_urls:
                    continue
                seen_urls.add(c.media_url)
                candidatos.append({
                    "id": f"image-search:{game_id}:{key}:{len(candidatos)}",
                    "tipo": None,
                    "label": c.nombre,
                    "url": c.media_url,
                    "previewUrl": c.preview_url,
                    "origenUrl": c.origen_url,
                    "delPadre": False,
                    "yaGuardada": False,
                    "source": _SOURCE_IMAGESEARCH,
                })
        return candidatos

    def _candidatos_launchbox(
        self, game_id: str, title: str, system: str, ya_guardados_urls: set[str],
    ) -> list[dict[str, Any]]:
        result = launchbox_search_game(title, system)
        if result is None:
            return []

        images = launchbox_fetch_images(result.game_id, result.slug)
        candidatos = []
        for i, img in enumerate(images):
            candidatos.append({
                "id": f"launchbox:{result.game_id}:{i}",
                "tipo": None,
                "label": f"{img.label} (Launchbox)",
                "url": img.media_url,
                "previewUrl": img.preview_url,
                "origenUrl": img.game_url,
                "delPadre": False,
                "yaGuardada": img.media_url in ya_guardados_urls,
                "source": _SOURCE_LAUNCHBOX,
            })
        return candidatos

    # -- guardar ------------------------------------------------------------

    def guardar_job(
        self, game_id: str, items: Sequence[GuardarGaleriaItem],
    ) -> Callable[[JobState], dict]:
        def job_fn(job: JobState) -> dict[str, object]:
            return self.guardar(game_id, items, job)

        return job_fn

    def guardar(
        self,
        game_id: str,
        items: Sequence[GuardarGaleriaItem],
        job: JobState | None = None,
    ) -> dict[str, object]:
        seen: set[tuple[str | None, str | None]] = set()
        pedidos: list[GuardarGaleriaItem] = []
        for item in items:
            key = (item.tipo, item.url)
            if key not in seen:
                seen.add(key)
                pedidos.append(item)
        if not pedidos:
            raise BadRequest("No se seleccionó ninguna imagen.")

        game = self.games.get(game_id)
        siguiente = _siguiente_numero(game.gallery)
        nuevas: list[GalleryImage] = []
        fallidas: list[str] = []

        for i, item in enumerate(pedidos):
            if job is not None and job.cancel_event.is_set():
                break

            try:
                if item.url:
                    imagen = self._descargar_url(game_id, item.url, item.source, siguiente + i)
                elif item.tipo:
                    imagen = self._descargar_tipo(game_id, item.tipo, siguiente + i)
                else:
                    fallidas.append(str(item))
                    continue
            except Exception:
                log.warning("No se pudo bajar imagen para %s", game_id, exc_info=True)
                fallidas.append(item.tipo or item.url or "?")
                continue

            nuevas.append(imagen)
            if job is not None:
                job.progress = int((i + 1) / len(pedidos) * 100)

        if nuevas:
            self.games.add_gallery_images(game_id, nuevas)
        return {
            "guardadas": [img.id for img in nuevas],
            "fallidas": fallidas,
        }

    def _descargar_tipo(
        self, game_id: str, tipo: str, numero: int,
    ) -> GalleryImage:
        """Descarga una imagen de ArcadeDB por tipo (flyer, marquee, etc.)."""
        game = self.games.get(game_id)
        romset = Path(game.romRef).stem.lower() if game.romRef else ""
        if not romset:
            raise BadRequest("El juego no tiene un romset del que traer imágenes.")

        juego, del_padre = fetch_con_padre(romset, self._http_factory())
        if juego is None:
            raise NotFound(f"ArcadeDB no conoce el romset: {romset}")
        if tipo not in juego.images:
            raise BadRequest(f"ArcadeDB no publica ese tipo para {romset}: {tipo}")

        imagen = self._descargar(game_id, tipo, juego.images[tipo], numero)
        if tipo in del_padre:
            imagen = imagen.model_copy(update={"source": _SOURCE_ARCADEDB_PADRE})
        return imagen

    def _descargar_url(
        self, game_id: str, url: str, source: str, numero: int,
    ) -> GalleryImage:
        """Descarga una imagen desde una URL (ImageSearch, Launchbox, etc.)."""
        return self._descargar(game_id, f"url-{numero}", url, numero, source=source)

    # -- usar como / eliminar -----------------------------------------------

    def usar_como(self, game_id: str, image_id: str, campo: str) -> Any:
        """Apunta un campo del contrato a una imagen de la galeria.

        La entrada de galeria se conserva: la misma imagen puede alimentar mas de un
        campo, y sacarla del banco al asignarla obligaria a volver a bajarla.
        """
        if campo not in image_keys():
            raise BadRequest(f"No es un campo de imagen del contrato: {campo}")
        game = self.games.get(game_id)
        imagen = next((img for img in game.gallery if img.id == image_id), None)
        if imagen is None:
            raise NotFound(f"Imagen de galería no encontrada: {image_id}")
        return self.games.apply_media_suggestion(game_id, campo, imagen.url, None)

    def eliminar(self, game_id: str, image_id: str) -> Any:
        game = self.games.get(game_id)
        imagen = next((img for img in game.gallery if img.id == image_id), None)
        if imagen is None:
            raise NotFound(f"Imagen de galería no encontrada: {image_id}")
        ruta = self._carpeta(game.systemId, game.id) / imagen.file
        ruta.unlink(missing_ok=True)
        return self.games.remove_gallery_image(game_id, image_id)

    # -- internos -----------------------------------------------------------

    def _http_factory(self) -> Callable[[], ProviderHttpClient]:
        quotas = QuotasStore(self.settings.quotas_path)

        def fabricar() -> ProviderHttpClient:
            # Uno nuevo por peticion: ProviderHttpClient cierra su cliente al salir.
            return ProviderHttpClient("arcadedb", _LIMITE, quotas, timeout=15.0)

        return fabricar

    def _carpeta(self, system_id: str, game_id: str) -> Path:
        return self.settings.media_dir / safe_id(system_id) / safe_id(game_id) / _SUBCARPETA

    def _descargar(
        self,
        game_id: str,
        tipo: str,
        url: str,
        numero: int,
        source: str = _SOURCE_ARCADEDB,
    ) -> GalleryImage:
        game = self.games.get(game_id)
        response = httpx.get(
            url,
            timeout=60.0,
            follow_redirects=True,
            headers={"User-Agent": "COINDOOR/0.1 (+local research)", "Accept": "image/*,*/*"},
        )
        if response.status_code >= 400:
            raise BadRequest(f"Error descargando {url}: {response.status_code}")

        # Por contenido y no por el nombre de la URL: ArcadeDB sirve todo desde
        # endpoints .php, sin extension util en el path.
        suffix = ext_por_magic(response.content[:16]) or ".png"
        nombre = f"g{numero:03d}{suffix}"
        system_dir, game_dir = safe_id(game.systemId), safe_id(game.id)
        escribir_binario(self._carpeta(game.systemId, game.id) / nombre, response.content)
        return GalleryImage(
            id=f"{tipo}-{numero:03d}",
            tipo=tipo,
            label=label_para(tipo),
            file=nombre,
            url=f"/media/{system_dir}/{game_dir}/{_SUBCARPETA}/{nombre}",
            source=source,
        )


def _siguiente_numero(gallery: Sequence[GalleryImage]) -> int:
    usados = []
    for img in gallery:
        raiz = Path(img.file).stem
        if raiz.startswith("g") and raiz[1:].isdigit():
            usados.append(int(raiz[1:]))
    return max(usados, default=0) + 1
