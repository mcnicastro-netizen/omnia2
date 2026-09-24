"""OMNIA — Daily view/lead buckets for private-seller (and agency) stats (D-093 / A-029).

Honest metrics: scheda openings + contact events — not feed impressions.
Series fills from ship date forward; lifetime totals stay on `properties`.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal

logger = logging.getLogger("omnia.listing_stats")

StatKind = Literal["view", "lead"]


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _day_range(days: int) -> List[str]:
    n = max(1, min(int(days or 30), 90))
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]


async def bump_daily_stat(
    db,
    property_id: str,
    kind: StatKind,
    *,
    n: int = 1,
) -> None:
    """Increment today's bucket. Best-effort — never raise to callers."""
    if not property_id or n <= 0:
        return
    field = "views" if kind == "view" else "leads"
    day = _utc_today()
    try:
        await db.property_stat_days.update_one(
            {"property_id": property_id, "day": day},
            {
                "$inc": {field: n},
                "$setOnInsert": {
                    "property_id": property_id,
                    "day": day,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
            },
            upsert=True,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("bump_daily_stat failed prop=%s kind=%s: %s", property_id, kind, e)


async def get_listing_stats(
    db,
    property_id: str,
    *,
    days: int = 30,
    lifetime_views: int = 0,
    lifetime_leads: int = 0,
) -> Dict[str, Any]:
    """Return lifetime totals + daily series (zeros for missing days)."""
    days_list = _day_range(days)
    cursor = db.property_stat_days.find(
        {"property_id": property_id, "day": {"$in": days_list}},
        {"_id": 0, "day": 1, "views": 1, "leads": 1},
    )
    by_day: Dict[str, dict] = {}
    async for row in cursor:
        by_day[row["day"]] = row

    series: List[Dict[str, Any]] = []
    period_views = 0
    period_leads = 0
    for d in days_list:
        row = by_day.get(d) or {}
        v = int(row.get("views") or 0)
        l = int(row.get("leads") or 0)
        period_views += v
        period_leads += l
        series.append({"day": d, "views": v, "leads": l})

    return {
        "property_id": property_id,
        "days": len(days_list),
        "lifetime": {
            "views": int(lifetime_views or 0),
            "leads": int(lifetime_leads or 0),
        },
        "period": {
            "views": period_views,
            "leads": period_leads,
            "contact_rate": (
                round(100.0 * period_leads / period_views, 1) if period_views else None
            ),
        },
        "series": series,
        "metric_note": (
            "views = aperture scheda annuncio; leads = richieste contatto. "
            "Non sono impressioni nel feed di ricerca."
        ),
    }
