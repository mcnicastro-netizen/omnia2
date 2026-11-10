"""Ops grant-agency-plan — provisioning assistito dogfood (super_admin)."""
from __future__ import annotations

import os
import uuid

import pytest
import requests
from pymongo import MongoClient

BASE = os.environ.get("REACT_APP_BACKEND_URL") or os.environ.get("BACKEND_URL") or "http://127.0.0.1:43121"
API = f"{BASE.rstrip('/')}/api"


def _login_bearer(email: str, password: str) -> requests.Session:
    """Login cookie Secure → copia access_token in Authorization Bearer."""
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, r.text
    tok = s.cookies.get("access_token")
    if not tok:
        # parse Set-Cookie header if cookie jar dropped Secure cookie on http
        raw = r.headers.get("Set-Cookie") or ""
        for part in raw.split(","):
            if "access_token=" in part:
                tok = part.split("access_token=", 1)[1].split(";", 1)[0].strip()
                break
    assert tok, "no access_token from login"
    s.headers["Authorization"] = f"Bearer {tok}"
    return s


@pytest.fixture(scope="module")
def super_sess():
    email = os.environ.get("ADMIN_EMAIL") or os.environ.get("OMNIA_ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD") or os.environ.get("OMNIA_ADMIN_PASSWORD")
    if not email or not password:
        pytest.skip("ADMIN_EMAIL/PASSWORD missing")
    return _login_bearer(email, password)


def test_agencies_lookup_super_admin(super_sess):
    r = super_sess.get(f"{API}/app/ops/agencies-lookup", params={"q": "nicastro", "limit": 10}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    assert "items" in body


def test_grant_agency_plan_by_slug(super_sess):
    uri = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    dbn = os.environ.get("DB_NAME", "omnia")
    db = MongoClient(uri)[dbn]

    slug = f"dogfood-grant-{uuid.uuid4().hex[:8]}"
    aid = str(uuid.uuid4())
    db.agencies.insert_one(
        {
            "id": aid,
            "slug": slug,
            "display_name": "Dogfood Grant Agency",
            "plan": "free",
            "owner_id": "test-owner",
            "is_active": True,
            "fiscal": {"vat": "IT000"},
        }
    )
    try:
        r = super_sess.post(
            f"{API}/app/ops/grant-agency-plan",
            json={
                "slug": slug,
                "tier": "pro",
                "credits": 150,
                "note": "pytest_dogfood",
            },
            timeout=30,
        )
        assert r.status_code == 200, r.text
        g = r.json()["grant"]
        assert g["ok"] is True
        assert g["plan_tier"] == "pro"
        assert g["credits_added"] == 150
        assert g["credits_balance"] >= 150

        sub = db.subscriptions.find_one({"agency_id": aid})
        assert sub and sub.get("status") == "active"
        assert sub.get("plan_tier") == "pro"
        assert sub.get("source") == "assisted_provisioning"

        ag = db.agencies.find_one({"id": aid})
        assert ag.get("billing_assisted_tier") == "pro"
        assert ag.get("plan") == "pro"
    finally:
        db.credit_transactions.delete_many({"agency_id": aid})
        db.credit_wallets.delete_many({"agency_id": aid})
        db.subscriptions.delete_many({"agency_id": aid})
        db.agencies.delete_many({"id": aid})


def test_grant_forbidden_for_non_super():
    email = os.environ.get("NICASTRO_ADMIN_EMAIL", "titolare@nicastroimmobiliare.it")
    password = os.environ.get("NICASTRO_ADMIN_PASSWORD", "NicastroDemo2026!")
    try:
        s = _login_bearer(email, password)
    except AssertionError:
        pytest.skip("nicastro titolare not available")
    deny = s.post(
        f"{API}/app/ops/grant-agency-plan",
        json={"slug": "x", "tier": "pro", "credits": 1},
        timeout=30,
    )
    assert deny.status_code == 403
