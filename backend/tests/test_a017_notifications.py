"""A-017 notification center API smoke."""
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import requests

BASE = os.environ.get("OMNIA_TEST_BASE", "http://127.0.0.1:43121")
EMAIL = os.environ.get("OMNIA_TEST_EMAIL", "mcnicastro@gmail.com")
PASSWORD = os.environ.get("OMNIA_TEST_PASSWORD", "OmniaFounder2026!")


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"login failed: {r.status_code}")
    return s


def _seed_notification(user_id: str) -> str:
    from pymongo import MongoClient

    mongo = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo or not db_name:
        pytest.skip("MONGO_URL/DB_NAME missing")
    client = MongoClient(mongo)
    nid = str(uuid4())
    client[db_name]["notifications"].insert_one(
        {
            "id": nid,
            "user_id": user_id,
            "agency_id": None,
            "type": "lead_new",
            "title": "Test notifica A-017",
            "body": "Smoke seed",
            "link": "/app/clients",
            "meta": {"test": True},
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read_at": None,
        }
    )
    return nid


def test_notifications_list_and_unread(session):
    r = session.get(f"{BASE}/api/notifications", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body
    assert "unread_count" in body
    assert isinstance(body["items"], list)

    r2 = session.get(f"{BASE}/api/notifications/unread-count", timeout=15)
    assert r2.status_code == 200
    assert "unread_count" in r2.json()


def test_notifications_mark_read_flow(session):
    me = session.get(f"{BASE}/api/auth/me", timeout=15)
    assert me.status_code == 200
    uid = me.json()["id"]
    nid = _seed_notification(uid)

    r = session.get(f"{BASE}/api/notifications", params={"unread_only": True}, timeout=15)
    assert r.status_code == 200
    ids = {i["id"] for i in r.json()["items"]}
    assert nid in ids
    assert r.json()["unread_count"] >= 1

    r2 = session.post(f"{BASE}/api/notifications/{nid}/read", timeout=15)
    assert r2.status_code == 200, r2.text

    r3 = session.get(f"{BASE}/api/notifications", params={"unread_only": True}, timeout=15)
    assert nid not in {i["id"] for i in r3.json()["items"]}

    session.post(f"{BASE}/api/notifications/read-all", timeout=15)
