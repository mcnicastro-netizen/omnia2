"""Backend tests for M2.5.3 (D-049): Track B Embeddable Widgets.

Covers:
- Widget assets served correctly (loader.js, valuator.html, mortgages.html)
- Origin whitelist enforcement (Origin OR Referer match)
- Widget lead capture creates CRM row with source=widget_* and partner_id
- Free widget_lead does not touch credits
- allowed_origins PATCH endpoint updates the whitelist
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]
ALLOWED_ORIGIN = "https://omnia-crm-docs.preview.emergentagent.com"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    return s


def _revoke_test_keys(session):
    r = session.get(f"{BASE_URL}/api/app/api-keys")
    if r.status_code == 200:
        for k in r.json().get("items", []):
            if k.get("name", "").startswith("TESTW_"):
                session.post(f"{BASE_URL}/api/app/api-keys/{k['id']}/revoke")


@pytest.fixture(scope="module", autouse=True)
def cleanup(session):
    _revoke_test_keys(session)
    yield
    _revoke_test_keys(session)


@pytest.fixture(scope="module")
def widget_key(session):
    """Issue a widget key with origin whitelist."""
    payload = {
        "name": f"TESTW_Widget_{uuid.uuid4().hex[:6]}",
        "initial_credits": 30,
        "partner_id": "webagency_TEST_W",
        "allowed_origins": [ALLOWED_ORIGIN, "https://*.example.com"],
    }
    r = session.post(f"{BASE_URL}/api/app/api-keys", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["api_key"]["allowed_origins"] == [ALLOWED_ORIGIN, "https://*.example.com"]
    return data


@pytest.fixture(scope="module")
def open_key(session):
    """Issue a key WITHOUT allowed_origins (permissive, server-side)."""
    payload = {
        "name": f"TESTW_Open_{uuid.uuid4().hex[:6]}",
        "initial_credits": 30,
    }
    r = session.post(f"{BASE_URL}/api/app/api-keys", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ---------- ASSETS ----------

class TestAssets:
    def test_loader_js_served(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/loader.js")
        assert r.status_code == 200
        assert "application/javascript" in r.headers.get("content-type", "")
        assert "omk_live_" in r.text
        # Backend base injected
        assert "__BACKEND_BASE__" not in r.text
        assert BASE_URL in r.text

    def test_valuator_html_served(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/valuator.html",
                         params={"primary": "#ff0000", "lang": "it"})
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        assert "#ff0000" in r.text  # color injected
        assert 'lang="it"' in r.text
        # Iframe-friendly headers
        assert r.headers.get("Content-Security-Policy", "").startswith("frame-ancestors")

    def test_mortgages_html_served(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/mortgages.html")
        assert r.status_code == 200
        assert "Comparatore Mutui" in r.text or "mortgages" in r.text.lower()

    def test_unknown_widget_404(self):
        # Sprint 1.5 recovery: staging + legal ora sono widget validi.
        # Testiamo con un nome davvero sconosciuto.
        r = requests.get(f"{BASE_URL}/api/widgets/v1/tiktok.html")
        assert r.status_code == 404


# ---------- ORIGIN WHITELIST ----------

class TestOriginWhitelist:
    def test_no_origin_no_referer_blocked_when_whitelist_set(self, widget_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/valuator",
            headers={"Authorization": f"Bearer {widget_key['key']}"},
            json={"city": "Roma", "surface_sqm": 80},
        )
        assert r.status_code == 403
        assert r.json()["detail"] == "origin_not_allowed"

    def test_allowed_origin_via_referer(self, widget_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/valuator",
            headers={
                "Authorization": f"Bearer {widget_key['key']}",
                "Referer": f"{ALLOWED_ORIGIN}/some/page.html",
            },
            json={"city": "Roma", "surface_sqm": 80},
        )
        assert r.status_code == 200, r.text
        assert r.json()["credits_charged"] == 5

    def test_disallowed_origin_403(self, widget_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/valuator",
            headers={
                "Authorization": f"Bearer {widget_key['key']}",
                "Origin": "https://evil.com",
                "Referer": "https://evil.com/hack",
            },
            json={"city": "Roma", "surface_sqm": 80},
        )
        assert r.status_code == 403

    def test_subdomain_wildcard_match(self, widget_key):
        r = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={
                "Authorization": f"Bearer {widget_key['key']}",
                "Referer": "https://foo.example.com/x",
            },
        )
        assert r.status_code == 200

    def test_open_key_no_whitelist_allows_all(self, open_key):
        """Key without allowed_origins is permissive (server-side use case)."""
        r = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": f"Bearer {open_key['key']}"},
        )
        assert r.status_code == 200


# ---------- WIDGET LEAD CAPTURE ----------

class TestWidgetLead:
    def test_lead_creates_crm_row(self, widget_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/widgets/lead",
            headers={
                "Authorization": f"Bearer {widget_key['key']}",
                "Referer": f"{ALLOWED_ORIGIN}/vendi",
            },
            json={
                "widget": "valuator",
                "name": "Test Lead",
                "email": "testlead@example.com",
                "phone": "+39 333 1234567",
                "consent": True,
                "context": {"input": {"city": "Milano"}},
                "source_url": f"{ALLOWED_ORIGIN}/vendi",
            },
        )
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["credits_charged"] == 0
        assert j["data"]["status"] == "new"
        assert j["data"]["id"]

    def test_lead_requires_consent(self, widget_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/widgets/lead",
            headers={
                "Authorization": f"Bearer {widget_key['key']}",
                "Referer": f"{ALLOWED_ORIGIN}/x",
            },
            json={"widget": "valuator", "email": "x@y.com", "consent": False},
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "consent_required"

    def test_lead_requires_email_or_phone(self, widget_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/widgets/lead",
            headers={
                "Authorization": f"Bearer {widget_key['key']}",
                "Referer": f"{ALLOWED_ORIGIN}/x",
            },
            json={"widget": "valuator", "consent": True, "name": "Foo"},
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "email_or_phone_required"

    def test_lead_invalid_widget(self, widget_key):
        # Sprint 1.5 recovery: pattern ora accetta valuator|mortgages|legal|staging.
        r = requests.post(
            f"{BASE_URL}/api/v1/widgets/lead",
            headers={
                "Authorization": f"Bearer {widget_key['key']}",
                "Referer": f"{ALLOWED_ORIGIN}/x",
            },
            json={"widget": "tiktok", "email": "x@y.com", "consent": True},
        )
        assert r.status_code == 422  # pydantic pattern validation


# ---------- ORIGINS PATCH ----------

class TestOriginsPatch:
    def test_update_origins(self, session, widget_key):
        r = session.patch(
            f"{BASE_URL}/api/app/api-keys/{widget_key['api_key']['id']}/origins",
            json={"allowed_origins": [ALLOWED_ORIGIN, "https://new.example.com"]},
        )
        assert r.status_code == 200
        assert "https://new.example.com" in r.json()["allowed_origins"]

    def test_clear_origins_makes_permissive(self, session, widget_key):
        r = session.patch(
            f"{BASE_URL}/api/app/api-keys/{widget_key['api_key']['id']}/origins",
            json={"allowed_origins": []},
        )
        assert r.status_code == 200
        # Now the key accepts calls without Origin/Referer
        r2 = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": f"Bearer {widget_key['key']}"},
        )
        assert r2.status_code == 200
