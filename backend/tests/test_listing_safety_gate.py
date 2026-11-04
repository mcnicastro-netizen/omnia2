"""D-137b — listing safety gate heuristics + submit wiring."""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
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


def test_hard_block_rejects():
    from apps.immocloud.listing_safety_gate import VERDICT_REJECT, evaluate_listing_safety

    async def _run():
        with patch("apps.immocloud.listing_safety_gate._llm_classify", new_callable=AsyncMock, return_value=None):
            return await evaluate_listing_safety({
                "title": "Bilocale centro",
                "description": "Invia soldi via Western Union prima della visita",
            })

    r = asyncio.get_event_loop().run_until_complete(_run()) if False else None
    loop = asyncio.new_event_loop()
    try:
        r = loop.run_until_complete(_run())
    finally:
        loop.close()
    assert r.verdict == VERDICT_REJECT
    assert r.hard_hits


def test_soft_block_reviews():
    from apps.immocloud.listing_safety_gate import VERDICT_REVIEW, evaluate_listing_safety

    async def _run():
        with patch("apps.immocloud.listing_safety_gate._llm_classify", new_callable=AsyncMock, return_value=None):
            return await evaluate_listing_safety({
                "title": "Appartamento",
                "description": "No extracomunitari grazie",
            })

    loop = asyncio.new_event_loop()
    try:
        r = loop.run_until_complete(_run())
    finally:
        loop.close()
    assert r.verdict == VERDICT_REVIEW


def test_clean_accepts_without_llm():
    from apps.immocloud.listing_safety_gate import VERDICT_ACCEPT, evaluate_listing_safety

    async def _run():
        with patch("apps.immocloud.listing_safety_gate._llm_classify", new_callable=AsyncMock, return_value=None):
            return await evaluate_listing_safety({
                "title": "Trilocale luminoso zona Università",
                "description": "Cucina abitabile, balcone, posto auto. Classe energetica D.",
                "city": "Catania",
            })

    loop = asyncio.new_event_loop()
    try:
        r = loop.run_until_complete(_run())
    finally:
        loop.close()
    assert r.verdict == VERDICT_ACCEPT


def test_submit_holds_offensive(mongo, monkeypatch):
    from shared.db.connection import Database

    Database._client = None
    Database._db = None
    Database._tenant_db = None
    Database.connect()
    monkeypatch.delenv("OMNIA_B2C_AUTO_PUBLISH", raising=False)

    uid = uuid4().hex
    pid = uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    mongo.users.insert_one({
        "id": uid, "email": f"safe-{uid[:6]}@example.com", "name": "S",
        "role": "client", "account_type": "b2c", "password_hash": "x",
        "created_at": now, "updated_at": now,
    })
    mongo.properties.insert_one({
        "id": pid, "agency_id": "_private_listings", "is_private_listing": True,
        "owner_user_id": uid, "title": "Casa", "city": "Milano", "price": 100000,
        "description": "No extracomunitari in condominio",
        "status": "draft", "moderation_status": "none",
        "contact_public": {"display_name": "S", "show_email": True},
        "owner": {"email": f"safe-{uid[:6]}@example.com"},
        "created_at": now, "updated_at": now,
    })

    async def _run():
        from apps.immocloud.private_listings import submit_for_moderation
        with patch("apps.immocloud.listing_safety_gate._llm_classify", new_callable=AsyncMock, return_value=None), \
             patch("apps.immocloud.listing_safety_gate.notify_founder_safety_flag", new_callable=AsyncMock):
            return await submit_for_moderation(
                pid,
                {"id": uid, "account_type": "b2c", "role": "client", "email": f"safe-{uid[:6]}@example.com"},
            )

    loop = asyncio.new_event_loop()
    try:
        out = loop.run_until_complete(_run())
    finally:
        loop.close()
        mongo.properties.delete_one({"id": pid})
        mongo.users.delete_one({"id": uid})

    assert out["auto_publish"] is False
    assert out["moderation_status"] == "pending"
    assert out["safety_verdict"] == "REVIEW"
