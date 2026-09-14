"""Backend tests for logo asset delivery (D-060)."""
import os
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com",
).rstrip("/")


class TestOmniaLogoAssets:
    """Verify OMNIA logo asset files are served correctly by frontend static."""

    def test_full_logo_served(self):
        r = requests.get(f"{BASE_URL}/omnia-logo.png", timeout=10)
        assert r.status_code == 200
        assert "image" in r.headers.get("content-type", "").lower()
        assert len(r.content) > 10000  # png con logo (>10KB)

    def test_mark_only_served(self):
        r = requests.get(f"{BASE_URL}/omnia-mark.png", timeout=10)
        assert r.status_code == 200
        assert "image" in r.headers.get("content-type", "").lower()
        assert len(r.content) > 1000

    def test_favicon_served(self):
        r = requests.get(f"{BASE_URL}/favicon.png", timeout=10)
        assert r.status_code == 200
        assert "image" in r.headers.get("content-type", "").lower()


class TestWidgetLogoFooter:
    """Verify widget assets include the OMNIA mini-logo in the footer."""

    def test_staging_widget_has_logo(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/staging.html?key=demo&lang=it", timeout=10)
        assert r.status_code == 200
        assert "/omnia-mark.png" in r.text

    def test_legal_widget_has_logo(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/legal.html?key=demo&lang=it", timeout=10)
        assert r.status_code == 200
        assert "/omnia-mark.png" in r.text

    def test_valuator_widget_has_logo(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/valuator.html?key=demo&lang=it", timeout=10)
        assert r.status_code == 200
        assert "/omnia-mark.png" in r.text

    def test_mortgages_widget_has_logo(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/mortgages.html?key=demo&lang=it", timeout=10)
        assert r.status_code == 200
        assert "/omnia-mark.png" in r.text
