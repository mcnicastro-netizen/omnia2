"""D-175 C6 — Post-payment fulfillment for H4 credits/storage (+ shared claim).

Credits → central CC wallet via grant_lot (no auto-allocate).
Storage → commercial_customers.storage_extra_gb (S1).
Idempotent claim on payment_transactions before side-effects.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("omnia.billing.checkout_fulfillment")

FULFILLMENT_PROCESSING = "processing"
FULFILLMENT_APPLIED = "applied"
FULFILLMENT_ERROR = "error"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def resolve_and_verify_cc_for_checkout(
    db,
    tx: dict,
    *,
    session_customer: Optional[str] = None,
) -> dict:
    """Resolve CommercialCustomer and verify Stripe/agency binding.

    Raises ValueError with stable code string on DENY/RETRY conditions.
    """
    cc_id = (tx.get("commercial_customer_id") or "").strip() or None
    agency_id = (tx.get("agency_id") or "").strip() or None

    if not cc_id and agency_id:
        agency = await db.agencies.find_one(
            {"id": agency_id}, {"_id": 0, "commercial_customer_id": 1}
        )
        cc_id = ((agency or {}).get("commercial_customer_id") or "").strip() or None

    if not cc_id:
        raise ValueError("commercial_customer_unresolved")

    cc = await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0})
    if not cc:
        raise ValueError("commercial_customer_not_found")

    if agency_id:
        agency = await db.agencies.find_one(
            {"id": agency_id}, {"_id": 0, "id": 1, "commercial_customer_id": 1}
        )
        if not agency:
            raise ValueError("agency_not_found")
        org_cc = (agency.get("commercial_customer_id") or "").strip()
        if org_cc != cc_id:
            raise ValueError("agency_cc_mismatch")

    tx_cus = (tx.get("stripe_customer_id") or "").strip() or None
    cc_cus = (cc.get("stripe_customer_id") or "").strip() or None
    sess_cus = (session_customer or "").strip() or None

    present = [x for x in (tx_cus, cc_cus, sess_cus) if x]
    if present and len(set(present)) > 1:
        raise ValueError("stripe_customer_mismatch")

    return cc


async def claim_fulfillment(db, session_id: str) -> Optional[dict]:
    """Atomically claim a paid, not-yet-applied transaction for processing."""
    now = _now()
    claimed = await db.payment_transactions.find_one_and_update(
        {
            "session_id": session_id,
            "payment_status": "paid",
            "$or": [
                {"applied_at": {"$exists": False}},
                {"applied_at": None},
            ],
            "fulfillment_status": {"$ne": FULFILLMENT_PROCESSING},
        },
        {
            "$set": {
                "fulfillment_status": FULFILLMENT_PROCESSING,
                "fulfillment_started_at": now,
                "updated_at": now,
            }
        },
    )
    return claimed


async def mark_fulfillment_applied(
    db, session_id: str, *, extra: Optional[dict] = None
) -> None:
    now = _now()
    fields: dict[str, Any] = {
        "applied_at": now,
        "fulfillment_status": FULFILLMENT_APPLIED,
        "updated_at": now,
    }
    if extra:
        fields.update(extra)
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": fields},
    )


async def mark_fulfillment_error(db, session_id: str, error: str) -> None:
    now = _now()
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "fulfillment_status": FULFILLMENT_ERROR,
                "fulfillment_error": (error or "")[:500],
                "updated_at": now,
            }
        },
    )


async def fulfill_credits_topup(db, tx: dict, cc: dict) -> None:
    from shared.billing.credit_wallet_service import grant_lot

    credits = int(tx.get("credits") or 0)
    if credits <= 0:
        return
    session_id = tx["session_id"]
    await grant_lot(
        db,
        commercial_customer_id=cc["id"],
        amount=credits,
        origin="stripe_topup",
        reason=f"topup_{tx.get('lookup_key')}",
        idempotency_key=f"checkout:{session_id}",
        allocate_to_organization_id=None,
        ref_id=session_id,
        ref_type="checkout_session",
    )
    logger.info(
        "C6 credits granted: cc=%s +%d session=%s (no auto-allocate)",
        cc["id"],
        credits,
        session_id,
    )


async def fulfill_storage_addon(db, tx: dict, cc: dict) -> None:
    """Increment CC storage SoT (S1). Idempotency relies on claim + applied_at."""
    gb = int(tx.get("storage_gb") or 0)
    if gb <= 0:
        return
    now = _now()
    await db.commercial_customers.update_one(
        {"id": cc["id"]},
        {
            "$inc": {"storage_extra_gb": gb},
            "$set": {"updated_at": now},
        },
    )
    logger.info(
        "C6 storage addon: cc=%s +%d GB session=%s",
        cc["id"],
        gb,
        tx.get("session_id"),
    )


async def apply_h4_session_side_effects(
    db,
    session_id: str,
    *,
    session_customer: Optional[str] = None,
) -> dict:
    """Apply credits_topup / storage_addon for a paid checkout session.

    Returns a small status dict for tests/logging.
    Subscription kind is handled by the caller (legacy path in routes).
    """
    claimed = await claim_fulfillment(db, session_id)
    if not claimed:
        return {"ok": True, "skipped": "not_claimable"}

    kind = claimed.get("kind")
    if kind not in ("credits_topup", "storage_addon"):
        await mark_fulfillment_error(db, session_id, f"unexpected_kind:{kind}")
        return {"ok": False, "error": f"unexpected_kind:{kind}"}

    try:
        cc = await resolve_and_verify_cc_for_checkout(
            db, claimed, session_customer=session_customer
        )
        if kind == "credits_topup":
            await fulfill_credits_topup(db, claimed, cc)
        else:
            await fulfill_storage_addon(db, claimed, cc)
        await mark_fulfillment_applied(
            db,
            session_id,
            extra={"commercial_customer_id": cc["id"]},
        )
        return {"ok": True, "applied": kind, "commercial_customer_id": cc["id"]}
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "C6 fulfillment error session=%s: %s", session_id, exc, exc_info=True
        )
        await mark_fulfillment_error(db, session_id, str(exc))
        return {"ok": False, "error": str(exc)}
