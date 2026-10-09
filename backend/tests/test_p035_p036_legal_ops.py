"""P-035 Ops saved_searches is_active · P-036 HAL Legal CRM debit 12 crediti."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import requests

API = os.environ.get("OMNIA_API_BASE", "http://127.0.0.1:43121/api")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")


@pytest.fixture(scope="module")
def mongo():
    from pymongo import MongoClient

    return MongoClient(MONGO_URL)[DB_NAME]


@pytest.fixture(scope="module")
def founder_session():
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        pytest.skip("ADMIN_EMAIL/ADMIN_PASSWORD missing")
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"founder login {r.status_code}")
    return s


@pytest.fixture(scope="module")
def demo_session(mongo):
    email = "demo.admin@omniaecosystem.it"
    password = os.environ.get("DEMO_ADMIN_PASSWORD") or "DemoAdmin2026!"
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"demo login {r.status_code}")
    # Seed wallet for debit tests
    now = datetime.now(timezone.utc).isoformat()
    mongo.credit_wallets.update_one(
        {"agency_id": "demo-agency-001"},
        {"$set": {"balance": 100, "updated_at": now}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return s


def test_p035_ops_counts_is_active(founder_session, mongo):
    uid = f"p035-{uuid.uuid4().hex[:8]}"
    mongo.saved_searches.insert_one({
        "id": uuid.uuid4().hex,
        "user_id": uid,
        "name": "P035",
        "filters": {"city": "Roma"},
        "frequency": "daily",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    r = founder_session.get(f"{API}/app/ops/overview", params={"days": 30}, timeout=60)
    assert r.status_code == 200, r.text[:300]
    portal = r.json().get("portal") or {}
    assert int(portal.get("saved_searches_active") or 0) >= 1


def test_p036_agency_legal_debits_12(demo_session, mongo):
    before = mongo.credit_wallets.find_one({"agency_id": "demo-agency-001"}, {"_id": 0, "balance": 1})
    bal_before = int((before or {}).get("balance") or 0)
    assert bal_before >= 12, "wallet must have credits for debit test"

    r = demo_session.post(
        f"{API}/app/legal/chat",
        json={"message": "Cos'è una visura catastale in breve?"},
        timeout=120,
    )
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert body.get("credits_charged") == 12
    assert body.get("payment_rail") == "agency_credits"

    after = mongo.credit_wallets.find_one({"agency_id": "demo-agency-001"}, {"_id": 0, "balance": 1})
    bal_after = int((after or {}).get("balance") or 0)
    assert bal_after == bal_before - 12

    ledger = mongo.credit_ledger.find_one(
        {"agency_id": "demo-agency-001", "reason": "hal_legal_query"},
        sort=[("created_at", -1)],
    )
    assert ledger is not None
    assert ledger.get("delta") == -12


def test_p036_insufficient_credits_402(demo_session, mongo):
    mongo.credit_wallets.update_one(
        {"agency_id": "demo-agency-001"},
        {"$set": {"balance": 5, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    r = demo_session.post(
        f"{API}/app/legal/chat",
        json={"message": "Test crediti insufficienti HAL Legal"},
        timeout=30,
    )
    assert r.status_code == 402, r.text[:300]
    detail = r.json().get("detail") or {}
    if isinstance(detail, dict):
        assert detail.get("error") == "insufficient_credits" or detail.get("required") == 12
    # restore for other tests / dogfood
    mongo.credit_wallets.update_one(
        {"agency_id": "demo-agency-001"},
        {"$set": {"balance": 100}},
    )
