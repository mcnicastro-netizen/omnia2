"""D-138 — B2C seller inquiry inbox (Idealista+)."""
from __future__ import annotations

import os
import time
import uuid

import pytest
import requests
from pymongo import MongoClient

API = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:43121").rstrip("/") + "/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")
TS = int(time.time())


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


def _soften_secure_cookies(session: requests.Session) -> None:
    """Cookie Secure=True is not sent on http://127.0.0.1 by requests — clear for local API."""
    for c in session.cookies:
        c.secure = False


def _csrf(session: requests.Session) -> str:
    session.get(f"{API}/auth/me", timeout=15)
    _soften_secure_cookies(session)
    return session.cookies.get("omnia_csrf") or ""


def _register_seller(session: requests.Session) -> dict:
    email = f"inq-seller-{TS}-{uuid.uuid4().hex[:6]}@example.com"
    csrf = _csrf(session)
    r = session.post(
        f"{API}/cloud/auth/register",
        json={
            "email": email,
            "password": "InboxTest1!",
            "name": "Seller Inbox",
            "phone": "3331112233",
            "whatsapp": "3331112233",
            "intents": ["sell"],
            "gdpr_consent": True,
            "age_confirmed": True,
        },
        headers={"X-CSRF-Token": csrf, "Content-Type": "application/json"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    _soften_secure_cookies(session)
    body = r.json()
    assert body["user"]["phone"] == "3331112233"
    # Confirm session works on local HTTP
    me = session.get(f"{API}/auth/me", timeout=15)
    assert me.status_code == 200, me.text
    return body["user"]


def test_inbox_list_patch_visit_and_summary(db):
    s = requests.Session()
    user = _register_seller(s)
    uid = user["id"]
    pid = str(uuid.uuid4())
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    inq_id = str(uuid.uuid4())
    db.properties.insert_one({
        "id": pid,
        "title": "Trilocale Test Inbox",
        "city": "Roma",
        "listing_code": "OM-L-TESTINQ",
        "owner_user_id": uid,
        "agency_id": "_private_listings",
        "is_private_listing": True,
        "status": "active",
        "created_at": now,
    })
    db.listing_inquiries.insert_one({
        "id": inq_id,
        "property_id": pid,
        "owner_user_id": uid,
        "name": "Mario",
        "surname": "Rossi",
        "email": f"buyer-{TS}@example.com",
        "phone": "3339998877",
        "message": "Vorrei info e visita weekend",
        "visit_requested": True,
        "visit_status": "requested",
        "archived": False,
        "read_at": None,
        "seller_note": "",
        "created_at": now,
        "updated_at": now,
        "source": "ImmobilCloud",
        "gdpr_consent": True,
    })

    csrf = _csrf(s)
    r = s.get(f"{API}/cloud/me/inquiries/summary", timeout=20)
    assert r.status_code == 200, r.text
    summary = r.json()
    assert summary["unread"] >= 1
    assert summary["visits_pending"] >= 1

    r = s.get(f"{API}/cloud/me/inquiries", params={"filter": "open"}, timeout=20)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert any(i["id"] == inq_id for i in items)
    hit = next(i for i in items if i["id"] == inq_id)
    assert hit["visit_status"] == "requested"
    assert hit["is_read"] is False
    assert hit["property_title"] == "Trilocale Test Inbox"

    r = s.patch(
        f"{API}/cloud/me/inquiries/{inq_id}",
        json={"read": True, "visit_status": "accepted", "seller_note": "Sabato 10:00"},
        headers={"X-CSRF-Token": csrf, "Content-Type": "application/json"},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    item = r.json()["item"]
    assert item["is_read"] is True
    assert item["visit_status"] == "accepted"
    assert item["seller_note"] == "Sabato 10:00"

    stored = db.listing_inquiries.find_one({"id": inq_id})
    assert stored["visit_status"] == "accepted"
    assert stored.get("read_at")

    # cleanup
    db.listing_inquiries.delete_one({"id": inq_id})
    db.properties.delete_one({"id": pid})
    db.users.delete_one({"id": uid})


def test_patch_me_phone_whatsapp():
    s = requests.Session()
    user = _register_seller(s)
    csrf = _csrf(s)
    r = s.patch(
        f"{API}/auth/me",
        json={"phone": "3401234567", "whatsapp": "3401234567"},
        headers={"X-CSRF-Token": csrf, "Content-Type": "application/json"},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["phone"] == "3401234567"
    assert body["whatsapp"] == "3401234567"
