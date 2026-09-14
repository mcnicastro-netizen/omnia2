"""OMNIA — Tests for M3.S1 ImmobilCloud B2C Auth (cloud_auth.py).

Validates POST /api/cloud/auth/register flow:
  - happy path (creates b2c user, sets cookies)
  - gdpr_consent required (400)
  - intents required (400)
  - duplicate email (409)
  - validation errors (422)
And re-verifies public facets/search endpoints used by Home B2C.
"""
import os
import time
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
CLOUD_API = f"{BASE_URL}/api/cloud"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia_db")


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


@pytest.fixture(scope="module")
def shared_email():
    """Single email reused across happy-path + 409 test."""
    return f"TEST_b2c_{int(time.time())}@omnia.it"


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_users(db):
    """Delete any test user with TEST_b2c_ prefix after the suite runs."""
    yield
    db.users.delete_many({"email": {"$regex": "^test_b2c_.*@omnia.it$", "$options": "i"}})


# ---------- happy path ----------
class TestCloudRegister:
    def test_register_happy_path(self, shared_email, db):
        payload = {
            "email": shared_email,
            "password": "TestB2C2026!",
            "name": "B2C Tester",
            "intents": ["get_alerts"],
            "notification_channels": ["email"],
            "lang": "it",
            "gdpr_consent": True,
        }
        r = requests.post(f"{CLOUD_API}/auth/register", json=payload, timeout=20)
        assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("ok") is True
        user = data.get("user", {})
        assert user.get("email") == shared_email.lower()
        assert user.get("role") == "client"
        assert user.get("account_type") == "b2c"
        assert user.get("intents") == ["get_alerts"]
        assert user.get("notification_channels") == ["email"]

        # cookies set on response
        cookie_names = {c.name for c in r.cookies}
        assert "access_token" in cookie_names, f"Missing access_token cookie. Got: {cookie_names}"
        assert "refresh_token" in cookie_names, f"Missing refresh_token cookie. Got: {cookie_names}"

        # DB persistence
        doc = db.users.find_one({"email": shared_email.lower()})
        assert doc is not None, "user not persisted"
        assert doc.get("account_type") == "b2c"
        assert doc.get("role") == "client"
        assert doc.get("intents") == ["get_alerts"]
        assert doc.get("notification_channels") == ["email"]
        assert doc.get("email_verified") is False
        assert doc.get("agency_ids") == []
        assert "password_hash" in doc and doc["password_hash"].startswith("$2")

    def test_register_missing_gdpr_returns_400(self):
        payload = {
            "email": f"TEST_b2c_nogdpr_{int(time.time())}@omnia.it",
            "password": "TestB2C2026!",
            "name": "No GDPR",
            "intents": ["get_alerts"],
            "notification_channels": ["email"],
            "lang": "it",
            "gdpr_consent": False,
        }
        r = requests.post(f"{CLOUD_API}/auth/register", json=payload, timeout=15)
        assert r.status_code == 400
        assert r.json().get("detail") == "gdpr_consent_required"

    def test_register_empty_intents_returns_400(self):
        payload = {
            "email": f"TEST_b2c_nointent_{int(time.time())}@omnia.it",
            "password": "TestB2C2026!",
            "name": "No Intents",
            "intents": [],
            "notification_channels": ["email"],
            "lang": "it",
            "gdpr_consent": True,
        }
        r = requests.post(f"{CLOUD_API}/auth/register", json=payload, timeout=15)
        assert r.status_code == 400
        assert r.json().get("detail") == "at_least_one_intent_required"

    def test_register_duplicate_email_returns_409(self, shared_email):
        payload = {
            "email": shared_email,
            "password": "TestB2C2026!",
            "name": "Dup",
            "intents": ["get_alerts"],
            "notification_channels": ["email"],
            "lang": "it",
            "gdpr_consent": True,
        }
        r = requests.post(f"{CLOUD_API}/auth/register", json=payload, timeout=15)
        assert r.status_code == 409, f"got {r.status_code}: {r.text}"
        assert r.json().get("detail") == "email_already_registered"

    def test_register_password_too_short_returns_422(self):
        payload = {
            "email": f"TEST_b2c_shortpw_{int(time.time())}@omnia.it",
            "password": "short1",  # < 8
            "name": "ShortPW",
            "intents": ["get_alerts"],
            "notification_channels": ["email"],
            "lang": "it",
            "gdpr_consent": True,
        }
        r = requests.post(f"{CLOUD_API}/auth/register", json=payload, timeout=15)
        assert r.status_code == 422

    def test_register_invalid_email_returns_422(self):
        payload = {
            "email": "not-an-email",
            "password": "TestB2C2026!",
            "name": "BadEmail",
            "intents": ["get_alerts"],
            "notification_channels": ["email"],
            "lang": "it",
            "gdpr_consent": True,
        }
        r = requests.post(f"{CLOUD_API}/auth/register", json=payload, timeout=15)
        assert r.status_code == 422


# ---------- public portal facets/search (B2C Home dependencies) ----------
class TestCloudPublicEndpoints:
    def test_facets_sale_no_auth(self):
        r = requests.get(f"{CLOUD_API}/facets?operation=sale", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, dict)

    def test_search_sale_no_auth(self):
        r = requests.get(f"{CLOUD_API}/search?operation=sale&page_size=6&sort=recent", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        # total field may be named "total" or similar — assert it's a known shape
        assert any(k in data for k in ("total", "total_count", "count"))
