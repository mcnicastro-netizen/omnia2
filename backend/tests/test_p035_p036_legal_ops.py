"""P-035 Ops saved_searches is_active · D-119 HAL Legal CRM incluso (ex P-036 debit)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import requests

API = os.environ.get("OMNIA_API_BASE", "http://127.0.0.1:43121/api")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")


class SecureCookieSession(requests.Session):
    """Keep Secure/SameSite=None cookies on http://127.0.0.1 (Cloud)."""

    def __init__(self) -> None:
        super().__init__()
        self._forced: dict[str, str] = {}
        self.csrf: str | None = None

    def request(self, method, url, **kwargs):  # type: ignore[override]
        headers = dict(kwargs.get("headers") or {})
        if self._forced:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self._forced.items())
        if self.csrf and method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
            headers["X-CSRF-Token"] = self.csrf
        kwargs["headers"] = headers
        r = super().request(method, url, **kwargs)
        for h in r.raw.headers.getlist("Set-Cookie"):
            part = h.split(";", 1)[0]
            if "=" not in part:
                continue
            name, val = part.split("=", 1)
            name, val = name.strip(), val.strip()
            self._forced[name] = val
            if name == "omnia_csrf":
                self.csrf = val
        return r


@pytest.fixture(scope="module")
def mongo():
    from pymongo import MongoClient

    return MongoClient(MONGO_URL)[DB_NAME]


@pytest.fixture(scope="module")
def founder_session():
    email = os.environ.get("ADMIN_EMAIL") or os.environ.get("OMNIA_ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD") or os.environ.get("OMNIA_ADMIN_PASSWORD")
    if not email or not password:
        pytest.skip("ADMIN_EMAIL/ADMIN_PASSWORD missing")
    s = SecureCookieSession()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"founder login {r.status_code}")
    return s


@pytest.fixture(scope="module")
def demo_session(mongo):
    email = "demo.admin@omniaecosystem.it"
    password = os.environ.get("DEMO_ADMIN_PASSWORD") or "DemoAdmin2026!"
    s = SecureCookieSession()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"demo login {r.status_code}")
    now = datetime.now(timezone.utc).isoformat()
    mongo.credit_wallets.update_one(
        {"agency_id": "demo-agency-001"},
        {"$set": {"balance": 100, "updated_at": now}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    # Ensure active tenant for Legal gate
    me = s.get(f"{API}/auth/me", timeout=15)
    if me.status_code == 200:
        body = me.json()
        if not body.get("active_agency_id"):
            s.post(
                f"{API}/auth/active-agency",
                json={"agency_id": "demo-agency-001"},
                timeout=15,
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


def test_d119_agency_legal_included_no_debit(demo_session, mongo):
    """CRM HAL Legal = incluso piano: wallet invariato, rail agency_included."""
    before = mongo.credit_wallets.find_one({"agency_id": "demo-agency-001"}, {"_id": 0, "balance": 1})
    bal_before = int((before or {}).get("balance") or 0)

    r = demo_session.post(
        f"{API}/app/legal/chat",
        json={"message": "Cos'è una visura catastale in breve?"},
        timeout=120,
    )
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert body.get("credits_charged") in (0, None)
    assert body.get("payment_rail") == "agency_included"

    after = mongo.credit_wallets.find_one({"agency_id": "demo-agency-001"}, {"_id": 0, "balance": 1})
    bal_after = int((after or {}).get("balance") or 0)
    assert bal_after == bal_before


def test_d119_low_wallet_still_ok(demo_session, mongo):
    """Wallet < 12 non blocca più Legal CRM (incluso)."""
    mongo.credit_wallets.update_one(
        {"agency_id": "demo-agency-001"},
        {"$set": {"balance": 5, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    r = demo_session.post(
        f"{API}/app/legal/chat",
        json={"message": "Test Legal incluso con pochi crediti"},
        timeout=120,
    )
    assert r.status_code == 200, r.text[:300]
    assert (r.json().get("credits_charged") or 0) == 0
    assert r.json().get("payment_rail") == "agency_included"
    mongo.credit_wallets.update_one(
        {"agency_id": "demo-agency-001"},
        {"$set": {"balance": 100}},
    )
