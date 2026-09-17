"""Scout HAL + price watch + market pulse — no-fluff consumer edge."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"


def _mongo():
    url = os.environ.get("MONGO_URL") or ""
    if not url:
        pytest.skip("MONGO_URL not set")
    return MongoClient(url, serverSelectionTimeoutMS=3000)[os.environ.get("DB_NAME") or "omnia_db"]


@pytest.fixture(scope="module")
def mongo():
    db = _mongo()
    yield db


@pytest.fixture(scope="module")
def listing(mongo):
    pid = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    mongo.properties.insert_one({
        "id": pid,
        "agency_id": "_private_listings",
        "is_private_listing": True,
        "owner_user_id": "scout-test-owner",
        "title": "Trilocale Navigli test Scout",
        "description": "Ampio trilocale luminoso con cucina abitabile, due balconi e cantina. "
                       "Ristrutturato nel 2019, riscaldamento autonomo, doppi vetri. "
                       "Zona servita da metro e negozi. Spese condominiali contenute. "
                       "Ideale per famiglia o investimento. Libero subito.",
        "city": "Milano",
        "zone": "Navigli",
        "address": "Via Tortona 12",
        "property_type": "appartamento",
        "operation": "sale",
        "price": 520000,
        "surface_sqm": 95,
        "rooms": 3,
        "bedrooms": 2,
        "bathrooms": 1,
        "energy": {"energy_class": "D"},
        "lat": 45.45,
        "lng": 9.17,
        "photos": [{"url": "/x.jpg", "is_cover": True}] * 6,
        "status": "active",
        "visibility": "public",
        "is_listed_on_immobilcloud": True,
        "moderation_status": "approved",
        "created_at": now,
        "updated_at": now,
    })
    yield pid
    mongo.properties.delete_one({"id": pid})


def test_01_pulse_endpoint():
    if not BASE_URL:
        pytest.skip("no backend")
    r = requests.get(f"{API}/cloud/pulse", params={"operation": "sale", "days": 7}, timeout=15)
    assert r.status_code == 200, r.text[:200]
    d = r.json()
    assert "new_listings" in d
    assert "price_drops" in d
    assert "label_it" in d


def test_02_scout_hal(listing):
    if not BASE_URL:
        pytest.skip("no backend")
    r = requests.post(f"{API}/cloud/property/{listing}/scout", json={"lang": "it"}, timeout=45)
    assert r.status_code == 200, r.text[:400]
    d = r.json()
    assert d["product"] == "scout_hal"
    assert d["completeness"]["score"] >= 50
    assert d["price_vs_zone"]["available"] is True
    assert d["price_vs_zone"]["signal"] in ("sotto_mercato", "in_linea", "sopra_mercato")
    assert d["price_vs_zone"]["estimated_band_eur"]["min"] > 0
    assert len(d["price_vs_zone"]["why"]) >= 2
    assert d["price_vs_zone"]["confidence"]["level"] in ("alta", "media", "bassa")
    assert len(d["questions_for_seller"]) >= 2
    assert 4 <= len(d["visit_checklist"]) <= 10
    assert 4 <= len(d["documents_before_offer"]) <= 9
    assert all("why_it" in x for x in d["documents_before_offer"])
    assert any("mutuabile" in q.lower() for q in d["questions_for_seller"])
    limits = " ".join((d["price_vs_zone"].get("confidence") or {}).get("limits_it") or [])
    assert "zona semicentro" in limits
    assert "benchmark semicentro" not in limits
    why = " ".join(w.get("label_it", "") for w in d["price_vs_zone"].get("why") or [])
    assert "La richiesta" in why or "richiesta" in why.lower()


def test_03_price_drop_recording(mongo, listing):
    import asyncio
    from shared.db.connection import Database
    Database._client = None
    Database._db = None
    Database._tenant_db = None
    Database.connect()

    async def _run():
        from apps.immocloud.price_watch import record_price_change
        db = Database.get()
        existing = await db.properties.find_one({"id": listing})
        await record_price_change(
            db,
            property_id=listing,
            existing=existing,
            new_price=480000,
            new_rent=None,
            touched_price=True,
            touched_rent=False,
        )
        await db.properties.update_one({"id": listing}, {"$set": {"price": 480000}})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())
    prop = mongo.properties.find_one({"id": listing})
    assert prop.get("price_dropped_at")
    assert prop.get("last_price_drop", {}).get("drop_eur") == 40000
    assert any(h.get("drop_eur") == 40000 for h in (prop.get("price_history") or []))


def test_04_home_search_form_still_serves():
    if not BASE_URL:
        pytest.skip("no backend")
    r = requests.get(f"{API}/cloud/facets", params={"operation": "sale"}, timeout=10)
    assert r.status_code == 200
