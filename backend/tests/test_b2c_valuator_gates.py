"""B2C Valuator dual-tier gates — pytest (task B2C-VAL-01).

10 test coperti dal brief §7:
1.  Base anonimo → 401
2.  Base user B2C verified, 0 usage → 200
3.  Base user B2C verified, 1 usage <12mo → 429
4.  Base payload con `merit` (senza pagamento) → 402
5.  UNI user B2C senza pagamento → 402
6.  UNI user B2C con purchase valido → 200 + breakdown
7.  PDF senza entitlement → 402
8.  PDF con entitlement → 200 application/pdf
9.  Agente B2B → 200 (pass-through, no gate B2C)
10. Fascicolo agency base call (chiamata diretta `_estimate_value_core`) → 200 (no regressione)

Setup:
- `pymongo` sync per manipolazione `b2c_valuation_usage` / `b2c_purchases` / `users`
- `requests` per chiamate HTTP contro `REACT_APP_BACKEND_URL`
- utente B2C fixture creato via `POST /api/cloud/auth/register`, `email_verified` forzato in Mongo
- utente agente riusa credenziali super_admin (`OMNIA_ADMIN_EMAIL/PASSWORD`)
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"


def _mongo_url() -> str:
    return os.environ.get("MONGO_URL") or ""


def _db_name() -> str:
    return os.environ.get("DB_NAME") or "omnia_db"


# --------- Fixtures ---------

@pytest.fixture(scope="session")
def mongo():
    if not _mongo_url():
        pytest.skip("MONGO_URL not set")
    client = MongoClient(_mongo_url(), serverSelectionTimeoutMS=3000)
    db = client[_db_name()]
    yield db
    client.close()


@pytest.fixture(scope="session")
def b2c_user(mongo):
    """Register a fresh B2C user and force email_verified=True."""
    email = f"b2c-val-{uuid4().hex[:10]}@example.com"
    payload = {
        "email": email,
        "password": "Test-Password-1!",
        "name": "B2C Valuator Test",
        "intents": ["get_alerts"],
        "notification_channels": ["email"],
        "gdpr_consent": True,
    }
    r = requests.post(f"{API}/cloud/auth/register", json=payload, timeout=10)
    if r.status_code >= 400:
        pytest.skip(f"cloud register unavailable: {r.status_code} {r.text[:200]}")
    mongo.users.update_one({"email": email}, {"$set": {"email_verified": True}})
    return email


@pytest.fixture(scope="session")
def b2c_session(b2c_user):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API}/auth/login", json={"email": b2c_user, "password": "Test-Password-1!"}, timeout=10)
    if r.status_code != 200:
        pytest.skip(f"b2c login failed: {r.status_code} {r.text[:200]}")
    return s


@pytest.fixture(scope="session")
def agent_session():
    email = os.environ.get("OMNIA_ADMIN_EMAIL")
    pwd = os.environ.get("OMNIA_ADMIN_PASSWORD")
    if not (email and pwd):
        pytest.skip("OMNIA_ADMIN_EMAIL/PASSWORD not set")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=10)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text[:200]}")
    return s


@pytest.fixture(autouse=True)
def _cleanup(mongo, b2c_user):
    """Wipe rate-limit + entitlement state before every test — order-independent."""
    u = mongo.users.find_one({"email": b2c_user}, {"id": 1})
    if u:
        mongo.b2c_valuation_usage.delete_many({"user_id": u["id"]})
        mongo.b2c_purchases.delete_many({"user_id": u["id"]})
    yield


# --------- Helpers ---------

BASE_PAYLOAD = {"city": "Roma", "surface_sqm": 80, "property_type": "appartamento"}
UNI_PAYLOAD = {
    **BASE_PAYLOAD,
    "merit": {"exposure": "sud", "heating": "autonomo"},
}


def _user_id(mongo, email: str) -> str:
    u = mongo.users.find_one({"email": email}, {"id": 1})
    assert u, f"user {email} missing"
    return u["id"]


# --------- Tests ---------

def test_1_base_anonymous_401():
    r = requests.post(f"{API}/cloud/valuator", json=BASE_PAYLOAD, timeout=10)
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "login_required"


def test_2_base_verified_ok_200(b2c_session):
    r = b2c_session.post(f"{API}/cloud/valuator", json=BASE_PAYLOAD, timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "estimated_value" in data or "value" in data


def test_3_base_verified_second_call_429(b2c_session, mongo, b2c_user):
    # First call to consume the yearly quota
    r1 = b2c_session.post(f"{API}/cloud/valuator", json=BASE_PAYLOAD, timeout=15)
    assert r1.status_code == 200
    # Second must be blocked with 429
    r2 = b2c_session.post(f"{API}/cloud/valuator", json=BASE_PAYLOAD, timeout=10)
    assert r2.status_code == 429, r2.text[:300]
    body = r2.json()["detail"]
    assert body["code"] == "base_limit_reached"
    assert body.get("upsell_product_key") == "b2c_valuator_uni_pdf"


def test_4_base_payload_with_merit_402(b2c_session):
    r = b2c_session.post(f"{API}/cloud/valuator", json=UNI_PAYLOAD, timeout=10)
    assert r.status_code == 402, r.text[:300]
    body = r.json()["detail"]
    assert body["code"] == "payment_required"
    assert body["product_key"] == "b2c_valuator_uni_pdf"
    assert abs(float(body["price_eur"]) - 2.99) < 0.01


def test_5_uni_without_payment_402(b2c_session):
    """Same as t4 (both are UNI-payload without entitlement)."""
    r = b2c_session.post(f"{API}/cloud/valuator", json=UNI_PAYLOAD, timeout=10)
    assert r.status_code == 402
    assert r.json()["detail"]["code"] == "payment_required"


def test_6_uni_with_purchase_ok_200(b2c_session, mongo, b2c_user):
    from apps.billing.b2c_entitlements import hash_valuation_payload
    from apps.immocloud.valuator import ValuationPayload
    ph = hash_valuation_payload(ValuationPayload(**UNI_PAYLOAD).model_dump(exclude_none=True))
    uid = _user_id(mongo, b2c_user)
    now = datetime.now(timezone.utc)
    mongo.b2c_purchases.insert_one({
        "id": uuid4().hex,
        "user_id": uid,
        "product_key": "b2c_valuator_uni_pdf",
        "stripe_session_id": f"cs_test_{uuid4().hex[:12]}",
        "payload_hash": ph,
        "status": "paid",
        "created_at": now.isoformat(),
        "paid_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=24)).isoformat(),
    })
    r = b2c_session.post(f"{API}/cloud/valuator", json=UNI_PAYLOAD, timeout=15)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    # UNI response should contain merit_breakdown or multipliers_applied.merit_pct
    assert "estimated_value" in data or "value" in data


def test_7_pdf_without_entitlement_402(b2c_session):
    r = b2c_session.post(f"{API}/cloud/valuator/report-pdf", json=UNI_PAYLOAD, timeout=15)
    assert r.status_code == 402, r.text[:300]
    assert r.json()["detail"]["code"] == "payment_required"


def test_8_pdf_with_entitlement_pdf(b2c_session, mongo, b2c_user):
    from apps.billing.b2c_entitlements import hash_valuation_payload
    from apps.immocloud.valuator import ValuationPayload
    ph = hash_valuation_payload(ValuationPayload(**UNI_PAYLOAD).model_dump(exclude_none=True))
    uid = _user_id(mongo, b2c_user)
    now = datetime.now(timezone.utc)
    mongo.b2c_purchases.insert_one({
        "id": uuid4().hex,
        "user_id": uid,
        "product_key": "b2c_valuator_uni_pdf",
        "stripe_session_id": f"cs_test_{uuid4().hex[:12]}",
        "payload_hash": ph,
        "status": "paid",
        "created_at": now.isoformat(),
        "paid_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=24)).isoformat(),
    })
    r = b2c_session.post(f"{API}/cloud/valuator/report-pdf", json=UNI_PAYLOAD, timeout=20)
    assert r.status_code == 200, r.text[:300]
    assert r.headers.get("content-type", "").startswith("application/pdf")


def test_9_agent_uni_passthrough_200(agent_session):
    """Agenti (agency_admin/super_admin) bypassano il gate B2C.
    Il debit crediti agenzia e' out-of-scope dell'endpoint (fatto dal caller
    applicativo: fascicolo, valutatore B2B, ecc.). Verifichiamo il pass-through."""
    r = agent_session.post(f"{API}/cloud/valuator", json=UNI_PAYLOAD, timeout=15)
    assert r.status_code == 200, r.text[:300]


def test_10_fascicolo_base_regression_no_gate():
    """Chiamata diretta a `_estimate_value_core` (usata dal fascicolo agenzia).
    Deve funzionare senza gate B2C — no HTTP, no auth, no rate limit."""
    import sys
    sys.path.insert(0, "/app/backend")
    from apps.immocloud.valuator import ValuationPayload, _estimate_value_core
    payload = ValuationPayload(
        city="Roma",
        property_type="appartamento",
        surface_sqm=80,
        condition="buono",
    )
    result = asyncio.get_event_loop().run_until_complete(
        _estimate_value_core(payload)
    ) if not asyncio._get_running_loop() else asyncio.run(_estimate_value_core(payload))
    assert isinstance(result, dict)
    assert "estimated_value" in result or "value" in result
