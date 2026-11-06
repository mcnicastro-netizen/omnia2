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


def test_founder_safety_alert_copy_is_plain_italian():
    from apps.immocloud.listing_safety_gate import (
        SafetyReport,
        VERDICT_REVIEW,
        founder_safety_alert_copy,
    )

    copy = founder_safety_alert_copy(
        {
            "id": "abc",
            "reference_code": "OM-L-N4KJN2",
            "title": "provaprova",
            "city": "Mascalucia",
        },
        SafetyReport(
            verdict=VERDICT_REVIEW,
            reasons=["llm_review"],
            hard_hits=[],
            soft_hits=[],
            llm_used=True,
            llm_verdict="REVIEW",
        ),
        event="rescan_live_soft",
    )
    blob = " ".join(copy.values()).lower()
    assert "resta online" in blob
    assert "da controllare" in blob
    assert "provaprova" in blob
    assert "om-l-n4kjn2" in blob
    # no raw ops jargon in Founder-facing fields
    for bad in ("verdict=", "motives=", "hits=", "rescan_live_soft", "llm_review"):
        assert bad not in copy["subject"].lower()
        assert bad not in copy["headline"].lower()
        assert bad not in copy["event_line"].lower()
        assert bad not in copy["why_line"].lower()
        assert bad not in copy["inbox_title"].lower()


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


def test_rescan_llm_review_without_heuristics_stays_live(mongo):
    """Live ads must not be yanked by pure Gemini REVIEW (no soft/hard hits)."""
    from shared.db.connection import Database
    from apps.immocloud.listing_safety_gate import (
        SafetyReport,
        VERDICT_REVIEW,
        rescan_live_private_listings,
    )

    Database._client = None
    Database._db = None
    Database._tenant_db = None
    Database.connect()

    pid = uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    mongo.properties.insert_one({
        "id": pid,
        "agency_id": "_private_listings",
        "is_private_listing": True,
        "owner_user_id": "u1",
        "title": "provaprova",
        "city": "Mascalucia",
        "price": 200000,
        "description": "Villetta con giardino",
        "status": "active",
        "moderation_status": "approved",
        "visibility": "public",
        "created_at": now,
        "updated_at": now,
    })

    soft = SafetyReport(
        verdict=VERDICT_REVIEW,
        reasons=["llm_review"],
        hard_hits=[],
        soft_hits=[],
        llm_used=True,
        llm_verdict="REVIEW",
    )

    async def _run():
        with patch(
            "apps.immocloud.listing_safety_gate.evaluate_listing_safety",
            new_callable=AsyncMock,
            return_value=soft,
        ), patch(
            "apps.immocloud.listing_safety_gate.notify_founder_safety_flag",
            new_callable=AsyncMock,
        ) as notify:
            out = await rescan_live_private_listings(limit=20)
            return out, notify

    loop = asyncio.new_event_loop()
    try:
        out, notify = loop.run_until_complete(_run())
    finally:
        loop.close()
        doc = mongo.properties.find_one({"id": pid}, {"_id": 0, "status": 1, "moderation_status": 1})
        mongo.properties.delete_one({"id": pid})

    assert out["held"] == 0
    assert out.get("flagged_soft", 0) >= 1
    assert doc["status"] == "active"
    assert doc["moderation_status"] == "approved"
    assert notify.await_count >= 1


def test_soft_alert_cooldown_skips_repeat_email(mongo):
    """Hourly rescan must not re-mail Founder for the same soft LLM REVIEW."""
    from shared.db.connection import Database
    from apps.immocloud.listing_safety_gate import (
        SafetyReport,
        VERDICT_REVIEW,
        rescan_live_private_listings,
        soft_alert_in_cooldown,
    )

    Database._client = None
    Database._db = None
    Database._tenant_db = None
    Database.connect()

    pid = uuid4().hex
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    mongo.properties.insert_one({
        "id": pid,
        "agency_id": "_private_listings",
        "is_private_listing": True,
        "owner_user_id": "u1",
        "title": "provaprova",
        "city": "Mascalucia",
        "price": 200000,
        "description": "Villetta con giardino",
        "status": "active",
        "moderation_status": "approved",
        "visibility": "public",
        "safety_soft_alerted_at": now_iso,
        "safety_gate": {
            "verdict": "REVIEW",
            "reasons": ["llm_review"],
            "hard_hits": [],
            "soft_hits": [],
            "checked_at": now_iso,
        },
        "created_at": now_iso,
        "updated_at": now_iso,
    })

    soft = SafetyReport(
        verdict=VERDICT_REVIEW,
        reasons=["llm_review"],
        hard_hits=[],
        soft_hits=[],
        llm_used=True,
        llm_verdict="REVIEW",
    )

    listing = mongo.properties.find_one({"id": pid}, {"_id": 0})
    assert soft_alert_in_cooldown(listing, now=now) is True

    async def _run():
        with patch(
            "apps.immocloud.listing_safety_gate.evaluate_listing_safety",
            new_callable=AsyncMock,
            return_value=soft,
        ), patch(
            "apps.immocloud.listing_safety_gate.notify_founder_safety_flag",
            new_callable=AsyncMock,
        ) as notify:
            out = await rescan_live_private_listings(limit=20)
            return out, notify

    loop = asyncio.new_event_loop()
    try:
        out, notify = loop.run_until_complete(_run())
    finally:
        loop.close()
        mongo.properties.delete_one({"id": pid})

    assert out["held"] == 0
    assert out.get("flagged_soft", 0) == 0
    assert notify.await_count == 0
