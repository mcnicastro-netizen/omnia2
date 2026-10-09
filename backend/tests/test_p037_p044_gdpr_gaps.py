"""P-037…P-044 — GDPR/AI Act portal gaps (export, register gates, TTL, valuator gdpr)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import requests

API = os.environ.get("OMNIA_API_BASE", "http://127.0.0.1:43121/api")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")


@pytest.fixture
def mongo():
    from pymongo import MongoClient

    return MongoClient(MONGO_URL)[DB_NAME]


def _register(extra=None):
    s = requests.Session()
    email = f"p037.{uuid.uuid4().hex[:8]}@example.com"
    body = {
        "email": email,
        "password": "GdprTest2026!",
        "name": "GDPR Tester",
        "intents": ["buy"],
        "gdpr_consent": True,
        "age_confirmed": True,
        "marketing_consent": True,
        "lang": "it",
    }
    if extra:
        body.update(extra)
    r = s.post(f"{API}/cloud/auth/register", json=body, timeout=30)
    return s, email, r


def test_register_requires_age(mongo):
    s, email, r = _register({"age_confirmed": False, "marketing_consent": False})
    assert r.status_code == 400
    assert r.json().get("detail") == "age_confirmation_required"


def test_register_marketing_and_age_stored(mongo):
    s, email, r = _register()
    assert r.status_code in (200, 201), r.text[:300]
    u = mongo.users.find_one({"email": email}, {"_id": 0})
    assert u.get("age_confirmed") is True
    assert u.get("marketing_consent") is True
    ce = mongo.consent_events.find_one(
        {"email": email, "action": "b2c_marketing_consent"},
        sort=[("created_at", -1)],
    )
    assert ce is not None
    assert "expire_at" in ce


def test_export_and_rectify(mongo):
    s, email, r = _register()
    assert r.status_code in (200, 201)
    r = s.get(f"{API}/auth/me/export", timeout=30)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("format") == "omnia_b2c_export_v1"
    assert data.get("profile", {}).get("email") == email

    r = s.patch(
        f"{API}/auth/me",
        json={"name": "Nome Rettificato", "marketing_consent": False},
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    assert r.json().get("name") == "Nome Rettificato"
    assert r.json().get("marketing_consent") is False


def test_valuator_lead_requires_gdpr():
    payload = {
        "city": "Roma",
        "surface_sqm": 80,
        "property_type": "appartamento",
        "name": "Lead Test",
        "email": f"val.lead.{uuid.uuid4().hex[:6]}@example.com",
        "gdpr_consent": False,
    }
    r = requests.post(f"{API}/cloud/valuator", json=payload, timeout=30)
    assert r.status_code == 400, r.text[:300]
    assert r.json().get("detail") == "gdpr_consent_required"


def test_ttl_indexes_exist(mongo):
    names = {i["name"] for i in mongo.consent_events.list_indexes()}
    assert "consent_expire_at_ttl" in names
    names = {i["name"] for i in mongo.al_legal_audit.list_indexes()}
    assert "al_legal_expire_at_ttl" in names
    names = {i["name"] for i in mongo.b2c_purchases.list_indexes()}
    assert "b2c_purchases_expire_at_ttl" in names


def test_log_redact_helper():
    from shared.privacy.log_redact import redact_emails

    assert "[REDACTED_EMAIL]" in redact_emails("hello user@example.com bye")
    assert "user@example.com" not in redact_emails("user@example.com")


def test_staging_flag_on_public_photos(mongo):
    # Find any listed property; inject staging flag on a photo; check API
    prop = mongo.properties.find_one(
        {"status": "active", "visibility": "public", "is_listed_on_immobilcloud": True},
        {"_id": 0, "id": 1, "photos": 1},
    )
    if not prop:
        pytest.skip("no public prop")
    photos = list(prop.get("photos") or [])
    if not photos:
        photos = [{"id": "ph1", "is_cover": True, "url": "/x"}]
    photos[0]["is_virtual_staging"] = True
    mongo.properties.update_one({"id": prop["id"]}, {"$set": {"photos": photos}})
    r = requests.get(f"{API}/cloud/property/{prop['id']}", timeout=30)
    assert r.status_code == 200, r.text[:200]
    out_photos = r.json().get("photos") or []
    assert out_photos, "expected photos in public detail"
    assert any(p.get("is_virtual_staging") for p in out_photos)
