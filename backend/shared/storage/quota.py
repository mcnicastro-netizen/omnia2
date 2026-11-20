"""OMNIA — storage quota (D-085 + D-175 C6).

C6 / S1–S3 / S3-bis:
  quota_cc = included_plan(CC) + commercial_customers.storage_extra_gb
  used_cc  = Σ usage(org)
  included_plan counted ONCE per CommercialCustomer (not per branch).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

# D-085 — included quota (GB) by commercial plan tier
TIER_QUOTA_GB = {
    "starter": 30,
    "pro": 100,
    "agency": 300,
}
# No active subscription → free / trial soft cap (once per CC)
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

_ACTIVE_SUB_STATUSES = ("active", "trialing", "past_due")


def bytes_to_gb(n: int) -> float:
    return round(n / (1024 ** 3), 4)


def gb_to_bytes(gb: float) -> int:
    return int(gb * (1024 ** 3))


def included_quota_gb(tier: Optional[str]) -> int:
    if not tier:
        return FREE_QUOTA_GB
    return TIER_QUOTA_GB.get(tier, FREE_QUOTA_GB)


def agency_extra_gb(agency: Optional[dict]) -> int:
    """Legacy agency extra (S2 compat / suspended). Not SoT after C6."""
    try:
        return max(0, int((agency or {}).get("storage_extra_gb") or 0))
    except (TypeError, ValueError):
        return 0


def total_quota_gb(tier: Optional[str], agency: Optional[dict]) -> int:
    """Legacy helper — prefer get_storage_status pool fields."""
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
    cursor = db.properties.find(
        {"agency_id": agency_id},
        {"_id": 0, "photos": 1, "videos": 1, "floor_plans": 1, "documents": 1},
    )
    props = await cursor.to_list(length=100_000)
    return sum(_sum_media_bytes(prop) for prop in props)


async def resolve_tier(db, agency_id: str, agency: Optional[dict] = None) -> Optional[str]:
    """Legacy per-agency tier (display / fallback when CC missing)."""
    sub = await db.subscriptions.find_one(
        {"agency_id": agency_id, "status": {"$in": list(_ACTIVE_SUB_STATUSES)}},
        {"_id": 0, "tier": 1, "plan_tier": 1, "status": 1},
    )
    sub_tier = (sub or {}).get("tier") or (sub or {}).get("plan_tier")
    if sub_tier in TIER_QUOTA_GB:
        return sub_tier
    if agency is None:
        agency = await db.agencies.find_one(
            {"id": agency_id}, {"_id": 0, "plan": 1, "plan_type": 1}
        )
    agency = agency or {}
    plan = agency.get("plan") or agency.get("plan_type")
    return _PLAN_ALIAS.get(plan)


async def list_orgs_for_cc(db, commercial_customer_id: str) -> List[dict]:
    rows = await db.agencies.find(
        {"commercial_customer_id": commercial_customer_id},
        {"_id": 0, "id": 1, "display_name": 1, "storage_extra_gb": 1, "plan": 1, "plan_type": 1},
    ).to_list(length=5000)
    return rows or []


async def resolve_cc_plan_tier(db, commercial_customer_id: str) -> Tuple[Optional[str], bool]:
    """Return (tier, ambiguous). Included counted once — never sum per org.

    If multiple distinct active tiers on the same CC (legacy anomaly): use max
    included tier and set ambiguous=True.
    """
    subs = await db.subscriptions.find(
        {
            "commercial_customer_id": commercial_customer_id,
            "status": {"$in": list(_ACTIVE_SUB_STATUSES)},
        },
        {"_id": 0, "tier": 1, "plan_tier": 1},
    ).to_list(length=100)

    tiers: List[str] = []
    for s in subs or []:
        t = (s.get("tier") or s.get("plan_tier") or "").strip().lower()
        if t in TIER_QUOTA_GB:
            tiers.append(t)

    if not tiers:
        # Fallback: any org-linked subscription by agency_id
        orgs = await list_orgs_for_cc(db, commercial_customer_id)
        for org in orgs:
            t = await resolve_tier(db, org["id"], org)
            if t in TIER_QUOTA_GB:
                tiers.append(t)

    if not tiers:
        return None, False

    distinct = sorted(set(tiers), key=lambda x: TIER_QUOTA_GB.get(x, 0))
    best = distinct[-1]
    return best, len(distinct) > 1


def effective_extra_gb(
    cc: Optional[dict],
    agencies: Optional[List[dict]] = None,
) -> int:
    """S1 SoT + S2 suspended compat (additive legacy agency extras)."""
    cc = cc or {}
    try:
        cc_extra = max(0, int(cc.get("storage_extra_gb") or 0))
    except (TypeError, ValueError):
        cc_extra = 0
    status = (cc.get("storage_migration_status") or "").strip().lower()
    if status == "suspended":
        legacy = 0
        for a in agencies or []:
            legacy += agency_extra_gb(a)
        return cc_extra + legacy
    if status == "migrated":
        return cc_extra
    # pending/none/unknown: prefer CC SoT; still add legacy so we never under-quota
    # before migration runs (safe default).
    legacy = sum(agency_extra_gb(a) for a in (agencies or []))
    if cc_extra > 0:
        return cc_extra + legacy
    return legacy if legacy else cc_extra


async def get_storage_status_for_cc(db, commercial_customer_id: str) -> Dict[str, Any]:
    cc = await db.commercial_customers.find_one(
        {"id": commercial_customer_id},
        {
            "_id": 0,
            "id": 1,
            "storage_extra_gb": 1,
            "storage_migration_status": 1,
            "legal_name": 1,
        },
    )
    if not cc:
        raise HTTPException(status_code=404, detail="commercial_customer_not_found")

    orgs = await list_orgs_for_cc(db, commercial_customer_id)
    tier, ambiguous = await resolve_cc_plan_tier(db, commercial_customer_id)
    included = included_quota_gb(tier)
    extra = effective_extra_gb(cc, orgs)
    quota_gb = included + extra

    org_rows: List[dict] = []
    used_cc = 0
    for org in orgs:
        u = await compute_usage_bytes(db, org["id"])
        used_cc += u
        org_rows.append(
            {
                "organization_id": org["id"],
                "display_name": org.get("display_name"),
                "used_bytes": u,
                "used_gb": bytes_to_gb(u),
            }
        )

    quota_b = gb_to_bytes(quota_gb)
    pct = (used_cc / quota_b * 100.0) if quota_b > 0 else 100.0
    return {
        "scope": "commercial_customer",
        "commercial_customer_id": commercial_customer_id,
        "plan_tier": tier,
        "plan_tier_ambiguous": ambiguous,
        "included_plan_gb": included,
        "extra_gb": extra,
        "quota_cc_gb": quota_gb,
        "quota_gb": quota_gb,  # alias
        "used_cc_bytes": used_cc,
        "used_bytes": used_cc,
        "used_cc_gb": bytes_to_gb(used_cc),
        "used_gb": bytes_to_gb(used_cc),
        "quota_bytes": quota_b,
        "percent_used_cc": round(min(pct, 999.0), 1),
        "percent_used": round(min(pct, 999.0), 1),
        "warn_80": pct >= 80,
        "warn_90": pct >= 90,
        "full": used_cc >= quota_b,
        "migration_status": cc.get("storage_migration_status") or "none",
        "organizations": org_rows,
        "addon": {
            "gb": STORAGE_ADDON_GB,
            "price_eur_monthly": STORAGE_ADDON_EUR,
            "key": "storage_100gb",
        },
    }


async def get_storage_status(db, agency_id: str) -> Dict[str, Any]:
    """Org-scoped meter that enforces / reports the CC shared pool (S3)."""
    agency = await db.agencies.find_one(
        {"id": agency_id},
        {
            "_id": 0,
            "id": 1,
            "plan": 1,
            "plan_type": 1,
            "storage_extra_gb": 1,
            "display_name": 1,
            "commercial_customer_id": 1,
        },
    )
    cc_id = ((agency or {}).get("commercial_customer_id") or "").strip() or None
    used_org = await compute_usage_bytes(db, agency_id)

    if not cc_id:
        # Fail-soft legacy: single-agency pool (pre-CC link)
        tier = await resolve_tier(db, agency_id, agency)
        included = included_quota_gb(tier)
        extra = agency_extra_gb(agency)
        quota_gb = included + extra
        quota_b = gb_to_bytes(quota_gb)
        pct = (used_org / quota_b * 100.0) if quota_b > 0 else 100.0
        return {
            "scope": "organization",
            "agency_id": agency_id,
            "organization_id": agency_id,
            "commercial_customer_id": None,
            "tier": tier,
            "plan_tier": tier,
            "included_plan_gb": included,
            "included_gb": included,
            "extra_gb": extra,
            "quota_cc_gb": quota_gb,
            "quota_gb": quota_gb,
            "used_org_bytes": used_org,
            "used_org_gb": bytes_to_gb(used_org),
            "used_cc_bytes": used_org,
            "used_bytes": used_org,
            "used_cc_gb": bytes_to_gb(used_org),
            "used_gb": bytes_to_gb(used_org),
            "quota_bytes": quota_b,
            "percent_used_cc": round(min(pct, 999.0), 1),
            "percent_used": round(min(pct, 999.0), 1),
            "warn_80": pct >= 80,
            "warn_90": pct >= 90,
            "full": used_org >= quota_b,
            "migration_status": "none",
            "addon": {
                "gb": STORAGE_ADDON_GB,
                "price_eur_monthly": STORAGE_ADDON_EUR,
                "key": "storage_100gb",
            },
        }

    pool = await get_storage_status_for_cc(db, cc_id)
    return {
        **pool,
        "scope": "organization",
        "agency_id": agency_id,
        "organization_id": agency_id,
        "tier": pool.get("plan_tier"),
        "included_gb": pool.get("included_plan_gb"),
        "used_org_bytes": used_org,
        "used_org_gb": bytes_to_gb(used_org),
        # used_bytes / quota_gb remain pool-level for assert_can_upload compat
        "used_bytes": pool["used_cc_bytes"],
        "used_gb": pool["used_cc_gb"],
        "quota_gb": pool["quota_cc_gb"],
        "quota_bytes": pool["quota_bytes"],
        "percent_used": pool["percent_used_cc"],
        "full": pool["full"],
        "warn_80": pool["warn_80"],
        "warn_90": pool["warn_90"],
    }


async def assert_can_upload(db, agency_id: str, incoming_bytes: int) -> Dict[str, Any]:
    """Raise 413 if upload would exceed the CC shared pool (S3)."""
    status = await get_storage_status(db, agency_id)
    if status["used_bytes"] + max(0, incoming_bytes) > status["quota_bytes"]:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "storage_quota_exceeded",
                "message": (
                    "Spazio archivio esaurito sul CommercialCustomer. "
                    f"Usati {status.get('used_cc_gb', status['used_gb'])} GB "
                    f"su {status.get('quota_cc_gb', status['quota_gb'])} GB "
                    f"(pool condiviso). "
                    f"Aggiungi {STORAGE_ADDON_GB} GB a €{STORAGE_ADDON_EUR:.0f}/mese "
                    "da Piano & Crediti, oppure libera spazio."
                ),
                "used_gb": status.get("used_cc_gb", status["used_gb"]),
                "quota_gb": status.get("quota_cc_gb", status["quota_gb"]),
                "used_org_gb": status.get("used_org_gb"),
                "used_cc_gb": status.get("used_cc_gb", status["used_gb"]),
                "quota_cc_gb": status.get("quota_cc_gb", status["quota_gb"]),
                "commercial_customer_id": status.get("commercial_customer_id"),
                "addon_gb": STORAGE_ADDON_GB,
                "addon_eur": STORAGE_ADDON_EUR,
            },
        )
    return status
