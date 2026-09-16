"""OMNIA — Price history + drop detection for ImmobilCloud.

Tracks price/rent changes on listings so saved-search alerts and Scout HAL
can surface real *ribassi* (Idealista/Immobiliare have this; we need it too).

Storage: embedded `price_history` array on `properties` (capped) +
`price_dropped_at` ISO timestamp for fast cron queries.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omnia.price_watch")

_HISTORY_CAP = 40


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _num(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


async def record_price_change(
    db,
    *,
    property_id: str,
    existing: Dict[str, Any],
    new_price: Any = None,
    new_rent: Any = None,
    touched_price: bool = False,
    touched_rent: bool = False,
) -> Optional[dict]:
    """If price/rent changed downward or upward, append history.

    Returns the history entry when a change was recorded, else None.
    Call only when the update payload actually includes price fields.
    """
    if not touched_price and not touched_rent:
        return None

    old_price = _num(existing.get("price"))
    old_rent = _num(existing.get("rent_monthly"))
    price = _num(new_price) if touched_price else old_price
    rent = _num(new_rent) if touched_rent else old_rent

    # Nothing meaningful changed
    if price == old_price and rent == old_rent:
        return None

    entry = {
        "at": _now_iso(),
        "price": price,
        "rent_monthly": rent,
        "prev_price": old_price,
        "prev_rent_monthly": old_rent,
    }
    drop = False
    if price is not None and old_price is not None and price < old_price:
        drop = True
        entry["drop_eur"] = round(old_price - price, 2)
        entry["drop_pct"] = round(100.0 * (old_price - price) / old_price, 2) if old_price else None
    if rent is not None and old_rent is not None and rent < old_rent:
        drop = True
        entry["drop_rent_eur"] = round(old_rent - rent, 2)

    hist: List[dict] = list(existing.get("price_history") or [])
    # Seed first snapshot of previous value if history empty
    if not hist and (old_price is not None or old_rent is not None):
        hist.append({
            "at": existing.get("created_at") or existing.get("updated_at") or _now_iso(),
            "price": old_price,
            "rent_monthly": old_rent,
            "seed": True,
        })
    hist.append(entry)
    hist = hist[-_HISTORY_CAP:]

    update: Dict[str, Any] = {"price_history": hist}
    if drop:
        update["price_dropped_at"] = entry["at"]
        update["last_price_drop"] = {
            "at": entry["at"],
            "from_price": old_price,
            "to_price": price,
            "from_rent": old_rent,
            "to_rent": rent,
            "drop_eur": entry.get("drop_eur") or entry.get("drop_rent_eur"),
            "drop_pct": entry.get("drop_pct"),
        }
    await db.properties.update_one({"id": property_id}, {"$set": update})
    logger.info(
        "price_watch prop=%s drop=%s price %s→%s rent %s→%s",
        property_id, drop, old_price, price, old_rent, rent,
    )
    if drop:
        try:
            from apps.immocloud.alert_fanout import fanout_listing_event
            await fanout_listing_event(property_id, event="price_drop")
        except Exception as e:
            logger.warning("fanout after price drop failed: %s", e)
    return entry


async def find_price_drops(
    db,
    *,
    mongo_filter: Dict[str, Any],
    since_iso: Optional[str],
    limit: int = 20,
) -> List[dict]:
    """Listings matching `mongo_filter` that dropped price after `since_iso`."""
    flt = dict(mongo_filter)
    if since_iso:
        flt["price_dropped_at"] = {"$gt": since_iso}
    else:
        flt["price_dropped_at"] = {"$exists": True}
    # Don't double-count brand-new listings as "drops"
    if "created_at" in flt:
        flt = {k: v for k, v in flt.items() if k != "created_at"}
        if since_iso:
            flt["price_dropped_at"] = {"$gt": since_iso}

    cursor = db.properties.find(flt, {
        "_id": 0, "id": 1, "title": 1, "city": 1, "zone": 1, "price": 1,
        "rent_monthly": 1, "surface_sqm": 1, "rooms": 1, "operation": 1,
        "property_type": 1, "created_at": 1, "price_dropped_at": 1,
        "last_price_drop": 1, "boost_tier": 1,
    }).sort("price_dropped_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
