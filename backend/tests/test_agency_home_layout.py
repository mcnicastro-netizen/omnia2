"""Agency home Track A — layout riferimento (dual search + vetrina)."""
import os
import pytest
import requests

_raw = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
BASE_URL = _raw if _raw.startswith("http") else "http://127.0.0.1:43121"


@pytest.fixture(scope="module")
def nicastro_html():
    r = requests.get(f"{BASE_URL}/api/p/nicastroimmobiliare/", timeout=20)
    if r.status_code == 404:
        pytest.skip("nicastroimmobiliare slug not seeded")
    assert r.status_code == 200, r.text
    return r.text


class TestAgencyHomeLayout:
    def test_home_has_dual_search_when_mls_enabled(self, nicastro_html):
        html = nicastro_html
        assert 'data-testid="agency-home"' in html
        assert 'data-testid="agency-home-mls-box"' in html
        assert "Cerca il tuo immobile" in html
        assert "Powered by OMNIA" in html
        assert "In evidenza" in html
        assert "Ultimi annunci inseriti" in html
        # no competitor badge
        assert "GESTANET" not in html.upper()
        assert "AGESTANET" not in html.upper()

    def test_home_keeps_theme_css_vars(self, nicastro_html):
        assert 'data-theme="' in nicastro_html
        assert "--o-primary:" in nicastro_html


class TestMlsBoxEmbed:
    def test_embed_html_structure(self):
        r = requests.get(f"{BASE_URL}/api/mls-box/agency/nicastroimmobiliare.html", timeout=20)
        if r.status_code == 404:
            pytest.skip("agency not found")
        assert r.status_code == 200
        assert "In evidenza" in r.text
        assert "Ultimi annunci inseriti" in r.text
        assert "Powered by OMNIA" in r.text
        assert "mls-box-embed" in r.text
