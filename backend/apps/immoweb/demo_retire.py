"""Retire GTM sandbox demo-agency-001 (primo cliente reale)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DEMO_AGENCY_ID = "demo-agency-001"
DEMO_ADMIN_EMAIL = "demo.admin@omniaecosystem.it"
KEEP_GLOBAL = {
    "hal_knowledge_chunks",
    "hal_knowledge_meta",
    "hal_knowledge_sessions",
    "publishing_catalog",
    "mls_network",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def wipe_demo_agency(db) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "agency_id": DEMO_AGENCY_ID,
        "deleted": {},
        "users_detached": 0,
        "demo_admin_deleted": 0,
        "agency_deleted": 0,
    }
    now = _now()
    names = await db.list_collection_names()
    for name in sorted(names):
        if name in KEEP_GLOBAL or name in {"agencies", "users"}:
            continue
        n = await db[name].count_documents({"agency_id": DEMO_AGENCY_ID})
        if n:
            res = await db[name].delete_many({"agency_id": DEMO_AGENCY_ID})
            report["deleted"][name] = res.deleted_count

    det = await db.users.update_many(
        {"agency_ids": DEMO_AGENCY_ID},
        {"$pull": {"agency_ids": DEMO_AGENCY_ID}, "$set": {"updated_at": now}},
    )
    report["users_detached"] = int(det.modified_count)
    await db.users.update_many(
        {"active_agency_id": DEMO_AGENCY_ID},
        {"$set": {"active_agency_id": None, "updated_at": now}},
    )
    adm = await db.users.delete_many({"email": DEMO_ADMIN_EMAIL.lower()})
    report["demo_admin_deleted"] = int(adm.deleted_count)
    ag = await db.agencies.delete_many({"id": DEMO_AGENCY_ID})
    report["agency_deleted"] = int(ag.deleted_count)
    inv = await db.agency_invites.delete_many({"agency_id": DEMO_AGENCY_ID})
    if inv.deleted_count:
        report["deleted"]["agency_invites"] = int(inv.deleted_count)
    return report


async def attach_user_to_agency_slug(db, email: str, slug: str) -> Dict[str, Any]:
    agency = await db.agencies.find_one({"slug": slug})
    if not agency:
        return {"ok": False, "error": "agency_not_found", "slug": slug}
    user = await db.users.find_one({"email": email.lower().strip()})
    if not user:
        return {"ok": False, "error": "user_not_found", "email": email}
    aid = agency["id"]
    ids = [i for i in (user.get("agency_ids") or []) if i != DEMO_AGENCY_ID]
    if aid not in ids:
        ids.append(aid)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"agency_ids": ids, "active_agency_id": aid, "updated_at": _now()}},
    )
    return {
        "ok": True,
        "agency_id": aid,
        "slug": slug,
        "display_name": agency.get("display_name") or agency.get("name"),
        "email": email.lower().strip(),
    }


async def grant_assisted_pro(db, agency_id: str, credits: int = 500) -> Dict[str, Any]:
    now = _now()
    await db.agencies.update_one(
        {"id": agency_id},
        {
            "$set": {
                "plan": "pro",
                "plan_type": "turnkey",
                "billing_assisted_at": now,
                "billing_assisted_tier": "pro",
                "updated_at": now,
            }
        },
    )
    await db.subscriptions.update_one(
        {"agency_id": agency_id},
        {
            "$set": {
                "agency_id": agency_id,
                "plan_tier": "pro",
                "status": "active",
                "billing_cycle": "monthly",
                "source": "assisted_provisioning",
                "updated_at": now,
                "activated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    wallet = await db.credit_wallets.find_one_and_update(
        {"agency_id": agency_id},
        {
            "$inc": {"balance": max(0, credits)},
            "$set": {"updated_at": now, "last_topup_at": now},
            "$setOnInsert": {"agency_id": agency_id, "created_at": now},
        },
        upsert=True,
        return_document=True,
    )
    bal = (wallet or {}).get("balance")
    await db.credit_transactions.insert_one(
        {
            "agency_id": agency_id,
            "kind": "assisted_topup",
            "credits": credits,
            "balance_after": bal,
            "reason": "first_client_nicastro",
            "created_at": now,
            "ref_type": "demo_retire",
        }
    )
    return {"ok": True, "plan": "pro", "credits_balance": bal}


async def purge_agency_shell(db, *, slug: str, force: bool = False) -> Dict[str, Any]:
    """Elimina un'agenzia orfana (0 membri) e i suoi documenti agency_id.

    Usato per ripartire puliti dopo uno shortcut di seed/dogfood.
    Con ``force=True`` stacca prima tutti i membri (reset Founder).
    """
    agency = await db.agencies.find_one({"slug": slug})
    if not agency:
        return {"ok": True, "slug": slug, "agency_deleted": 0, "note": "already_absent"}
    aid = agency["id"]
    members = await db.users.count_documents({"agency_ids": aid})
    detached = 0
    if members > 0 and force:
        now = _now()
        det = await db.users.update_many(
            {"agency_ids": aid},
            {"$pull": {"agency_ids": aid}, "$set": {"updated_at": now}},
        )
        detached = int(det.modified_count)
        await db.users.update_many(
            {"active_agency_id": aid},
            {"$set": {"active_agency_id": None, "updated_at": now}},
        )
        members = 0
    if members > 0:
        return {
            "ok": False,
            "error": "agency_has_members",
            "slug": slug,
            "agency_id": aid,
            "members": members,
        }
    deleted: Dict[str, int] = {}
    names = await db.list_collection_names()
    for name in sorted(names):
        if name in KEEP_GLOBAL or name in {"agencies", "users"}:
            continue
        n = await db[name].count_documents({"agency_id": aid})
        if n:
            res = await db[name].delete_many({"agency_id": aid})
            deleted[name] = res.deleted_count
    inv = await db.agency_invites.delete_many({"agency_id": aid})
    if inv.deleted_count:
        deleted["agency_invites"] = int(inv.deleted_count)
    ag = await db.agencies.delete_many({"id": aid})
    return {
        "ok": True,
        "slug": slug,
        "agency_id": aid,
        "agency_deleted": int(ag.deleted_count),
        "members_detached": detached,
        "deleted": deleted,
    }


async def retire_demo_and_promote_first_client(
    db,
    *,
    attach_slug: str = "nicastro-immobiliare",
    grant_pro: bool = True,
    credits: int = 500,
    founder_email: Optional[str] = None,
) -> Dict[str, Any]:
    """One-shot: wipe demo + attach Founder + grant Pro on first client."""
    wipe = await wipe_demo_agency(db)
    email = (founder_email or os.environ.get("ADMIN_EMAIL") or "").lower().strip()
    attach = await attach_user_to_agency_slug(db, email, attach_slug) if email else {
        "ok": False,
        "error": "ADMIN_EMAIL_missing",
    }
    grant = None
    if grant_pro and attach.get("ok"):
        grant = await grant_assisted_pro(db, attach["agency_id"], credits)
    return {"wipe": wipe, "attach": attach, "grant": grant}
