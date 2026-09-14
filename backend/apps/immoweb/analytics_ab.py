"""OMNIA — Analytics A/B testing dashboard (M5.S4.4, Sprint 3 · Item #3).

Confronta performance di 2+ proprietà dell'agenzia su:
- views totali (portal + immobilcloud)
- leads generati (source: portal / widget / immobilcloud)
- CTR (leads / views)
- portali attivi + tasso di successo sync
- prezzo/prezzo-per-mq (baseline zone reference)

Serve al agente per capire quale variante di annuncio (foto, prezzo, testo)
converte meglio prima di committare su un solo listing.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles
from shared.db.connection import Database

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ABTestBody(BaseModel):
    property_ids: List[str] = Field(min_length=2, max_length=6)
    days_lookback: int = Field(default=30, ge=1, le=365)


from shared.auth.tenant import require_agency_404 as _agency_id


async def _property_metrics(db, prop: dict, since_iso: str) -> Dict[str, Any]:
    pid = prop["id"]
    # Leads by property since threshold
    leads_total = await db.leads.count_documents({"property_id": pid})
    leads_recent = await db.leads.count_documents({
        "property_id": pid,
        "created_at": {"$gte": since_iso},
    })
    # Sync log counts (portal publish attempts)
    sync_ok = await db.publishing_sync_logs.count_documents({
        "property_id": pid, "status": "success",
    })
    sync_failed = await db.publishing_sync_logs.count_documents({
        "property_id": pid, "status": "failed",
    })
    # Social posts
    social_ok = await db.social_posts.count_documents({
        "property_id": pid, "status": "success",
    })
    views = int(prop.get("view_count") or 0)
    ctr = round(leads_total / views, 4) if views > 0 else None
    return {
        "id": pid,
        "title": prop.get("title"),
        "price": prop.get("price") or prop.get("rent_monthly"),
        "operation": prop.get("operation"),
        "surface_sqm": prop.get("surface_sqm"),
        "price_per_sqm": (
            round((prop.get("price") or prop.get("rent_monthly") or 0) / prop["surface_sqm"], 2)
            if prop.get("surface_sqm") else None
        ),
        "photos_count": len(prop.get("photos") or []),
        "views_total": views,
        "leads_total": leads_total,
        "leads_recent_period": leads_recent,
        "conversion_rate": ctr,  # leads/views
        "publishing": {
            "sync_success": sync_ok,
            "sync_failed": sync_failed,
            "social_success": social_ok,
        },
        "status": prop.get("status"),
        "created_at": prop.get("created_at"),
    }


@router.post("/ab-test")
async def analytics_ab_test(
    body: ABTestBody,
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    """Compare 2-6 properties (same agency) on views, leads, CTR, publishing."""
    db = Database.get()
    aid = _agency_id(user)
    since = (datetime.now(timezone.utc) - timedelta(days=body.days_lookback)).isoformat()

    props = await db.properties.find(
        {"id": {"$in": body.property_ids}, "agency_id": aid}
    ).to_list(len(body.property_ids))
    if len(props) < 2:
        raise HTTPException(status_code=422, detail="need_at_least_2_owned_properties")
    if len(props) != len(body.property_ids):
        # Some ids don't belong to caller's agency — silently drop for tenant safety
        pass

    metrics = []
    for p in props:
        metrics.append(await _property_metrics(db, p, since))

    # Compute deltas vs group average (positive = above average, negative = below)
    avg_views = sum(m["views_total"] for m in metrics) / len(metrics)
    avg_leads = sum(m["leads_total"] for m in metrics) / len(metrics)
    for m in metrics:
        m["delta_views_vs_avg"] = round(m["views_total"] - avg_views, 1)
        m["delta_leads_vs_avg"] = round(m["leads_total"] - avg_leads, 1)

    # Winner: highest conversion_rate (fallback to leads if no views)
    winner = max(metrics, key=lambda m: (m["conversion_rate"] or 0, m["leads_total"]))
    return {
        "days_lookback": body.days_lookback,
        "compared": len(metrics),
        "avg_views": round(avg_views, 1),
        "avg_leads": round(avg_leads, 1),
        "winner_id": winner["id"],
        "items": metrics,
    }


@router.get("/agency/overview")
async def analytics_agency_overview(
    days_lookback: int = 30,
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    """Aggregate view + lead + publishing metrics across the whole agency."""
    db = Database.get()
    aid = _agency_id(user)
    days_lookback = max(1, min(days_lookback, 365))
    since = (datetime.now(timezone.utc) - timedelta(days=days_lookback)).isoformat()

    total_properties = await db.properties.count_documents({"agency_id": aid})
    active_properties = await db.properties.count_documents({"agency_id": aid, "status": "active"})

    # Top 5 by views
    top_views_cursor = db.properties.find(
        {"agency_id": aid, "view_count": {"$gt": 0}},
        {"_id": 0, "id": 1, "title": 1, "view_count": 1, "price": 1, "city": 1},
    ).sort("view_count", -1).limit(5)
    top_views = await top_views_cursor.to_list(5)

    # Leads recent
    leads_recent = await db.leads.count_documents({
        "agency_id": aid,
        "created_at": {"$gte": since},
    })
    leads_total = await db.leads.count_documents({"agency_id": aid})

    # Publishing snapshot
    sync_ok_recent = await db.publishing_sync_logs.count_documents({
        "agency_id": aid, "status": "success", "created_at": {"$gte": since},
    })
    sync_failed_recent = await db.publishing_sync_logs.count_documents({
        "agency_id": aid, "status": "failed", "created_at": {"$gte": since},
    })

    return {
        "days_lookback": days_lookback,
        "properties": {"total": total_properties, "active": active_properties},
        "leads": {"total": leads_total, "recent_period": leads_recent},
        "publishing_recent": {"sync_success": sync_ok_recent, "sync_failed": sync_failed_recent},
        "top_views": top_views,
    }
