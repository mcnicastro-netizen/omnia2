"""B04-DES-03 — Versioned plan catalog + commercial terms snapshot.

Published catalog versions are immutable documents. Runtime LAUNCH/POST_TRACTION
tables in plans.py remain the source for building the published snapshot;
once written to Mongo as a version, they must not be overwritten in place.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from apps.billing.plans import (
    LAUNCH_PLANS,
    POST_TRACTION_PLANS,
    Plan,
    PlanTier,
    get_plan,
)

# Baseline listino handoff B04 — PRICING_OMNIA.md v3.3 (9 nov 2026)
CATALOG_VERSION_ID = "v3.3-2026-11-09"
CATALOG_VERSION_LABEL = "v3.3"
CATALOG_EFFECTIVE_FROM = "2026-11-09"

PricingPhase = Literal["launch", "post_traction"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plan_to_dict(plan: Plan) -> dict:
    return plan.model_dump()


def build_catalog_payload(*, phase: PricingPhase) -> dict:
    source = LAUNCH_PLANS if phase == "launch" else POST_TRACTION_PLANS
    return {
        "pricing_phase": phase,
        "plans": {tier: _plan_to_dict(p) for tier, p in source.items()},
        "notes": {
            "annual_equals_11_months": True,
            "credit_eur": 0.05,
            "public_tiers": ["starter", "pro", "agency"],
            "no_public_enterprise": True,
            "no_self_serve_trial": True,
        },
    }


def published_catalog_document() -> dict:
    """Immutable published version covering both Founder and Standard price lists."""
    return {
        "id": CATALOG_VERSION_ID,
        "version_label": CATALOG_VERSION_LABEL,
        "effective_from": CATALOG_EFFECTIVE_FROM,
        "immutable": True,
        "phases": {
            "launch": build_catalog_payload(phase="launch"),
            "post_traction": build_catalog_payload(phase="post_traction"),
        },
        "published_at": f"{CATALOG_EFFECTIVE_FROM}T00:00:00+00:00",
    }


async def ensure_plan_catalog_version(db) -> dict:
    """Insert published catalog once; never overwrite an existing version id."""
    existing = await db.plan_catalog_versions.find_one(
        {"id": CATALOG_VERSION_ID}, {"_id": 0}
    )
    if existing:
        return existing
    doc = published_catalog_document()
    doc["created_at"] = _now()
    try:
        await db.plan_catalog_versions.insert_one(doc)
    except Exception:
        existing = await db.plan_catalog_versions.find_one(
            {"id": CATALOG_VERSION_ID}, {"_id": 0}
        )
        if existing:
            return existing
        raise
    return {k: v for k, v in doc.items() if k != "_id"}


def resolve_pricing_phase_for_customer(
    *,
    first_paid_activated_at: Optional[str],
    now: Optional[datetime] = None,
) -> PricingPhase:
    """Founder = 12 months from first paid activation (DES-03)."""
    if not first_paid_activated_at:
        return "launch"
    try:
        start = datetime.fromisoformat(first_paid_activated_at.replace("Z", "+00:00"))
    except ValueError:
        return "launch"
    ref = now or datetime.now(timezone.utc)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    delta_days = (ref - start).days
    if delta_days < 365:
        return "launch"
    return "post_traction"


def snapshot_commercial_terms(
    *,
    tier: PlanTier | str,
    billing_cycle: Literal["monthly", "yearly"],
    pricing_phase: PricingPhase,
    catalog_version_id: str = CATALOG_VERSION_ID,
) -> Dict[str, Any]:
    """Frozen commercial terms attached to a subscription (DES-03)."""
    catalog = LAUNCH_PLANS if pricing_phase == "launch" else POST_TRACTION_PLANS
    plan = catalog.get(tier)  # type: ignore[arg-type]
    if not plan:
        plan = get_plan(tier)  # type: ignore[arg-type]
    if not plan:
        raise ValueError(f"unknown_plan_tier:{tier}")
    price = plan.price_yearly if billing_cycle == "yearly" else plan.price_monthly
    return {
        "catalog_version_id": catalog_version_id,
        "version_label": CATALOG_VERSION_LABEL,
        "pricing_phase": pricing_phase,
        "tier": plan.tier,
        "billing_cycle": billing_cycle,
        "price_eur": price,
        "max_agents": plan.max_agents,
        "max_properties": plan.max_properties,
        "credits_included_monthly": plan.credits_included_monthly,
        "snapshotted_at": _now(),
    }


def active_runtime_phase_from_env() -> PricingPhase:
    """Legacy env switch — used only when CC has no first_paid_activated_at context."""
    import os

    phase = (os.environ.get("PRICING_PHASE") or "launch").lower()
    if phase == "post_traction":
        return "post_traction"
    return "launch"
