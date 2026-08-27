"""Tests for the Launchbox Games Database provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend.lib.providers.base import Consulta
from backend.lib.providers.launchbox.cliente import (
    CATEGORY_MAP,
    LaunchboxImage,
    _build_search_query,
    _extract_category,
    _parse_images_page,
    _parse_search_results,
    _unescape_html,
)
from backend.lib.providers.launchbox.proveedor import LaunchboxImageProvider

# ── cliente.py: parsing tests ─────────────────────────────────────────


class TestBuildSearchQuery:
    def test_simple_title(self):
        result = _build_search_query("Golden Axe", "Arcade")
        assert "golden" in result.lower()
        assert "axe" in result.lower()
        assert "platform=Arcade" in result

    def test_title_without_system(self):
        result = _build_search_query("Pac-Man", "")
        assert "pac" in result.lower()
        assert "man" in result.lower()
        assert "platform" not in result

    def test_special_chars_removed(self):
        result = _build_search_query("Game: Subtitle!", "NES")
        assert "!" not in result
        assert ":" not in result


class TestUnescapeHtml:
    def test_basic_entities(self):
        assert _unescape_html("&amp;") == "&"
        assert _unescape_html("&lt;") == "<"
        assert _unescape_html("&gt;") == ">"
        assert _unescape_html("&#x2B;") == "+"

    def test_no_entities(self):
        assert _unescape_html("plain text") == "plain text"


class TestExtractCategory:
    def test_box_front(self):
        cat, label = _extract_category("Golden Axe - Box - Front (World)")
        assert cat == "box - front"
        assert "Carátula" in label

    def test_screenshot_gameplay(self):
        cat, label = _extract_category("Golden Axe - Screenshot - Gameplay")
        assert cat == "screenshot - gameplay"
        assert "Gameplay" in label

    def test_arcade_marquee(self):
        cat, label = _extract_category("Golden Axe - Arcade - Marquee (World)")
        assert cat == "arcade - marquee"
        assert "Marquesina" in label

    def test_unknown_category(self):
        cat, label = _extract_category("Golden Axe - Some New Type")
        assert cat is None

    def test_no_dash(self):
        cat, label = _extract_category("Golden Axe")
        assert cat is None


# ── HTML fixture: search results ──────────────────────────────────────

_SEARCH_HTML = '''
<div class="games-grid-card">
    <a class="list-item link-no-underline" href="/games/details/5222-golden-axe">
        <div class="gameCard">
            <div class="cardContent">
                <div class="cardHeading">
                    <div class="cardTitle">
                        <h3>Golden Axe</h3>
                        <p>Arcade</p>
                    </div>
                </div>
            </div>
        </div>
    </a>
</div>
<div class="games-grid-card">
    <a class="list-item link-no-underline" href="/games/details/76996-golden-axe-ii">
        <div class="gameCard">
            <div class="cardContent">
                <div class="cardHeading">
                    <div class="cardTitle">
                        <h3>Golden Axe II</h3>
                        <p>Arcade</p>
                    </div>
                </div>
            </div>
        </div>
    </a>
</div>
<div class="games-grid-card">
    <a class="list-item link-no-underline" href="/games/details/1234-mario-bros">
        <div class="gameCard">
            <div class="cardContent">
                <div class="cardHeading">
                    <div class="cardTitle">
                        <h3>Super Mario Bros</h3>
                        <p>NES</p>
                    </div>
                </div>
            </div>
        </div>
    </a>
</div>
'''

_IMAGES_HTML = '''
<a href="https://images.launchbox-app.com/r2_5693f191-6ff0-4183-81d7-48cf7c173d32.jpg"
   data-gameimageid="19896086"
   data-title="Golden Axe - Fanart - Background (World)">
   <img class="imageCard" src="https://images.launchbox-app.com/r2_thumb1.jpg" />
</a>
<a href="https://images.launchbox-app.com/25862ce5-8469-41af-98a8-b68c61e030a4.jpg"
   data-gameimageid="22136"
   data-title="Golden Axe - Arcade - Marquee (World)">
   <img class="imageCard" src="https://images.launchbox-app.com/marquee_thumb.jpg" />
</a>
<a href="https://images.launchbox-app.com/39043e52-4cad-461d-a67a-1826c07181b1.png"
   data-gameimageid="1725042"
   data-title="Golden Axe - Screenshot - Gameplay">
   <img class="imageCard" src="https://images.launchbox-app.com/screen_thumb.png" />
</a>
<a href="https://images.launchbox-app.com/3e50f36a-b42e-416d-b69c-8805ff237842.png"
   data-gameimageid="706985"
   data-title="Golden Axe - Arcade - Cabinet">
   <img class="imageCard" src="https://images.launchbox-app.com/cabinet_thumb.png" />
</a>
<a href="https://images.launchbox-app.com/d710ed46-fce0-48c5-b167-99b7b26dfb84.png"
   data-gameimageid="841479"
   data-title="Golden Axe - Box - 3D">
   <img class="imageCard" src="https://images.launchbox-app.com/box3d_thumb.png" />
</a>
'''


class TestParseSearchResults:
    def test_finds_matching_game(self):
        result = _parse_search_results(_SEARCH_HTML, "Golden Axe", "Arcade")
        assert result is not None
        assert result.game_id == "5222"
        assert result.slug == "golden-axe"
        assert result.platform == "Arcade"
        assert result.title == "Golden Axe"

    def test_no_match_wrong_system(self):
        result = _parse_search_results(_SEARCH_HTML, "Golden Axe", "NES")
        assert result is None

    def test_no_match_wrong_title(self):
        result = _parse_search_results(_SEARCH_HTML, "Pac-Man", "Arcade")
        assert result is None

    def test_partial_title_match(self):
        result = _parse_search_results(_SEARCH_HTML, "Golden Axe II", "Arcade")
        assert result is not None
        assert result.game_id == "76996"

    def test_different_platform(self):
        result = _parse_search_results(_SEARCH_HTML, "Super Mario", "NES")
        assert result is not None
        assert result.game_id == "1234"

    def test_empty_html(self):
        result = _parse_search_results("", "Golden Axe", "Arcade")
        assert result is None


class TestParseImagesPage:
    def test_extracts_images(self):
        images = _parse_images_page(_IMAGES_HTML, "5222", "golden-axe")
        # Fanart - Background is not mapped, so only 4 of 5 are extracted
        assert len(images) == 4

    def test_image_category_mapping(self):
        images = _parse_images_page(_IMAGES_HTML, "5222", "golden-axe")
        marquee = [i for i in images if i.field_key == "marquesina"]
        assert len(marquee) == 1
        assert "Marquesina" in marquee[0].label

    def test_image_urls(self):
        images = _parse_images_page(_IMAGES_HTML, "5222", "golden-axe")
        for img in images:
            assert img.media_url.startswith("https://images.launchbox-app.com/")

    def test_screenshot_mapping(self):
        images = _parse_images_page(_IMAGES_HTML, "5222", "golden-axe")
        screenshots = [i for i in images if i.field_key == "captura"]
        assert len(screenshots) == 2  # gameplay + cabinet

    def test_empty_html(self):
        images = _parse_images_page("", "5222", "golden-axe")
        assert images == []

    def test_deduplication(self):
        # Duplicate URLs should be deduplicated
        html = _IMAGES_HTML + _IMAGES_HTML
        images = _parse_images_page(html, "5222", "golden-axe")
        # 5 images in fixture, but Fanart - Background is not mapped (4 unique)
        assert len(images) == 4


# ── proveedor.py: integration tests ───────────────────────────────────


class TestLaunchboxImageProvider:
    def test_init(self):
        provider = LaunchboxImageProvider()
        assert provider.nombre == "Launchbox"
        assert provider.tipo == "scrape"
        assert "caratula" in provider.campos
        assert "captura" in provider.campos

    @patch("backend.lib.providers.launchbox.proveedor.search_game")
    def test_buscar_sin_resultados(self, mock_search):
        mock_search.return_value = None
        provider = LaunchboxImageProvider()
        consulta = Consulta(
            game_id="test-1",
            key="caratula",
            title="Unknown Game",
            system="Arcade",
        )
        result = provider.buscar(consulta)
        assert len(result.candidatos) == 0
        assert result.trace.estado == "sin resultados"

    @patch("backend.lib.providers.launchbox.proveedor.fetch_images")
    @patch("backend.lib.providers.launchbox.proveedor.search_game")
    def test_buscar_con_resultados(self, mock_search, mock_images):
        mock_search.return_value = MagicMock(
            game_id="5222",
            slug="golden-axe",
            platform="Arcade",
            title="Golden Axe",
        )
        mock_images.return_value = [
            LaunchboxImage(
                media_url="https://images.launchbox-app.com/marquee.jpg",
                preview_url="https://images.launchbox-app.com/marquee_thumb.jpg",
                category="arcade - marquee",
                field_key="marquesina",
                label="Marquesina",
                game_url="https://gamesdb.launchbox-app.com/games/images/5222-golden-axe",
            ),
        ]
        provider = LaunchboxImageProvider()
        consulta = Consulta(
            game_id="test-1",
            key="marquesina",
            title="Golden Axe",
            system="Arcade",
        )
        result = provider.buscar(consulta)
        assert len(result.candidatos) == 1
        assert result.candidatos[0].kind == "media"
        assert result.candidatos[0].clase == "aplicable"
        assert result.candidatos[0].media_url == "https://images.launchbox-app.com/marquee.jpg"

    @patch("backend.lib.providers.launchbox.proveedor.fetch_images")
    @patch("backend.lib.providers.launchbox.proveedor.search_game")
    def test_buscar_campo_no_match(self, mock_search, mock_images):
        mock_search.return_value = MagicMock(
            game_id="5222",
            slug="golden-axe",
            platform="Arcade",
            title="Golden Axe",
        )
        # Only marquee images, but asking for caratula
        mock_images.return_value = [
            LaunchboxImage(
                media_url="https://images.launchbox-app.com/marquee.jpg",
                preview_url="https://images.launchbox-app.com/marquee_thumb.jpg",
                category="arcade - marquee",
                field_key="marquesina",
                label="Marquesina",
                game_url="https://gamesdb.launchbox-app.com/games/images/5222-golden-axe",
            ),
        ]
        provider = LaunchboxImageProvider()
        consulta = Consulta(
            game_id="test-1",
            key="caratula",
            title="Golden Axe",
            system="Arcade",
        )
        result = provider.buscar(consulta)
        # Should get a "referencia" candidate linking to the gallery
        assert len(result.candidatos) == 1
        assert result.candidatos[0].clase == "referencia"
        assert "5222" in result.candidatos[0].origen_url

    def test_campos_coverage(self):
        provider = LaunchboxImageProvider()
        assert provider.campos == frozenset({
            "caratula", "marquesina", "poster", "logo", "captura",
        })


# ── Category map completeness ─────────────────────────────────────────


class TestCategoryMap:
    def test_all_categories_have_valid_field_keys(self):
        valid_keys = {"caratula", "marquesina", "poster", "logo", "captura"}
        for cat_key, (field_key, label) in CATEGORY_MAP.items():
            assert field_key in valid_keys, f"{cat_key} maps to invalid key {field_key}"
            assert label, f"{cat_key} has empty label"

    def test_category_keys_are_lowercase(self):
        for cat_key in CATEGORY_MAP:
            assert cat_key == cat_key.lower(), f"{cat_key} is not lowercase"
