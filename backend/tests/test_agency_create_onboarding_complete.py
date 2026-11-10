"""Create agency from onboarding marks onboarding_completed + promotes role."""
from __future__ import annotations

import os
import uuid

import pytest
import requests
from pymongo import MongoClient

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://127.0.0.1:43121"
API = f"{BASE.rstrip('/')}/api"


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


def test_create_agency_promotes_and_completes_onboarding():
    email = f"onb-{uuid.uuid4().hex[:10]}@example.com"
    password = "TestPass123!"
    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "password": password, "name": "Onb Tester", "role": "client", "lang": "it"},
        timeout=30,
    )
    assert r.status_code in (200, 201), r.text

    s = _bearer_login(email, password)
    me = s.get(f"{API}/auth/me", timeout=30)
    assert me.status_code == 200
    assert me.json().get("role") == "client"

    name = f"Agenzia Onb {uuid.uuid4().hex[:6]}"
    create = s.post(
        f"{API}/app/agencies",
        json={
            "display_name": name,
            "fiscal": {"legal_name": f"{name} SRL"},
            "address": {"street": "Via Test 1", "city": "Roma", "province": "RM", "postal_code": "00100"},
            "contact": {
                "email": email,
                "phone": "+39 06 12345678",
                "pec": f"pec-{uuid.uuid4().hex[:8]}@pec.it",
            },
        },
        timeout=30,
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body.get("onboarding_completed") is True
    assert body.get("activation_status") == "pending"
    aid = body.get("id")

    me2 = s.get(f"{API}/auth/me", timeout=30)
    assert me2.status_code == 200
    assert me2.json().get("role") == "agency_admin"
    assert aid in (me2.json().get("agency_ids") or [])
    assert me2.json().get("active_agency_id") == aid

    # cleanup
    db = MongoClient(os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017"))[
        os.environ.get("DB_NAME", "omnia")
    ]
    db.agencies.delete_many({"id": aid})
    db.users.delete_many({"email": email})
