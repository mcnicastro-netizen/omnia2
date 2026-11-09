"""Unit tests — clone capture helpers (D-023 fase A / D-149)."""
from apps.immoweb.site_clone import _classify, _page_summary, _discover_links


class TestSiteCloneHelpers:
    def test_classify_home_listing_property(self):
        assert _classify("https://ex.it/", "", is_seed=True) == "home"
        assert _classify("https://ex.it/immobili-vendita", "lista annunci") == "listing"
        assert _classify("https://ex.it/scheda/12345", "dettaglio immobile") == "property"
        # Nicastro / Agestanet-style
        assert (
            _classify(
                "https://www.nicastroimmobiliare.it/web/immobili.asp?tipo_contratto=V",
                "Immobili in vendita",
            )
            == "listing"
        )
        assert (
            _classify(
                "https://www.nicastroimmobiliare.it/web/immobile_dettaglio.asp?cod_annuncio=2428410",
                "Appartamento in vendita",
            )
            == "property"
        )

    def test_page_summary_extracts_title_and_nav(self):
        html = """
        <html><head><title>Agenzia X</title></head>
        <body>
          <h1>Benvenuti</h1>
          <img class="logo" src="/logo.png" alt="logo"/>
          <a href="/immobili">Immobili</a>
          <form><input/></form>
        </body></html>
        """
        s = _page_summary("https://ex.it/", html, "home")
        assert s["title"] == "Agenzia X"
        assert s["h1"] == "Benvenuti"
        assert s["has_forms"] is True
        assert any(n["label"] == "Immobili" for n in s["nav_sample"])
        assert s["logo_candidates"]

    def test_discover_prefers_listing_links(self):
        html = """
        <a href="/chi-siamo">Chi siamo</a>
        <a href="/immobili/vendita">Vendita</a>
        <a href="https://other.it/x">Esterno</a>
        """
        links = _discover_links("https://ex.it/", html)
        assert any("/immobili/vendita" in u for u in links)
        assert all("other.it" not in u for u in links)
