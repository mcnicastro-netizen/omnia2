"""D-149 — casi migrazione sito: MLS on (caso 1) vs off (caso 2)."""
from apps.immoweb.theme_render import render_index


def _agency(**over):
    base = {
        "id": "ag-test",
        "name": "Agenzia Test",
        "display_name": "Agenzia Test",
        "mls_enabled": False,
        "website": {"theme_config": {"theme_id": "minimal"}},
        "contact": {"email": "info@test.it", "phone": "095000"},
        "address": {"city": "Catania", "province": "CT"},
        "fiscal": {},
    }
    base.update(over)
    return base


def _prop(i=1):
    return {
        "id": f"p{i}",
        "title": f"Appartamento {i}",
        "city": "Catania",
        "zone": "Centro",
        "operation": "sale",
        "price": 100000 + i,
        "surface_sqm": 80,
        "rooms": 3,
        "bedrooms": 2,
        "photos": [],
        "is_exclusive": i == 1,
    }


class TestAgencyHomeMlsCases:
    def test_case_2_no_mls_box_no_network_section(self):
        html = render_index(_agency(mls_enabled=False), [_prop(1), _prop(2)], "agenzia-test")
        assert 'data-testid="agency-home"' in html
        assert 'data-testid="agency-home-mls-box"' not in html
        assert 'data-testid="agency-home-mls-network"' not in html
        assert "Cerca il tuo immobile" in html
        assert "ah-search-row solo" in html
        assert "In evidenza" in html

    def test_case_1_mls_box_and_network_section(self):
        agency = _agency(
            mls_enabled=True,
            _mls_network_count=12,
            _mls_network_props=[
                {
                    **_prop(9),
                    "id": "net-1",
                    "_partner_name": "Partner Immobiliare",
                }
            ],
        )
        html = render_index(agency, [_prop(1)], "agenzia-test")
        assert 'data-testid="agency-home-mls-box"' in html
        assert "Powered by OMNIA" in html
        assert 'data-testid="agency-home-mls-network"' in html
        assert "Immobili dalla Rete MLS Partner" in html
        assert 'data-testid="agency-home-mls-chip"' in html
        assert "MLS · Partner Immobiliare" in html
        assert "/it/cloud/property/net-1" in html

    def test_case_1_empty_network_has_elegant_fallback(self):
        agency = _agency(mls_enabled=True, _mls_network_count=0, _mls_network_props=[])
        html = render_index(agency, [], "agenzia-test")
        assert 'data-testid="agency-home-mls-network"' in html
        assert 'data-testid="agency-home-mls-empty"' in html
        assert "Nessun immobile di rete" in html
