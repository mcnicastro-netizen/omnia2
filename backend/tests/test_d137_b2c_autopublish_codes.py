"""D-137 — auto-publish, public codes, staging duplicate guard, payment alerts."""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")


@pytest.fixture
def mongo():
    from pymongo import MongoClient

    client = MongoClient(MONGO_URL, serverSelectionTimeoutMs=3000)
    client.admin.command("ping")
    return client[DB_NAME]


def test_generate_public_code_shape():
    from shared.ids import generate_public_code

    c = generate_public_code("client")
    l = generate_public_code("listing")
    assert c.startswith("OM-C-") and len(c) == 11
    assert l.startswith("OM-L-") and len(l) == 11


def test_auto_publish_default_on(monkeypatch):
    from apps.immocloud import private_listings as pl

    monkeypatch.delenv("OMNIA_B2C_AUTO_PUBLISH", raising=False)
    monkeypatch.delenv("OMNIA_B2C_SANDBOX_AUTO_APPROVE", raising=False)
    assert pl._b2c_auto_publish_enabled() is True
    monkeypatch.setenv("OMNIA_B2C_AUTO_PUBLISH", "false")
    assert pl._b2c_auto_publish_enabled() is False


def test_submit_auto_publishes(mongo, monkeypatch):
    from shared.db.connection import Database

    Database._client = None
    Database._db = None
    Database._tenant_db = None
    Database.connect()

    uid = uuid4().hex
    pid = uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    mongo.users.insert_one({
        "id": uid, "email": f"d137-{uid[:6]}@example.com", "name": "D137",
        "role": "client", "account_type": "b2c", "password_hash": "x",
        "created_at": now, "updated_at": now,
    })
    mongo.properties.insert_one({
        "id": pid, "agency_id": "_private_listings", "is_private_listing": True,
        "owner_user_id": uid, "title": "Test D137", "city": "Roma", "price": 200000,
        "status": "draft", "moderation_status": "none",
        "contact_public": {"display_name": "D", "show_email": True},
        "owner": {"email": f"d137-{uid[:6]}@example.com"},
        "created_at": now, "updated_at": now,
    })
    monkeypatch.delenv("OMNIA_B2C_AUTO_PUBLISH", raising=False)

    async def _run():
        from apps.immocloud.private_listings import submit_for_moderation
        with patch("apps.immocloud.alert_fanout.fanout_listing_event", new_callable=AsyncMock), \
             patch("apps.immoweb.private_listing_matching.run_private_listing_request_matching", new_callable=AsyncMock):
            return await submit_for_moderation(pid, {"id": uid, "account_type": "b2c", "role": "client", "email": f"d137-{uid[:6]}@example.com"})

    loop = asyncio.new_event_loop()
    try:
        out = loop.run_until_complete(_run())
    finally:
        loop.close()
        mongo.properties.delete_one({"id": pid})
        mongo.users.delete_one({"id": uid})

    assert out["moderation_status"] == "approved"
    assert out["status"] == "active"
    assert out.get("auto_publish") is True
    assert str(out.get("reference_code") or "").startswith("OM-L-")
    assert str(out.get("client_code") or "").startswith("OM-C-")


def test_staging_duplicate_guard_unit(mongo):
    from shared.db.connection import Database

    Database._client = None
    Database._db = None
    Database._tenant_db = None
    Database.connect()

    uid = uuid4().hex
    lid = uuid4().hex
    photo = "ph1"
    now = datetime.now(timezone.utc)
    mongo.b2c_purchases.insert_one({
        "id": uuid4().hex,
        "user_id": uid,
        "product_key": "b2c_staging_render",
        "listing_id": lid,
        "photo_id": photo,
        "staging_mode": "reverse",
        "status": "paid",
        "paid_at": now.isoformat(),
        "created_at": now.isoformat(),
        "stripe_session_id": "cs_test_dup",
    })

    async def _check():
        db = Database.get()
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        return await db.b2c_purchases.find_one({
            "user_id": uid,
            "product_key": "b2c_staging_render",
            "listing_id": lid,
            "photo_id": photo,
            "staging_mode": "reverse",
            "status": "paid",
            "paid_at": {"$gte": since},
        })

    loop = asyncio.new_event_loop()
    try:
        hit = loop.run_until_complete(_check())
    finally:
        loop.close()
        mongo.b2c_purchases.delete_many({"user_id": uid})

    assert hit is not None


def test_notify_b2c_payment_sends_emails(monkeypatch):
    calls = []

    async def fake_send(**kwargs):
        calls.append(kwargs)
        return {"id": "mock", "status": "ok"}

    monkeypatch.setenv("OMNIA_ADMIN_EMAIL", "founder@example.com")

    async def _run():
        with patch("shared.email.client.send_email", side_effect=fake_send), \
             patch("shared.db.connection.Database.get") as gdb:
            db = AsyncMock()
            db.users.find_one = AsyncMock(return_value={
                "id": "u1", "email": "buyer@example.com", "name": "Buyer", "client_code": "OM-C-TEST01",
            })
            db.users.find = MagicFind([])
            db.properties.find_one = AsyncMock(return_value={"id": "p1", "reference_code": "OM-L-TEST01"})
            gdb.return_value = db
            from apps.billing.b2c_payment_alerts import notify_b2c_payment
            await notify_b2c_payment(
                session={
                    "id": "cs_test_x",
                    "amount_total": 149,
                    "currency": "eur",
                    "customer_email": "buyer@example.com",
                    "metadata": {
                        "b2c_product_key": "b2c_staging_render",
                        "user_id": "u1",
                        "listing_id": "p1",
                    },
                },
                purchase={"product_key": "b2c_staging_render", "amount_eur": 1.49},
            )

    class MagicFind:
        def __init__(self, items):
            self.items = items
        def to_list(self, length=20):
            async def _():
                return self.items
            return _()

    # simplify: patch ensure_* and inbox
    async def _run2():
        with patch("shared.email.client.send_email", side_effect=fake_send), \
             patch("shared.ids.ensure_client_code", new_callable=AsyncMock, return_value="OM-C-AAA111"), \
             patch("shared.ids.ensure_listing_code", new_callable=AsyncMock, return_value="OM-L-BBB222"), \
             patch("shared.db.connection.Database.get") as gdb, \
             patch("shared.notifications.center.notify_users", new_callable=AsyncMock):
            db = AsyncMock()
            db.users.find_one = AsyncMock(return_value={"email": "buyer@example.com", "name": "Buyer"})
            cur = AsyncMock()
            cur.to_list = AsyncMock(return_value=[{"id": "admin1"}])
            db.users.find = MagicMockReturn(cur)
            gdb.return_value = db
            from apps.billing.b2c_payment_alerts import notify_b2c_payment
            await notify_b2c_payment(
                session={
                    "id": "cs_test_x",
                    "amount_total": 149,
                    "currency": "eur",
                    "customer_email": "buyer@example.com",
                    "metadata": {
                        "b2c_product_key": "b2c_staging_render",
                        "user_id": "u1",
                        "listing_id": "p1",
                    },
                },
                purchase={"product_key": "b2c_staging_render", "amount_eur": 1.49},
            )

    class MagicMockReturn:
        def __init__(self, cur):
            self.cur = cur
        def __call__(self, *a, **k):
            return self.cur

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run2())
    finally:
        loop.close()

    templates = {c["template"] for c in calls}
    assert "b2c_payment_receipt" in templates
    assert "b2c_payment_founder" in templates
    assert any(c["to"] == "buyer@example.com" for c in calls)
    assert any(c["to"] == "founder@example.com" for c in calls)
