"""OMNIA — B2C paid listing slots + add-ons (pubblicazione dal 3°).

SKU:
  - b2c_listing_extra_90 / b2c_listing_premium → slot 90gg
  - b2c_hide_address / b2c_photo_pack → add-on per listing

Slot senza listing_id = credito consumabile alla create oltre free tier.
Slot con listing_id = applica subito paid_until sul listing.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from pymongo import ReturnDocument

from shared.db.connection import Database
from apps.billing.b2c_products import (
    B2C_ONE_SHOT_PRODUCTS,
    get_b2c_product,
    is_b2c_listing_addon_product,
    is_b2c_listing_slot_product,
)

logger = logging.getLogger("omnia.billing.b2c_listing_publish")

FREE_TIER_MAX_ACTIVE = 2
BASE_PHOTO_LIMIT = 20
PHOTO_PACK_EXTRA = 10
HARD_PHOTO_CAP = 30
PREMIUM_PRICE_EUR = 1_000_000.0
PREMIUM_RENT_EUR = 2_500.0


def listing_requires_premium_sku(prop: Dict[str, Any]) -> bool:
    try:
        price = float(prop.get("price") or 0)
    except (TypeError, ValueError):
        price = 0.0
    try:
        rent = float(prop.get("rent_monthly") or 0)
    except (TypeError, ValueError):
        rent = 0.0
    return price > PREMIUM_PRICE_EUR or rent > PREMIUM_RENT_EUR


def photo_limit_for(doc: Dict[str, Any]) -> int:
    extra = int(doc.get("photo_pack_extra") or 0)
    return min(HARD_PHOTO_CAP, BASE_PHOTO_LIMIT + max(0, extra))


async def count_slot_usage(user_id: str) -> int:
    db = Database.get()
    from shared.db.trash import with_not_trashed
    return await db.properties.count_documents(
        with_not_trashed({
            "owner_user_id": user_id,
            "is_private_listing": True,
            "status": {"$in": ["draft", "active"]},
        })
    )


async def count_unused_slot_credits(user_id: str) -> int:
    db = Database.get()
    return await db.b2c_purchases.count_documents({
        "user_id": user_id,
        "status": "paid",
        "slot_credit": True,
        "slot_consumed": {"$ne": True},
        "product_key": {"$in": ["b2c_listing_extra_90", "b2c_listing_premium"]},
    })


async def consume_listing_slot_credit(user_id: str) -> Optional[dict]:
    """Atomically consume one unused paid slot credit. Returns purchase doc."""
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    doc = await db.b2c_purchases.find_one_and_update(
        {
            "user_id": user_id,
            "status": "paid",
            "slot_credit": True,
            "slot_consumed": {"$ne": True},
            "product_key": {"$in": ["b2c_listing_extra_90", "b2c_listing_premium"]},
        },
        {"$set": {"slot_consumed": True, "slot_consumed_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        return None
    doc.pop("_id", None)
    return doc


def slot_fields_from_purchase(purchase: dict, *, paid_at: Optional[datetime] = None) -> dict:
    paid_at = paid_at or datetime.now(timezone.utc)
    pk = purchase.get("product_key") or ""
    catalog = get_b2c_product(pk) or {}
    days = int(catalog.get("duration_days") or 90)
    until = paid_at + timedelta(days=days)
    return {
        "listing_publish_tier": catalog.get("listing_tier") or "standard",
        "listing_paid_until": until.isoformat(),
        "listing_slot_product_key": pk,
        "listing_slot_purchase_id": purchase.get("stripe_session_id") or purchase.get("id"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def apply_slot_to_listing(
    *,
    listing_id: str,
    user_id: str,
    product_key: str,
    purchase: dict,
    paid_at: Optional[datetime] = None,
) -> Optional[dict]:
    if not is_b2c_listing_slot_product(product_key):
        return None
    db = Database.get()
    listing = await db.properties.find_one(
        {"id": listing_id, "owner_user_id": user_id, "is_private_listing": True},
        {"_id": 0, "id": 1, "price": 1, "rent_monthly": 1},
    )
    if not listing:
        logger.error("apply_slot: listing missing listing=%s user=%s", listing_id, user_id)
        return None
    if listing_requires_premium_sku(listing) and product_key != "b2c_listing_premium":
        logger.error(
            "apply_slot: premium property requires b2c_listing_premium listing=%s product=%s",
            listing_id, product_key,
        )
        return None
    fields = slot_fields_from_purchase(purchase, paid_at=paid_at)
    await db.properties.update_one({"id": listing_id}, {"$set": fields})
    logger.info(
        "listing slot applied listing=%s tier=%s until=%s product=%s",
        listing_id, fields["listing_publish_tier"], fields["listing_paid_until"], product_key,
    )
    return {"listing_id": listing_id, **fields}


async def mark_slot_credit(stripe_session_id: str, *, product_key: str) -> None:
    """Mark a paid purchase as an unused slot credit (no listing bound)."""
    if not is_b2c_listing_slot_product(product_key):
        return
    db = Database.get()
    await db.b2c_purchases.update_one(
        {"stripe_session_id": stripe_session_id},
        {"$set": {"slot_credit": True, "slot_consumed": False}},
    )


async def apply_listing_addon(
    *,
    listing_id: str,
    user_id: str,
    product_key: str,
) -> Optional[dict]:
    if not is_b2c_listing_addon_product(product_key):
        return None
    catalog = B2C_ONE_SHOT_PRODUCTS.get(product_key) or {}
    addon = catalog.get("listing_addon")
    db = Database.get()
    listing = await db.properties.find_one(
        {"id": listing_id, "owner_user_id": user_id, "is_private_listing": True},
        {"_id": 0, "id": 1, "photo_pack_extra": 1},
    )
    if not listing:
        logger.error("apply_addon: listing missing listing=%s user=%s", listing_id, user_id)
        return None
    now = datetime.now(timezone.utc).isoformat()
    update: Dict[str, Any] = {"updated_at": now}
    if addon == "hide_address":
        update["hide_address"] = True
        update["hide_address_paid"] = True
        update["hide_address_paid_at"] = now
    elif addon == "photo_pack":
        current = int(listing.get("photo_pack_extra") or 0)
        update["photo_pack_extra"] = min(PHOTO_PACK_EXTRA, current + PHOTO_PACK_EXTRA) \
            if current else PHOTO_PACK_EXTRA
        # idempotent: one pack → +10 once
        if current >= PHOTO_PACK_EXTRA:
            update["photo_pack_extra"] = current
        update["photo_pack_paid_at"] = now
    else:
        logger.warning("apply_addon: unknown addon=%s product=%s", addon, product_key)
        return None
    await db.properties.update_one({"id": listing_id}, {"$set": update})
    logger.info("listing addon applied listing=%s addon=%s product=%s", listing_id, addon, product_key)
    return {"listing_id": listing_id, **update}


async def fulfill_listing_publish_purchase(
    *,
    session_id: str,
    product_key: str,
    user_id: str,
    listing_id: Optional[str],
    purchase: dict,
    paid_at: Optional[datetime] = None,
) -> None:
    """Webhook/status fulfillment for slot + addon SKUs."""
    paid_at = paid_at or datetime.now(timezone.utc)
    if is_b2c_listing_slot_product(product_key):
        if listing_id:
            await apply_slot_to_listing(
                listing_id=listing_id,
                user_id=user_id,
                product_key=product_key,
                purchase=purchase,
                paid_at=paid_at,
            )
            # Bound to listing → not a free-floating credit
            db = Database.get()
            await db.b2c_purchases.update_one(
                {"stripe_session_id": session_id},
                {"$set": {"slot_credit": False, "slot_consumed": True, "listing_id": listing_id}},
            )
        else:
            await mark_slot_credit(session_id, product_key=product_key)
        return
    if is_b2c_listing_addon_product(product_key):
        if not listing_id:
            logger.error("addon paid without listing session=%s product=%s", session_id, product_key)
            return
        await apply_listing_addon(
            listing_id=listing_id,
            user_id=user_id,
            product_key=product_key,
        )
