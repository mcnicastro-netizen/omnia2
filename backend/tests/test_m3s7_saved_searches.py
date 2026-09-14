"""OMNIA M3.S7 — Saved Searches & Alert Email Matching tests."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]
B2C_PASSWORD = "TestB2C2026!"
TS = int(time.time())
B2C_EMAIL = f"b2csavedtest_{TS}@example.com"


# ----------------------------- Fixtures -----------------------------

@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def b2c_session():
    s = requests.Session()
    payload = {
        "email": B2C_EMAIL,
        "password": B2C_PASSWORD,
        "name": "B2C SavedTest",
        "lang": "it",
        "gdpr_consent": True,
        "intents": ["get_alerts"],
    }
    r = s.post(f"{API}/cloud/auth/register", json=payload)
    assert r.status_code in (200, 201), f"register failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def b2c_user_id(b2c_session):
    r = b2c_session.get(f"{API}/cloud/auth/me")
    if r.status_code != 200:
        # try alt endpoint
        r = b2c_session.get(f"{API}/auth/me")
    assert r.status_code == 200, f"me failed: {r.status_code} {r.text}"
    return r.json().get("id") or r.json().get("user", {}).get("id")


# ----------------------------- AUTH -----------------------------

class TestAuthGuards:
    def test_no_cookie_returns_401(self):
        r = requests.get(f"{API}/cloud/me/saved-searches")
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_admin_account_returns_403(self, admin_session):
        r = admin_session.get(f"{API}/cloud/me/saved-searches")
        assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text}"
        body = r.json()
        assert "b2c_account_required" in str(body.get("detail", ""))


# ----------------------------- CRUD -----------------------------

class TestSavedSearchCRUD:
    def test_01_create(self, b2c_session):
        payload = {
            "name": "Test Roma alerts",
            "filters": {"city": "Roma", "operation": "sale", "price_max": 300000},
            "frequency": "daily",
        }
        r = b2c_session.post(f"{API}/cloud/me/saved-searches", json=payload)
        assert r.status_code == 201, f"create failed: {r.status_code} {r.text}"
        d = r.json()
        assert "id" in d
        assert d["name"] == "Test Roma alerts"
        assert d["frequency"] == "daily"
        assert d["is_active"] is True
        assert d["filters"]["city"] == "Roma"
        pytest.created_id = d["id"]

    def test_02_list_only_my(self, b2c_session):
        r = b2c_session.get(f"{API}/cloud/me/saved-searches")
        assert r.status_code == 200
        d = r.json()
        assert "items" in d
        ids = [s["id"] for s in d["items"]]
        assert pytest.created_id in ids

    def test_03_patch_frequency(self, b2c_session):
        sid = pytest.created_id
        r = b2c_session.patch(f"{API}/cloud/me/saved-searches/{sid}", json={"frequency": "instant"})
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        assert r.json()["frequency"] == "instant"

    def test_04_patch_inactive(self, b2c_session):
        sid = pytest.created_id
        r = b2c_session.patch(f"{API}/cloud/me/saved-searches/{sid}", json={"is_active": False})
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_05_run_preview(self, b2c_session):
        sid = pytest.created_id
        r = b2c_session.post(f"{API}/cloud/me/saved-searches/{sid}/run")
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        d = r.json()
        assert "matches" in d
        assert isinstance(d["matches"], list)
        assert d["saved_search_id"] == sid

    def test_06_limit_10(self, b2c_session):
        # We already created 1; create 9 more then expect 11th to fail
        created = []
        # Check how many exist now
        existing = b2c_session.get(f"{API}/cloud/me/saved-searches").json()["items"]
        to_make = 10 - len(existing)
        for i in range(to_make):
            r = b2c_session.post(f"{API}/cloud/me/saved-searches", json={
                "name": f"limit-test-{i}",
                "filters": {"city": "Milano"},
                "frequency": "daily",
            })
            assert r.status_code == 201, f"fill #{i}: {r.status_code} {r.text}"
            created.append(r.json()["id"])
        # 11th must fail
        r = b2c_session.post(f"{API}/cloud/me/saved-searches", json={
            "name": "overflow", "filters": {"city": "Milano"}, "frequency": "daily",
        })
        assert r.status_code == 409, f"expected 409, got {r.status_code} {r.text}"
        assert "saved_searches_limit_reached" in str(r.json().get("detail", ""))

    def test_07_delete_all(self, b2c_session):
        items = b2c_session.get(f"{API}/cloud/me/saved-searches").json()["items"]
        for s in items:
            r = b2c_session.delete(f"{API}/cloud/me/saved-searches/{s['id']}")
            assert r.status_code == 204, f"delete {s['id']}: {r.status_code} {r.text}"
        # verify list empty
        r = b2c_session.get(f"{API}/cloud/me/saved-searches")
        assert r.json()["total"] == 0


# ----------------------------- CRON -----------------------------

class TestCron:
    def test_non_admin_forbidden(self, b2c_session):
        r = b2c_session.post(f"{API}/app/cron/saved-searches/run-all")
        assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text}"

    def test_no_auth_forbidden(self):
        r = requests.post(f"{API}/app/cron/saved-searches/run-all")
        assert r.status_code in (401, 403)

    def test_admin_ok(self, admin_session):
        r = admin_session.post(f"{API}/app/cron/saved-searches/run-all")
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        d = r.json()
        assert d.get("ok") is True
        assert "searches_checked" in d
        assert "emails_sent" in d
        assert "total_matches" in d
        assert "run_at" in d
