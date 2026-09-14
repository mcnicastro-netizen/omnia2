"""Backend tests for M2.S5 Layer D Phase 2 — Theme Registry & Site Generation."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASS = os.environ["OMNIA_ADMIN_PASSWORD"]
AGENT_EMAIL = "test_agent@omnia.it"
AGENT_PASS = os.environ["OMNIA_AGENT_PASSWORD"]


def _login(email, password):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": email, "password": password},
               headers={"Content-Type": "application/json"})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def admin_session():
    return _login(ADMIN_EMAIL, ADMIN_PASS)


@pytest.fixture(scope="module")
def agent_session():
    try:
        return _login(AGENT_EMAIL, AGENT_PASS)
    except AssertionError:
        pytest.skip("Agent test user not available")


@pytest.fixture(scope="module")
def agency_slug(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/app/website/theme")
    assert r.status_code == 200, r.text
    return r.json().get("agency_slug")


# --- Theme catalog ---
class TestThemeCatalog:
    def test_list_themes(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/website/themes")
        assert r.status_code == 200
        data = r.json()
        assert "themes" in data
        ids = [t["id"] for t in data["themes"]]
        assert set(ids) == {"minimal", "classic", "bold", "luxury"}
        # metadata validation
        for t in data["themes"]:
            assert t.get("name")
            assert t.get("description")
            assert "preview_palette" in t
            assert "primary" in t["preview_palette"]
        assert data.get("default_theme_id") == "minimal"


# --- Get theme ---
class TestGetTheme:
    def test_get_theme_returns_structure(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/website/theme")
        assert r.status_code == 200
        d = r.json()
        for k in ("agency_id", "agency_slug", "saved_theme_config", "resolved",
                  "extracted_profile", "public_url"):
            assert k in d, f"missing key {k}"
        assert d["resolved"]["theme_id"] in {"minimal", "classic", "bold", "luxury"}
        # palette has 4 keys
        for pk in ("primary", "accent", "neutral_dark", "neutral_light"):
            assert pk in d["resolved"]["palette"]


# --- Apply theme ---
class TestApplyTheme:
    def test_apply_luxury_with_palette_overrides(self, admin_session):
        payload = {
            "theme_id": "luxury",
            "palette": {"primary": "#0a0a0a", "accent": "#B89D5E"},
        }
        r = admin_session.post(f"{BASE_URL}/api/app/website/theme/apply", json=payload)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["resolved"]["theme_id"] == "luxury"
        assert d["resolved"]["palette"]["primary"] == "#0a0a0a"
        assert d["resolved"]["palette"]["accent"] == "#B89D5E"

        # Re-read with GET to verify persistence
        r2 = admin_session.get(f"{BASE_URL}/api/app/website/theme")
        assert r2.status_code == 200
        saved = r2.json()["saved_theme_config"]
        assert saved["theme_id"] == "luxury"
        assert saved["palette"]["primary"] == "#0a0a0a"

    def test_apply_invalid_theme_id(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/app/website/theme/apply",
                               json={"theme_id": "xyz"})
        assert r.status_code == 400
        assert "invalid_theme_id" in r.text


# --- Auto configure ---
class TestAutoConfigure:
    def test_auto_configure_from_extracted_profile(self, admin_session):
        # Ensure extracted profile exists
        cur = admin_session.get(f"{BASE_URL}/api/app/website/theme").json()
        if not cur.get("extracted_profile"):
            pytest.skip("No extracted_profile present; skipping auto-configure positive test")

        r = admin_session.post(f"{BASE_URL}/api/app/website/theme/auto-configure")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["theme_id"] in {"minimal", "classic", "bold", "luxury"}
        assert d["resolved"]["theme_id"] == d["theme_id"]


# --- Preview ---
class TestPreview:
    def test_preview_returns_html_with_data_theme(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/website/preview/classic")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        assert r.headers.get("X-Robots-Tag", "").lower().startswith("noindex")
        assert 'data-theme="classic"' in r.text

    def test_preview_invalid_theme(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/website/preview/zzz")
        assert r.status_code == 400


# --- Public site reflects saved theme ---
class TestPublicSite:
    def test_public_index_reflects_saved_theme(self, admin_session, agency_slug):
        # Re-apply luxury freshly so we're not affected by prior auto-configure
        r0 = admin_session.post(
            f"{BASE_URL}/api/app/website/theme/apply",
            json={"theme_id": "luxury",
                  "palette": {"primary": "#0a0a0a", "accent": "#B89D5E"}},
        )
        assert r0.status_code == 200
        # Public no-auth GET
        r = requests.get(f"{BASE_URL}/api/p/{agency_slug}/")
        assert r.status_code == 200, r.text
        assert "text/html" in r.headers.get("content-type", "")
        assert 'data-theme="luxury"' in r.text
        assert "--o-primary: #0a0a0a" in r.text
        assert "--o-accent: #B89D5E" in r.text

    def test_public_property_page(self, admin_session, agency_slug):
        # find an active property
        r_idx = requests.get(f"{BASE_URL}/api/p/{agency_slug}/")
        # extract first property link from HTML
        m = re.search(rf'/api/p/{re.escape(agency_slug)}/([a-f0-9\-]{{8,}})', r_idx.text)
        if not m:
            pytest.skip("No active properties to test detail page")
        pid = m.group(1)
        r = requests.get(f"{BASE_URL}/api/p/{agency_slug}/{pid}")
        assert r.status_code == 200
        assert 'data-theme="luxury"' in r.text


# --- Permissions ---
class TestPermissions:
    def test_agent_can_get_themes(self, agent_session):
        r = agent_session.get(f"{BASE_URL}/api/app/website/themes")
        assert r.status_code == 200

    def test_agent_can_get_theme(self, agent_session):
        r = agent_session.get(f"{BASE_URL}/api/app/website/theme")
        # could be 200 or 400 if agent has no agency. Accept both as long as not 403
        assert r.status_code in (200, 400)

    def test_agent_cannot_apply_theme(self, agent_session):
        r = agent_session.post(f"{BASE_URL}/api/app/website/theme/apply",
                               json={"theme_id": "minimal"})
        assert r.status_code in (401, 403), f"agent should not apply: {r.status_code}"

    def test_agent_cannot_auto_configure(self, agent_session):
        r = agent_session.post(f"{BASE_URL}/api/app/website/theme/auto-configure")
        assert r.status_code in (401, 403)


# --- Unauth check ---
class TestUnauth:
    def test_get_themes_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/app/website/themes")
        assert r.status_code in (401, 403)


# --- Social Share Block (rendered on property page) ---
class TestSocialShare:
    def test_share_block_present_on_property_page(self, admin_session, agency_slug):
        r_idx = requests.get(f"{BASE_URL}/api/p/{agency_slug}/")
        m = re.search(rf'/api/p/{re.escape(agency_slug)}/([a-f0-9\-]{{8,}})', r_idx.text)
        if not m:
            pytest.skip("No active properties to test detail page")
        pid = m.group(1)
        r = requests.get(f"{BASE_URL}/api/p/{agency_slug}/{pid}")
        assert r.status_code == 200
        # 4 share buttons must be present
        assert 'class="share-block"' in r.text
        assert "wa.me/?text=" in r.text, "WhatsApp share URL missing"
        assert "facebook.com/sharer/sharer.php" in r.text, "Facebook share URL missing"
        assert "mailto:?subject=" in r.text, "Email share URL missing"
        assert 'data-action="copy"' in r.text, "Copy-link button missing"
        # data-share-url must be absolute (start with http)
        m2 = re.search(r'data-share-url="(http[^"]+)"', r.text)
        assert m2, "Share URL not absolute"
        assert m2.group(1).startswith("http")

    def test_share_block_not_on_index_page(self, agency_slug):
        # Share block is per-property, not on the listing index
        r = requests.get(f"{BASE_URL}/api/p/{agency_slug}/")
        assert r.status_code == 200
        assert 'class="share-block"' not in r.text
