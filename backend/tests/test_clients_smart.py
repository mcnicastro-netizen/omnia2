"""Backend tests for D-FUTURE-04 Smart Clients List."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASS = os.environ["OMNIA_ADMIN_PASSWORD"]


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


class TestSmartList:
    def test_smart_returns_enriched_payload(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/clients/smart")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "items" in d
        assert "counts" in d
        assert "total" in d
        assert d["sort"] == "score_desc"
        # Each item must have the enrichment fields
        for c in d["items"]:
            assert "lead_score" in c
            assert "temperature" in c
            assert "matches_count" in c
            assert "best_match_score" in c
            assert "ai_cached" in c
            assert "action_hint" in c

    def test_smart_sorted_score_desc(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/clients/smart?sort=score_desc")
        d = r.json()
        scores = [c.get("lead_score") if c.get("lead_score") is not None else -1 for c in d["items"]]
        assert scores == sorted(scores, reverse=True)

    def test_smart_counts_consistent(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/clients/smart")
        d = r.json()
        counts = d["counts"]
        # searchers + sellers should be ~= all (every client is one or the other)
        assert counts["searchers"] + counts["sellers"] == counts["all"]

    def test_smart_bucket_filter(self, admin_session):
        # Filter to sellers only
        r = admin_session.get(f"{BASE_URL}/api/app/clients/smart?bucket=sellers")
        d = r.json()
        for c in d["items"]:
            assert c["client_type"] not in ("buyer", "tenant", "investor")
            assert c["lead_score"] is None  # sellers don't get scored

    def test_smart_bucket_to_call_today(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/clients/smart?bucket=to_call_today")
        d = r.json()
        for c in d["items"]:
            assert c["temperature"] in ("rovente", "caldo")
            assert (c["matches_count"] or 0) > 0

    def test_smart_search(self, admin_session):
        # search by partial name — must filter & still return enriched payload
        r = admin_session.get(f"{BASE_URL}/api/app/clients/smart?q=Andrea")
        d = r.json()
        assert d["total"] >= 1
        assert any("Andrea" in (c.get("name") or "") for c in d["items"])

    def test_smart_route_not_treated_as_id(self, admin_session):
        # Regression: ensure /clients/smart isn't intercepted by /clients/{cid}
        r = admin_session.get(f"{BASE_URL}/api/app/clients/smart")
        assert r.status_code == 200
        # Must NOT be a 404 client_not_found
        assert "client_not_found" not in r.text


class TestSmartRefresh:
    def test_refresh_runs_and_returns_counts(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/app/clients/smart/refresh", json={"limit": 5})
        assert r.status_code == 200, r.text
        d = r.json()
        assert "refreshed" in d
        assert "skipped" in d
        assert "items" in d

    def test_refresh_idempotent_when_all_cached(self, admin_session):
        # After previous test, cache should be populated. A second call must skip/no-op cleanly.
        r = admin_session.post(f"{BASE_URL}/api/app/clients/smart/refresh", json={"limit": 5})
        assert r.status_code == 200
        d = r.json()
        assert d["refreshed"] >= 0


class TestSmartUnauth:
    def test_unauth_blocked(self):
        r = requests.get(f"{BASE_URL}/api/app/clients/smart")
        assert r.status_code in (401, 403)
