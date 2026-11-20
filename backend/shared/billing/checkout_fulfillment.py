"""D-175 C6 — Post-payment fulfillment for H4 credits/storage (+ shared claim).

Credits → central CC wallet via grant_lot (no auto-allocate).
Storage → commercial_customers.storage_extra_gb (S1), idempotent per session_id.
Idempotent claim on payment_transactions; stale processing reclaimable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger("omnia.billing.checkout_fulfillment")

FULFILLMENT_PROCESSING = "processing"
FULFILLMENT_APPLIED = "applied"
FULFILLMENT_ERROR = "error"

# Stale processing older than this can be reclaimed (crash between side-effect and applied_at)
STALE_PROCESSING_SECONDS = 300


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


async def resolve_and_verify_cc_for_checkout(
    db,
    tx: dict,
    *,
    session_customer: Optional[str] = None,
    require_session_customer: bool = True,
) -> dict:
    """Resolve CommercialCustomer and verify Stripe/agency binding.

    Raises ValueError with stable code string on DENY/RETRY conditions.
    When require_session_customer=True (webhook/fallback), Session.customer is mandatory.
    """
    sess_cus = (session_customer or "").strip() or None
    if require_session_customer and not sess_cus:
        raise ValueError("stripe_customer_missing")

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

    # Session customer (when provided) must agree with tx and CC bindings.
    if sess_cus:
        if tx_cus and tx_cus != sess_cus:
            raise ValueError("stripe_customer_mismatch")
        if cc_cus and cc_cus != sess_cus:
            raise ValueError("stripe_customer_mismatch")
    else:
        present = [x for x in (tx_cus, cc_cus) if x]
        if present and len(set(present)) > 1:
            raise ValueError("stripe_customer_mismatch")

    return cc


async def claim_fulfillment(
    db,
    session_id: str,
    *,
    stale_seconds: int = STALE_PROCESSING_SECONDS,
) -> Optional[dict]:
    """Atomically claim a paid, not-yet-applied transaction for processing.

    Also reclaims stale ``processing`` rows (crash after side-effect, before applied_at).
    """
    now = _now()
    now_iso = now.isoformat()

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
                "fulfillment_started_at": now_iso,
                "updated_at": now_iso,
            }
        },
    )
    if claimed:
        return claimed

    # Reclaim stale processing
    cutoff = (now - timedelta(seconds=max(1, int(stale_seconds)))).isoformat()
    reclaimed = await db.payment_transactions.find_one_and_update(
        {
            "session_id": session_id,
            "payment_status": "paid",
            "$or": [
                {"applied_at": {"$exists": False}},
                {"applied_at": None},
            ],
            "fulfillment_status": FULFILLMENT_PROCESSING,
            "fulfillment_started_at": {"$lt": cutoff},
        },
        {
            "$set": {
                "fulfillment_status": FULFILLMENT_PROCESSING,
                "fulfillment_started_at": now_iso,
                "fulfillment_reclaimed_at": now_iso,
                "updated_at": now_iso,
            }
        },
    )
    if reclaimed:
        logger.warning(
            "C6 reclaimed stale processing session=%s started_at=%s",
            session_id,
            reclaimed.get("fulfillment_started_at"),
        )
    return reclaimed


async def mark_fulfillment_applied(
    db, session_id: str, *, extra: Optional[dict] = None
) -> None:
    now = _now_iso()
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
    now = _now_iso()
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
    """Increment CC storage SoT idempotently per checkout session_id.

    Ledger row ``storage_checkout_fulfillments`` (unique on session_id) gates the $inc.
    Retry after crash: insert fails → skip $inc → safe to mark applied.
    """
    gb = int(tx.get("storage_gb") or 0)
    if gb <= 0:
        return
    session_id = tx["session_id"]
    now = _now_iso()
    ledger = {
        "id": session_id,
        "session_id": session_id,
        "commercial_customer_id": cc["id"],
        "storage_gb": gb,
        "created_at": now,
    }
    try:
        await db.storage_checkout_fulfillments.insert_one(ledger)
    except Exception:
        existing = await db.storage_checkout_fulfillments.find_one(
            {"session_id": session_id}, {"_id": 0}
        )
        if existing:
            logger.info(
                "C6 storage already ledgered session=%s cc=%s — skip $inc",
                session_id,
                cc["id"],
            )
            return
        # Fallback uniqueness on id
        existing = await db.storage_checkout_fulfillments.find_one(
            {"id": session_id}, {"_id": 0}
        )
        if existing:
            return
        raise

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
        session_id,
    )


async def apply_h4_session_side_effects(
    db,
    session_id: str,
    *,
    session_customer: Optional[str] = None,
    require_session_customer: bool = True,
    stale_seconds: int = STALE_PROCESSING_SECONDS,
) -> dict:
    """Apply credits_topup / storage_addon for a paid checkout session."""
    claimed = await claim_fulfillment(db, session_id, stale_seconds=stale_seconds)
    if not claimed:
        return {"ok": True, "skipped": "not_claimable"}

    kind = claimed.get("kind")
    if kind not in ("credits_topup", "storage_addon"):
        await mark_fulfillment_error(db, session_id, f"unexpected_kind:{kind}")
        return {"ok": False, "error": f"unexpected_kind:{kind}"}

    try:
        cc = await resolve_and_verify_cc_for_checkout(
            db,
            claimed,
            session_customer=session_customer,
            require_session_customer=require_session_customer,
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
