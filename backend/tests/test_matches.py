"""Backend tests for M2.S4 (D-025): Matching Engine + Lead Scoring AI."""
import os
import sys
import pytest
import requests

# Add backend root to import path for the matching algorithm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.immoweb.matching import compute_match, is_searcher, W  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]

# Known canonical seed data (from iteration_2 context)
MARIO_SELLER_ID = "ded16e9d-3e10-4c2a-8373-2601c8573787"
ANDREA_BUYER_ID = "d38dc20e-a6fa-4423-bd89-b43af958335d"
ROMA_FLAT_ID = "3b81db11-2988-47a7-ae26-f4396913c3a7"


# ---------- compute_match unit tests (pure, no API) ----------

class TestComputeMatchUnit:
    def test_weights_sum_to_100(self):
        assert sum(W.values()) == 100

    def test_perfect_match_yields_100(self):
        prop = {
            "operation": "sale", "property_type": "flat", "city": "Roma", "zone": "Centro",
            "price": 300000, "surface_sqm": 90, "rooms": 4, "bedrooms": 2, "bathrooms": 2,
            "condition": "good", "floor": 2, "total_floors": 5,
            "energy": {"energy_class": "B"}, "features": {"balcone": True, "ascensore": True},
            "photos": [{"url": "x", "is_cover": True}], "virtual_tour_url": "http://x",
        }
        client = {
            "client_type": "buyer", "preferences": {
                "operation": "sale", "property_types": ["flat"], "cities": ["Roma"], "zones": ["Centro"],
                "price_min": 200000, "price_max": 350000, "surface_min": 60, "surface_max": 120,
                "rooms_min": 3, "rooms_max": 5, "bedrooms_min": 2, "bathrooms_min": 1,
                "conditions": ["good", "new"], "floor_preferences": ["intermedi"],
                "energy_min_class": "C", "must_have_features": ["balcone"],
                "needs_photos": True, "needs_virtual_tour": True,
            }
        }
        m = compute_match(prop, client)
        assert m["score"] == 100, m
        assert m["is_compatible"] is True
        assert m["missing"] == []

    def test_operation_mismatch_returns_zero(self):
        prop = {"operation": "rent", "property_type": "flat", "city": "Roma"}
        client = {"client_type": "buyer", "preferences": {"operation": "sale"}}
        m = compute_match(prop, client)
        assert m["score"] == 0
        assert m["is_compatible"] is False
        assert any("operation" in x for x in m["missing"])

    def test_city_mismatch_lowers_score(self):
        prop = {
            "operation": "sale", "property_type": "flat", "city": "Milano",
            "price": 300000, "surface_sqm": 90, "rooms": 4, "bedrooms": 2, "bathrooms": 2,
            "condition": "good", "floor": 2, "total_floors": 5,
            "energy": {"energy_class": "B"}, "features": {"balcone": True},
            "photos": [{"url": "x", "is_cover": True}], "virtual_tour_url": "http://x",
        }
        client = {
            "client_type": "buyer", "preferences": {
                "operation": "sale", "property_types": ["flat"], "cities": ["Roma"],
                "price_min": 200000, "price_max": 350000, "surface_min": 60, "surface_max": 120,
                "rooms_min": 3, "rooms_max": 5, "bedrooms_min": 2, "bathrooms_min": 1,
                "conditions": ["good"], "energy_min_class": "C", "must_have_features": ["balcone"],
                "needs_photos": True, "needs_virtual_tour": True,
            }
        }
        m = compute_match(prop, client)
        # City weight = 12 → 100 - 12 = 88, but zone also constraints; ~ 83-88
        assert 75 <= m["score"] < 95
        assert "city" in m["missing"]

    def test_score_never_exceeds_100(self):
        prop = {"operation": "sale", "property_type": "flat", "city": "Roma"}
        client = {"client_type": "buyer", "preferences": {"operation": "sale"}}
        m = compute_match(prop, client)
        assert 0 <= m["score"] <= 100

    def test_is_searcher(self):
        assert is_searcher({"client_type": "buyer"}) is True
        assert is_searcher({"client_type": "tenant"}) is True
        assert is_searcher({"client_type": "investor"}) is True
        assert is_searcher({"client_type": "seller"}) is False
        assert is_searcher({"client_type": "landlord"}) is False


# ---------- API tests ----------

@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


class TestMatchesAPI:
    def test_list_matches_default(self, session):
        r = session.get(f"{BASE_URL}/api/app/matches?min_score=50")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data and "total" in data and "min_score" in data
        assert data["min_score"] == 50
        # sorted desc
        scores = [it["score"] for it in data["items"]]
        assert scores == sorted(scores, reverse=True)
        # only searcher clients in items
        for it in data["items"]:
            assert it["client"]["client_type"] in ("buyer", "tenant", "investor")
            assert it["score"] >= 50

    def test_min_score_filter_narrows_results(self, session):
        r_low = session.get(f"{BASE_URL}/api/app/matches?min_score=40").json()
        r_high = session.get(f"{BASE_URL}/api/app/matches?min_score=85").json()
        assert r_high["total"] <= r_low["total"]
        for it in r_high["items"]:
            assert it["score"] >= 85

    def test_matches_for_property_ok(self, session):
        r = session.get(f"{BASE_URL}/api/app/matches/property/{ROMA_FLAT_ID}?min_score=0")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["property"]["id"] == ROMA_FLAT_ID
        assert "items" in data
        # All items must be searchers
        for it in data["items"]:
            assert it["client"]["client_type"] in ("buyer", "tenant", "investor")

    def test_matches_for_property_404(self, session):
        r = session.get(f"{BASE_URL}/api/app/matches/property/does-not-exist-xyz")
        assert r.status_code == 404

    def test_matches_for_client_buyer(self, session):
        r = session.get(f"{BASE_URL}/api/app/matches/client/{ANDREA_BUYER_ID}?min_score=0")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["client"]["id"] == ANDREA_BUYER_ID
        assert "items" in data
        # should NOT include the info flag
        assert data.get("info") != "client_type_does_not_search"

    def test_matches_for_client_seller_returns_info(self, session):
        r = session.get(f"{BASE_URL}/api/app/matches/client/{MARIO_SELLER_ID}")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("info") == "client_type_does_not_search"
        assert data["items"] == []

    def test_matches_for_client_404(self, session):
        r = session.get(f"{BASE_URL}/api/app/matches/client/does-not-exist-xyz")
        assert r.status_code == 404

    def test_matches_canonical_perfect_pair(self, session):
        """Andrea buyer ↔ Roma flat should be a known high-score pair (deterministic ~100)."""
        r = session.get(f"{BASE_URL}/api/app/matches/property/{ROMA_FLAT_ID}?min_score=0&limit=100")
        items = r.json()["items"]
        andrea = [it for it in items if it["client"]["id"] == ANDREA_BUYER_ID]
        assert andrea, f"Andrea not in matches for Roma flat. items={[it['client']['id'] for it in items]}"
        assert andrea[0]["score"] >= 90, f"Expected ≥90, got {andrea[0]['score']}"


class TestLeadScoreAPI:
    def test_lead_score_404_unknown_property(self, session):
        r = session.post(f"{BASE_URL}/api/app/matches/lead-score?property_id=nope&client_id={ANDREA_BUYER_ID}")
        assert r.status_code == 404

    def test_lead_score_404_unknown_client(self, session):
        r = session.post(f"{BASE_URL}/api/app/matches/lead-score?property_id={ROMA_FLAT_ID}&client_id=nope")
        assert r.status_code == 404

    def test_lead_score_canonical_pair(self, session):
        """One real AI call. Validates schema and italian engine response."""
        r = session.post(
            f"{BASE_URL}/api/app/matches/lead-score?property_id={ROMA_FLAT_ID}&client_id={ANDREA_BUYER_ID}",
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Top-level structure
        assert "property" in data and data["property"]["id"] == ROMA_FLAT_ID
        assert "client" in data and data["client"]["id"] == ANDREA_BUYER_ID
        assert "match" in data and "score" in data["match"] and "breakdown" in data["match"]
        # Lead score structure
        ls = data["lead_score"]
        assert isinstance(ls["score"], int) and 0 <= ls["score"] <= 100
        assert ls["temperature"] in ("freddo", "tiepido", "caldo", "rovente")
        assert isinstance(ls["reasons"], list) and len(ls["reasons"]) >= 1
        assert isinstance(ls["action_hint"], str) and len(ls["action_hint"]) > 0
        assert ls["engine"] in ("gemini-3-flash", "rule-based")
