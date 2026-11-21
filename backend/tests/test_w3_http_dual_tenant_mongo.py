"""PRE-GTM W3 — HTTP dual-tenant isolation against real local Mongo (+ live API).

This is NOT FakeDB. It seeds two agencies into the configured MongoDB and hits
the running API (REACT_APP_BACKEND_URL / 127.0.0.1:43121) with real JWTs.

Skipped when Mongo or API is unreachable.
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
RUN = f"w3dt-{uuid.uuid4().hex[:10]}"


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


@pytest.fixture(scope="module")
def dual(mongo, api_up):
    """Seed agency A/B + users + properties; yield auth helpers; cleanup."""
    _load_jwt_env()
    from shared.auth.hashing import hash_password
    from shared.auth.jwt_tokens import create_access_token

    now = datetime.now(timezone.utc).isoformat()
    ag_a, ag_b = f"{RUN}-agA", f"{RUN}-agB"
    u_a, u_b = f"{RUN}-userA", f"{RUN}-userB"
    p_a, p_b = f"{RUN}-propA", f"{RUN}-propB"
    deal_ab = f"{RUN}-dealAB"
    vid_a = f"{RUN}-vidA"

    mongo.agencies.insert_many(
        [
            {
                "id": ag_a,
                "slug": f"{ag_a}-slug",
                "display_name": "W3 Dual A",
                "activation_status": "active",
                "created_at": now,
            },
            {
                "id": ag_b,
                "slug": f"{ag_b}-slug",
                "display_name": "W3 Dual B",
                "activation_status": "active",
                "created_at": now,
            },
        ]
    )
    pwd = hash_password("W3DualTenant!99")
    mongo.users.insert_many(
        [
            {
                "id": u_a,
                "email": f"{u_a}@example.test",
                "password_hash": pwd,
                "role": "agency_admin",
                "agency_ids": [ag_a],
                "active_agency_id": ag_a,
                "is_active": True,
                "created_at": now,
            },
            {
                "id": u_b,
                "email": f"{u_b}@example.test",
                "password_hash": pwd,
                "role": "agency_admin",
                "agency_ids": [ag_b],
                "active_agency_id": ag_b,
                "is_active": True,
                "created_at": now,
            },
        ]
    )
    mongo.properties.insert_many(
        [
            {
                "id": p_a,
                "agency_id": ag_a,
                "title": "Prop A secret",
                "status": "active",
                "visibility": "private",
                "created_at": now,
            },
            {
                "id": p_b,
                "agency_id": ag_b,
                "title": "Prop B secret",
                "status": "active",
                "visibility": "private",
                "created_at": now,
            },
        ]
    )
    mongo.deals.insert_one(
        {
            "id": deal_ab,
            "agency_id": ag_a,
            "partner_agency_id": ag_b,
            "status": "open",
            "property_id": p_a,
            "created_at": now,
        }
    )
    mongo.videos.insert_one(
        {
            "id": vid_a,
            "agency_id": ag_a,
            "property_id": p_a,
            "status": "ready",
            "mode": "ken_burns",
            "created_at": now,
        }
    )
    mongo.activities.insert_many(
        [
            {
                "id": f"{RUN}-actA",
                "agency_id": ag_a,
                "title": "Act A",
                "status": "open",
                "created_at": now,
            },
            {
                "id": f"{RUN}-actB",
                "agency_id": ag_b,
                "title": "Act B",
                "status": "open",
                "created_at": now,
            },
        ]
    )
    collab_id = f"{RUN}-collab"
    dr_id = f"{RUN}-dr"
    thread_id = f"{RUN}-thread"
    cal_a = f"{RUN}-calA"
    mongo.mls_collaborations.insert_one(
        {
            "id": collab_id,
            "property_id": p_a,
            "owner_agency_id": ag_a,
            "partner_agency_id": ag_b,
            "status": "active",
            "created_at": now,
        }
    )
    mongo.mls_document_requests.insert_one(
        {
            "id": dr_id,
            "collaboration_id": collab_id,
            "owner_agency_id": ag_a,
            "requesting_agency_id": ag_b,
            "status": "fulfilled",
            "shared_document_ids": ["doc-x"],
            "access_log": [],
            "created_at": now,
        }
    )
    mongo.mls_chat_threads.insert_one(
        {
            "id": thread_id,
            "collaboration_id": collab_id,
            "agency_ids": [ag_a, ag_b],
            "status": "open",
            "created_at": now,
        }
    )
    mongo.calendar_events.insert_one(
        {
            "id": cal_a,
            "agency_id": ag_a,
            "event_type": "visit",
            "title": "Visit A",
            "start_at": now,
            "created_at": now,
        }
    )

    def session_for(user_id: str, email: str, role: str = "agency_admin") -> requests.Session:
        # B14 — bind JWT to Mongo active_session_ids
        sid = f"{RUN}-sid-{user_id[-6:]}"
        mongo.users.update_one(
            {"id": user_id},
            {
                "$addToSet": {"active_session_ids": sid},
                "$setOnInsert": {"session_epoch": 0},
            },
        )
        doc = mongo.users.find_one({"id": user_id}) or {}
        epoch = int(doc.get("session_epoch") or 0)
        tok = create_access_token(
            user_id, email, role, session_id=sid, session_epoch=epoch
        )
        s = requests.Session()
        s.cookies.set("access_token", tok)
        s.headers["Authorization"] = f"Bearer {tok}"
        return s

    ctx = {
        "ag_a": ag_a,
        "ag_b": ag_b,
        "u_a": u_a,
        "u_b": u_b,
        "p_a": p_a,
        "p_b": p_b,
        "deal_ab": deal_ab,
        "vid_a": vid_a,
        "act_a": f"{RUN}-actA",
        "act_b": f"{RUN}-actB",
        "collab": collab_id,
        "dr": dr_id,
        "thread": thread_id,
        "cal_a": cal_a,
        "sess_a": session_for(u_a, f"{u_a}@example.test"),
        "sess_b": session_for(u_b, f"{u_b}@example.test"),
        "session_for": session_for,
    }
    yield ctx

    # cleanup tagged docs
    for coll, field, vals in [
        ("agencies", "id", [ag_a, ag_b]),
        ("users", "id", [u_a, u_b]),
        ("properties", "id", [p_a, p_b]),
        ("deals", "id", [deal_ab]),
        ("videos", "id", [vid_a]),
        ("activities", "id", [f"{RUN}-actA", f"{RUN}-actB"]),
        ("mls_collaborations", "id", [collab_id]),
        ("mls_document_requests", "id", [dr_id]),
        ("mls_chat_threads", "id", [thread_id]),
        ("calendar_events", "id", [cal_a]),
    ]:
        mongo[coll].delete_many({field: {"$in": vals}})


def test_http_property_cross_tenant_404(dual):
    r = dual["sess_a"].get(f"{API}/app/properties/{dual['p_b']}", timeout=20)
    assert r.status_code in (403, 404), r.text[:300]
    r2 = dual["sess_b"].get(f"{API}/app/properties/{dual['p_a']}", timeout=20)
    assert r2.status_code in (403, 404), r2.text[:300]
    # own property may 200 or 404 depending on CRM gate — if 200 must be own
    own = dual["sess_a"].get(f"{API}/app/properties/{dual['p_a']}", timeout=20)
    if own.status_code == 200:
        assert own.json().get("agency_id") == dual["ag_a"]


def test_http_activity_cross_tenant_cannot_mutate(dual):
    r = dual["sess_a"].patch(
        f"{API}/app/activities/{dual['act_b']}",
        json={"status": "done"},
        timeout=20,
    )
    assert r.status_code in (403, 404), r.text[:300]
    r_del = dual["sess_a"].delete(
        f"{API}/app/activities/{dual['act_b']}", timeout=20
    )
    assert r_del.status_code in (403, 404), r_del.text[:300]
    # own activity patch should succeed (or CRM lock 403)
    r_ok = dual["sess_a"].patch(
        f"{API}/app/activities/{dual['act_a']}",
        json={"notes": "w3-ok"},
        timeout=20,
    )
    assert r_ok.status_code in (200, 403), r_ok.text[:300]
    if r_ok.status_code == 200:
        assert r_ok.json().get("agency_id") == dual["ag_a"]


def test_http_deal_outsider_forbidden(dual, mongo):
    # Create outsider C
    ag_c = f"{RUN}-agC"
    u_c = f"{RUN}-userC"
    now = datetime.now(timezone.utc).isoformat()
    mongo.agencies.insert_one(
        {
            "id": ag_c,
            "slug": f"{ag_c}-slug",
            "display_name": "C",
            "activation_status": "active",
        }
    )
    from shared.auth.hashing import hash_password
    from shared.auth.jwt_tokens import create_access_token

    mongo.users.insert_one(
        {
            "id": u_c,
            "email": f"{u_c}@example.test",
            "password_hash": hash_password("x"),
            "role": "agency_admin",
            "agency_ids": [ag_c],
            "active_agency_id": ag_c,
            "is_active": True,
        }
    )
    s = dual["session_for"](u_c, f"{u_c}@example.test")
    r = s.get(f"{API}/app/deals/{dual['deal_ab']}", timeout=20)
    assert r.status_code in (403, 404), r.text[:300]
    # partners/owners ok
    r_a = dual["sess_a"].get(f"{API}/app/deals/{dual['deal_ab']}", timeout=20)
    r_b = dual["sess_b"].get(f"{API}/app/deals/{dual['deal_ab']}", timeout=20)
    assert r_a.status_code in (200, 403, 404), r_a.text[:200]
    assert r_b.status_code in (200, 403, 404), r_b.text[:200]
    if r_a.status_code == 200:
        assert r_a.json().get("agency_id") == dual["ag_a"]
    mongo.agencies.delete_one({"id": ag_c})
    mongo.users.delete_one({"id": u_c})


def test_http_public_video_does_not_leak_agency_private(dual):
    r = requests.get(f"{API}/cloud/videos/{dual['vid_a']}", timeout=20)
    # private agency video on private property must not be public
    assert r.status_code in (403, 404), r.text[:300]


def test_http_unauthenticated_app_wall(dual):
    r = requests.get(f"{API}/app/properties/{dual['p_a']}", timeout=20)
    assert r.status_code in (401, 403)


def test_http_document_request_outsider_denied(dual, mongo):
    ag_c = f"{RUN}-agC2"
    u_c = f"{RUN}-userC2"
    mongo.agencies.insert_one(
        {"id": ag_c, "slug": f"{ag_c}-slug", "display_name": "C2", "activation_status": "active"}
    )
    from shared.auth.hashing import hash_password
    from shared.auth.jwt_tokens import create_access_token

    mongo.users.insert_one(
        {
            "id": u_c,
            "email": f"{u_c}@example.test",
            "password_hash": hash_password("x"),
            "role": "agency_admin",
            "agency_ids": [ag_c],
            "active_agency_id": ag_c,
            "is_active": True,
        }
    )
    s = dual["session_for"](u_c, f"{u_c}@example.test")
    r = s.post(
        f"{API}/app/document-requests/{dual['dr']}/access",
        timeout=20,
    )
    assert r.status_code in (403, 404), r.text[:300]
    # participant B may access consult path (or 403 if CRM locked)
    r_b = dual["sess_b"].post(
        f"{API}/app/document-requests/{dual['dr']}/access",
        timeout=20,
    )
    assert r_b.status_code in (200, 403), r_b.text[:300]
    mongo.agencies.delete_one({"id": ag_c})
    mongo.users.delete_one({"id": u_c})


def test_http_chat_outsider_cannot_post(dual, mongo):
    ag_c = f"{RUN}-agC3"
    u_c = f"{RUN}-userC3"
    mongo.agencies.insert_one(
        {"id": ag_c, "slug": f"{ag_c}-slug", "display_name": "C3", "activation_status": "active"}
    )
    from shared.auth.hashing import hash_password

    mongo.users.insert_one(
        {
            "id": u_c,
            "email": f"{u_c}@example.test",
            "password_hash": hash_password("x"),
            "role": "agency_admin",
            "agency_ids": [ag_c],
            "active_agency_id": ag_c,
            "is_active": True,
        }
    )
    s = dual["session_for"](u_c, f"{u_c}@example.test")
    r = s.post(
        f"{API}/app/collab-chat/threads/{dual['thread']}/messages",
        json={"body": "intrusion"},
        timeout=20,
    )
    assert r.status_code in (403, 404), r.text[:300]
    mongo.agencies.delete_one({"id": ag_c})
    mongo.users.delete_one({"id": u_c})


def test_http_dashboard_requires_agency(dual, mongo):
    """User without active_agency_id must fail closed on dashboard."""
    u_na = f"{RUN}-userNA"
    from shared.auth.hashing import hash_password

    mongo.users.insert_one(
        {
            "id": u_na,
            "email": f"{u_na}@example.test",
            "password_hash": hash_password("x"),
            "role": "agency_admin",
            "agency_ids": [dual["ag_a"]],
            "active_agency_id": None,
            "is_active": True,
        }
    )
    s = dual["session_for"](u_na, f"{u_na}@example.test")
    r = s.get(f"{API}/app/dashboard/kpis", timeout=20)
    assert r.status_code in (400, 403, 404), r.text[:300]
    mongo.users.delete_one({"id": u_na})


def test_http_membership_revoked_denied(dual, mongo):
    """Clear agency membership → app resource denied."""
    u = dual["u_a"]
    before = mongo.users.find_one({"id": u})
    mongo.users.update_one(
        {"id": u},
        {"$set": {"agency_ids": [], "active_agency_id": None}},
    )
    try:
        r = dual["sess_a"].get(f"{API}/app/properties/{dual['p_a']}", timeout=20)
        assert r.status_code in (400, 401, 403, 404), r.text[:300]
    finally:
        mongo.users.update_one(
            {"id": u},
            {
                "$set": {
                    "agency_ids": before.get("agency_ids") or [dual["ag_a"]],
                    "active_agency_id": before.get("active_agency_id") or dual["ag_a"],
                }
            },
        )


def test_http_payload_agency_spoof_ignored_on_activity_create(dual):
    """Client-supplied agency_id must not create activity under tenant B."""
    r = dual["sess_a"].post(
        f"{API}/app/activities",
        json={
            "title": f"spoof-{RUN}",
            "kind": "follow_up",
            "agency_id": dual["ag_b"],
        },
        timeout=20,
    )
    # 201 with agency A, or CRM lock 403 — never agency B
    assert r.status_code in (201, 403, 422), r.text[:300]
    if r.status_code == 201:
        body = r.json()
        assert body.get("agency_id") == dual["ag_a"]
        # cleanup created activity
        dual["sess_a"].delete(f"{API}/app/activities/{body['id']}", timeout=20)


def test_http_video_job_scope_mongo_direct(dual, mongo):
    """Background-style update with wrong agency must not match (Mongo real)."""
    from apps.immoweb.micro_tour_video import _video_job_filter

    wrong = _video_job_filter(
        dual["vid_a"], agency_id=dual["ag_b"], property_id=dual["p_a"]
    )
    r = mongo.videos.update_one(wrong, {"$set": {"status": "hacked"}})
    assert r.matched_count == 0
    doc = mongo.videos.find_one({"id": dual["vid_a"]})
    assert doc["status"] == "ready"
    assert doc["agency_id"] == dual["ag_a"]


def test_http_collab_detail_outsider(dual, mongo):
    ag_c = f"{RUN}-agC4"
    u_c = f"{RUN}-userC4"
    mongo.agencies.insert_one(
        {"id": ag_c, "slug": f"{ag_c}-slug", "display_name": "C4", "activation_status": "active"}
    )
    from shared.auth.hashing import hash_password

    mongo.users.insert_one(
        {
            "id": u_c,
            "email": f"{u_c}@example.test",
            "password_hash": hash_password("x"),
            "role": "agency_admin",
            "agency_ids": [ag_c],
            "active_agency_id": ag_c,
            "is_active": True,
        }
    )
    s = dual["session_for"](u_c, f"{u_c}@example.test")
    r = s.get(f"{API}/app/collaborations/{dual['collab']}", timeout=20)
    assert r.status_code in (403, 404), r.text[:300]
    mongo.agencies.delete_one({"id": ag_c})
    mongo.users.delete_one({"id": u_c})


# ---------- W3 Staging Readiness expansions (CC / wallet / branch / revoke) ----------


@pytest.fixture(scope="module")
def dual_cc(mongo, api_up, dual):
    """Two independent CommercialCustomers + Main Admin + branch_admin under A."""
    from shared.auth.hashing import hash_password

    now = datetime.now(timezone.utc).isoformat()
    cc_a, cc_b = f"{RUN}-ccA", f"{RUN}-ccB"
    ma_a, ma_b = f"{RUN}-maA", f"{RUN}-maB"
    br_a = f"{RUN}-branchA"
    wallet_a, wallet_b = f"{RUN}-walA", f"{RUN}-walB"

    mongo.commercial_customers.insert_many(
        [
            {
                "id": cc_a,
                "country_code": "IT",
                "vat_number_normalized": f"VAT{RUN}A",
                "legal_name": "CC Dual A",
                "main_admin_user_id": ma_a,
                "customer_status": "active",
                "commercial_status": "active",
                "created_at": now,
            },
            {
                "id": cc_b,
                "country_code": "IT",
                "vat_number_normalized": f"VAT{RUN}B",
                "legal_name": "CC Dual B",
                "main_admin_user_id": ma_b,
                "customer_status": "active",
                "commercial_status": "active",
                "created_at": now,
            },
        ]
    )
    mongo.agencies.update_one(
        {"id": dual["ag_a"]},
        {"$set": {"commercial_customer_id": cc_a, "owner_id": ma_a}},
    )
    mongo.agencies.update_one(
        {"id": dual["ag_b"]},
        {"$set": {"commercial_customer_id": cc_b, "owner_id": ma_b}},
    )
    pwd = hash_password("W3DualTenant!99")
    mongo.users.insert_many(
        [
            {
                "id": ma_a,
                "email": f"{ma_a}@example.test",
                "password_hash": pwd,
                "role": "agency_admin",
                "agency_ids": [dual["ag_a"]],
                "active_agency_id": dual["ag_a"],
                "is_active": True,
                "created_at": now,
            },
            {
                "id": ma_b,
                "email": f"{ma_b}@example.test",
                "password_hash": pwd,
                "role": "agency_admin",
                "agency_ids": [dual["ag_b"]],
                "active_agency_id": dual["ag_b"],
                "is_active": True,
                "created_at": now,
            },
            {
                "id": br_a,
                "email": f"{br_a}@example.test",
                "password_hash": pwd,
                "role": "branch_admin",
                "agency_ids": [dual["ag_a"]],
                "active_agency_id": dual["ag_a"],
                "is_active": True,
                "created_at": now,
            },
        ]
    )
    # Minimal wallet docs (shape tolerant — endpoints may 403/404 without balance)
    for wid, ccid, aid in (
        (wallet_a, cc_a, dual["ag_a"]),
        (wallet_b, cc_b, dual["ag_b"]),
    ):
        mongo.credit_wallets.insert_one(
            {
                "id": wid,
                "commercial_customer_id": ccid,
                "agency_id": aid,
                "balance": 100,
                "created_at": now,
            }
        )

    ctx = {
        **dual,
        "cc_a": cc_a,
        "cc_b": cc_b,
        "ma_a": ma_a,
        "ma_b": ma_b,
        "br_a": br_a,
        "sess_ma_a": dual["session_for"](ma_a, f"{ma_a}@example.test", "agency_admin"),
        "sess_ma_b": dual["session_for"](ma_b, f"{ma_b}@example.test", "agency_admin"),
        "sess_br_a": dual["session_for"](br_a, f"{br_a}@example.test", "branch_admin"),
    }
    yield ctx

    mongo.commercial_customers.delete_many({"id": {"$in": [cc_a, cc_b]}})
    mongo.users.delete_many({"id": {"$in": [ma_a, ma_b, br_a]}})
    mongo.credit_wallets.delete_many({"id": {"$in": [wallet_a, wallet_b]}})
    mongo.memberships.delete_many({"user_id": {"$in": [ma_a, ma_b, br_a, f"{RUN}-memVictim"]}})
    mongo.refresh_tokens.delete_many(
        {"user_id": {"$in": [ma_a, ma_b, br_a, f"{RUN}-memVictim"]}}
    )


def test_http_branch_admin_cannot_create_group(dual_cc):
    r = dual_cc["sess_br_a"].post(
        f"{API}/app/groups",
        json={"name": f"evil-group-{RUN}", "credits_mode": "pooled"},
        timeout=20,
    )
    assert r.status_code in (401, 403), r.text[:300]


def test_http_branch_admin_wallet_central_denied(dual_cc):
    """Branch admin must not read/mutate central wallet of the CC."""
    r = dual_cc["sess_br_a"].get(f"{API}/billing/wallet", timeout=20)
    assert r.status_code in (401, 403, 404), r.text[:300]
    r2 = dual_cc["sess_br_a"].post(
        f"{API}/billing/wallet/allocate",
        json={
            "organization_id": dual_cc["ag_a"],
            "amount": 1,
            "commercial_customer_id": dual_cc["cc_b"],
        },
        timeout=20,
    )
    assert r2.status_code in (401, 403, 404, 405, 422), r2.text[:300]


def test_http_cc_spoof_on_wallet_allocate_denied(dual_cc):
    """Main Admin A must not allocate against CC B via payload spoof."""
    r = dual_cc["sess_ma_a"].post(
        f"{API}/billing/wallet/allocate",
        json={
            "organization_id": dual_cc["ag_b"],
            "amount": 5,
            "commercial_customer_id": dual_cc["cc_b"],
        },
        timeout=20,
    )
    assert r.status_code in (401, 403, 404, 422), r.text[:300]


def test_http_cross_cc_property_still_isolated(dual_cc):
    r = dual_cc["sess_ma_a"].get(
        f"{API}/app/properties/{dual_cc['p_b']}", timeout=20
    )
    assert r.status_code in (403, 404), r.text[:300]


def test_http_remove_member_ends_membership_and_refresh(dual_cc, mongo):
    """remove_member must end Membership + delete refresh tokens (Mongo proof)."""
    from shared.auth.hashing import hash_password

    victim = f"{RUN}-memVictim"
    now = datetime.now(timezone.utc).isoformat()
    mongo.users.insert_one(
        {
            "id": victim,
            "email": f"{victim}@example.test",
            "password_hash": hash_password("x"),
            "role": "agent",
            "agency_ids": [dual_cc["ag_a"]],
            "active_agency_id": dual_cc["ag_a"],
            "is_active": True,
            "created_at": now,
        }
    )
    mongo.memberships.insert_one(
        {
            "id": f"{RUN}-mem1",
            "user_id": victim,
            "organization_id": dual_cc["ag_a"],
            "operational_role": "agent",
            "membership_status": "active",
            "valid_from": now,
        }
    )
    mongo.refresh_tokens.insert_one(
        {
            "jti": f"{RUN}-jti",
            "user_id": victim,
            "created_at": now,
        }
    )
    r = dual_cc["sess_ma_a"].delete(
        f"{API}/app/agencies/me/members/{victim}", timeout=20
    )
    # 200 on success; 403 if CRM activation gate; never 500
    assert r.status_code in (200, 403, 404), r.text[:300]
    if r.status_code == 200:
        mem = mongo.memberships.find_one({"user_id": victim, "organization_id": dual_cc["ag_a"]})
        assert mem is None or mem.get("membership_status") == "ended"
        assert mongo.refresh_tokens.count_documents({"user_id": victim}) == 0
        u = mongo.users.find_one({"id": victim})
        assert dual_cc["ag_a"] not in (u.get("agency_ids") or [])
    mongo.users.delete_one({"id": victim})
    mongo.memberships.delete_many({"user_id": victim})
    mongo.refresh_tokens.delete_many({"user_id": victim})


def test_http_calendar_cross_tenant(dual_cc):
    r = dual_cc["sess_ma_b"].get(
        f"{API}/app/calendar/events/{dual_cc['cal_a']}", timeout=20
    )
    # endpoint may be list-only; accept 403/404/405
    assert r.status_code in (403, 404, 405), r.text[:300]


def test_http_mls_partner_outsider_cannot_respond(dual_cc, mongo):
    partner_id = f"{RUN}-partner"
    mongo.mls_partners.insert_one(
        {
            "id": partner_id,
            "agency_a": dual_cc["ag_a"],
            "agency_b": dual_cc["ag_b"],
            "initiator_id": dual_cc["ag_a"],
            "status": "pending",
        }
    )
    # Outsider C
    ag_c = f"{RUN}-agC5"
    u_c = f"{RUN}-userC5"
    from shared.auth.hashing import hash_password

    mongo.agencies.insert_one(
        {"id": ag_c, "slug": f"{ag_c}-slug", "display_name": "C5", "activation_status": "active"}
    )
    mongo.users.insert_one(
        {
            "id": u_c,
            "email": f"{u_c}@example.test",
            "password_hash": hash_password("x"),
            "role": "agency_admin",
            "agency_ids": [ag_c],
            "active_agency_id": ag_c,
            "is_active": True,
        }
    )
    s = dual_cc["session_for"](u_c, f"{u_c}@example.test")
    r = s.post(
        f"{API}/app/mls/partners/{partner_id}/respond",
        json={"action": "accept"},
        timeout=20,
    )
    assert r.status_code in (403, 404), r.text[:300]
    doc = mongo.mls_partners.find_one({"id": partner_id})
    assert doc["status"] == "pending"
    mongo.mls_partners.delete_one({"id": partner_id})
    mongo.agencies.delete_one({"id": ag_c})
    mongo.users.delete_one({"id": u_c})
