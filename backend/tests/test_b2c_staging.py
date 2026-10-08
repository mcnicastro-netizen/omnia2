"""P-011 — B2C staging: listing_id at checkout, consume + fulfill job path."""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:43121").rstrip("/")
API = f"{BASE_URL}/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")


@pytest.fixture(scope="module")
def mongo():
    from pymongo import MongoClient

    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    return client[DB_NAME]


@pytest.fixture
def b2c_user(mongo):
    uid = uuid4().hex
    email = f"staging-p011-{uid[:8]}@example.com"
    now = datetime.now(timezone.utc).isoformat()
    mongo.users.insert_one({
        "id": uid,
        "email": email,
        "password_hash": "x",
        "name": "Staging Tester",
        "role": "client",
        "account_type": "b2c",
        "email_verified": True,
        "created_at": now,
    })
    yield {"id": uid, "email": email}
    mongo.users.delete_one({"id": uid})
    mongo.b2c_purchases.delete_many({"user_id": uid})
    mongo.virtual_staging_jobs.delete_many({"user_id": uid})
    mongo.properties.delete_many({"owner_user_id": uid})


@pytest.fixture
def listing_with_photo(mongo, b2c_user):
    pid = uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    mongo.properties.insert_one({
        "id": pid,
        "agency_id": "_private_listings",
        "is_private_listing": True,
        "owner_user_id": b2c_user["id"],
        "title": "Attico staging test",
        "city": "Milano",
        "property_type": "appartamento",
        "operation": "sale",
        "price": 350000,
        "status": "draft",
        "moderation_status": "pending",
        "photos": [
            {"id": "ph1", "url": "/api/media/omnia/private/x/photos/a.jpg", "order": 0, "is_cover": True},
        ],
        "created_at": now,
        "updated_at": now,
    })
    yield pid
    mongo.properties.delete_one({"id": pid})


def test_catalog_staging_requires_listing_not_in_boosts():
    if not BASE_URL:
        pytest.skip("no backend url")
    r = requests.get(f"{API}/billing/b2c/catalog", timeout=10)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    staging = next(p for p in data["products"] if p["key"] == "b2c_staging_render")
    assert staging.get("requires_listing") is True
    boost_keys = {p["key"] for p in data["boosts"]}
    assert "b2c_staging_render" not in boost_keys


def test_checkout_staging_requires_listing(b2c_session_factory=None):
    """Live checkout gate — needs a real B2C session when available."""
    email = os.environ.get("OMNIA_DEMO_B2C_EMAIL")
    password = os.environ.get("OMNIA_DEMO_B2C_PASSWORD")
    if not email or not password or not BASE_URL:
        pytest.skip("demo B2C credentials not configured")
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"demo B2C login failed: {r.status_code}")
    fe = os.environ.get("FRONTEND_URL", "http://127.0.0.1:43123")
    r = s.post(
        f"{API}/billing/b2c/checkout",
        json={
            "product_key": "b2c_staging_render",
            "success_url": f"{fe}/ok?staging=ok",
            "cancel_url": f"{fe}/cancel",
        },
        timeout=20,
    )
    assert r.status_code == 400
    assert "listing_id_required" in str(r.json().get("detail"))


def test_consume_and_fulfill_creates_job(mongo, b2c_user, listing_with_photo):
    from shared.db.connection import Database

    Database._client = None
    Database._db = None
    Database._tenant_db = None
    Database.connect()

    session_id = f"cs_test_staging_{uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    mongo.b2c_purchases.insert_one({
        "id": uuid4().hex,
        "user_id": b2c_user["id"],
        "product_key": "b2c_staging_render",
        "stripe_session_id": session_id,
        "payload_hash": None,
        "listing_id": listing_with_photo,
        "status": "paid",
        "created_at": now.isoformat(),
        "paid_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=24)).isoformat(),
    })

    async def _run():
        from apps.immoweb.virtual_staging import fulfill_paid_staging_render

        with patch("apps.immoweb.virtual_staging.asyncio.create_task", return_value=None):
            with patch("apps.immoweb.virtual_staging._run_pipeline", new_callable=AsyncMock):
                result = await fulfill_paid_staging_render(session_id)
                # second call idempotent
                result2 = await fulfill_paid_staging_render(session_id)
                return result, result2

    loop = asyncio.new_event_loop()
    try:
        result, result2 = loop.run_until_complete(_run())
    finally:
        loop.close()

    assert result and result.get("job")
    job_id = result["job"]["id"]
    assert result2["job"]["id"] == job_id

    purchase = mongo.b2c_purchases.find_one({"stripe_session_id": session_id})
    assert purchase.get("consumed_at")
    assert purchase.get("job_id") == job_id

    job = mongo.virtual_staging_jobs.find_one({"id": job_id})
    assert job["payment_rail"] == "b2c_stripe"
    assert job["agency_id"] is None
    assert job["property_id"] == listing_with_photo
    assert job["source_url"].startswith("/api/media/")


def test_consume_b2c_staging_render_unit(mongo, b2c_user, listing_with_photo):
    from shared.db.connection import Database

    Database._client = None
    Database._db = None
    Database._tenant_db = None
    Database.connect()

    session_id = f"cs_consume_{uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    mongo.b2c_purchases.insert_one({
        "id": uuid4().hex,
        "user_id": b2c_user["id"],
        "product_key": "b2c_staging_render",
        "stripe_session_id": session_id,
        "listing_id": listing_with_photo,
        "status": "paid",
        "created_at": now.isoformat(),
        "paid_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=24)).isoformat(),
    })

    async def _run():
        from apps.billing.b2c_entitlements import consume_b2c_staging_render

        first = await consume_b2c_staging_render(
            b2c_user["id"], listing_id=listing_with_photo, stripe_session_id=session_id, job_id="job-1",
        )
        second = await consume_b2c_staging_render(
            b2c_user["id"], listing_id=listing_with_photo, stripe_session_id=session_id, job_id="job-2",
        )
        return first, second

    loop = asyncio.new_event_loop()
    try:
        first, second = loop.run_until_complete(_run())
    finally:
        loop.close()

    assert first and first.get("job_id") == "job-1"
    assert second is None
