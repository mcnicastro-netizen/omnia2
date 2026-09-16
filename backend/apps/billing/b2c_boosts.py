"""OMNIA — B2C listing visibility boosts (Vetrina / Premium / TOP).

Applies Stripe one-shot purchases onto private listings:
  - boost_tier: "vetrina" | "premium" | "top"
  - boost_rank: numeric sort key (top > premium > vetrina)
  - boost_until: ISO expiry
  - boost_product_key: catalog key that activated the boost

Idempotent: webhook re-delivery re-applies the same fields.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from shared.db.connection import Database
from apps.billing.b2c_products import (
    B2C_ONE_SHOT_PRODUCTS,
    BOOST_RANK,
    get_b2c_product,
    is_b2c_boost_product,
)

logger = logging.getLogger("omnia.billing.b2c_boosts")


def boost_duration_days(product_key: str) -> int:
    catalog = get_b2c_product(product_key) or {}
    return int(catalog.get("duration_days") or 0)


def boost_tier_for(product_key: str) -> Optional[str]:
    catalog = get_b2c_product(product_key) or {}
    return catalog.get("boost_tier")


def effective_boost(doc: Dict[str, Any], *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Return active boost info for a listing document (empty if expired/none)."""
    now = now or datetime.now(timezone.utc)
    tier = doc.get("boost_tier")
    until_raw = doc.get("boost_until")
    if not tier or not until_raw:
        return {"active": False, "tier": None, "rank": 0, "until": None}
    try:
        until = datetime.fromisoformat(str(until_raw).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return {"active": False, "tier": None, "rank": 0, "until": None}
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    if until <= now:
        return {"active": False, "tier": None, "rank": 0, "until": until_raw}
    return {
        "active": True,
        "tier": tier,
        "rank": int(doc.get("boost_rank") or BOOST_RANK.get(tier, 0)),
        "until": until_raw,
        "product_key": doc.get("boost_product_key"),
    }


async def apply_boost_to_listing(
    *,
    listing_id: str,
    user_id: str,
    product_key: str,
    paid_at: Optional[datetime] = None,
) -> Optional[dict]:
    """Activate a paid boost on a private listing owned by `user_id`."""
    if not is_b2c_boost_product(product_key):
        logger.warning("apply_boost: not a boost product_key=%s", product_key)
        return None
    catalog = B2C_ONE_SHOT_PRODUCTS[product_key]
    tier = catalog["boost_tier"]
    days = int(catalog["duration_days"])
    rank = int(BOOST_RANK.get(tier, 0))
    paid_at = paid_at or datetime.now(timezone.utc)
    until = paid_at + timedelta(days=days)

    db = Database.get()
    listing = await db.properties.find_one(
        {
            "id": listing_id,
            "owner_user_id": user_id,
            "is_private_listing": True,
        },
        {"_id": 0, "id": 1},
    )
    if not listing:
        logger.error(
            "apply_boost: listing not found or not owned listing=%s user=%s product=%s",
            listing_id, user_id, product_key,
        )
        return None

    update = {
        "boost_tier": tier,
        "boost_rank": rank,
        "boost_until": until.isoformat(),
        "boost_product_key": product_key,
        "boost_activated_at": paid_at.isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.properties.update_one({"id": listing_id}, {"$set": update})
    logger.info(
        "boost applied listing=%s tier=%s days=%s until=%s product=%s",
        listing_id, tier, days, until.isoformat(), product_key,
    )
    return {"listing_id": listing_id, **update}
