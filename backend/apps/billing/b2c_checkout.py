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
    is_b2c_listing_addon_product,
    is_b2c_listing_slot_product,
    list_b2c_catalog,
    list_boost_products,
    list_listing_publish_products,
    product_requires_listing,
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
from apps.billing.b2c_listing_publish import (
    FREE_TIER_MAX_ACTIVE,
    count_slot_usage,
    count_unused_slot_credits,
    fulfill_listing_publish_purchase,
    listing_requires_premium_sku,
)

logger = logging.getLogger("omnia.billing.b2c")

router = APIRouter(prefix="/billing/b2c", tags=["billing-b2c"])

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


def _refresh_stripe_api_key() -> str:
    key = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    stripe.api_key = key
    return key


def _is_enabled() -> bool:
    key = _refresh_stripe_api_key()
    return os.environ.get("STRIPE_ENABLED", "").lower() == "true" and bool(key)


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
    # Virtual staging: attach a free preview / chosen photo after pay
    preview_job_id: Optional[str] = Field(default=None, max_length=80)
    photo_id: Optional[str] = Field(default=None, max_length=80)
    staging_mode: Optional[str] = Field(default=None, max_length=20)


def _get_or_create_stripe_price(product_key: str) -> str:
    """Return Stripe Price ID for a b2c product, creating on-the-fly if missing.

    Uses `lookup_key` so re-runs are idempotent. If catalog `price_eur` changed,
    creates a new Price and transfers the lookup_key (old price stays for history).
    """
    catalog = B2C_ONE_SHOT_PRODUCTS.get(product_key)
    if not catalog:
        raise HTTPException(status_code=400, detail=f"unknown_product:{product_key}")
    lookup = catalog["stripe_lookup_key"]
    wanted_cents = int(round(float(catalog["price_eur"]) * 100))
    prices = stripe.Price.list(lookup_keys=[lookup], active=True, limit=1).data
    if prices:
        existing = prices[0]
        if int(existing.unit_amount or 0) == wanted_cents and (existing.currency or "") == "eur":
            return existing.id
        # Price mismatch (e.g. staging 0.90 → 1.49): mint new Price + transfer lookup.
        product_id = existing.product if isinstance(existing.product, str) else existing.product.id
        price = stripe.Price.create(
            product=product_id,
            unit_amount=wanted_cents,
            currency="eur",
            lookup_key=lookup,
            transfer_lookup_key=True,
            metadata={"b2c_product_key": product_key},
        )
        try:
            stripe.Price.modify(existing.id, active=False)
        except Exception:
            pass
        return price.id

    product = stripe.Product.create(
        name=catalog["label_it"],
        metadata={"b2c_product_key": product_key},
    )
    price = stripe.Price.create(
        product=product.id,
        unit_amount=wanted_cents,
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
         "price": 1, "rent_monthly": 1,
         "boost_tier": 1, "boost_until": 1, "boost_rank": 1, "boost_product_key": 1,
         "hide_address": 1, "hide_address_paid": 1,
         "photo_pack_extra": 1, "listing_paid_until": 1, "listing_publish_tier": 1},
    )
    if not listing:
        raise HTTPException(status_code=404, detail="listing_not_found")
    return listing


@router.get("/catalog")
async def b2c_catalog():
    """Public listino B2C (strumenti + boost + pubblicazione). No auth required."""
    return {
        "currency": "eur",
        "rail": "stripe_one_shot",
        "products": list_b2c_catalog(include_boosts=True),
        "boosts": list_boost_products(),
        "listing_publish": list_listing_publish_products(),
        "free_listing_slots": FREE_TIER_MAX_ACTIVE,
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


@router.get("/listing-publish")
async def b2c_listing_publish_catalog(user: dict = Depends(get_current_user)):
    """Slot dal 3° + add-on (hide address / foto pack) + usage corrente."""
    used = await count_slot_usage(user["id"])
    credits = await count_unused_slot_credits(user["id"])
    return {
        "currency": "eur",
        "free_max": FREE_TIER_MAX_ACTIVE,
        "used_slots": used,
        "unused_credits": credits,
        "products": list_listing_publish_products(),
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
    if product_requires_listing(payload.product_key):
        if not payload.listing_id:
            raise HTTPException(status_code=400, detail="listing_id_required")
        listing = await _assert_listing_owned(user["id"], payload.listing_id)
        listing_id = payload.listing_id
    elif payload.listing_id and is_b2c_listing_slot_product(payload.product_key):
        listing = await _assert_listing_owned(user["id"], payload.listing_id)
        listing_id = payload.listing_id
    else:
        listing = None

    if is_b2c_listing_slot_product(payload.product_key) and listing is not None:
        if listing_requires_premium_sku(listing) and payload.product_key != "b2c_listing_premium":
            raise HTTPException(status_code=400, detail={
                "code": "premium_listing_sku_required",
                "message": "Per immobili >€1M o affitti >€2.500/mese serve lo slot premium (€19,90).",
            })

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

    staging_mode = None
    preview_job_id = None
    photo_id = None
    if payload.product_key == "b2c_staging_render":
        staging_mode = (payload.staging_mode or "standard").strip() or "standard"
        if staging_mode not in ("standard", "reverse", "empty"):
            raise HTTPException(status_code=400, detail="unsupported_staging_mode")
        preview_job_id = (payload.preview_job_id or "").strip() or None
        photo_id = (payload.photo_id or "").strip() or None

    meta = {
        "b2c_product_key": payload.product_key,
        "user_id": user["id"],
        "payload_hash": payload.payload_hash or "",
        "listing_id": listing_id or "",
    }
    if is_b2c_boost_product(payload.product_key):
        meta["boost_tier"] = str(catalog.get("boost_tier") or "")
        meta["duration_days"] = str(catalog.get("duration_days") or "")
    if is_b2c_listing_slot_product(payload.product_key):
        meta["listing_tier"] = str(catalog.get("listing_tier") or "standard")
        meta["duration_days"] = str(catalog.get("duration_days") or "90")
    if is_b2c_listing_addon_product(payload.product_key):
        meta["listing_addon"] = str(catalog.get("listing_addon") or "")
    if payload.product_key == "b2c_staging_render":
        meta["staging_mode"] = staging_mode or "standard"
        meta["preview_job_id"] = preview_job_id or ""
        meta["photo_id"] = photo_id or ""

    try:
        price_id = _get_or_create_stripe_price(payload.product_key)
        success = str(payload.success_url)
        sep = "&" if "?" in success else "?"
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{success}{sep}session_id={{CHECKOUT_SESSION_ID}}",
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
        preview_job_id=preview_job_id,
        photo_id=photo_id,
        staging_mode=staging_mode,
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
    """Post-checkout polling. Returns purchase status + entitlement info.

    P-049: if Mongo still pending, retrieve Stripe Checkout Session and apply
    the same paid side-effects as the webhook (idempotent).
    """
    db = Database.get()
    doc = await db.b2c_purchases.find_one(
        {"stripe_session_id": session_id, "user_id": user["id"]},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="purchase_not_found")

    if doc.get("status") != "paid":
        try:
            s = stripe.checkout.Session.retrieve(session_id)
            sess = s.to_dict() if hasattr(s, "to_dict") else dict(s)
            if sess.get("payment_status") == "paid" or sess.get("status") == "complete":
                # Ensure metadata present for apply_b2c_purchase_side_effects
                md = dict(sess.get("metadata") or {})
                if not md.get("b2c_product_key"):
                    md["b2c_product_key"] = doc.get("product_key") or ""
                if not md.get("user_id"):
                    md["user_id"] = user["id"]
                if doc.get("listing_id") and not md.get("listing_id"):
                    md["listing_id"] = doc["listing_id"]
                sess["metadata"] = md
                if not sess.get("id"):
                    sess["id"] = session_id
                await apply_b2c_purchase_side_effects(sess)
                doc = await db.b2c_purchases.find_one(
                    {"stripe_session_id": session_id, "user_id": user["id"]},
                    {"_id": 0},
                ) or doc
        except stripe.error.StripeError:
            pass

    return {
        "status": doc.get("status"),
        "product_key": doc.get("product_key"),
        "payload_hash": doc.get("payload_hash"),
        "listing_id": doc.get("listing_id"),
        "expires_at": doc.get("expires_at"),
        "paid_at": doc.get("paid_at"),
        "consumed_at": doc.get("consumed_at"),
        "job_id": doc.get("job_id"),
    }


def _session_amount_eur(session: dict) -> Optional[float]:
    """Stripe Checkout amount_total is in cents."""
    total = session.get("amount_total")
    if total is None:
        return None
    try:
        return round(float(total) / 100.0, 2)
    except (TypeError, ValueError):
        return None


async def apply_b2c_purchase_side_effects(session: dict) -> None:
    """Called by the shared Stripe webhook when a `checkout.session.completed`
    event carries `metadata.b2c_product_key`. Idempotent."""
    session_id = session.get("id")
    md = session.get("metadata") or {}
    product_key = md.get("b2c_product_key")
    if not session_id or not product_key:
        return

    from apps.billing.b2c_entitlements import mark_uni_purchase_paid

    amount_eur = _session_amount_eur(session)

    if is_b2c_boost_product(product_key):
        days = boost_duration_days(product_key) or 30
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=days)
        updated = await mark_uni_purchase_paid(
            session_id, expires_at=expires, amount_eur=amount_eur,
        )
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

    if is_b2c_listing_slot_product(product_key) or is_b2c_listing_addon_product(product_key):
        now = datetime.now(timezone.utc)
        days = int((B2C_ONE_SHOT_PRODUCTS.get(product_key) or {}).get("duration_days") or 90)
        expires = now + timedelta(days=days) if is_b2c_listing_slot_product(product_key) else None
        updated = await mark_uni_purchase_paid(
            session_id, expires_at=expires, amount_eur=amount_eur,
        )
        if not updated:
            logger.warning("b2c_purchase webhook: no local record for session=%s", session_id)
            return
        listing_id = md.get("listing_id") or updated.get("listing_id") or None
        user_id = md.get("user_id") or updated.get("user_id")
        if not user_id:
            logger.error("listing publish paid without user session=%s", session_id)
            return
        await fulfill_listing_publish_purchase(
            session_id=session_id,
            product_key=product_key,
            user_id=user_id,
            listing_id=listing_id or None,
            purchase=updated,
            paid_at=now,
        )
        logger.info(
            "b2c_purchase paid (listing_publish): session=%s product=%s user=%s listing=%s",
            session_id, product_key, user_id, listing_id,
        )
        return

    if product_key in ("b2c_valuator_uni_pdf", "b2c_visura_catastale"):
        updated = await mark_uni_purchase_paid(session_id, amount_eur=amount_eur)
        if updated:
            logger.info(
                "b2c_purchase paid: session=%s product=%s user=%s amount_eur=%s",
                session_id, product_key, updated.get("user_id"), updated.get("amount_eur"),
            )
            if product_key == "b2c_visura_catastale":
                from apps.immocloud.visura_b2c import fulfill_paid_visura_order
                await fulfill_paid_visura_order(session_id)
        else:
            logger.warning("b2c_purchase webhook: no local record for session=%s", session_id)
        return

    if product_key == "b2c_staging_render":
        updated = await mark_uni_purchase_paid(session_id, amount_eur=amount_eur)
        if updated:
            logger.info(
                "b2c_purchase paid (staging): session=%s user=%s listing=%s amount_eur=%s",
                session_id, updated.get("user_id"), updated.get("listing_id"),
                updated.get("amount_eur"),
            )
            from apps.immoweb.virtual_staging import fulfill_paid_staging_render
            await fulfill_paid_staging_render(session_id)
        else:
            logger.warning("b2c_purchase webhook: no local record for session=%s", session_id)
        return

    # Other catalog products (HAL legal): mark paid with 24h ledger window;
    # fulfillment is consumed at feature call-time via b2c_purchases.
    if product_key in B2C_ONE_SHOT_PRODUCTS:
        updated = await mark_uni_purchase_paid(session_id, amount_eur=amount_eur)
        if updated:
            logger.info(
                "b2c_purchase paid: session=%s product=%s user=%s amount_eur=%s",
                session_id, product_key, updated.get("user_id"), updated.get("amount_eur"),
            )
        else:
            logger.warning("b2c_purchase webhook: no local record for session=%s", session_id)
        return

    logger.info("b2c webhook: unsupported product_key=%s (skipping)", product_key)
