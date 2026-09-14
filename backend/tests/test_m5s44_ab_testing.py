"""Backend tests for M5.S4.4 A/B Testing Dashboard (Sprint 3 · Item #3)."""
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
def two_properties(session):
    """Create 2 test properties for A/B comparison."""
    pids = []
    for i in range(2):
        r = session.post(f"{BASE_URL}/api/app/properties", json={
            "title": f"AB Test property #{i+1}",
            "property_type": "appartamento",
            "operation": "sale",
            "price": 180000 + i * 20000,
            "surface_sqm": 70 + i * 5,
            "city": "Milano",
            "province": "MI",
            "status": "active",
        })
        assert r.status_code == 201, r.text
        pids.append(r.json()["id"])
    yield pids
    for pid in pids:
        session.delete(f"{BASE_URL}/api/app/properties/{pid}")


class TestAgencyOverview:
    def test_overview_returns_metrics(self, session):
        r = session.get(f"{BASE_URL}/api/app/analytics/agency/overview?days_lookback=30")
        assert r.status_code == 200
        data = r.json()
        assert data["days_lookback"] == 30
        assert "properties" in data
        assert "total" in data["properties"]
        assert "leads" in data
        assert "publishing_recent" in data
        assert "top_views" in data

    def test_overview_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/app/analytics/agency/overview")
        assert r.status_code in (401, 403)


class TestABTest:
    def test_ab_test_needs_at_least_2_ids(self, session, two_properties):
        r = session.post(f"{BASE_URL}/api/app/analytics/ab-test", json={
            "property_ids": [two_properties[0]],
        })
        assert r.status_code == 422

    def test_ab_test_needs_at_most_6_ids(self, session, two_properties):
        r = session.post(f"{BASE_URL}/api/app/analytics/ab-test", json={
            "property_ids": [f"fake-{i}" for i in range(7)],
        })
        assert r.status_code == 422

    def test_ab_test_returns_comparison(self, session, two_properties):
        r = session.post(f"{BASE_URL}/api/app/analytics/ab-test", json={
            "property_ids": two_properties,
            "days_lookback": 30,
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["compared"] == 2
        assert data["days_lookback"] == 30
        assert "winner_id" in data
        assert data["winner_id"] in two_properties
        assert len(data["items"]) == 2
        for it in data["items"]:
            assert "views_total" in it
            assert "leads_total" in it
            assert "conversion_rate" in it
            assert "delta_views_vs_avg" in it
            assert "delta_leads_vs_avg" in it
            assert "publishing" in it

    def test_ab_test_ignores_other_agency_ids(self, session, two_properties):
        """Property IDs not owned by caller are silently dropped."""
        r = session.post(f"{BASE_URL}/api/app/analytics/ab-test", json={
            "property_ids": [*two_properties, "not-my-property-uuid"],
        })
        assert r.status_code == 200
        assert r.json()["compared"] == 2  # unowned dropped

    def test_ab_test_requires_2_owned_min(self, session):
        r = session.post(f"{BASE_URL}/api/app/analytics/ab-test", json={
            "property_ids": ["fake-uuid-1", "fake-uuid-2", "fake-uuid-3"],
        })
        # None owned → fewer than 2 → 422
        assert r.status_code == 422
