"""Provisioning assistito piano + crediti (O6 self-serve OFF · D-115).

Usato da Ops Founder e dagli script CLI. Non tocca Stripe.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from apps.billing.plans import get_plan

PlanTierName = Literal["starter", "pro", "agency"]

# agencies.plan (legacy Literal) vs subscriptions.plan_tier (billing SoT)
_AGENCY_PLAN_FIELD = {
    "starter": "starter",
    "pro": "pro",
    "agency": "enterprise",  # AgencyPlan legacy alias → quota maps enterprise→agency
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def resolve_agency(
    db,
    *,
    agency_id: Optional[str] = None,
    slug: Optional[str] = None,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve an agency by id, slug, or titolare email (active_agency_id)."""
    aid = (agency_id or "").strip()
    sl = (slug or "").strip().lower()
    em = (email or "").strip().lower()

    if aid:
        agency = await db.agencies.find_one({"id": aid})
        if not agency:
            return {"ok": False, "error": "agency_not_found", "agency_id": aid}
        return {"ok": True, "agency": agency, "agency_id": agency["id"]}

    if sl:
        agency = await db.agencies.find_one({"slug": sl})
        if not agency:
            return {"ok": False, "error": "agency_not_found", "slug": sl}
        return {"ok": True, "agency": agency, "agency_id": agency["id"]}

    if em:
        user = await db.users.find_one({"email": em})
        if not user:
            return {"ok": False, "error": "user_not_found", "email": em}
        aid2 = user.get("active_agency_id") or (
            (user.get("agency_ids") or [None])[0]
        )
        if not aid2:
            return {"ok": False, "error": "user_has_no_agency", "email": em}
        agency = await db.agencies.find_one({"id": aid2})
        if not agency:
            return {"ok": False, "error": "agency_not_found", "agency_id": aid2, "email": em}
        return {
            "ok": True,
            "agency": agency,
            "agency_id": agency["id"],
            "user_email": em,
        }

    return {"ok": False, "error": "need_agency_id_slug_or_email"}


async def grant_assisted_plan(
    db,
    agency_id: str,
    *,
    tier: PlanTierName = "pro",
    credits: int = 2000,
    reason: str = "assisted_grant",
    granted_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Set active assisted subscription + top-up wallet. Idempotent on subscription upsert."""
    plan = get_plan(tier)  # type: ignore[arg-type]
    if not plan:
        return {"ok": False, "error": "unknown_tier", "tier": tier}

    agency = await db.agencies.find_one({"id": agency_id})
    if not agency:
        return {"ok": False, "error": "agency_not_found", "agency_id": agency_id}

    now = _now()
    agency_plan = _AGENCY_PLAN_FIELD.get(tier, "pro")
    cr = max(0, int(credits))

    await db.agencies.update_one(
        {"id": agency_id},
        {
            "$set": {
                "plan": agency_plan,
                "plan_type": agency.get("plan_type") or "hybrid",
                "billing_assisted_at": now,
                "billing_assisted_tier": tier,
                "billing_assisted_by": granted_by,
                "updated_at": now,
            }
        },
    )

    await db.subscriptions.update_one(
        {"agency_id": agency_id},
        {
            "$set": {
                "agency_id": agency_id,
                "plan_tier": tier,
                "tier": tier,  # alias letto da resolve_tier quota
                "status": "active",
                "billing_cycle": "monthly",
                "source": "assisted_provisioning",
                "updated_at": now,
                "activated_at": now,
                "granted_by": granted_by,
                "grant_reason": reason,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )

    wallet = await db.credit_wallets.find_one_and_update(
        {"agency_id": agency_id},
        {
            "$inc": {"balance": cr},
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
            "credits": cr,
            "balance_after": bal,
            "reason": reason or f"assisted_grant_{tier}",
            "created_at": now,
            "ref_type": "ops_grant_agency_plan",
            "granted_by": granted_by,
        }
    )
    return {
        "ok": True,
        "agency_id": agency_id,
        "slug": agency.get("slug"),
        "display_name": agency.get("display_name") or agency.get("name"),
        "plan": agency_plan,
        "plan_tier": tier,
        "credits_added": cr,
        "credits_balance": bal,
        "max_properties": plan.max_properties,
        "credits_included_monthly": plan.credits_included_monthly,
    }
