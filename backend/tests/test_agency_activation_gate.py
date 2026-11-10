"""Agency CRM stays pending until Ops activate; create forces active_agency_id."""
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


def test_create_agency_pending_blocks_kpis_and_activate_unlocks():
    email = f"act-{uuid.uuid4().hex[:10]}@example.com"
    password = "TestPass123!"
    seed_agency_id = f"seed-{uuid.uuid4().hex[:8]}"
    db = _db()

    # Pre-attach a fake membership so we can prove force_active switches away from it
    db.agencies.insert_one(
        {
            "id": seed_agency_id,
            "slug": f"seed-{uuid.uuid4().hex[:6]}",
            "display_name": "Seed Leak Agency",
            "owner_id": "nobody",
            "is_active": True,
            "activation_status": "active",
            "onboarding_completed": True,
            "plan": "free",
            "fiscal": {},
            "address": {},
            "contact": {},
            "branding": {},
            "website": {},
        }
    )
    # Extra fake member on seed (would show as «2 collaboratori» if active stayed on seed)
    fake_email = f"fake-{uuid.uuid4().hex[:6]}@example.com"
    db.users.insert_one(
        {
            "id": f"fake-{uuid.uuid4().hex[:8]}",
            "email": fake_email,
            "name": "Fake Collab",
            "role": "agent",
            "agency_ids": [seed_agency_id],
            "active_agency_id": seed_agency_id,
            "is_active": True,
            "password_hash": "x",
        }
    )

    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "password": password, "name": "Act Tester", "role": "client", "lang": "it"},
        timeout=30,
    )
    assert r.status_code in (200, 201), r.text
    # Simulate leaked active_agency before create
    db.users.update_one(
        {"email": email},
        {"$set": {"agency_ids": [seed_agency_id], "active_agency_id": seed_agency_id}},
    )

    s = _bearer_login(email, password)
    name = f"Agenzia Act {uuid.uuid4().hex[:6]}"
    create = s.post(
        f"{API}/app/agencies",
        json={
            "display_name": name,
            "fiscal": {"legal_name": f"{name} SRL"},
            "address": {"street": "Via Test 1", "city": "Roma", "province": "RM", "postal_code": "00100"},
        },
        timeout=30,
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body.get("activation_status") == "pending"
    aid = body.get("id")

    me = s.get(f"{API}/auth/me", timeout=30).json()
    assert me.get("active_agency_id") == aid
    assert aid in (me.get("agency_ids") or [])

    kpis = s.get(f"{API}/app/dashboard/kpis", timeout=30)
    assert kpis.status_code == 403, kpis.text
    detail = kpis.json().get("detail")
    if isinstance(detail, dict):
        assert detail.get("code") == "agency_pending_activation" or detail.get("error") == "agency_pending_activation"

    props = s.get(f"{API}/app/properties", timeout=30)
    assert props.status_code == 403, props.text

    members = s.get(f"{API}/app/agencies/me/members", timeout=30)
    assert members.status_code == 200
    member_ids = [m.get("id") for m in members.json()]
    assert me.get("id") in member_ids
    # Must not list the fake seed collaborator under the new agency
    assert fake_email not in [m.get("email") for m in members.json()]

    # Activate without Ops JWT: use Mongo + call activate as… need super_admin.
    # Promote temp: set activation via Ops endpoint if ADMIN available, else direct Mongo + re-check.
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if admin_email and admin_password:
        ops = _bearer_login(admin_email, admin_password)
        act = ops.post(
            f"{API}/app/ops/activate-agency",
            json={
                "agency_id": aid,
                "grant_plan": False,
                "send_email": False,
                "credits": 0,
                "require_kyc_verified": False,
                "require_payment": False,
                "issue_login_credential": False,
            },
            timeout=30,
        )
        assert act.status_code == 200, act.text
        assert act.json().get("activation_status") == "active"
    else:
        db.agencies.update_one(
            {"id": aid},
            {"$set": {"activation_status": "active", "activated_at": "2026-01-01T00:00:00+00:00"}},
        )

    kpis2 = s.get(f"{API}/app/dashboard/kpis", timeout=30)
    assert kpis2.status_code == 200, kpis2.text
    # Only owner on new agency → members KPI should be 1 (not seed's 2)
    members_kpi = next((k for k in kpis2.json() if k.get("key") == "members_active"), None)
    assert members_kpi is not None
    assert int(members_kpi.get("value") or 0) == 1

    # cleanup
    db.agencies.delete_many({"id": {"$in": [aid, seed_agency_id]}})
    db.users.delete_many({"email": {"$in": [email, fake_email]}})
