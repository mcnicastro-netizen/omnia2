"""B04-DES-01 — Stable 1:1 CommercialCustomer ↔ Stripe Customer."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import stripe
from fastapi import HTTPException
from pymongo import ReturnDocument

from shared.auth.commercial_customer_service import get_or_create_commercial_customer
from shared.models.commercial_customer import (
    operational_status_for,
)

logger = logging.getLogger("omnia.billing.stripe_customer")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def resolve_commercial_customer_for_agency(db, agency_id: str) -> dict:
    """Load linked CommercialCustomer; create from agency fiscal VAT if missing (legacy)."""
    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0})
    if not agency:
        raise HTTPException(status_code=404, detail={"error": "agency_not_found"})

    cc_id = agency.get("commercial_customer_id")
    if cc_id:
        cc = await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0})
        if cc:
            return cc

    fiscal = agency.get("fiscal") or {}
    vat = (fiscal.get("vat_number") or "").strip()
    if not vat:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "commercial_customer_required",
                "hint": "P.IVA / CommercialCustomer obbligatorio prima del checkout B2B",
            },
        )
    legal = (
        fiscal.get("legal_name")
        or agency.get("display_name")
        or vat
    )
    cc = await get_or_create_commercial_customer(
        db,
        vat_number=vat,
        legal_name=str(legal),
        country_code="IT",
        fiscal_extra={"source": "b04i_checkout_resolve"},
    )
    await db.agencies.update_one(
        {"id": agency_id},
        {"$set": {"commercial_customer_id": cc["id"], "updated_at": _now()}},
    )
    return cc


async def get_or_create_stripe_customer(
    db,
    commercial_customer: dict,
    *,
    email: str,
    name: Optional[str] = None,
) -> str:
    """Return existing Stripe Customer id for this CC, or create and bind one.

    Never associates a Stripe Customer by email similarity alone (DES-01).
    """
    existing = (commercial_customer.get("stripe_customer_id") or "").strip()
    if existing:
        return existing

    cc_id = commercial_customer["id"]
    display = (name or commercial_customer.get("legal_name") or "").strip() or None
    try:
        created = stripe.Customer.create(
            email=(email or "").strip() or None,
            name=display,
            metadata={
                "commercial_customer_id": cc_id,
                "vat_number_normalized": commercial_customer.get("vat_number_normalized")
                or "",
                "country_code": commercial_customer.get("country_code") or "IT",
            },
        )
    except stripe.error.StripeError as e:
        logger.exception("stripe Customer.create failed cc=%s: %s", cc_id, e)
        raise HTTPException(status_code=502, detail={"stripe_error": str(e)})

    new_id = created.id
    # Bind only if still empty (race-safe)
    updated = await db.commercial_customers.find_one_and_update(
        {
            "id": cc_id,
            "$or": [
                {"stripe_customer_id": {"$exists": False}},
                {"stripe_customer_id": None},
                {"stripe_customer_id": ""},
            ],
        },
        {"$set": {"stripe_customer_id": new_id, "updated_at": _now()}},
        return_document=ReturnDocument.AFTER,
    )
    if updated and (updated.get("stripe_customer_id") or "") == new_id:
        return new_id

    # Lost race — keep the winner, drop orphan Stripe customer when possible
    refreshed = await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0})
    winner = (refreshed or {}).get("stripe_customer_id") or ""
    if winner and winner != new_id:
        try:
            stripe.Customer.delete(new_id)
        except Exception:  # noqa: BLE001
            logger.warning("orphan stripe customer cleanup failed: %s", new_id)
        return winner
    if winner:
        return winner
    # Fallback: force-set if somehow still empty
    await db.commercial_customers.update_one(
        {"id": cc_id},
        {"$set": {"stripe_customer_id": new_id, "updated_at": _now()}},
    )
    return new_id


async def attach_stripe_customer_id_if_missing(
    db, commercial_customer_id: str, stripe_customer_id: str
) -> None:
    """Persist Stripe customer id discovered from webhooks without overwriting."""
    if not commercial_customer_id or not stripe_customer_id:
        return
    await db.commercial_customers.update_one(
        {
            "id": commercial_customer_id,
            "$or": [
                {"stripe_customer_id": {"$exists": False}},
                {"stripe_customer_id": None},
                {"stripe_customer_id": ""},
            ],
        },
        {"$set": {"stripe_customer_id": stripe_customer_id, "updated_at": _now()}},
    )


async def mark_first_paid_activation(db, commercial_customer_id: str) -> dict[str, Any]:
    """Set first_paid_activated_at + Founder window once; move to commercial active."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    founder_end = (now + timedelta(days=365)).isoformat()
    existing = await db.commercial_customers.find_one(
        {"id": commercial_customer_id}, {"_id": 0}
    )
    if not existing:
        return {}
    if existing.get("first_paid_activated_at"):
        # Already activated — ensure commercial/operational if still pre_activation
        if existing.get("commercial_status") == "pre_activation":
            await db.commercial_customers.update_one(
                {"id": commercial_customer_id},
                {
                    "$set": {
                        "commercial_status": "active",
                        "operational_status": operational_status_for("active"),
                        "customer_status": "active",
                        "updated_at": now_iso,
                    }
                },
            )
        return existing

    await db.commercial_customers.update_one(
        {"id": commercial_customer_id, "first_paid_activated_at": {"$exists": False}},
        {
            "$set": {
                "first_paid_activated_at": now_iso,
                "founder_period_ends_at": founder_end,
                "commercial_status": "active",
                "operational_status": operational_status_for("active"),
                "customer_status": "active",
                "updated_at": now_iso,
            }
        },
    )
    # Also handle null first_paid
    await db.commercial_customers.update_one(
        {"id": commercial_customer_id, "first_paid_activated_at": None},
        {
            "$set": {
                "first_paid_activated_at": now_iso,
                "founder_period_ends_at": founder_end,
                "commercial_status": "active",
                "operational_status": operational_status_for("active"),
                "customer_status": "active",
                "updated_at": now_iso,
            }
        },
    )
    return await db.commercial_customers.find_one(
        {"id": commercial_customer_id}, {"_id": 0}
    ) or {}
