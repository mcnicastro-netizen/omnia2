"""OMNIA — D-085 agency media storage quota.

Single counter (foto + documenti + video + planimetrie).
Included GB by subscription tier + storage_extra_gb on the agency.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException

# D-085 — included quota (GB)
TIER_QUOTA_GB = {
    "starter": 30,
    "pro": 100,
    "agency": 300,
}
# No active subscription → free / trial soft cap
FREE_QUOTA_GB = 5

# Legacy agencies.plan / agencies.plan_type → tier
_PLAN_ALIAS = {
    "free": None,
    "starter": "starter",
    "pro": "pro",
    "enterprise": "agency",
    "agency": "agency",
    "turnkey": "pro",
}

STORAGE_ADDON_GB = 100
STORAGE_ADDON_EUR = 15.0

# Estimate when size_bytes missing (photos often lack it pre-D-085)
_MISSING_PHOTO_BYTES = 600_000


def bytes_to_gb(n: int) -> float:
    return round(n / (1024 ** 3), 4)


def gb_to_bytes(gb: float) -> int:
    return int(gb * (1024 ** 3))


async def resolve_tier(db, agency_id: str, agency: Optional[dict] = None) -> Optional[str]:
    sub = await db.subscriptions.find_one(
        {"agency_id": agency_id, "status": {"$in": ["active", "trialing", "past_due"]}},
        {"_id": 0, "tier": 1, "status": 1},
    )
    if sub and sub.get("tier") in TIER_QUOTA_GB:
        return sub["tier"]
    if agency is None:
        agency = await db.agencies.find_one(
            {"id": agency_id}, {"_id": 0, "plan": 1, "plan_type": 1}
        )
    agency = agency or {}
    plan = agency.get("plan") or agency.get("plan_type")
    return _PLAN_ALIAS.get(plan)


def included_quota_gb(tier: Optional[str]) -> int:
    if not tier:
        return FREE_QUOTA_GB
    return TIER_QUOTA_GB.get(tier, FREE_QUOTA_GB)


def agency_extra_gb(agency: Optional[dict]) -> int:
    try:
        return max(0, int((agency or {}).get("storage_extra_gb") or 0))
    except (TypeError, ValueError):
        return 0


def total_quota_gb(tier: Optional[str], agency: Optional[dict]) -> int:
    return included_quota_gb(tier) + agency_extra_gb(agency)


def _sum_media_bytes(prop: dict) -> int:
    total = 0
    for p in prop.get("photos") or []:
        total += int(p.get("size_bytes") or _MISSING_PHOTO_BYTES)
    for v in prop.get("videos") or []:
        total += int(v.get("size_bytes") or 0)
    for f in prop.get("floor_plans") or []:
        total += int(f.get("size_bytes") or 0)
    for d in prop.get("documents") or []:
        total += int(d.get("size") or d.get("size_bytes") or 0)
    return total


async def compute_usage_bytes(db, agency_id: str) -> int:
    """Sum media on all agency properties (incl. Cestino — still on disk)."""
    total = 0
    cursor = db.properties.find(
        {"agency_id": agency_id},
        {"_id": 0, "photos": 1, "videos": 1, "floor_plans": 1, "documents": 1},
    )
    async for prop in cursor:
        total += _sum_media_bytes(prop)
    return total


async def get_storage_status(db, agency_id: str) -> Dict[str, Any]:
    agency = await db.agencies.find_one(
        {"id": agency_id},
        {"_id": 0, "id": 1, "plan": 1, "plan_type": 1, "storage_extra_gb": 1, "display_name": 1},
    )
    tier = await resolve_tier(db, agency_id, agency)
    included = included_quota_gb(tier)
    extra = agency_extra_gb(agency)
    quota_gb = included + extra
    used = await compute_usage_bytes(db, agency_id)
    quota_b = gb_to_bytes(quota_gb)
    pct = (used / quota_b * 100.0) if quota_b > 0 else 100.0
    return {
        "agency_id": agency_id,
        "tier": tier,
        "included_gb": included,
        "extra_gb": extra,
        "quota_gb": quota_gb,
        "used_bytes": used,
        "used_gb": bytes_to_gb(used),
        "quota_bytes": quota_b,
        "percent_used": round(min(pct, 999.0), 1),
        "warn_80": pct >= 80,
        "warn_90": pct >= 90,
        "full": used >= quota_b,
        "addon": {
            "gb": STORAGE_ADDON_GB,
            "price_eur_monthly": STORAGE_ADDON_EUR,
            "key": "storage_100gb",
        },
    }


async def assert_can_upload(db, agency_id: str, incoming_bytes: int) -> Dict[str, Any]:
    """Raise 413 storage_quota_exceeded if upload would exceed quota."""
    status = await get_storage_status(db, agency_id)
    if status["used_bytes"] + max(0, incoming_bytes) > status["quota_bytes"]:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "storage_quota_exceeded",
                "message": (
                    "Spazio archivio esaurito. "
                    f"Usati {status['used_gb']} GB su {status['quota_gb']} GB. "
                    f"Aggiungi {STORAGE_ADDON_GB} GB a €{STORAGE_ADDON_EUR:.0f}/mese "
                    "da Piano & Crediti, oppure libera spazio."
                ),
                "used_gb": status["used_gb"],
                "quota_gb": status["quota_gb"],
                "addon_gb": STORAGE_ADDON_GB,
                "addon_eur": STORAGE_ADDON_EUR,
            },
        )
    return status
