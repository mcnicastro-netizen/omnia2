"""OMNIA — B2C one-shot Stripe checkout (Cap. 21 · B2C-VAL-01 + boosts).

Endpoint namespace: `/api/billing/b2c/*`

Endpoints:
- `GET  /catalog`                → listino prodotti one-shot (strumenti + boost)
- `GET  /boosts`                 → solo Vetrina / Premium / TOP
- `POST /checkout`               → create Stripe hosted checkout session
- `GET  /valuator-status`        → UI status (base remaining, entitlement, price)
- `GET  /status/{session_id}`    → post-checkout polling (session state)

The webhook `checkout.session.completed` is handled in `apps/billing/routes.py`
via `apply_b2c_purchase_side_effects` (kept in one place for signature
verification consistency).

Environment:
- `STRIPE_ENABLED=true` (bool)
- `STRIPE_SECRET_KEY=sk_...`
- `OMNIA_PUBLIC_URL=https://...` (fallback for absolute success/cancel URLs)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database

from apps.billing.b2c_products import (
    B2C_ONE_SHOT_PRODUCTS,
    is_b2c_boost_product,
    list_b2c_catalog,
    list_boost_products,
)
from apps.billing.b2c_entitlements import (
    check_base_valuation_allowed,
    count_uni_purchases_today,
    record_uni_purchase,
)
from apps.billing.b2c_boosts import (
    apply_boost_to_listing,
    boost_duration_days,
    effective_boost,
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
    listing_id: Optional[str] = Field(default=None, max_length=80)


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


async def _assert_listing_owned(user_id: str, listing_id: str) -> dict:
    db = Database.get()
    listing = await db.properties.find_one(
        {
            "id": listing_id,
            "owner_user_id": user_id,
            "is_private_listing": True,
        },
        {"_id": 0, "id": 1, "title": 1, "status": 1, "moderation_status": 1,
         "boost_tier": 1, "boost_until": 1, "boost_rank": 1, "boost_product_key": 1},
    )
    if not listing:
        raise HTTPException(status_code=404, detail="listing_not_found")
    return listing


@router.get("/catalog")
async def b2c_catalog():
    """Public listino B2C (strumenti + boost). No auth required."""
    return {
        "currency": "eur",
        "rail": "stripe_one_shot",
        "products": list_b2c_catalog(include_boosts=True),
        "boosts": list_boost_products(),
        "stripe_enabled": _is_enabled(),
    }


@router.get("/boosts")
async def b2c_boost_catalog():
    """Boost SKUs only (Vetrina / Premium / TOP)."""
    return {
        "currency": "eur",
        "products": list_boost_products(),
        "stripe_enabled": _is_enabled(),
    }


@router.get("/boosts/listing/{listing_id}")
async def b2c_listing_boost_status(
    listing_id: str,
    user: dict = Depends(get_current_user),
):
    """Current boost status for one of the caller's private listings."""
    listing = await _assert_listing_owned(user["id"], listing_id)
    return {
        "listing_id": listing_id,
        "boost": effective_boost(listing),
        "products": list_boost_products(),
    }


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

    listing_id: Optional[str] = None
    if is_b2c_boost_product(payload.product_key):
        if not payload.listing_id:
            raise HTTPException(status_code=400, detail="listing_id_required")
        await _assert_listing_owned(user["id"], payload.listing_id)
        listing_id = payload.listing_id

    daily_cap = catalog.get("daily_limit_per_user")
    if daily_cap:
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

    meta = {
        "b2c_product_key": payload.product_key,
        "user_id": user["id"],
        "payload_hash": payload.payload_hash or "",
        "listing_id": listing_id or "",
    }
    if is_b2c_boost_product(payload.product_key):
        meta["boost_tier"] = str(catalog.get("boost_tier") or "")
        meta["duration_days"] = str(catalog.get("duration_days") or "")

    try:
        price_id = _get_or_create_stripe_price(payload.product_key)
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{str(payload.success_url)}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=str(payload.cancel_url),
            customer_email=user.get("email"),
            metadata=meta,
            payment_intent_data={"metadata": meta},
        )
    except stripe.error.StripeError as e:
        logger.error("b2c_checkout stripe error: %s", e)
        raise HTTPException(status_code=502, detail={"code": "stripe_error", "message": str(e)})

    await record_uni_purchase(
        user_id=user["id"],
        stripe_session_id=session["id"],
        payload_hash=payload.payload_hash,
        product_key=payload.product_key,
        status="pending",
        listing_id=listing_id,
    )

    return {
        "checkout_url": session["url"],
        "session_id": session["id"],
        "product_key": payload.product_key,
        "listing_id": listing_id,
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
        "listing_id": doc.get("listing_id"),
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

    from apps.billing.b2c_entitlements import mark_uni_purchase_paid

    if is_b2c_boost_product(product_key):
        days = boost_duration_days(product_key) or 30
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=days)
        updated = await mark_uni_purchase_paid(session_id, expires_at=expires)
        if not updated:
            logger.warning("b2c_purchase webhook: no local record for session=%s", session_id)
            return
        listing_id = md.get("listing_id") or updated.get("listing_id")
        user_id = md.get("user_id") or updated.get("user_id")
        if listing_id and user_id:
            await apply_boost_to_listing(
                listing_id=listing_id,
                user_id=user_id,
                product_key=product_key,
                paid_at=now,
            )
        else:
            logger.error(
                "b2c boost paid but missing listing/user session=%s md=%s",
                session_id, md,
            )
        logger.info(
            "b2c_purchase paid (boost): session=%s product=%s user=%s listing=%s",
            session_id, product_key, user_id, listing_id,
        )
        return

    if product_key in ("b2c_valuator_uni_pdf", "b2c_visura_catastale"):
        updated = await mark_uni_purchase_paid(session_id)
        if updated:
            logger.info(
                "b2c_purchase paid: session=%s product=%s user=%s",
                session_id, product_key, updated.get("user_id"),
            )
            if product_key == "b2c_visura_catastale":
                from apps.immocloud.visura_b2c import fulfill_paid_visura_order
                await fulfill_paid_visura_order(session_id)
        else:
            logger.warning("b2c_purchase webhook: no local record for session=%s", session_id)
        return

    # Other catalog products (staging, HAL legal): mark paid with 24h ledger window;
    # fulfillment is consumed at feature call-time via b2c_purchases.
    if product_key in B2C_ONE_SHOT_PRODUCTS:
        updated = await mark_uni_purchase_paid(session_id)
        if updated:
            logger.info(
                "b2c_purchase paid: session=%s product=%s user=%s",
                session_id, product_key, updated.get("user_id"),
            )
        else:
            logger.warning("b2c_purchase webhook: no local record for session=%s", session_id)
        return

    logger.info("b2c webhook: unsupported product_key=%s (skipping)", product_key)
