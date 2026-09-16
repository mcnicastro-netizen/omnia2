"""B2C visibility boosts (Vetrina / Premium / TOP) — catalog + checkout + fulfill.

Covers:
1. Catalog lists all 7 boost SKUs
2. Checkout without listing_id → 400
3. Checkout with owned listing → 200 + cs_test URL (Stripe sandbox)
4. Unknown product → 400
5. apply_b2c_purchase_side_effects activates boost on listing
6. Public search sorts boosted listings first
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


@pytest.fixture(scope="module")
def mongo():
    if not _mongo_url():
        pytest.skip("MONGO_URL not set")
    client = MongoClient(_mongo_url(), serverSelectionTimeoutMS=3000)
    db = client[_db_name()]
    yield db
    client.close()


@pytest.fixture(scope="module")
def b2c_session(mongo):
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    email = f"b2c-boost-{uuid4().hex[:10]}@example.com"
    password = "Test-Password-1!"
    s = requests.Session()
    r = s.post(
        f"{API}/cloud/auth/register",
        json={
            "email": email,
            "password": password,
            "name": "B2C Boost Test",
            "intents": ["sell"],
            "notification_channels": ["email"],
            "gdpr_consent": True,
        },
        timeout=15,
    )
    if r.status_code >= 400:
        pytest.skip(f"cloud register unavailable: {r.status_code} {r.text[:200]}")
    return s, email


@pytest.fixture(scope="module")
def listing_id(b2c_session, mongo):
    s, email = b2c_session
    user = mongo.users.find_one({"email": email})
    assert user
    pid = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    mongo.properties.insert_one({
        "id": pid,
        "agency_id": "_private_listings",
        "is_private_listing": True,
        "owner_user_id": user["id"],
        "title": "Appartamento boost test",
        "city": "Milano",
        "property_type": "appartamento",
        "operation": "sale",
        "price": 320000,
        "status": "active",
        "visibility": "public",
        "is_listed_on_immobilcloud": True,
        "moderation_status": "approved",
        "photos": [],
        "created_at": now,
        "updated_at": now,
    })
    yield pid
    mongo.properties.delete_one({"id": pid})


def test_01_catalog_includes_boosts():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    r = requests.get(f"{API}/billing/b2c/catalog", timeout=10)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    keys = {p["key"] for p in data["products"]}
    for k in (
        "b2c_vetrina_30",
        "b2c_premium_30", "b2c_premium_90", "b2c_premium_180",
        "b2c_top_30", "b2c_top_90", "b2c_top_180",
        "b2c_staging_render",
    ):
        assert k in keys
    boosts = data["boosts"]
    assert len(boosts) == 7
    assert boosts[0]["boost_tier"] == "vetrina"
    assert boosts[-1]["boost_tier"] == "top"


def test_02_checkout_requires_listing(b2c_session):
    s, _ = b2c_session
    fe = os.environ.get("FRONTEND_URL", "http://127.0.0.1:43122")
    r = s.post(
        f"{API}/billing/b2c/checkout",
        json={
            "product_key": "b2c_vetrina_30",
            "success_url": f"{fe}/ok",
            "cancel_url": f"{fe}/cancel",
        },
        timeout=20,
    )
    assert r.status_code == 400
    assert "listing_id_required" in str(r.json().get("detail"))


def test_03_checkout_vetrina_premium_top_sandbox(b2c_session, listing_id):
    s, _ = b2c_session
    fe = os.environ.get("FRONTEND_URL", "http://127.0.0.1:43122")
    for key in ("b2c_vetrina_30", "b2c_premium_30", "b2c_top_30"):
        r = s.post(
            f"{API}/billing/b2c/checkout",
            json={
                "product_key": key,
                "listing_id": listing_id,
                "success_url": f"{fe}/ok",
                "cancel_url": f"{fe}/cancel",
            },
            timeout=45,
        )
        assert r.status_code == 200, f"{key}: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("session_id", "").startswith("cs_test_")
        assert "checkout.stripe.com" in (body.get("checkout_url") or "")
        assert body.get("listing_id") == listing_id


def test_04_unknown_product_still_400(b2c_session, listing_id):
    s, _ = b2c_session
    fe = os.environ.get("FRONTEND_URL", "http://127.0.0.1:43122")
    r = s.post(
        f"{API}/billing/b2c/checkout",
        json={
            "product_key": "vetrina",
            "listing_id": listing_id,
            "success_url": f"{fe}/ok",
            "cancel_url": f"{fe}/cancel",
        },
        timeout=15,
    )
    assert r.status_code == 400
    assert "unknown_product" in str(r.json().get("detail"))


def test_05_webhook_side_effects_apply_boost(b2c_session, listing_id, mongo):
    s, email = b2c_session
    user = mongo.users.find_one({"email": email})
    session_id = f"cs_test_fake_{uuid4().hex[:16]}"
    mongo.b2c_purchases.insert_one({
        "id": uuid4().hex,
        "user_id": user["id"],
        "product_key": "b2c_premium_30",
        "stripe_session_id": session_id,
        "listing_id": listing_id,
        "payload_hash": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
    })

    from shared.db.connection import Database
    Database.connect()

    async def _run():
        from apps.billing.b2c_checkout import apply_b2c_purchase_side_effects
        await apply_b2c_purchase_side_effects({
            "id": session_id,
            "metadata": {
                "b2c_product_key": "b2c_premium_30",
                "user_id": user["id"],
                "listing_id": listing_id,
            },
        })

    asyncio.run(_run())

    prop = mongo.properties.find_one({"id": listing_id})
    assert prop.get("boost_tier") == "premium"
    assert prop.get("boost_rank") == 200
    assert prop.get("boost_product_key") == "b2c_premium_30"
    until = datetime.fromisoformat(prop["boost_until"].replace("Z", "+00:00"))
    assert until > datetime.now(timezone.utc) + timedelta(days=25)

    purchase = mongo.b2c_purchases.find_one({"stripe_session_id": session_id})
    assert purchase["status"] == "paid"


def test_06_search_promotes_boosted(listing_id, mongo):
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    # Ensure boost still active from previous test or set explicitly
    until = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    mongo.properties.update_one(
        {"id": listing_id},
        {"$set": {
            "boost_tier": "top",
            "boost_rank": 300,
            "boost_until": until,
            "status": "active",
            "visibility": "public",
            "is_listed_on_immobilcloud": True,
            "moderation_status": "approved",
        }},
    )
    # Insert a newer non-boosted listing that would otherwise rank first
    other = str(uuid4())
    now = datetime.now(timezone.utc)
    mongo.properties.insert_one({
        "id": other,
        "agency_id": "_private_listings",
        "is_private_listing": True,
        "owner_user_id": "other-user",
        "title": "Nuovo senza boost",
        "city": "Milano",
        "property_type": "appartamento",
        "operation": "sale",
        "price": 200000,
        "status": "active",
        "visibility": "public",
        "is_listed_on_immobilcloud": True,
        "moderation_status": "approved",
        "photos": [],
        "created_at": now.isoformat(),
        "updated_at": (now + timedelta(hours=1)).isoformat(),
    })
    try:
        r = requests.get(
            f"{API}/cloud/search",
            params={"city": "Milano", "operation": "sale", "page_size": 20, "sort": "recent"},
            timeout=15,
        )
        assert r.status_code == 200
        ids = [i["id"] for i in r.json().get("items") or []]
        assert listing_id in ids
        assert ids.index(listing_id) < ids.index(other)
        card = next(i for i in r.json()["items"] if i["id"] == listing_id)
        assert card.get("boost_tier") == "top"
    finally:
        mongo.properties.delete_one({"id": other})
