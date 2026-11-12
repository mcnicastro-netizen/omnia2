"""Accredito crediti inclusi piano da fattura Stripe (D-167).

SoT quantità: `plans.get_plan(tier).credits_included_monthly`.
Yearly: una fattura annuale → tranche annuale = credits_included_monthly × 12.
Idempotenza: `credit_ledger` con ref_type=stripe_invoice + ref_id=invoice.id.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from apps.billing.plans import get_plan

logger = logging.getLogger("omnia.plan_credits")

PLAN_CREDIT_REASON = "plan_included"
LEDGER_REF_TYPE = "stripe_invoice"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_tier_and_cycle_from_invoice(invoice: dict) -> tuple[Optional[str], str]:
    """Estrae tier + billing_cycle da metadata / lines lookup_key."""
    md = invoice.get("metadata") or {}
    tier = (md.get("tier") or "").strip().lower() or None
    cycle = (md.get("billing_cycle") or "").strip().lower() or None

    lines = invoice.get("lines") or {}
    rows = lines.get("data") if isinstance(lines, dict) else (lines or [])
    for row in rows or []:
        price = row.get("price") if isinstance(row, dict) else None
        if not isinstance(price, dict):
            continue
        lk = (price.get("lookup_key") or "").strip().lower()
        if not lk:
            continue
        # pro_monthly | pro_yearly | starter_monthly …
        parts = lk.split("_")
        if len(parts) >= 2 and parts[0] in ("starter", "pro", "agency"):
            if not tier:
                tier = parts[0]
            if not cycle and parts[-1] in ("monthly", "yearly"):
                cycle = parts[-1]
        if tier and cycle:
            break

    if cycle not in ("monthly", "yearly"):
        cycle = "monthly"
    if tier not in ("starter", "pro", "agency"):
        tier = None
    return tier, cycle


def plan_included_amount(tier: str, billing_cycle: str = "monthly") -> int:
    plan = get_plan(tier)  # type: ignore[arg-type]
    if not plan:
        return 0
    base = int(plan.credits_included_monthly or 0)
    if (billing_cycle or "monthly").lower() == "yearly":
        return base * 12
    return base


async def resolve_agency_id_for_invoice(db, invoice: dict) -> Optional[str]:
    md = invoice.get("metadata") or {}
    aid = (md.get("agency_id") or "").strip() or None
    if aid:
        return aid
    sub_id = invoice.get("subscription")
    if isinstance(sub_id, dict):
        sub_id = sub_id.get("id")
    if not sub_id:
        return None
    sub = await db.subscriptions.find_one(
        {"stripe_subscription_id": sub_id}, {"agency_id": 1}
    )
    return (sub or {}).get("agency_id")


async def grant_plan_credits_from_stripe_invoice(
    db,
    invoice: dict,
    *,
    agency_id: Optional[str] = None,
    tier_fallback: Optional[str] = None,
    cycle_fallback: Optional[str] = None,
) -> Dict[str, Any]:
    """Accredita crediti piano per una invoice Stripe paid (idempotente)."""
    inv_id = invoice.get("id")
    if not inv_id:
        return {"ok": False, "skipped": "no_invoice_id"}

    billing_reason = (invoice.get("billing_reason") or "").strip()
    # Solo ciclo abbonamento (primo + rinnovi). Skip one-off / manuali.
    if billing_reason and billing_reason not in (
        "subscription_create",
        "subscription_cycle",
    ):
        return {"ok": False, "skipped": "billing_reason", "billing_reason": billing_reason}

    existing = await db.credit_ledger.find_one(
        {"ref_type": LEDGER_REF_TYPE, "ref_id": inv_id},
        {"_id": 0, "id": 1, "delta": 1},
    )
    if existing:
        return {
            "ok": True,
            "skipped": "already_granted",
            "invoice_id": inv_id,
            "ledger_id": existing.get("id"),
            "delta": existing.get("delta"),
        }

    aid = agency_id or await resolve_agency_id_for_invoice(db, invoice)
    if not aid:
        return {"ok": False, "skipped": "agency_unresolved", "invoice_id": inv_id}

    tier, cycle = resolve_tier_and_cycle_from_invoice(invoice)
    if not tier:
        sub = await db.subscriptions.find_one({"agency_id": aid}, {"tier": 1, "plan_tier": 1})
        tier = (
            tier_fallback
            or (sub or {}).get("tier")
            or (sub or {}).get("plan_tier")
            or None
        )
    if not tier:
        return {"ok": False, "skipped": "tier_unresolved", "invoice_id": inv_id, "agency_id": aid}
    if cycle_fallback and cycle == "monthly" and cycle_fallback in ("monthly", "yearly"):
        # Preferisci ciclo noto dal checkout se invoice lines non hanno lookup_key
        lines = invoice.get("lines") or {}
        rows = lines.get("data") if isinstance(lines, dict) else []
        has_lk = any(
            ((r.get("price") or {}) if isinstance(r, dict) else {}).get("lookup_key")
            for r in (rows or [])
        )
        if not has_lk:
            cycle = cycle_fallback

    amount = plan_included_amount(tier, cycle)
    if amount <= 0:
        return {
            "ok": False,
            "skipped": "zero_credits",
            "tier": tier,
            "billing_cycle": cycle,
            "agency_id": aid,
        }

    now = _now()
    # Clawback dogfood pre-D-167 (KYC/Ops grant fisso 2000) al primo accredito listino Stripe
    clawback = 0
    prior_plan = await db.credit_ledger.find_one(
        {"agency_id": aid, "reason": {"$regex": f"^{PLAN_CREDIT_REASON}_"}},
        {"_id": 0, "id": 1},
    )
    if not prior_plan:
        dog = await db.credit_transactions.find_one(
            {
                "agency_id": aid,
                "kind": "assisted_topup",
                "credits": 2000,
                "reason": {
                    "$in": [
                        "kyc_auto_activate_d163",
                        "ops_activate_agency",
                        "coda_attivazione",
                        "cabina_scheda",
                        "cabina_ingresso",
                    ]
                },
            },
            {"_id": 0, "credits": 1},
        )
        if dog:
            clawback = 2000

    net = amount - clawback
    wallet = await db.credit_wallets.find_one_and_update(
        {"agency_id": aid},
        {
            "$inc": {"balance": net},
            "$set": {"last_topup_at": now, "updated_at": now},
            "$setOnInsert": {"agency_id": aid, "created_at": now},
        },
        upsert=True,
        return_document=True,
    )
    new_balance = (wallet or {}).get("balance", net)
    ledger_id = uuid.uuid4().hex
    await db.credit_ledger.insert_one(
        {
            "id": ledger_id,
            "agency_id": aid,
            "delta": amount,
            "reason": f"{PLAN_CREDIT_REASON}_{tier}_{cycle}",
            "balance_after": new_balance,
            "ref_id": inv_id,
            "ref_type": LEDGER_REF_TYPE,
            "clawback_dogfood_2000": clawback or None,
            "created_at": now,
        }
    )
    if clawback:
        await db.credit_ledger.insert_one(
            {
                "id": uuid.uuid4().hex,
                "agency_id": aid,
                "delta": -clawback,
                "reason": "clawback_dogfood_2000_d167",
                "balance_after": new_balance,
                "ref_id": inv_id,
                "ref_type": LEDGER_REF_TYPE,
                "created_at": now,
            }
        )
    logger.info(
        "plan credits granted agency=%s +%s net=%s clawback=%s tier=%s cycle=%s invoice=%s",
        aid,
        amount,
        net,
        clawback,
        tier,
        cycle,
        inv_id,
    )
    return {
        "ok": True,
        "agency_id": aid,
        "invoice_id": inv_id,
        "tier": tier,
        "billing_cycle": cycle,
        "credits_added": amount,
        "credits_net": net,
        "clawback_dogfood": clawback,
        "credits_balance": new_balance,
        "ledger_id": ledger_id,
    }


async def agency_has_stripe_subscription(db, agency_id: str) -> bool:
    sub = await db.subscriptions.find_one(
        {"agency_id": agency_id},
        {"stripe_subscription_id": 1, "status": 1},
    )
    if not sub or not sub.get("stripe_subscription_id"):
        return False
    st = (sub.get("status") or "").lower()
    return st in ("active", "trialing", "past_due")
