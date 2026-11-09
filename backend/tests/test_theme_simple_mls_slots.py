"""D-151 — gallery 8: MLS on/off senza spezzare il linguaggio del tema."""
import pytest

from apps.immoweb.theme_catalog import THEME_CATALOG
from apps.immoweb.theme_render import render_index

LIVE_IDS = [t["id"] for t in THEME_CATALOG]


def _agency(theme_id: str, mls: bool):
    return {
        "id": "ag-test",
        "name": "Agenzia Demo",
        "display_name": "Agenzia Demo",
        "mls_enabled": mls,
        "_mls_network_count": 12 if mls else 0,
        "website": {
            "theme_config": {
                "theme_id": theme_id,
                "tagline": "La casa giusta",
            }
        },
        "contact": {"email": "info@demo.it", "phone": "095000"},
        "address": {"city": "Catania", "province": "CT"},
        "fiscal": {},
        "branding": {},
    }


def _props():
    return [
        {
            "id": f"p{i}",
            "title": f"Appartamento {i}",
            "city": "Catania",
            "zone": "Centro",
            "operation": "sale",
            "price": 200000 + i,
            "surface_sqm": 90,
            "rooms": 3,
            "bedrooms": 2,
            "photos": [],
            "is_exclusive": i == 1,
        }
        for i in range(1, 4)
    ]


# Theme-specific CSS markers that prove MLS slot adopts the theme language
MLS_SLOT_MARKERS = {
    "minimal": 'body.agency-home[data-theme="minimal"] .ah-mls',
    "classic": 'body.agency-home[data-theme="classic"] .ah-box',
    "bold": 'body.agency-home[data-theme="bold"] .ah-mls',
    "luxury": 'body.agency-home[data-theme="luxury"] .ah-box',
    "atelier": 'body.agency-home[data-theme="atelier"] .ah-mls',
    "cinematic": 'body.agency-home[data-theme="cinematic"] .ah-box',
    "editorial": 'body.agency-home[data-theme="editorial"] .ah-mls',
    "mediterranean": 'body.agency-home[data-theme="mediterranean"] .ah-mls',
}


@pytest.mark.parametrize("theme_id", LIVE_IDS)
def test_mls_on_renders_network_box_and_theme_slot(theme_id):
    html = render_index(_agency(theme_id, True), _props(), "agenzia-demo")
    assert f'data-theme="{theme_id}"' in html
    assert 'data-testid="agency-home-mls-box"' in html
    assert "Powered by OMNIA" in html
    assert "Cerca il tuo immobile" in html
    assert MLS_SLOT_MARKERS[theme_id] in html


@pytest.mark.parametrize("theme_id", LIVE_IDS)
def test_mls_off_no_network_box_keeps_agency_search(theme_id):
    html = render_index(_agency(theme_id, False), _props(), "agenzia-demo")
    assert f'data-theme="{theme_id}"' in html
    assert 'data-testid="agency-home-mls-box"' not in html
    assert 'data-testid="agency-home-agency-search"' in html
    assert "ah-search-row solo" in html
    assert "Cerca il tuo immobile" in html


class TestMinimalClassicLegacyMarkers:
    """Keep explicit style markers for €99 fascia (D-151)."""

    def test_minimal_light_accent_rule(self):
        html = render_index(_agency("minimal", True), _props(), "agenzia-demo")
        assert "border-top:3px solid var(--o-accent" in html

    def test_classic_gold_nav_rule(self):
        html = render_index(_agency("classic", True), _props(), "agenzia-demo")
        assert "border-bottom:3px solid var(--o-accent" in html
