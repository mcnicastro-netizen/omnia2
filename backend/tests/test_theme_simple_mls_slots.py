"""D-151 — Minimal/Classic (€99): MLS on/off senza stravolgere il look del tema."""
from apps.immoweb.theme_render import render_index


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


class TestMinimalMlsSlots:
    def test_mls_on_keeps_light_slot_not_full_primary_block(self):
        html = render_index(_agency("minimal", True), _props(), "agenzia-demo")
        assert 'data-theme="minimal"' in html
        assert 'data-testid="agency-home-mls-box"' in html
        assert "Powered by OMNIA" in html
        assert "Cerca il tuo immobile" in html
        # Theme-specific light MLS slot (not only generic solid primary)
        assert 'body.agency-home[data-theme="minimal"] .ah-mls' in html
        assert "border-top:3px solid var(--o-accent" in html

    def test_mls_off_no_network_box(self):
        html = render_index(_agency("minimal", False), _props(), "agenzia-demo")
        assert 'data-testid="agency-home-mls-box"' not in html
        assert "ah-search-row solo" in html
        assert "Cerca il tuo immobile" in html


class TestClassicMlsSlots:
    def test_mls_on_uses_classic_surface(self):
        html = render_index(_agency("classic", True), _props(), "agenzia-demo")
        assert 'data-theme="classic"' in html
        assert 'data-testid="agency-home-mls-box"' in html
        assert 'body.agency-home[data-theme="classic"] .ah-box' in html
        assert "border-bottom:3px solid var(--o-accent" in html  # classic nav gold rule

    def test_mls_off_keeps_agency_search(self):
        html = render_index(_agency("classic", False), _props(), "agenzia-demo")
        assert 'data-testid="agency-home-mls-box"' not in html
        assert 'data-testid="agency-home-agency-search"' in html
