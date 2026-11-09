"""D-149 — casi migrazione sito: MLS on (caso 1) vs off (caso 2) + listing."""
from apps.immoweb.theme_render import render_index, render_listing, render_property


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
        assert "Powered by" in html and "OMNIA" in html
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

    def test_listing_and_property_pages_for_clone_ready(self):
        agency = _agency(mls_enabled=False)
        props = [_prop(1), {**_prop(2), "operation": "rent"}]
        listing = render_listing(agency, props, "agenzia-test", operation="sale")
        assert 'data-testid="agency-listing"' in listing
        assert "Immobili in vendita" in listing
        assert 'data-testid="agency-listing-search-side"' in listing
        assert "Cerca il tuo immobile" in listing
        # solo box bianco, niente box verde agenzia in lista
        assert 'data-testid="agency-home-agency-search"' not in listing
        assert 'data-testid="agency-home-mls-box"' in listing
        assert "/api/p/agenzia-test/lista" in listing
        scheda = render_property(
            agency,
            {**props[0], "property_type": "apartment", "operation": "sale"},
            "agenzia-test",
        )
        assert "Appartamento 1" in scheda
        assert "<h1>" in scheda
        assert "Appartamento" in scheda
        assert "Vendita" in scheda
        assert ">apartment<" not in scheda
        assert ">sale<" not in scheda
        assert 'data-testid="agency-property-contact"' in scheda
        assert "Contattaci" in scheda
        assert "Invia il modulo" in scheda

    def test_logo_does_not_duplicate_agency_name_text(self):
        agency = _agency(
            mls_enabled=False,
            website={"theme_config": {"theme_id": "classic", "logo_url": "https://cdn.example/logo.png"}},
        )
        html = render_index(agency, [_prop(1)], "agenzia-test")
        assert 'src="https://cdn.example/logo.png"' in html
        # brand mark = logo only (no second text span next to it)
        assert 'data-testid="agency-home-brand"' in html
        brand = html.split('data-testid="agency-home-brand"', 1)[1].split("</a>", 1)[0]
        assert "ah-brand-name" not in brand
        assert "<img" in brand
