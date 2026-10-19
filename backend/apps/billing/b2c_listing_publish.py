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


# --- Scadenza slot a pagamento (cron) ------------------------------------

EXPIRE_BATCH_CAP = 200


def expired_paid_slot_query(now_iso: str) -> Dict[str, Any]:
    """Annunci privati con slot pagato scaduto, ancora bozza/attivi, non già scaduti."""
    from shared.db.trash import with_not_trashed
    return with_not_trashed({
        "is_private_listing": True,
        "listing_paid_until": {"$exists": True, "$ne": None, "$lte": now_iso},
        "status": {"$in": ["draft", "active"]},
        "listing_slot_expired_at": {"$exists": False},
    })


async def _notify_owner_slot_expired(db, listing: Dict[str, Any]) -> None:
    owner_id = listing.get("owner_user_id")
    if not owner_id:
        return
    title = listing.get("title") or "Annuncio"
    try:
        from shared.notifications.center import TYPE_LISTING_SLOT_EXPIRED, notify_users
        await notify_users(
            [owner_id],
            type=TYPE_LISTING_SLOT_EXPIRED,
            title=f"Slot scaduto · {title}",
            body="I 90 giorni di pubblicazione a pagamento sono terminati. L'annuncio non è più online.",
            link="/cloud/account/sell",
            agency_id=None,
            meta={"property_id": listing.get("id"), "reason": "listing_slot_expired"},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("slot expire in-app notify failed listing=%s: %s", listing.get("id"), e)

    try:
        owner = await db.users.find_one(
            {"id": owner_id},
            {"_id": 0, "email": 1, "lang": 1},
        )
        email = (owner or {}).get("email") or (listing.get("owner") or {}).get("email")
        if not email:
            return
        from shared.email.client import send_email
        await send_email(
            to=email,
            template="listing_moderation",
            lang=(owner or {}).get("lang") or "it",
            subject=f"ImmobilCloud — slot scaduto · {title}",
            variables={
                "title": title,
                "body": (
                    "Il periodo di 90 giorni dello slot a pagamento è terminato. "
                    "L'annuncio non è più visibile sul portale. "
                    "Puoi acquistare un nuovo slot da Area venditore."
                ),
                "listing_id": listing.get("id") or "",
            },
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("slot expire email failed listing=%s: %s", listing.get("id"), e)


async def expire_one_paid_listing(db, listing: Dict[str, Any], *, now_iso: str) -> bool:
    """Ritira un annuncio con slot scaduto. Idempotente. Returns True se modificato."""
    pid = listing.get("id")
    if not pid:
        return False
    update = {
        "status": "withdrawn",
        "visibility": "private",
        "is_listed_on_immobilcloud": False,
        "listing_slot_expired_at": now_iso,
        "listing_slot_expire_reason": "paid_slot_90d",
        "updated_at": now_iso,
    }
    r = await db.properties.update_one(
        {
            "id": pid,
            "is_private_listing": True,
            "status": {"$in": ["draft", "active"]},
            "listing_slot_expired_at": {"$exists": False},
        },
        {"$set": update},
    )
    if r.modified_count == 0:
        return False

    try:
        from apps.immocloud.favorite_watch import record_listing_ended
        await record_listing_ended(
            db,
            property_id=pid,
            existing=listing,
            new_status="withdrawn",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("favorite_watch on slot expire failed listing=%s: %s", pid, e)

    await _notify_owner_slot_expired(db, listing)
    logger.info("paid listing slot expired listing=%s owner=%s", pid, listing.get("owner_user_id"))
    return True


async def run_expire_paid_listing_slots(*, limit: int = EXPIRE_BATCH_CAP) -> Dict[str, Any]:
    """Cron: ritira annunci privati con listing_paid_until scaduto."""
    db = Database.get()
    now_iso = datetime.now(timezone.utc).isoformat()
    q = expired_paid_slot_query(now_iso)
    cursor = db.properties.find(
        q,
        {"_id": 0, "id": 1, "title": 1, "owner_user_id": 1, "owner": 1,
         "status": 1, "listing_paid_until": 1},
    ).sort("listing_paid_until", 1).limit(max(1, min(int(limit), EXPIRE_BATCH_CAP)))
    scanned = 0
    expired = 0
    async for listing in cursor:
        scanned += 1
        if await expire_one_paid_listing(db, listing, now_iso=now_iso):
            expired += 1
    return {
        "ok": True,
        "scanned": scanned,
        "expired": expired,
        "now": now_iso,
    }
