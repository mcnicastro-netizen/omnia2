"""PRE-GTM W3 — multi-process session revocation (B14).

Two distinct uvicorn processes share MongoDB. Access JWT revoked on A must be
rejected immediately on B. NOT Railway-equivalent.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient

BASE_PRIMARY = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:43121").rstrip("/")
API_PRIMARY = f"{BASE_PRIMARY}/api"
SECONDARY_PORT = int(os.environ.get("W3_MP_PORT", "43122"))
API_SECONDARY = f"http://127.0.0.1:{SECONDARY_PORT}/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")
RUN = f"w3mp-{uuid.uuid4().hex[:8]}"
BACKEND = Path(__file__).resolve().parents[1]


def _load_jwt_env():
    env_path = BACKEND / ".env"
    if not env_path.is_file():
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
def primary_up():
    try:
        r = requests.get(f"{API_PRIMARY}/health", timeout=5)
        if r.status_code != 200:
            pytest.skip(f"primary API health {r.status_code}")
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"primary API unavailable: {e}")


@pytest.fixture(scope="module")
def secondary(primary_up, mongo):
    env = os.environ.copy()
    env.setdefault("MONGO_URL", MONGO_URL)
    env.setdefault("DB_NAME", DB_NAME)
    py = BACKEND / ".venv" / "bin" / "python3"
    if not py.is_file():
        py = Path(sys.executable)
    cmd = [
        str(py),
        "-m",
        "uvicorn",
        "server:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(SECONDARY_PORT),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(BACKEND),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ok = False
    for _ in range(40):
        try:
            r = requests.get(f"{API_SECONDARY}/health", timeout=1)
            if r.status_code == 200:
                ok = True
                break
        except Exception:  # noqa: BLE001
            pass
        if proc.poll() is not None:
            break
        time.sleep(0.25)
    if not ok:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except Exception:  # noqa: BLE001
            proc.kill()
        pytest.skip("secondary uvicorn failed to become healthy")
    yield proc
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=8)
    except Exception:  # noqa: BLE001
        proc.kill()


@pytest.fixture(scope="module")
def mp_seed(mongo, secondary):
    _load_jwt_env()
    from shared.auth.hashing import hash_password
    from shared.auth.jwt_tokens import create_access_token, create_refresh_token
    from shared.auth.session_store import store_refresh
    from shared.db.connection import Database
    import asyncio

    Database.connect()
    now = datetime.now(timezone.utc).isoformat()
    ag = f"{RUN}-ag"
    u = f"{RUN}-user"
    p = f"{RUN}-prop"
    sid = f"{RUN}-sid"
    mongo.agencies.insert_one(
        {
            "id": ag,
            "slug": f"{ag}-slug",
            "display_name": "MP A",
            "activation_status": "active",
            "created_at": now,
        }
    )
    mongo.users.insert_one(
        {
            "id": u,
            "email": f"{u}@example.test",
            "password_hash": hash_password("W3Mp!99"),
            "role": "agency_admin",
            "agency_ids": [ag],
            "active_agency_id": ag,
            "is_active": True,
            "email_verified": True,
            "active_session_ids": [sid],
            "session_epoch": 0,
            "created_at": now,
        }
    )
    mongo.properties.insert_one(
        {
            "id": p,
            "agency_id": ag,
            "title": "MP prop",
            "status": "active",
            "visibility": "private",
            "created_at": now,
        }
    )
    access = create_access_token(
        u, f"{u}@example.test", "agency_admin", session_id=sid, session_epoch=0
    )
    refresh = create_refresh_token(u, session_id=sid)
    Database.reset()
    asyncio.run(store_refresh(refresh))
    ctx = {"ag": ag, "u": u, "p": p, "sid": sid, "access": access, "refresh": refresh}
    yield ctx
    mongo.agencies.delete_one({"id": ag})
    mongo.users.delete_one({"id": u})
    mongo.properties.delete_one({"id": p})
    mongo.refresh_tokens.delete_many({"user_id": u})


def _auth_get(api_base: str, path: str, tok: str):
    return requests.get(
        f"{api_base}{path}",
        headers={"Authorization": f"Bearer {tok}"},
        cookies={"access_token": tok},
        timeout=15,
    )


def test_mp_health_both_processes(secondary):
    r1 = requests.get(f"{API_PRIMARY}/health", timeout=10)
    r2 = requests.get(f"{API_SECONDARY}/health", timeout=10)
    assert r1.status_code == 200
    assert r2.status_code == 200


def test_mp_same_jwt_accepted_on_both_before_revoke(mp_seed):
    r1 = _auth_get(API_PRIMARY, f"/app/properties/{mp_seed['p']}", mp_seed["access"])
    r2 = _auth_get(API_SECONDARY, f"/app/properties/{mp_seed['p']}", mp_seed["access"])
    assert r1.status_code == r2.status_code
    assert r1.status_code != 401
    assert r1.status_code in (200, 403, 404)


def test_mp_revoke_on_a_rejects_access_on_b_immediately(mp_seed, mongo):
    """Core B14 proof: revoke via process A's Mongo path → B rejects access JWT."""
    from shared.auth.session_store import revoke_all_sessions
    from shared.db.connection import Database
    import asyncio

    # Confirm still valid on B
    pre = _auth_get(API_SECONDARY, "/auth/me", mp_seed["access"])
    assert pre.status_code == 200, pre.text[:300]

    # Revoke through shared Mongo (same path process A would use)
    Database.reset()
    asyncio.run(revoke_all_sessions(mp_seed["u"], reason="security"))

    # Immediate reject on B (different process)
    post = _auth_get(API_SECONDARY, "/auth/me", mp_seed["access"])
    assert post.status_code == 401, post.text[:300]
    post2 = _auth_get(API_PRIMARY, "/auth/me", mp_seed["access"])
    assert post2.status_code == 401, post2.text[:300]
    # Protected resource too
    prop = _auth_get(API_SECONDARY, f"/app/properties/{mp_seed['p']}", mp_seed["access"])
    assert prop.status_code == 401


def test_mp_refresh_rejected_after_revoke(mp_seed):
    s = requests.Session()
    s.cookies.set("refresh_token", mp_seed["refresh"])
    # already revoked in previous test if order depends — re-seed refresh path
    from shared.auth.session_store import revoke_all_sessions, store_refresh, register_session
    from shared.auth.jwt_tokens import create_access_token, create_refresh_token
    import asyncio

    # Open a fresh session, confirm refresh works on B, then revoke, reject on B
    async def _prep():
        await revoke_all_sessions(mp_seed["u"], reason="reset")
        sid, epoch = await register_session(mp_seed["u"])
        access = create_access_token(
            mp_seed["u"],
            f"{mp_seed['u']}@example.test",
            "agency_admin",
            session_id=sid,
            session_epoch=epoch,
        )
        refresh = create_refresh_token(mp_seed["u"], session_id=sid)
        await store_refresh(refresh)
        return access, refresh

    from shared.db.connection import Database

    Database.reset()
    access, refresh = asyncio.run(_prep())
    # refresh OK on secondary before revoke
    s = requests.Session()
    s.cookies.set("refresh_token", refresh)
    ok = s.post(f"{API_SECONDARY}/auth/refresh", timeout=15)
    assert ok.status_code == 200, ok.text[:300]
    # revoke all
    Database.reset()
    asyncio.run(revoke_all_sessions(mp_seed["u"], reason="security"))
    bad = s.post(f"{API_SECONDARY}/auth/refresh", timeout=15)
    assert bad.status_code in (401, 403), bad.text[:300]
    # old access also dead on B
    assert _auth_get(API_SECONDARY, "/auth/me", access).status_code == 401


def test_mp_membership_revoke_cross_process(mp_seed, mongo):
    from shared.auth.session_store import revoke_all_sessions, register_session, store_refresh
    from shared.auth.jwt_tokens import create_access_token, create_refresh_token
    from shared.db.connection import Database
    import asyncio

    async def _prep():
        await revoke_all_sessions(mp_seed["u"], reason="reset")
        sid, epoch = await register_session(mp_seed["u"])
        access = create_access_token(
            mp_seed["u"],
            f"{mp_seed['u']}@example.test",
            "agency_admin",
            session_id=sid,
            session_epoch=epoch,
        )
        refresh = create_refresh_token(mp_seed["u"], session_id=sid)
        await store_refresh(refresh)
        return access

    Database.reset()
    access = asyncio.run(_prep())
    assert _auth_get(API_SECONDARY, "/auth/me", access).status_code == 200
    # membership revoke scope: clear agency + sessions
    mongo.users.update_one(
        {"id": mp_seed["u"]},
        {"$set": {"agency_ids": [], "active_agency_id": None}},
    )
    Database.reset()
    asyncio.run(revoke_all_sessions(mp_seed["u"], reason="membership_revoke"))
    assert _auth_get(API_SECONDARY, "/auth/me", access).status_code == 401
    assert _auth_get(API_PRIMARY, f"/app/properties/{mp_seed['p']}", access).status_code == 401
