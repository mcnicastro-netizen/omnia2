"""OMNIA — Market Pulse for ImmobilCloud home.

Real 7-day stats for a city: new listings, price drops, avg asking €/mq.
Not fluff — computed from live Mongo inventory.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from shared.db.connection import Database
from apps.immocloud.public_portal import _base_filter

router = APIRouter(tags=["cloud-pulse"])


@router.get("/pulse")
async def market_pulse(
    city: Optional[str] = Query(None, max_length=100),
    operation: str = Query("sale", pattern="^(sale|rent)$"),
    days: int = Query(7, ge=1, le=30),
):
    db = Database.get()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    flt: Dict[str, Any] = _base_filter()
    flt["operation"] = operation
    if city:
        flt["city"] = {"$regex": f"^{city}", "$options": "i"}

    new_flt = {**flt, "created_at": {"$gte": since}}
    drop_flt = {**flt, "price_dropped_at": {"$gte": since}}

    new_count = await db.properties.count_documents(new_flt)
    drop_count = await db.properties.count_documents(drop_flt)

    price_field = "rent_monthly" if operation == "rent" else "price"
    match_avg = {**flt, "surface_sqm": {"$gt": 0}, price_field: {"$gt": 0}}
    pipeline = [
        {"$match": match_avg},
        {"$project": {
            "e_mq": {"$divide": [f"${price_field}", "$surface_sqm"]},
        }},
        {"$group": {"_id": None, "avg": {"$avg": "$e_mq"}, "n": {"$sum": 1}}},
    ]
    agg = await db.properties.aggregate(pipeline).to_list(length=1)
    avg_mq = round(agg[0]["avg"]) if agg else None
    sample_n = int(agg[0]["n"]) if agg else 0

    total_active = await db.properties.count_documents(flt)

    return {
        "city": city,
        "operation": operation,
        "window_days": days,
        "new_listings": new_count,
        "price_drops": drop_count,
        "avg_eur_mq": avg_mq,
        "avg_sample_size": sample_n,
        "total_active": total_active,
        "label_it": (
            f"Ultimi {days} giorni"
            + (f" a {city}" if city else " in Italia")
            + f": {new_count} nuovi"
            + (f", {drop_count} ribassi" if drop_count else "")
            + (f", media ~€{avg_mq}/m²" if avg_mq else "")
        ),
    }
