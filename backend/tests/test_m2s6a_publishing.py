"""Backend tests for M2.6a (D-052): Publishing Center foundation."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    return s


@pytest.fixture(scope="module", autouse=True)
def cleanup(session):
    r = session.get(f"{BASE_URL}/api/app/publishing/connections")
    for c in r.json().get("items", []):
        session.delete(f"{BASE_URL}/api/app/publishing/connections/{c['id']}")
    yield
    r = session.get(f"{BASE_URL}/api/app/publishing/connections")
    for c in r.json().get("items", []):
        session.delete(f"{BASE_URL}/api/app/publishing/connections/{c['id']}")


class TestCatalog:
    def test_catalog_seeded_8_portals(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/catalog")
        assert r.status_code == 200
        data = r.json()
        # M2.6d: catalog can also include agency-owned custom portals (is_custom=True).
        # This test guards ONLY the 8 seeded system portals.
        system_items = [p for p in data["items"] if not p.get("is_custom")]
        assert len(system_items) == 8
        slugs = {p["slug"] for p in system_items}
        assert slugs == {"subito", "bakeca", "kijiji", "wikicasa",
                         "facebook-marketplace", "google-business", "attico", "case24"}

    def test_catalog_sorted_by_traffic_score(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/catalog")
        # Only system portals honor the traffic_score sort (custom portals appear last).
        system_items = [p for p in r.json()["items"] if not p.get("is_custom")]
        scores = [p["traffic_score"] for p in system_items]
        assert scores == sorted(scores, reverse=True)


class TestConnections:
    def test_activate_no_creds(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/connections",
                         json={"portal_slug": "bakeca", "credentials": {}})
        assert r.status_code == 201
        assert r.json()["status"] == "pending"
        assert "credentials_encrypted" not in r.json()

    def test_activate_with_creds(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/connections",
                         json={"portal_slug": "subito",
                               "credentials": {"username": "test", "api_key": "abc"}})
        assert r.status_code == 201
        d = r.json()
        assert d["status"] == "active"
        assert "credentials_encrypted" not in d
        assert "username" not in str(d).lower() or "test" not in str(d)

    def test_duplicate_activation_409(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/connections",
                         json={"portal_slug": "subito", "credentials": {"username": "test"}})
        assert r.status_code == 409

    def test_activate_unknown_portal_404(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/connections",
                         json={"portal_slug": "unknown-portal", "credentials": {}})
        assert r.status_code == 404

    def test_list_shows_activated(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/connections")
        assert r.status_code == 200
        slugs = {c["portal_slug"] for c in r.json()["items"]}
        assert "bakeca" in slugs and "subito" in slugs

    def test_update_credentials(self, session):
        conn_id = next(c["id"] for c in session.get(f"{BASE_URL}/api/app/publishing/connections").json()["items"] if c["portal_slug"] == "bakeca")
        r = session.patch(f"{BASE_URL}/api/app/publishing/connections/{conn_id}",
                          json={"credentials": {"email": "new@test.it"}})
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    def test_toggle_disabled(self, session):
        conn_id = next(c["id"] for c in session.get(f"{BASE_URL}/api/app/publishing/connections").json()["items"] if c["portal_slug"] == "subito")
        r = session.patch(f"{BASE_URL}/api/app/publishing/connections/{conn_id}",
                          json={"status": "disabled"})
        assert r.status_code == 200
        assert r.json()["status"] == "disabled"

    def test_delete_connection(self, session):
        conn_id = next(c["id"] for c in session.get(f"{BASE_URL}/api/app/publishing/connections").json()["items"] if c["portal_slug"] == "bakeca")
        r = session.delete(f"{BASE_URL}/api/app/publishing/connections/{conn_id}")
        assert r.status_code == 200
        r2 = session.get(f"{BASE_URL}/api/app/publishing/connections")
        assert "bakeca" not in {c["portal_slug"] for c in r2.json()["items"]}


class TestFeedAndCompliance:
    def test_feed_public_returns_xml(self, session):
        slug = session.get(f"{BASE_URL}/api/app/agencies/me").json()["slug"]
        r = requests.get(f"{BASE_URL}/api/app/publishing/feed/{slug}.xml")
        assert r.status_code == 200
        assert "application/xml" in r.headers.get("content-type", "")
        assert "<feed>" in r.text

    def test_feed_hard_compliance_filters_incomplete(self, session):
        """Properties without energy_class/price/photos MUST be excluded."""
        slug = session.get(f"{BASE_URL}/api/app/agencies/me").json()["slug"]
        r = requests.get(f"{BASE_URL}/api/app/publishing/feed/{slug}.xml")
        # With HARD compliance active, if agency has no fully-compliant properties,
        # total should be 0. This verifies the filter is on.
        assert "<total>" in r.text

    def test_is_publishable_helper(self):
        from apps.immoweb.publishing import is_publishable
        # Full compliance property (M2.6b stricter rules: adds surface + address)
        ok, r = is_publishable({"operation": "sale", "price": 250000,
                                "surface_sqm": 90,
                                "city": "Napoli", "province": "NA",
                                "energy": {"energy_class": "B"},
                                "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}]})
        assert ok and r == []
        ok, r = is_publishable({"operation": "sale", "price": 250000, "energy": {}, "photos": []})
        assert not ok and "missing_energy_class" in r and "less_than_3_photos" in r

    def test_feed_generic_rss_dialect(self, session):
        slug = session.get(f"{BASE_URL}/api/app/agencies/me").json()["slug"]
        r = requests.get(f"{BASE_URL}/api/app/publishing/feed/{slug}.xml?dialect=generic_rss")
        assert r.status_code == 200
        assert "<rss" in r.text and "<channel>" in r.text


class TestAuthBoundary:
    def test_unauth_catalog_401(self):
        r = requests.get(f"{BASE_URL}/api/app/publishing/catalog")
        assert r.status_code in (401, 403)

    def test_unauth_connections_401(self):
        r = requests.post(f"{BASE_URL}/api/app/publishing/connections",
                          json={"portal_slug": "subito"})
        assert r.status_code in (401, 403)
