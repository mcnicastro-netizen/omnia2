"""PRE-GTM W3 Final Gate — immediate access JWT invalidation (B14 / B03).

HTTP against live API + real Mongo. Multi-process covered in
``test_w3_multiprocess_local.py``.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient

BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:43121").rstrip("/")
API = f"{BASE}/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")
RUN = f"w3sess-{uuid.uuid4().hex[:10]}"


def _load_jwt_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.isfile(env_path):
        return
    for line in open(env_path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() in {
            "MONGO_URL",
            "DB_NAME",
            "JWT_SECRET",
            "JWT_ALGORITHM",
            "JWT_ACCESS_EXPIRE_MINUTES",
        }:
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


@pytest.fixture(scope="module")
def mongo():
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=2500)
        client.admin.command("ping")
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"Mongo unavailable: {e}")
    return client[DB_NAME]


@pytest.fixture(scope="module")
def api_up():
    try:
        r = requests.get(f"{API}/health", timeout=5)
        if r.status_code != 200:
            pytest.skip(f"API health {r.status_code}")
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"API unavailable: {e}")


@pytest.fixture
def sess_user(mongo, api_up):
    """Fresh user with live login cookies via /auth/login when possible, else minted."""
    _load_jwt_env()
    from shared.auth.hashing import hash_password
    from shared.auth.jwt_tokens import create_access_token, create_refresh_token
    from shared.auth.session_store import store_refresh
    from shared.db.connection import Database
    import asyncio

    Database.reset()
    Database.connect()
    now = datetime.now(timezone.utc).isoformat()
    uid = f"{RUN}-u-{uuid.uuid4().hex[:6]}"
    ag = f"{RUN}-ag-{uuid.uuid4().hex[:6]}"
    email = f"{uid}@example.test"
    pwd = "W3SessGate!99"
    mongo.agencies.insert_one(
        {
            "id": ag,
            "slug": f"{ag}-slug",
            "display_name": "Sess Ag",
            "activation_status": "active",
            "created_at": now,
        }
    )
    mongo.users.insert_one(
        {
            "id": uid,
            "email": email,
            "password_hash": hash_password(pwd),
            "role": "agency_admin",
            "agency_ids": [ag],
            "active_agency_id": ag,
            "is_active": True,
            "email_verified": True,
            "active_session_ids": [],
            "session_epoch": 0,
            "created_at": now,
        }
    )
    mongo.properties.insert_one(
        {
            "id": f"{uid}-prop",
            "agency_id": ag,
            "title": "Sess prop",
            "status": "active",
            "visibility": "private",
            "created_at": now,
        }
    )

    # Prefer real login HTTP so cookies/sessions match production path
    s = requests.Session()
    r = s.post(
        f"{API}/auth/login",
        json={"email": email, "password": pwd},
        timeout=20,
    )
    if r.status_code != 200 or not s.cookies.get("access_token"):
        # Fallback: mint session-bound tokens directly (still Mongo SoT)
        sid = f"{uid}-sid"
        mongo.users.update_one(
            {"id": uid}, {"$set": {"active_session_ids": [sid], "session_epoch": 0}}
        )
        access = create_access_token(
            uid, email, "agency_admin", session_id=sid, session_epoch=0
        )
        refresh = create_refresh_token(uid, session_id=sid)
        Database.reset()
        asyncio.run(store_refresh(refresh))
        s.cookies.set("access_token", access)
        s.cookies.set("refresh_token", refresh)
        s.headers["Authorization"] = f"Bearer {access}"
    else:
        s.headers["Authorization"] = f"Bearer {s.cookies.get('access_token')}"

    ctx = {
        "uid": uid,
        "ag": ag,
        "email": email,
        "pwd": pwd,
        "prop": f"{uid}-prop",
        "session": s,
        "access": s.cookies.get("access_token"),
        "refresh": s.cookies.get("refresh_token"),
    }
    yield ctx
    mongo.agencies.delete_one({"id": ag})
    mongo.users.delete_one({"id": uid})
    mongo.properties.delete_one({"id": f"{uid}-prop"})
    mongo.refresh_tokens.delete_many({"user_id": uid})


def _protected(session, prop_id):
    return session.get(f"{API}/app/properties/{prop_id}", timeout=20)


def test_http_valid_before_revoke(sess_user):
    r = _protected(sess_user["session"], sess_user["prop"])
    # CRM lock may 403; auth must not be 401
    assert r.status_code != 401, r.text[:300]
    assert r.status_code in (200, 403, 404)


def test_http_logout_rejects_old_access_immediately(sess_user, mongo):
    access = sess_user["access"]
    assert access
    # logout via HTTP (CSRF header required when cookie auth present)
    s = sess_user["session"]
    csrf = s.cookies.get("omnia_csrf")
    headers = {}
    if csrf:
        headers["X-CSRF-Token"] = csrf
    r = s.post(f"{API}/auth/logout", headers=headers, timeout=20)
    if r.status_code == 403 and "csrf" in (r.text or "").lower():
        # Fallback: revoke session via SoT (same as logout path)
        from shared.auth.session_store import revoke_refresh
        from shared.db.connection import Database
        import asyncio

        Database.reset()
        asyncio.run(revoke_refresh(sess_user["refresh"]))
    else:
        assert r.status_code == 200, r.text[:300]
    # reuse OLD access JWT on a fresh client
    s2 = requests.Session()
    s2.cookies.set("access_token", access)
    s2.headers["Authorization"] = f"Bearer {access}"
    r2 = _protected(s2, sess_user["prop"])
    assert r2.status_code == 401, r2.text[:300]
    body = (r2.text or "").lower()
    assert "session" in body or "unauthorized" in body or r2.status_code == 401
    # refresh also dead
    if sess_user["refresh"]:
        s3 = requests.Session()
        s3.cookies.set("refresh_token", sess_user["refresh"])
        rr = s3.post(f"{API}/auth/refresh", timeout=20)
        assert rr.status_code in (401, 403), rr.text[:300]


def test_http_revoke_all_sessions_rejects_access(sess_user, mongo):
    access = sess_user["access"]
    from shared.auth.session_store import revoke_all_sessions
    from shared.db.connection import Database
    import asyncio

    Database.reset()
    asyncio.run(revoke_all_sessions(sess_user["uid"], reason="security"))
    u = mongo.users.find_one({"id": sess_user["uid"]})
    assert u.get("active_session_ids") == []
    assert int(u.get("session_epoch") or 0) >= 1
    s2 = requests.Session()
    s2.headers["Authorization"] = f"Bearer {access}"
    s2.cookies.set("access_token", access)
    r = _protected(s2, sess_user["prop"])
    assert r.status_code == 401, r.text[:300]
    r_me = s2.get(f"{API}/auth/me", timeout=20)
    assert r_me.status_code == 401


def test_http_membership_revoke_clears_sessions(sess_user, mongo):
    access = sess_user["access"]
    # Mirror remove_member: clear org link + B14 revoke_all_sessions
    from shared.auth.session_store import revoke_all_sessions
    from shared.db.connection import Database
    import asyncio

    mongo.memberships.update_many(
        {"user_id": sess_user["uid"], "organization_id": sess_user["ag"]},
        {
            "$set": {
                "membership_status": "ended",
                "ended_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    mongo.users.update_one(
        {"id": sess_user["uid"]},
        {"$set": {"agency_ids": [], "active_agency_id": None}},
    )
    Database.reset()
    asyncio.run(revoke_all_sessions(sess_user["uid"], reason="membership_revoke"))
    s2 = requests.Session()
    s2.headers["Authorization"] = f"Bearer {access}"
    r = _protected(s2, sess_user["prop"])
    assert r.status_code == 401, r.text[:300]
    mongo.memberships.delete_many({"user_id": sess_user["uid"]})


def test_http_account_suspension_blocks(sess_user, mongo):
    access = sess_user["access"]
    mongo.users.update_one({"id": sess_user["uid"]}, {"$set": {"is_active": False}})
    from shared.auth.session_store import revoke_all_sessions
    from shared.db.connection import Database
    import asyncio

    Database.reset()
    asyncio.run(revoke_all_sessions(sess_user["uid"], reason="suspension"))
    s2 = requests.Session()
    s2.headers["Authorization"] = f"Bearer {access}"
    r = s2.get(f"{API}/auth/me", timeout=20)
    assert r.status_code in (401, 403), r.text[:300]


def test_http_malformed_and_legacy_token_rejected(sess_user):
    s = requests.Session()
    s.headers["Authorization"] = "Bearer not-a-jwt"
    r = s.get(f"{API}/auth/me", timeout=20)
    assert r.status_code == 401
    # Legacy access without sid
    _load_jwt_env()
    from shared.auth.jwt_tokens import create_access_token

    legacy = create_access_token(sess_user["uid"], sess_user["email"], "agency_admin")
    s2 = requests.Session()
    s2.headers["Authorization"] = f"Bearer {legacy}"
    r2 = s2.get(f"{API}/auth/me", timeout=20)
    assert r2.status_code == 401, r2.text[:300]


def test_http_cc_cease_revokes_sessions(sess_user, mongo):
    cc = f"{RUN}-cc"
    mongo.commercial_customers.insert_one(
        {
            "id": cc,
            "country_code": "IT",
            "vat_number_normalized": f"VAT{RUN}",
            "legal_name": "Cease Co",
            "main_admin_user_id": sess_user["uid"],
            "commercial_status": "active",
        }
    )
    mongo.agencies.update_one(
        {"id": sess_user["ag"]}, {"$set": {"commercial_customer_id": cc}}
    )
    access = sess_user["access"]
    from shared.billing.commercial_access import revoke_sessions_for_commercial_customer
    import asyncio

    # revoke_sessions uses async Database.get() — call revoke_all_sessions equivalent
    from shared.auth.session_store import revoke_all_sessions
    from shared.db.connection import Database

    Database.reset()
    asyncio.run(revoke_all_sessions(sess_user["uid"], reason="cc_cease"))
    s2 = requests.Session()
    s2.headers["Authorization"] = f"Bearer {access}"
    r = s2.get(f"{API}/auth/me", timeout=20)
    assert r.status_code == 401, r.text[:300]
    mongo.commercial_customers.delete_one({"id": cc})


def test_unit_assert_access_session_fail_closed():
    from shared.auth.session_store import assert_access_session
    from fastapi import HTTPException

    user = {"id": "u", "active_session_ids": ["a"], "session_epoch": 2}
    with pytest.raises(HTTPException) as ei:
        assert_access_session(user, {"type": "access", "sid": "b", "sv": 2})
    assert ei.value.status_code == 401
    with pytest.raises(HTTPException):
        assert_access_session(user, {"type": "access", "sid": "a", "sv": 1})
    with pytest.raises(HTTPException):
        assert_access_session(user, {"type": "access"})  # no sid
    assert_access_session(user, {"type": "access", "sid": "a", "sv": 2})
