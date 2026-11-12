"""D-170 — sito già proprio + box MLS embed (caso Nicastro)."""
from apps.immoweb.mls_box import build_embed_kit, render_mls_search_html, search_iframe_snippet
from apps.immoweb.setup_journey import public_mls_via_embed
from apps.immoweb.theme_home import _mls_search_box


def test_external_plus_mls_uses_embed_not_theme():
    assert public_mls_via_embed("external", True) is True
    assert public_mls_via_embed("keep_brand", True) is True
    assert public_mls_via_embed("omnia_theme", True) is False
    assert public_mls_via_embed("external", False) is False
    assert public_mls_via_embed(None, True) is False


def test_embed_kit_points_to_search_box():
    kit = build_embed_kit(
        "nicastroimmobiliare", ready=True, api_base="https://www.omniarealestateecosystem.it"
    )
    assert kit["mode"] == "iframe_on_own_site"
    assert kit["ready"] is True
    assert kit["search_url"].endswith("/api/mls-box/search/nicastroimmobiliare.html")
    assert kit["iframe_html"].startswith("<iframe")
    assert "/api/mls-box/search/nicastroimmobiliare.html" in kit["iframe_html"]
    assert "min-height:540px" in kit["iframe_html"]
    assert len(kit["how_to"]) == 3
    snippet = search_iframe_snippet("nicastroimmobiliare", "https://x")
    assert 'src="https://x/api/mls-box/search/nicastroimmobiliare.html"' in snippet


def test_embed_kit_not_ready_still_has_snippet():
    kit = build_embed_kit("agenzia-test", ready=False, api_base="https://x")
    assert kit["ready"] is False
    assert "agenzia-test" in kit["iframe_html"]


def test_search_html_matches_home_box_fields():
    html = render_mls_search_html(
        agency_name="Nicastro Immobiliare",
        primary="#3D8B40",
        network_count=12890,
        default_province="CT",
        operation="sale",
        categoria="residential",
        province="CT",
        city="",
        price_min="",
        price_max="",
        searched=False,
        items=[],
        result_total=0,
        detail_base="https://www.omniarealestateecosystem.it",
    )
    assert 'data-testid="mls-search-embed"' in html
    assert "12.890 immobili condivisi" in html
    assert "Contratto" in html
    assert "Categoria" in html
    assert "Provincia" in html
    assert "Comune" in html
    assert "avvia la ricerca" in html
    assert "Powered by" in html and "OMNIA" in html
    assert 'name="go"' in html
    assert "CATANIA" in html
    assert 'option value="CT" selected' in html


def test_search_html_results_and_escape():
    html = render_mls_search_html(
        agency_name='<script>alert(1)</script>',
        primary="#111",
        network_count=3,
        default_province="CT",
        operation="sale",
        categoria="residential",
        province="CT",
        city="Catania",
        price_min="50000",
        price_max="",
        searched=True,
        items=[
            {
                "id": "p1",
                "title": "Villa <b>test</b>",
                "city": "Catania",
                "price": 220000,
                "cover_url": "https://cdn.example/a.jpg",
            }
        ],
        result_total=1,
        detail_base="https://fe.example",
    )
    assert "<script>" not in html
    assert "Villa &lt;b&gt;test&lt;/b&gt;" in html
    assert "https://fe.example/it/cloud/property/p1" in html
    assert "1 in rete" in html
    assert "€ 220.000" in html


def test_omnia_theme_box_submits_to_cloud():
    html = _mls_search_box(42)
    assert 'data-testid="agency-home-mls-box"' in html
    assert 'action="/it/cloud"' in html
    assert 'name="mls"' in html
    assert 'name="operation"' in html
    assert 'name="province"' in html
    assert 'name="city"' in html
    assert "avvia la ricerca" in html
    assert "onclick=" not in html
