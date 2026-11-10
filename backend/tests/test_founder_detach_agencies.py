"""D-153 — super_admin can detach from client agencies."""
from __future__ import annotations

import os
import uuid

import pytest
import requests
from pymongo import MongoClient

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://127.0.0.1:43121"
API = f"{BASE.rstrip('/')}/api"


def _db():
    return MongoClient(os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017"))[
        os.environ.get("DB_NAME", "omnia")
    ]


def _bearer_login(email: str, password: str) -> requests.Session:
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, r.text
    tok = s.cookies.get("access_token")
    if not tok:
        raw = r.headers.get("Set-Cookie") or ""
        for part in raw.split(","):
            if "access_token=" in part:
                tok = part.split("access_token=", 1)[1].split(";", 1)[0].strip()
                break
    assert tok
    s.headers["Authorization"] = f"Bearer {tok}"
    return s


@pytest.mark.skipif(
    not (os.environ.get("ADMIN_EMAIL") and os.environ.get("ADMIN_PASSWORD")),
    reason="ADMIN_EMAIL/PASSWORD required",
)
def test_detach_founder_clears_agency_membership():
    email = os.environ["ADMIN_EMAIL"]
    password = os.environ["ADMIN_PASSWORD"]
    db = _db()
    fake_aid = f"fake-agency-{uuid.uuid4().hex[:8]}"
    db.users.update_one(
        {"email": email.lower()},
        {"$set": {"agency_ids": [fake_aid], "active_agency_id": fake_aid}},
    )
    s = _bearer_login(email, password)
    me = s.get(f"{API}/auth/me", timeout=30)
    assert me.status_code == 200
    assert me.json().get("role") == "super_admin"

    r = s.post(f"{API}/app/ops/detach-founder-agencies", timeout=30)
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True
    assert r.json().get("agency_ids") == []

    me2 = s.get(f"{API}/auth/me", timeout=30).json()
    assert not (me2.get("agency_ids") or [])
    assert not me2.get("active_agency_id")
