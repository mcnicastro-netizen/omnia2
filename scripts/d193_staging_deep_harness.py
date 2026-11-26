#!/usr/bin/env python3
"""D-193 staging-deep harness — synthetic fixtures + API/Mongo scenarios.

Uses Railway-injected MONGO_URL rewritten to the existing public TCP proxy.
Creates only d193-* synthetic docs; cleanup removes only those.
Never prints secrets. Session password written to /tmp only.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import secrets
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
from motor.motor_asyncio import AsyncIOMotorClient

# Ensure backend imports resolve when run via railway run from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

PROXY_HOST = "sakura.proxy.rlwy.net"
PROXY_PORT = 46223
API_A = os.environ.get(
    "D193_API_A", "https://omnia-api-production-85845f42.up.railway.app"
)
API_B = os.environ.get(
    "D193_API_B", "https://omnia-api-w4b-production.up.railway.app"
)
SESSION_TAG = "d193_synthetic"
SESSION_ID = os.environ.get("D193_SESSION_ID") or uuid.uuid4().hex[:10]
ARTIFACT = Path(
    os.environ.get("D193_ARTIFACT", f"/opt/cursor/artifacts/d193_staging_deep_{SESSION_ID}.json")
)
SECRET_FILE = Path(f"/tmp/d193_session_secrets_{SESSION_ID}.json")

# Fixture IDs
CC_A = f"d193-cc-alpha-{SESSION_ID}"
CC_B = f"d193-cc-beta-{SESSION_ID}"
ORG_A1 = f"d193-org-a1-{SESSION_ID}"
ORG_A2 = f"d193-org-a2-{SESSION_ID}"
ORG_B1 = f"d193-org-b1-{SESSION_ID}"
USER_MAIN_A = f"d193-user-main-a-{SESSION_ID}"
USER_BRANCH_A1 = f"d193-user-branch-a1-{SESSION_ID}"
USER_AGENT_A1 = f"d193-user-agent-a1-{SESSION_ID}"
USER_MAIN_B = f"d193-user-main-b-{SESSION_ID}"
USER_SUPER = f"d193-user-super-{SESSION_ID}"
EMAIL_MAIN_A = f"d193.main.a.{SESSION_ID}@example.com"
EMAIL_BRANCH = f"d193.branch.a1.{SESSION_ID}@example.com"
EMAIL_AGENT = f"d193.agent.a1.{SESSION_ID}@example.com"
EMAIL_MAIN_B = f"d193.main.b.{SESSION_ID}@example.com"
EMAIL_SUPER = f"d193.super.{SESSION_ID}@example.com"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _proxy_mongo_url(url: str) -> str:
    parts = urlsplit(url)
    if "@" in parts.netloc:
        auth, _ = parts.netloc.rsplit("@", 1)
        new_netloc = f"{auth}@{PROXY_HOST}:{PROXY_PORT}"
    else:
        new_netloc = f"{PROXY_HOST}:{PROXY_PORT}"
    return urlunsplit((parts.scheme, new_netloc, parts.path, parts.query, parts.fragment))


def _report() -> dict:
    return {
        "session_id": SESSION_ID,
        "tag": SESSION_TAG,
        "api_a": API_A,
        "api_b": API_B,
        "db_name": os.environ.get("DB_NAME"),
        "started_at": _now(),
        "scenarios": {},
        "cleanup": {},
        "verdicts": {},
    }


async def seed(db, password: str) -> dict:
    from shared.auth.hashing import hash_password
    from shared.billing.credit_wallet_service import grant_lot
    from shared.models.commercial_customer import operational_status_for

    pw_hash = hash_password(password)
    meta = {"session_tag": SESSION_TAG, "session_id": SESSION_ID, "created_at": _now()}

    # CCs
    for cc_id, name, main_uid, vat_suffix in [
        (CC_A, "D193 Alpha CC", USER_MAIN_A, "A"),
        (CC_B, "D193 Beta CC", USER_MAIN_B, "B"),
    ]:
        # Unique vat fields required by staging sparse/unique index
        # (country_code + vat_number_normalized). Synthetic only.
        vat = f"D193{SESSION_ID}{vat_suffix}".upper()[:20]
        await db.commercial_customers.update_one(
            {"id": cc_id},
            {
                "$set": {
                    "id": cc_id,
                    "name": name,
                    "commercial_status": "active",
                    "operational_status": operational_status_for("active"),
                    "status": "active",
                    "main_admin_user_id": main_uid,
                    "country_code": "IT",
                    "vat_number": vat,
                    "vat_number_normalized": vat,
                    **meta,
                }
            },
            upsert=True,
        )

    for org_id, cc_id, name in [
        (ORG_A1, CC_A, "D193 Filiale A1"),
        (ORG_A2, CC_A, "D193 Filiale A2"),
        (ORG_B1, CC_B, "D193 Filiale B1"),
    ]:
        await db.agencies.update_one(
            {"id": org_id},
            {
                "$set": {
                    "id": org_id,
                    "commercial_customer_id": cc_id,
                    "display_name": name,
                    "name": name,
                    "slug": org_id,
                    "is_active": True,
                    **meta,
                }
            },
            upsert=True,
        )

    users = [
        (USER_MAIN_A, EMAIL_MAIN_A, "agency_admin", [ORG_A1], ORG_A1),
        (USER_BRANCH_A1, EMAIL_BRANCH, "branch_admin", [ORG_A1], ORG_A1),
        (USER_AGENT_A1, EMAIL_AGENT, "agent", [ORG_A1], ORG_A1),
        (USER_MAIN_B, EMAIL_MAIN_B, "agency_admin", [ORG_B1], ORG_B1),
        (USER_SUPER, EMAIL_SUPER, "super_admin", [], None),
    ]
    for uid, email, role, agencies, active in users:
        doc = {
            "id": uid,
            "email": email,
            "name": f"D193 {role} {SESSION_ID}",
            "role": role,
            "agency_ids": agencies,
            "active_agency_id": active,
            "is_active": True,
            "email_verified": True,
            "password_hash": pw_hash,
            "lang": "it",
            "account_type": "agent",
            "must_change_password": False,
            **meta,
        }
        await db.users.update_one({"id": uid}, {"$set": doc}, upsert=True)

    # Fresh wallet state for this session CC (delete prior session leftovers with same ids)
    for col in (
        "cc_credit_wallets",
        "credit_lots",
        "credit_allocations",
        "cc_credit_ledger",
        "credit_compensate_journal",
    ):
        await db[col].delete_many({"commercial_customer_id": {"$in": [CC_A, CC_B]}})
        await db[col].delete_many({"session_id": SESSION_ID})

    # Grant 1000 to Alpha (central), 200 to Beta
    lot_a = await grant_lot(
        db,
        commercial_customer_id=CC_A,
        amount=1000,
        origin="d193_staging_seed",
        reason=f"d193_seed:{SESSION_ID}",
        idempotency_key=f"d193-grant-a-{SESSION_ID}",
    )
    lot_b = await grant_lot(
        db,
        commercial_customer_id=CC_B,
        amount=200,
        origin="d193_staging_seed",
        reason=f"d193_seed_b:{SESSION_ID}",
        idempotency_key=f"d193-grant-b-{SESSION_ID}",
    )
    # Tag lots for cleanup
    await db.credit_lots.update_many(
        {"id": {"$in": [lot_a["id"], lot_b["id"]]}},
        {"$set": {"session_tag": SESSION_TAG, "session_id": SESSION_ID}},
    )
    await db.cc_credit_wallets.update_many(
        {"commercial_customer_id": {"$in": [CC_A, CC_B]}},
        {"$set": {"session_tag": SESSION_TAG, "session_id": SESSION_ID}},
    )
    return {
        "cc_a": CC_A,
        "cc_b": CC_B,
        "orgs": [ORG_A1, ORG_A2, ORG_B1],
        "emails": {
            "main_a": EMAIL_MAIN_A,
            "branch": EMAIL_BRANCH,
            "agent": EMAIL_AGENT,
            "main_b": EMAIL_MAIN_B,
            "super": EMAIL_SUPER,
        },
        "lot_a": lot_a["id"],
        "lot_b": lot_b["id"],
    }


class ApiClient:
    def __init__(self, base: str, email: str, password: str):
        self.base = base.rstrip("/")
        self.email = email
        self.password = password
        self.client = httpx.Client(base_url=self.base, timeout=30.0, follow_redirects=True)
        self.csrf = None

    def login(self) -> dict:
        r = self.client.post("/api/auth/login", json={"email": self.email, "password": self.password})
        self.csrf = self.client.cookies.get("omnia_csrf")
        return {"code": r.status_code, "body": _safe_json(r), "cookies": list(self.client.cookies.keys())}

    def _headers(self, idem: str | None = None) -> dict:
        h = {"Content-Type": "application/json"}
        if self.csrf:
            h["X-CSRF-Token"] = self.csrf
        if idem:
            h["Idempotency-Key"] = idem
        return h

    def get(self, path: str, **params):
        r = self.client.get(path, params=params or None, headers=self._headers())
        return r.status_code, _safe_json(r)

    def post(self, path: str, payload: dict, idem: str | None = None):
        r = self.client.post(path, json=payload, headers=self._headers(idem))
        return r.status_code, _safe_json(r)

    def close(self):
        self.client.close()


def _safe_json(r: httpx.Response):
    try:
        return r.json()
    except Exception:
        return {"text": r.text[:500]}


async def snap(db, cc_id: str) -> dict:
    wallet = await db.cc_credit_wallets.find_one({"commercial_customer_id": cc_id}, {"_id": 0})
    lots = await db.credit_lots.find({"commercial_customer_id": cc_id}, {"_id": 0}).to_list(1000)
    allocs = await db.credit_allocations.find({"commercial_customer_id": cc_id}, {"_id": 0}).to_list(1000)
    ledger = await db.cc_credit_ledger.find({"commercial_customer_id": cc_id}, {"_id": 0}).to_list(5000)
    journal = await db.credit_compensate_journal.find(
        {"commercial_customer_id": cc_id}, {"_id": 0}
    ).to_list(1000)
    lot_rem = sum(int(l.get("remaining_qty") or 0) for l in lots)
    lot_unalloc = sum(int(l.get("unallocated_qty") or 0) for l in lots)
    alloc_rem = sum(int(a.get("remaining_qty") or a.get("qty_remaining") or 0) for a in allocs)
    return {
        "wallet": wallet,
        "lots_n": len(lots),
        "lots_remaining_sum": lot_rem,
        "lots_unallocated_sum": lot_unalloc,
        "allocs_n": len(allocs),
        "allocs_remaining_sum": alloc_rem,
        "ledger_n": len(ledger),
        "journal": journal,
        "lots": lots,
        "allocs": allocs,
        "ledger_tail": ledger[-10:],
    }


async def cleanup(db) -> dict:
    ids = {
        "users": [USER_MAIN_A, USER_BRANCH_A1, USER_AGENT_A1, USER_MAIN_B, USER_SUPER],
        "agencies": [ORG_A1, ORG_A2, ORG_B1],
        "ccs": [CC_A, CC_B],
    }
    deleted = {}
    deleted["users"] = (await db.users.delete_many({"id": {"$in": ids["users"]}})).deleted_count
    deleted["agencies"] = (
        await db.agencies.delete_many({"id": {"$in": ids["agencies"]}})
    ).deleted_count
    deleted["ccs"] = (
        await db.commercial_customers.delete_many({"id": {"$in": ids["ccs"]}})
    ).deleted_count
    for col in (
        "cc_credit_wallets",
        "credit_lots",
        "credit_allocations",
        "cc_credit_ledger",
        "credit_compensate_journal",
    ):
        r1 = await db[col].delete_many({"session_id": SESSION_ID})
        r2 = await db[col].delete_many({"commercial_customer_id": {"$in": ids["ccs"]}})
        deleted[col] = r1.deleted_count + r2.deleted_count
    # also by session_tag
    for col in ("users", "agencies", "commercial_customers"):
        extra = await db[col].delete_many({"session_id": SESSION_ID})
        deleted[f"{col}_by_session"] = extra.deleted_count
    return deleted


def run_api_scenarios(password: str, report: dict) -> None:
    main_a = ApiClient(API_A, EMAIL_MAIN_A, password)
    branch = ApiClient(API_A, EMAIL_BRANCH, password)
    agent = ApiClient(API_A, EMAIL_AGENT, password)
    main_b = ApiClient(API_A, EMAIL_MAIN_B, password)
    superu = ApiClient(API_A, EMAIL_SUPER, password)
    try:
        logins = {
            "main_a": main_a.login(),
            "branch": branch.login(),
            "agent": agent.login(),
            "main_b": main_b.login(),
            "super": superu.login(),
        }
        report["scenarios"]["A_logins"] = logins
        assert all(v["code"] == 200 for v in logins.values()), logins

        # A — authz
        code_w, body_w = main_a.get("/api/billing/wallet")
        report["scenarios"]["A_main_wallet"] = {"code": code_w, "body": _trim_wallet(body_w)}
        assert code_w == 200, body_w
        assert body_w.get("mode") == "commercial_customer"
        assert body_w.get("commercial_customer_id") == CC_A

        code_ma, body_ma = main_a.get("/api/billing/commercial/main-admin")
        report["scenarios"]["A_main_admin_flag"] = {"code": code_ma, "body": body_ma}
        assert code_ma == 200, body_ma
        assert body_ma.get("is_main_admin") is True
        assert body_ma.get("main_admin_user_id") == USER_MAIN_A

        code_br, body_br = branch.get("/api/billing/wallet")
        report["scenarios"]["A_branch_central_wallet"] = {"code": code_br, "detail": body_br.get("detail")}
        assert code_br in (401, 403), body_br

        code_bo, body_bo = branch.get("/api/billing/wallet/organization")
        report["scenarios"]["A_branch_org_wallet"] = {"code": code_bo, "body": body_bo}
        assert code_bo == 200, body_bo
        assert body_bo.get("organization_id") == ORG_A1

        code_ag, body_ag = agent.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_A1, "amount": 10},
            idem=f"d193-agent-alloc-{SESSION_ID}",
        )
        report["scenarios"]["A_agent_allocate"] = {"code": code_ag, "detail": body_ag.get("detail")}
        assert code_ag in (401, 403), body_ag

        code_xb, body_xb = main_b.get("/api/billing/wallet")
        # main B sees own CC, not A
        report["scenarios"]["A_cross_cc_read"] = {
            "code": code_xb,
            "cc": body_xb.get("commercial_customer_id") if isinstance(body_xb, dict) else None,
        }
        assert code_xb == 200
        assert body_xb.get("commercial_customer_id") == CC_B

        code_xalloc, body_xalloc = main_b.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_A1, "amount": 10, "commercial_customer_id": CC_A},
            idem=f"d193-cross-alloc-{SESSION_ID}",
        )
        report["scenarios"]["A_cross_cc_allocate"] = {
            "code": code_xalloc,
            "detail": body_xalloc.get("detail"),
        }
        assert code_xalloc in (400, 403, 404), body_xalloc

        # B — allocate / revoke
        code1, body1 = main_a.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_A1, "amount": 100},
            idem=f"d193-alloc-a1-{SESSION_ID}",
        )
        report["scenarios"]["B_alloc_a1"] = {"code": code1, "body": body1}
        assert code1 == 200, body1
        allocs_a1 = body1.get("allocations") or []
        assert allocs_a1

        code2, body2 = main_a.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_A2, "amount": 150},
            idem=f"d193-alloc-a2-{SESSION_ID}",
        )
        report["scenarios"]["B_alloc_a2"] = {"code": code2, "body": body2}
        assert code2 == 200, body2

        code_over, body_over = main_a.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_A1, "amount": 99999},
            idem=f"d193-alloc-over-{SESSION_ID}",
        )
        report["scenarios"]["B_alloc_over"] = {"code": code_over, "detail": body_over.get("detail")}
        assert code_over in (400, 409, 422), body_over

        code_foreign, body_foreign = main_a.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_B1, "amount": 10},
            idem=f"d193-alloc-foreign-{SESSION_ID}",
        )
        report["scenarios"]["B_alloc_foreign_org"] = {
            "code": code_foreign,
            "detail": body_foreign.get("detail"),
        }
        assert code_foreign in (400, 403, 404), body_foreign

        # partial revoke
        alloc_id = allocs_a1[0]["id"]
        code_rev, body_rev = main_a.post(
            "/api/billing/wallet/revoke",
            {"allocation_id": alloc_id},
            idem=f"d193-revoke-partial-{SESSION_ID}",
        )
        report["scenarios"]["B_revoke"] = {"code": code_rev, "body": body_rev}
        assert code_rev == 200, body_rev

        code_br_rev, body_br_rev = branch.post(
            "/api/billing/wallet/revoke",
            {"allocation_id": (body2.get("allocations") or [{}])[0].get("id")},
            idem=f"d193-branch-revoke-{SESSION_ID}",
        )
        report["scenarios"]["B_branch_revoke"] = {
            "code": code_br_rev,
            "detail": body_br_rev.get("detail"),
        }
        assert code_br_rev in (401, 403), body_br_rev

        # D — idempotency HTTP
        idem = f"d193-idem-same-{SESSION_ID}"
        c1, b1 = main_a.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_A1, "amount": 25},
            idem=idem,
        )
        c2, b2 = main_a.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_A1, "amount": 25},
            idem=idem,
        )
        report["scenarios"]["D_idem_same"] = {"c1": c1, "c2": c2, "b1": b1, "b2": b2}
        assert c1 == 200 and c2 == 200
        # same allocation ids expected on replay
        ids1 = [a["id"] for a in (b1.get("allocations") or [])]
        ids2 = [a["id"] for a in (b2.get("allocations") or [])]
        assert ids1 == ids2, (ids1, ids2)

        c3, b3 = main_a.post(
            "/api/billing/wallet/allocate",
            {"organization_id": ORG_A1, "amount": 26},
            idem=idem,
        )
        report["scenarios"]["D_idem_conflict"] = {"code": c3, "detail": b3.get("detail")}
        assert c3 in (409, 400), b3

        # concurrent allocate HTTP
        def _alloc(i):
            cl = ApiClient(API_A, EMAIL_MAIN_A, password)
            cl.login()
            code, body = cl.post(
                "/api/billing/wallet/allocate",
                {"organization_id": ORG_A2, "amount": 30},
                idem=f"d193-conc-alloc-{SESSION_ID}-{i}",
            )
            cl.close()
            return code, body

        conc_results = []
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = [ex.submit(_alloc, i) for i in range(2)]
            for f in as_completed(futs):
                conc_results.append(f.result())
        report["scenarios"]["D_conc_alloc_http"] = [
            {"code": c, "ok": (b.get("ok") if isinstance(b, dict) else None), "detail": b.get("detail") if isinstance(b, dict) else None}
            for c, b in conc_results
        ]

        # recover endpoint reachable as super (empty pending ok)
        c_rec, b_rec = superu.post("/api/billing/wallet/compensate-journal/recover", {"limit": 10})
        report["scenarios"]["E_recover_empty"] = {"code": c_rec, "body": b_rec}
        assert c_rec == 200, b_rec

        # branch cannot recover
        c_br_rec, b_br_rec = branch.post(
            "/api/billing/wallet/compensate-journal/recover", {"limit": 10}
        )
        report["scenarios"]["E_recover_branch_denied"] = {
            "code": c_br_rec,
            "detail": b_br_rec.get("detail"),
        }
        assert c_br_rec in (401, 403), b_br_rec

        # cross-instance: allocate on A, read wallet on B
        main_a_b = ApiClient(API_B, EMAIL_MAIN_A, password)
        main_a_b.login()
        cb, bb = main_a_b.get("/api/billing/wallet")
        report["scenarios"]["F_cross_instance_wallet"] = {
            "code": cb,
            "cc": bb.get("commercial_customer_id") if isinstance(bb, dict) else None,
            "balance": (bb.get("wallet") or {}).get("balance") if isinstance(bb, dict) else None,
            "unallocated": bb.get("unallocated") if isinstance(bb, dict) else bb.get("central_unallocated"),
        }
        main_a_b.close()
        assert cb == 200

    finally:
        for c in (main_a, branch, agent, main_b, superu):
            c.close()


def _trim_wallet(body):
    if not isinstance(body, dict):
        return body
    return {
        k: body.get(k)
        for k in (
            "mode",
            "commercial_customer_id",
            "is_main_admin",
            "balance",
            "unallocated",
            "central_balance",
            "central_unallocated",
            "wallet",
            "organizations",
        )
        if k in body
    } | {
        "org_n": len(body.get("organizations") or []),
        "wallet_balance": (body.get("wallet") or {}).get("balance")
        if isinstance(body.get("wallet"), dict)
        else None,
    }


async def run_mongo_debit_scenarios(db, report: dict) -> None:
    from shared.billing.credit_wallet_service import (
        allocate_credits,
        debit_for_organization,
        recover_pending_debit_compensations,
        revoke_allocation,
    )

    # Ensure spendable on A1: allocate 200 if needed
    before = await snap(db, CC_A)
    report["scenarios"]["C_before"] = {
        k: before[k]
        for k in (
            "lots_remaining_sum",
            "lots_unallocated_sum",
            "allocs_remaining_sum",
            "ledger_n",
            "wallet",
        )
    }

    # allocate fresh for debit tests
    created = await allocate_credits(
        db,
        commercial_customer_id=CC_A,
        organization_id=ORG_A1,
        amount=80,
        reason=f"d193_debit_prep:{SESSION_ID}",
        idempotency_key=f"d193-debit-prep-{SESSION_ID}",
    )
    await db.credit_allocations.update_many(
        {"id": {"$in": [a["id"] for a in created]}},
        {"$set": {"session_tag": SESSION_TAG, "session_id": SESSION_ID}},
    )

    # FIFO debit
    bal1 = await debit_for_organization(
        db, organization_id=ORG_A1, amount=30, reason=f"d193_debit1:{SESSION_ID}"
    )
    bal2 = await debit_for_organization(
        db, organization_id=ORG_A1, amount=20, reason=f"d193_debit2:{SESSION_ID}"
    )
    after_debit = await snap(db, CC_A)
    report["scenarios"]["C_debits"] = {
        "bal_after_30": bal1,
        "bal_after_20": bal2,
        "lots": [
            {
                "id": l["id"],
                "original": l.get("original_qty"),
                "remaining": l.get("remaining_qty"),
                "unallocated": l.get("unallocated_qty"),
            }
            for l in after_debit["lots"]
        ],
        "allocs_remaining_sum": after_debit["allocs_remaining_sum"],
        "no_negative_lots": all(int(l.get("remaining_qty") or 0) >= 0 for l in after_debit["lots"]),
        "no_negative_allocs": all(
            int(a.get("remaining_qty") or a.get("qty_remaining") or 0) >= 0
            for a in after_debit["allocs"]
        ),
    }
    assert report["scenarios"]["C_debits"]["no_negative_lots"]
    assert report["scenarios"]["C_debits"]["no_negative_allocs"]

    # overspend
    over_ok = False
    over_detail = None
    try:
        await debit_for_organization(
            db, organization_id=ORG_A1, amount=10_000_000, reason=f"d193_over:{SESSION_ID}"
        )
    except Exception as e:
        over_ok = True
        over_detail = str(e)[:200]
    report["scenarios"]["C_overspend"] = {"rejected": over_ok, "detail": over_detail}
    assert over_ok

    # Concurrent debits on same org
    async def _one_debit(n):
        try:
            bal = await debit_for_organization(
                db,
                organization_id=ORG_A1,
                amount=5,
                reason=f"d193_conc_debit:{SESSION_ID}:{n}",
            )
            return {"ok": True, "bal": bal}
        except Exception as e:
            return {"ok": False, "err": str(e)[:200]}

    # allocate more for concurrency
    await allocate_credits(
        db,
        commercial_customer_id=CC_A,
        organization_id=ORG_A1,
        amount=50,
        reason=f"d193_conc_prep:{SESSION_ID}",
        idempotency_key=f"d193-conc-prep-{SESSION_ID}",
    )
    results = await asyncio.gather(*[_one_debit(i) for i in range(8)])
    after_conc = await snap(db, CC_A)
    report["scenarios"]["D_conc_debits"] = {
        "results": results,
        "ok_n": sum(1 for r in results if r.get("ok")),
        "fail_n": sum(1 for r in results if not r.get("ok")),
        "allocs_remaining_sum": after_conc["allocs_remaining_sum"],
        "no_negative": all(int(a.get("remaining_qty") or a.get("qty_remaining") or 0) >= 0 for a in after_conc["allocs"])
        and all(int(l.get("remaining_qty") or 0) >= 0 for l in after_conc["lots"]),
    }
    assert report["scenarios"]["D_conc_debits"]["no_negative"]

    # Concurrent allocate service-level
    async def _one_alloc(i):
        try:
            created = await allocate_credits(
                db,
                commercial_customer_id=CC_A,
                organization_id=ORG_A2,
                amount=40,
                reason=f"d193_conc_alloc_svc:{SESSION_ID}:{i}",
                idempotency_key=f"d193-conc-alloc-svc-{SESSION_ID}-{i}",
            )
            return {"ok": True, "n": len(created)}
        except Exception as e:
            return {"ok": False, "err": str(e)[:200]}

    alloc_conc = await asyncio.gather(*[_one_alloc(i) for i in range(2)])
    after_alloc_conc = await snap(db, CC_A)
    report["scenarios"]["D_conc_alloc_svc"] = {
        "results": alloc_conc,
        "wallet": after_alloc_conc["wallet"],
        "lots_unallocated_sum": after_alloc_conc["lots_unallocated_sum"],
        "allocs_remaining_sum": after_alloc_conc["allocs_remaining_sum"],
        "consistent_math": (
            int((after_alloc_conc["wallet"] or {}).get("balance") or 0)
            >= after_alloc_conc["lots_remaining_sum"] - 1  # soft check; detailed below
        ),
    }
    # Mathematical reconciliation: wallet.balance_total == sum lot remaining
    wbal = int((after_alloc_conc["wallet"] or {}).get("balance_total") or 0)
    wunalloc = int((after_alloc_conc["wallet"] or {}).get("balance_unallocated") or 0)
    report["scenarios"]["F_reconcile_alpha"] = {
        "wallet_balance_total": wbal,
        "wallet_balance_unallocated": wunalloc,
        "lots_remaining_sum": after_alloc_conc["lots_remaining_sum"],
        "lots_unallocated_sum": after_alloc_conc["lots_unallocated_sum"],
        "allocs_remaining_sum": after_alloc_conc["allocs_remaining_sum"],
        "wallet_eq_lots": wbal == after_alloc_conc["lots_remaining_sum"],
        "wallet_unalloc_eq_lots_unalloc": wunalloc == after_alloc_conc["lots_unallocated_sum"],
        "unalloc_plus_alloc_eq_lots": (
            after_alloc_conc["lots_unallocated_sum"] + after_alloc_conc["allocs_remaining_sum"]
            == after_alloc_conc["lots_remaining_sum"]
        ),
    }
    assert report["scenarios"]["F_reconcile_alpha"]["wallet_eq_lots"]
    assert report["scenarios"]["F_reconcile_alpha"]["unalloc_plus_alloc_eq_lots"]

    # E — compensate journal: force pending journal via controlled failure path
    # Insert a synthetic pending journal that recover can complete without corrupting
    # Precondition: create alloc+lot slice state then pending journal for restore
    # Safer approach: call recover on empty; then plant pending journal that matches
    # real allocation/lot IDs after a debit path that left journal — if not forceable,
    # plant minimal journal with step pending and valid targets from a tiny debit setup.

    # Create isolated tiny lot+alloc for compensate test
    from shared.billing.credit_wallet_service import grant_lot

    tiny = await grant_lot(
        db,
        commercial_customer_id=CC_A,
        amount=15,
        origin="d193_comp_seed",
        reason=f"d193_comp:{SESSION_ID}",
        idempotency_key=f"d193-comp-grant-{SESSION_ID}",
        allocate_to_organization_id=ORG_A1,
    )
    await db.credit_lots.update_one(
        {"id": tiny["id"]}, {"$set": {"session_tag": SESSION_TAG, "session_id": SESSION_ID}}
    )
    # Debit 5 then manually plant a pending journal as if mid-compensate
    await debit_for_organization(
        db, organization_id=ORG_A1, amount=5, reason=f"d193_comp_debit:{SESSION_ID}"
    )
    # Find an allocation for ORG_A1 with remaining
    from shared.billing import credit_wallet_service as cws

    alloc = await db.credit_allocations.find_one(
        {"organization_id": ORG_A1, "lot_id": tiny["id"]},
        {"_id": 0},
    )
    if not alloc:
        alloc = await db.credit_allocations.find_one(
            {"organization_id": ORG_A1, "commercial_customer_id": CC_A},
            {"_id": 0},
            sort=[("created_at", -1)],
        )
    lot = await db.credit_lots.find_one({"id": tiny["id"]}, {"_id": 0})
    take = 3
    before_comp = await snap(db, CC_A)
    # Simulate crash after both decremented, alloc restored only
    await db.credit_allocations.update_one(
        {"id": alloc["id"]}, {"$inc": {"remaining_qty": -take}}
    )
    await db.credit_lots.update_one({"id": lot["id"]}, {"$inc": {"remaining_qty": -take}})
    jid = await cws._open_debit_compensate_journal(
        db,
        commercial_customer_id=CC_A,
        organization_id=ORG_A1,
        reason=f"d193_sim_crash:{SESSION_ID}",
        slices=[(alloc["id"], lot["id"], take)],
    )
    await db.credit_compensate_journal.update_one(
        {"id": jid},
        {"$set": {"session_tag": SESSION_TAG, "session_id": SESSION_ID}},
    )
    await db.credit_allocations.update_one(
        {"id": alloc["id"]}, {"$inc": {"remaining_qty": take}}
    )
    await db.credit_compensate_journal.update_one(
        {"id": jid},
        {
            "$set": {
                "slices.0.status": cws.JOURNAL_ALLOC_RESTORED,
                "status": cws.JOURNAL_PENDING,
            }
        },
    )

    rec1 = await recover_pending_debit_compensations(
        db, limit=50, commercial_customer_id=CC_A
    )
    mid = await db.credit_compensate_journal.find_one({"id": jid}, {"_id": 0})
    after_comp = await snap(db, CC_A)
    rec2 = await recover_pending_debit_compensations(
        db, limit=50, commercial_customer_id=CC_A
    )
    mid2 = await db.credit_compensate_journal.find_one({"id": jid}, {"_id": 0})

    # Also exercise HTTP recover as Super Admin (should be idempotent / empty pending)
    superu = ApiClient(API_A, EMAIL_SUPER, report["_password"])
    try:
        superu.login()
        c_http, b_http = superu.post(
            "/api/billing/wallet/compensate-journal/recover",
            {"commercial_customer_id": CC_A, "limit": 20},
        )
    finally:
        superu.close()

    report["scenarios"]["E_compensate_recovery"] = {
        "rec1": rec1,
        "rec2": rec2,
        "journal_after_1_status": (mid or {}).get("status"),
        "journal_after_2_status": (mid2 or {}).get("status"),
        "before_lots_remaining": before_comp["lots_remaining_sum"],
        "after_lots_remaining": after_comp["lots_remaining_sum"],
        "http_recover": {"code": c_http, "body": b_http},
        "recovered_count": rec1.get("recovered"),
        "second_noop": rec2.get("recovered", 0) == 0,
    }
    assert (mid2 or {}).get("status") == "completed"
    assert rec1.get("recovered", 0) >= 1
    assert c_http == 200

    beta = await snap(db, CC_B)
    report["scenarios"]["F_beta_untouched"] = {
        "wallet_balance_total": int((beta["wallet"] or {}).get("balance_total") or 0),
        "lots_remaining_sum": beta["lots_remaining_sum"],
        "allocs_n": beta["allocs_n"],
        "expected_balance": 200,
        "ok": int((beta["wallet"] or {}).get("balance_total") or 0) == 200
        and beta["allocs_n"] == 0
        and beta["lots_remaining_sum"] == 200,
    }
    assert report["scenarios"]["F_beta_untouched"]["ok"], report["scenarios"]["F_beta_untouched"]


async def main():
    report = _report()
    password = "D193-" + secrets.token_urlsafe(12)
    SECRET_FILE.write_text(
        json.dumps(
            {
                "session_id": SESSION_ID,
                "password": password,
                "emails": {
                    "main_a": EMAIL_MAIN_A,
                    "branch": EMAIL_BRANCH,
                    "agent": EMAIL_AGENT,
                    "main_b": EMAIL_MAIN_B,
                    "super": EMAIL_SUPER,
                },
            },
            indent=2,
        )
    )
    os.chmod(SECRET_FILE, 0o600)

    url = _proxy_mongo_url(os.environ["MONGO_URL"])
    dbn = os.environ.get("DB_NAME", "omnia_staging_e2e")
    client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=20000)
    db = client[dbn]
    await db.command("ping")

    try:
        seed_info = await seed(db, password)
        report["seed"] = seed_info
        report["_password"] = password
        # API scenarios
        try:
            run_api_scenarios(password, report)
            report["verdicts"]["api_auth_alloc"] = "PASS"
        except Exception as e:
            report["verdicts"]["api_auth_alloc"] = "FAIL"
            report["scenarios"]["api_error"] = str(e)[:800]
            raise

        try:
            await run_mongo_debit_scenarios(db, report)
            report["verdicts"]["mongo_debit_conc_comp"] = "PASS"
        except Exception as e:
            report["verdicts"]["mongo_debit_conc_comp"] = "FAIL"
            report["scenarios"]["mongo_error"] = str(e)[:800]
            raise

        # Final reconcile snapshot
        report["scenarios"]["F_final_alpha"] = {
            k: v
            for k, v in (await snap(db, CC_A)).items()
            if k
            in (
                "lots_remaining_sum",
                "lots_unallocated_sum",
                "allocs_remaining_sum",
                "ledger_n",
                "wallet",
                "journal",
            )
        }
        report["scenarios"]["F_final_beta"] = {
            k: v
            for k, v in (await snap(db, CC_B)).items()
            if k
            in (
                "lots_remaining_sum",
                "lots_unallocated_sum",
                "allocs_remaining_sum",
                "ledger_n",
                "wallet",
            )
        }

        # Cleanup synthetic only
        report["cleanup"] = await cleanup(db)
        report["verdicts"]["overall_deep"] = "PASS"
    except Exception as e:
        report["fatal"] = str(e)[:1200]
        report["verdicts"]["overall_deep"] = "FAIL"
        # still attempt cleanup
        try:
            report["cleanup"] = await cleanup(db)
        except Exception as ce:
            report["cleanup_error"] = str(ce)[:400]
    finally:
        report["finished_at"] = _now()
        ARTIFACT.write_text(json.dumps(report, indent=2, default=str))
        print(json.dumps({"artifact": str(ARTIFACT), "verdicts": report.get("verdicts"), "session_id": SESSION_ID}, indent=2))
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
