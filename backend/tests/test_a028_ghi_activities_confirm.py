"""A-028g/h — confirm-apply audit + activities CRUD smoke."""
from __future__ import annotations

import os
import uuid

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:43121").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ.get("OMNIA_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("OMNIA_ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD")

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia_db")


@pytest.fixture(scope="module")
def mongo_db():
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]


@pytest.fixture(scope="module")
def admin_session():
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        pytest.skip("ADMIN credentials missing")
    s = requests.Session()
    r = s.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return s


def test_confirm_apply_writes_audit(admin_session, mongo_db):
    proposal_id = str(uuid.uuid4())
    r = admin_session.post(
        f"{API}/app/al/confirm-apply",
        json={
            "proposal_id": proposal_id,
            "field": "title",
            "property_id": None,
            "previous_text": "Vecchio titolo",
            "new_text": "Nuovo titolo professionale zona centro",
        },
        timeout=20,
    )
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body.get("ok") is True
    assert body.get("field") == "title"
    audit_id = body.get("audit_id")
    assert audit_id
    doc = mongo_db.al_audit.find_one({"id": audit_id}, {"_id": 0})
    assert doc is not None
    assert doc.get("kind") == "apply_confirmed"
    assert doc.get("proposal_id") == proposal_id


def test_activities_crud_and_today_queue(admin_session, mongo_db):
    title = f"TEST follow-up {uuid.uuid4().hex[:8]}"
    r = admin_session.post(
        f"{API}/app/activities",
        json={
            "title": title,
            "kind": "follow_up",
            "due_at": "2020-01-01T12:00:00.000Z",  # overdue
        },
        timeout=20,
    )
    assert r.status_code == 201, r.text[:300]
    act = r.json()
    act_id = act["id"]
    assert act["status"] == "open"

    listed = admin_session.get(f"{API}/app/activities?status=open&due=overdue&limit=50", timeout=20)
    assert listed.status_code == 200
    ids = {i["id"] for i in listed.json().get("items") or []}
    assert act_id in ids

    today = admin_session.get(f"{API}/app/dashboard/today", timeout=20)
    assert today.status_code == 200
    groups = today.json().get("actions") or []
    act_group = next((g for g in groups if g.get("id") == "activities_open"), None)
    assert act_group is not None, "dashboard today should surface open activities"
    assert act_group.get("count", 0) >= 1

    done = admin_session.patch(
        f"{API}/app/activities/{act_id}",
        json={"status": "done"},
        timeout=20,
    )
    assert done.status_code == 200
    assert done.json().get("status") == "done"

    deleted = admin_session.delete(f"{API}/app/activities/{act_id}", timeout=20)
    assert deleted.status_code == 204
