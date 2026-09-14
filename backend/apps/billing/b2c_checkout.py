"""OMNIA — B2C one-shot Stripe checkout (Cap. 21 · task B2C-VAL-01).

Endpoint namespace: `/api/billing/b2c/*`

Endpoints:
- `POST /checkout`               → create Stripe hosted checkout session for a b2c product
- `GET  /valuator-status`        → UI status (base remaining, entitlement, price)
- `GET  /status/{session_id}`    → post-checkout polling (session state)

The webhook `checkout.session.completed` is handled in `apps/billing/routes.py`
via `_apply_b2c_purchase_side_effects(session_id)` (kept in one place for
signature verification consistency).

Environment:
- `STRIPE_ENABLED=true` (bool)
- `STRIPE_SECRET_KEY=sk_...`
- `OMNIA_PUBLIC_URL=https://...` (fallback for absolute success/cancel URLs)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, HttpUrl

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database

from apps.billing.b2c_products import B2C_ONE_SHOT_PRODUCTS
from apps.billing.b2c_entitlements import (
    check_base_valuation_allowed,
    check_uni_entitlement,
    count_uni_purchases_today,
    record_uni_purchase,
)

logger = logging.getLogger("omnia.billing.b2c")

router = APIRouter(prefix="/billing/b2c", tags=["billing-b2c"])

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


def _is_enabled() -> bool:
    return os.environ.get("STRIPE_ENABLED", "").lower() == "true" and bool(stripe.api_key)


def _guard_enabled() -> None:
    if not _is_enabled():
        raise HTTPException(status_code=503, detail={
            "code": "stripe_not_configured",
            "message": "Il pagamento e' in preparazione. Riprova a breve.",
        })


class B2CCheckoutRequest(BaseModel):
    product_key: str = Field(min_length=3, max_length=80)
    success_url: HttpUrl
    cancel_url: HttpUrl
    payload_hash: Optional[str] = Field(default=None, max_length=128)


def _get_or_create_stripe_price(product_key: str) -> str:
    """Return Stripe Price ID for a b2c product, creating on-the-fly if missing.

    Uses `lookup_key` so re-runs are idempotent.
    """
    catalog = B2C_ONE_SHOT_PRODUCTS.get(product_key)
    if not catalog:
        raise HTTPException(status_code=400, detail=f"unknown_product:{product_key}")
    lookup = catalog["stripe_lookup_key"]
    prices = stripe.Price.list(lookup_keys=[lookup], active=True, limit=1).data
    if prices:
        return prices[0].id

    # Create Product + Price (test-mode friendly)
    product = stripe.Product.create(
        name=catalog["label_it"],
        metadata={"b2c_product_key": product_key},
    )
    price = stripe.Price.create(
        product=product.id,
        unit_amount=int(round(float(catalog["price_eur"]) * 100)),
        currency="eur",
        lookup_key=lookup,
        transfer_lookup_key=True,
        metadata={"b2c_product_key": product_key},
    )
    return price.id


@router.post("/checkout")
async def b2c_checkout(
    payload: B2CCheckoutRequest,
    user: dict = Depends(get_current_user),
):
    """Create a Stripe Checkout Session for a one-shot B2C product."""
    _guard_enabled()

    catalog = B2C_ONE_SHOT_PRODUCTS.get(payload.product_key)
    if not catalog:
        raise HTTPException(status_code=400, detail=f"unknown_product:{payload.product_key}")

    # Daily cap check for UNI (defensive; UI already blocks)
    daily_cap = catalog.get("daily_limit_per_user")
    if daily_cap:
        # Only track "paid" against cap; pending sessions do not count
        db = Database.get()
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        used = await db.b2c_purchases.count_documents({
            "user_id": user["id"],
            "product_key": payload.product_key,
            "status": "paid",
            "created_at": {"$gte": start.isoformat()},
        })
        if used >= int(daily_cap):
            raise HTTPException(status_code=429, detail={
                "code": "daily_cap_reached",
                "message": f"Hai raggiunto il limite giornaliero di {daily_cap} acquisti.",
            })

    try:
        price_id = _get_or_create_stripe_price(payload.product_key)
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{str(payload.success_url)}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=str(payload.cancel_url),
            customer_email=user.get("email"),
            metadata={
                "b2c_product_key": payload.product_key,
                "user_id": user["id"],
                "payload_hash": payload.payload_hash or "",
            },
            payment_intent_data={
                "metadata": {
                    "b2c_product_key": payload.product_key,
                    "user_id": user["id"],
                    "payload_hash": payload.payload_hash or "",
                },
            },
        )
    except stripe.error.StripeError as e:
        logger.error("b2c_checkout stripe error: %s", e)
        raise HTTPException(status_code=502, detail={"code": "stripe_error", "message": str(e)})

    # Persist pending purchase (webhook will mark it paid + set expires_at)
    await record_uni_purchase(
        user_id=user["id"],
        stripe_session_id=session["id"],
        payload_hash=payload.payload_hash,
        product_key=payload.product_key,
        status="pending",
    )

    return {
        "checkout_url": session["url"],
        "session_id": session["id"],
    }


@router.get("/valuator-status")
async def valuator_status(user: dict = Depends(get_current_user)):
    """UI status endpoint for the B2C valuator dual-tier UX."""
    allowed, reset_at = await check_base_valuation_allowed(user["id"])
    catalog = B2C_ONE_SHOT_PRODUCTS.get("b2c_valuator_uni_pdf") or {}
    is_agent = bool(user.get("agency_id") or user.get("agency_ids"))
    daily_used = 0
    if not is_agent:
        daily_used = await count_uni_purchases_today(user["id"])
    return {
        "base_remaining": 1 if allowed else 0,
        "base_reset_at": reset_at,
        "email_verified": bool(user.get("email_verified")),
        "uni_price_eur": float(catalog.get("price_eur") or 2.99),
        "uni_product_key": "b2c_valuator_uni_pdf",
        "uni_daily_cap": catalog.get("daily_limit_per_user") or 5,
        "uni_daily_used": daily_used,
        "is_agent": is_agent,
    }


@router.get("/status/{session_id}")
async def b2c_status(session_id: str, user: dict = Depends(get_current_user)):
    """Post-checkout polling. Returns purchase status + entitlement info."""
    db = Database.get()
    doc = await db.b2c_purchases.find_one(
        {"stripe_session_id": session_id, "user_id": user["id"]},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="purchase_not_found")
    return {
        "status": doc.get("status"),
        "product_key": doc.get("product_key"),
        "payload_hash": doc.get("payload_hash"),
        "expires_at": doc.get("expires_at"),
        "paid_at": doc.get("paid_at"),
    }


async def apply_b2c_purchase_side_effects(session: dict) -> None:
    """Called by the shared Stripe webhook when a `checkout.session.completed`
    event carries `metadata.b2c_product_key`. Idempotent."""
    session_id = session.get("id")
    md = session.get("metadata") or {}
    product_key = md.get("b2c_product_key")
    if not session_id or not product_key:
        return
    if product_key != "b2c_valuator_uni_pdf":
        # Future B2C products (staging, legal) — not in scope for B2C-VAL-01
        logger.info("b2c webhook: unsupported product_key=%s (skipping)", product_key)
        return
    from apps.billing.b2c_entitlements import mark_uni_purchase_paid
    updated = await mark_uni_purchase_paid(session_id)
    if updated:
        logger.info("b2c_purchase paid: session=%s user=%s", session_id, updated.get("user_id"))
    else:
        # Session not tracked locally — create the record now for resilience
        logger.warning("b2c_purchase webhook: no local record for session=%s", session_id)
