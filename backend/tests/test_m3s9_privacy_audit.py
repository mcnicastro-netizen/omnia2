"""Backend tests for M3.S9 Privacy Audit 4 livelli (Sprint 3 · Item #1, D-062)."""
import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def test_property(session):
    """Create a fresh property for privacy tests."""
    r = session.post(f"{BASE_URL}/api/app/properties", json={
        "title": "Attico test privacy L4-secrets",
        "property_type": "appartamento",
        "operation": "sale",
        "price": 285000,
        "min_price_negotiable": 260000,
        "surface_sqm": 90,
        "rooms": 4,
        "bathrooms": 2,
        "city": "Milano",
        "province": "MI",
        "postal_code": "20121",
        "address": "Via Segreta 42, int 5",
        "zone": "Brera",
        "floor": 5,
        "energy": {"class": "A", "epgl_kwh_sqm_year": 45.2},
        "owner": {"name": "Cliente Riservato", "phone": "+393401234567"},
        "seller_notes": "vuole vendere entro fine anno per divorzio",
        "commission_pct": 3.0,
        "reference_code": "MI-BRERA-42",
        "privacy_level": "L2",
        "status": "active",
        "visibility": "public",
        "is_listed_on_immobilcloud": True,
    })
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    yield pid
    session.delete(f"{BASE_URL}/api/app/properties/{pid}")


class TestPrivacyModel:
    def test_privacy_level_persists(self, session, test_property):
        r = session.get(f"{BASE_URL}/api/app/properties/{test_property}/privacy")
        assert r.status_code == 200
        data = r.json()
        assert data["privacy_level"] == "L2"


class TestPrivacyChangesAudit:
    def test_change_creates_audit_event(self, session, test_property):
        r = session.patch(f"{BASE_URL}/api/app/properties/{test_property}/privacy",
                          json={"privacy_level": "L3", "reason": "richiesta proprietario"})
        assert r.status_code == 200
        assert r.json()["privacy_level"] == "L3"

        r2 = session.get(f"{BASE_URL}/api/app/properties/{test_property}/privacy")
        events = r2.json()["audit_events"]
        assert len(events) >= 1
        assert events[0]["from_level"] == "L2"
        assert events[0]["to_level"] == "L3"
        assert events[0]["reason"] == "richiesta proprietario"

    def test_same_level_is_idempotent(self, session, test_property):
        r = session.patch(f"{BASE_URL}/api/app/properties/{test_property}/privacy",
                          json={"privacy_level": "L3"})
        assert r.status_code == 200
        assert r.json().get("unchanged") is True

    def test_invalid_level_rejected(self, session, test_property):
        r = session.patch(f"{BASE_URL}/api/app/properties/{test_property}/privacy",
                          json={"privacy_level": "L5"})
        assert r.status_code == 422


class TestPreviewViewLevels:
    def test_l1_hides_sensitive(self, session, test_property):
        r = session.get(f"{BASE_URL}/api/app/properties/{test_property}/privacy/preview?viewer=L1")
        assert r.status_code == 200
        v = r.json()["view"]
        assert "address" not in v or v.get("address") is None
        assert "owner" not in v
        assert "seller_notes" not in v
        assert "min_price_negotiable" not in v
        assert "reference_code" not in v
        # Price rounded (buckets)
        assert v.get("price_is_approximate") is True

    def test_l2_shows_partial(self, session, test_property):
        r = session.get(f"{BASE_URL}/api/app/properties/{test_property}/privacy/preview?viewer=L2")
        v = r.json()["view"]
        assert "address" not in v or v.get("address") is None
        # exact price present
        assert v.get("price") == 285000
        assert "price_is_approximate" not in v
        assert "owner" not in v
        assert "seller_notes" not in v
        assert v.get("postal_code") == "20121"

    def test_l3_shows_address_and_planimetry(self, session, test_property):
        r = session.get(f"{BASE_URL}/api/app/properties/{test_property}/privacy/preview?viewer=L3")
        v = r.json()["view"]
        assert v.get("address") == "Via Segreta 42, int 5"
        assert v.get("reference_code") == "MI-BRERA-42"
        # Still no seller internal data
        assert "owner" not in v
        assert "seller_notes" not in v
        assert "min_price_negotiable" not in v

    def test_l4_shows_everything(self, session, test_property):
        r = session.get(f"{BASE_URL}/api/app/properties/{test_property}/privacy/preview?viewer=L4")
        v = r.json()["view"]
        assert v.get("address") == "Via Segreta 42, int 5"
        assert v.get("owner", {}).get("name") == "Cliente Riservato"
        assert v.get("seller_notes") == "vuole vendere entro fine anno per divorzio"
        assert v.get("min_price_negotiable") == 260000
        assert v.get("commission_pct") == 3.0


class TestPublicPortalGating:
    def test_l1_default_returns_property_without_secrets(self, session, test_property):
        # Reset to L2 to make it visible to anonymous
        session.patch(f"{BASE_URL}/api/app/properties/{test_property}/privacy",
                      json={"privacy_level": "L2"})
        # Anonymous public access (no auth)
        r = requests.get(f"{BASE_URL}/api/cloud/property/{test_property}")
        if r.status_code == 404:
            pytest.skip("Property not visible on public portal (feature-flagged agency)")
        assert r.status_code == 200
        v = r.json()
        assert v.get("_viewer_level") == "L1"
        assert "owner" not in v
        assert "seller_notes" not in v
        assert v.get("address") is None or v.get("address") == ""

    def test_l3_property_hidden_from_l1(self, session, test_property):
        # Set property privacy to L3 (only qualified viewers can see it)
        session.patch(f"{BASE_URL}/api/app/properties/{test_property}/privacy",
                      json={"privacy_level": "L3"})
        r = requests.get(f"{BASE_URL}/api/cloud/property/{test_property}")
        # Anonymous L1 viewer < L3 required → gate returns 404
        assert r.status_code == 404


class TestAuthorization:
    def test_privacy_endpoints_require_auth(self, test_property):
        for path in (
            f"/api/app/properties/{test_property}/privacy",
            f"/api/app/properties/{test_property}/privacy/preview",
        ):
            r = requests.get(f"{BASE_URL}{path}")
            assert r.status_code in (401, 403)
