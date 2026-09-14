"""Backend tests for M2.5.2 (D-041/D-046): API Gateway + API Keys + credits.

Covers:
- Key issuance (management via JWT) + one-time plaintext exposure
- Auth via Bearer on /api/v1/*
- Credit debit on success, no debit on failure, log rows
- partner_id preserved on log (for D-046 rev-share tracking)
- Revocation cuts access immediately
- Insufficient credits → 402
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


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert r.status_code == 200, r.text
    return s


def _revoke_all_keys(session):
    r = session.get(f"{BASE_URL}/api/app/api-keys")
    if r.status_code == 200:
        for k in r.json().get("items", []):
            if k.get("name", "").startswith("TEST_"):
                session.post(f"{BASE_URL}/api/app/api-keys/{k['id']}/revoke")


@pytest.fixture(scope="module", autouse=True)
def cleanup(session):
    _revoke_all_keys(session)
    yield
    _revoke_all_keys(session)


@pytest.fixture(scope="module")
def issued(session):
    """Issue a fresh test key with 20 credits and a partner_id."""
    payload = {
        "name": f"TEST_Key_{uuid.uuid4().hex[:6]}",
        "initial_credits": 20,
        "partner_id": "webagency_TEST_001",
    }
    r = session.post(f"{BASE_URL}/api/app/api-keys", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["key"].startswith("omk_live_")
    assert data["api_key"]["credits_balance"] == 20
    assert data["api_key"]["partner_id"] == "webagency_TEST_001"
    return data


# ---------- ISSUANCE ----------

class TestIssuance:
    def test_key_plaintext_shape(self, issued):
        k = issued["key"]
        assert k.startswith("omk_live_")
        assert len(k) >= len("omk_live_") + 10
        # prefix is first 12 chars
        assert issued["api_key"]["key_prefix"] == k[:12]

    def test_hash_never_returned(self, issued):
        assert "key_hash" not in issued["api_key"]

    def test_list_hides_hash(self, session):
        r = session.get(f"{BASE_URL}/api/app/api-keys")
        assert r.status_code == 200
        for k in r.json()["items"]:
            assert "key_hash" not in k


# ---------- V1 AUTH ----------

class TestV1Auth:
    def test_health_public(self):
        r = requests.get(f"{BASE_URL}/api/v1/health")
        assert r.status_code == 200
        assert r.json()["credit_costs"]["valuator"] == 5

    def test_me_requires_key(self):
        r = requests.get(f"{BASE_URL}/api/v1/me")
        assert r.status_code == 401

    def test_me_rejects_bad_prefix(self):
        r = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": "Bearer sk_stripe_style"},
        )
        assert r.status_code == 401

    def test_me_rejects_unknown_key(self):
        r = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": "Bearer omk_live_unknownXXX123"},
        )
        assert r.status_code == 401

    def test_me_with_valid_key(self, issued):
        r = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": f"Bearer {issued['key']}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["credits_balance"] == 20
        assert data["partner_id"] == "webagency_TEST_001"


# ---------- CREDIT DEBIT ----------

class TestCredits:
    def test_mortgages_charges_1(self, session, issued):
        # Refresh balance from server
        r0 = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": f"Bearer {issued['key']}"},
        )
        before = r0.json()["credits_balance"]

        r = requests.post(
            f"{BASE_URL}/api/v1/mortgages/compare",
            headers={"Authorization": f"Bearer {issued['key']}"},
            json={
                "property_price": 200000,
                "down_payment": 40000,
                "duration_years": 20,
                "rate_type": "fisso",
                "first_home": True,
                "under_36": False,
                "monthly_income": 2500,
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["credits_charged"] == 1

        r1 = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": f"Bearer {issued['key']}"},
        )
        after = r1.json()["credits_balance"]
        assert after == before - 1

    def test_valuator_charges_5(self, issued):
        r = requests.post(
            f"{BASE_URL}/api/v1/valuator",
            headers={"Authorization": f"Bearer {issued['key']}"},
            json={
                "city": "Roma",
                "surface_sqm": 90,
                "property_type": "appartamento",
                "condition": "buono",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["credits_charged"] == 5
        assert "estimated_value" in r.json()["data"]

    def test_usage_log_records_partner_id(self, session, issued):
        r = session.get(
            f"{BASE_URL}/api/app/api-keys/{issued['api_key']['id']}/usage?limit=10"
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 1
        for it in items:
            assert it["partner_id"] == "webagency_TEST_001"


# ---------- INSUFFICIENT CREDITS ----------

class TestInsufficient:
    def test_402_when_low(self, session, issued):
        # Drain balance to 2 (below valuator cost of 5)
        r = session.post(
            f"{BASE_URL}/api/app/api-keys/{issued['api_key']['id']}/credits",
            json={"delta": -100, "reason": "test drain"},
        )
        # accept either success (if enough balance) or 400 (guard)
        # then set to a low value via a second adjust to reach exactly 2
        kget = session.get(f"{BASE_URL}/api/app/api-keys")
        cur = next(x for x in kget.json()["items"] if x["id"] == issued["api_key"]["id"])
        current = cur["credits_balance"]
        need = 2 - current
        if need != 0:
            adj = session.post(
                f"{BASE_URL}/api/app/api-keys/{issued['api_key']['id']}/credits",
                json={"delta": need, "reason": "set to 2"},
            )
            assert adj.status_code == 200, adj.text

        # Valuator now insufficient
        r = requests.post(
            f"{BASE_URL}/api/v1/valuator",
            headers={"Authorization": f"Bearer {issued['key']}"},
            json={"city": "Roma", "surface_sqm": 90},
        )
        assert r.status_code == 402
        assert r.json()["detail"] == "insufficient_credits"

    def test_free_endpoint_still_works_when_low(self, issued):
        # /v1/me uses "feed_properties" cost=0, must still work at balance 2
        r = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": f"Bearer {issued['key']}"},
        )
        assert r.status_code == 200


# ---------- REVOKE ----------

class TestRevocation:
    def test_revoke_cuts_access(self, session, issued):
        rv = session.post(
            f"{BASE_URL}/api/app/api-keys/{issued['api_key']['id']}/revoke"
        )
        assert rv.status_code == 200, rv.text

        r = requests.get(
            f"{BASE_URL}/api/v1/me",
            headers={"Authorization": f"Bearer {issued['key']}"},
        )
        assert r.status_code == 403
        assert r.json()["detail"] == "api_key_revoked"


# ---------- AUTH BOUNDARY ----------

class TestBoundary:
    def test_management_requires_jwt(self):
        r = requests.get(f"{BASE_URL}/api/app/api-keys")
        assert r.status_code in (401, 403)
