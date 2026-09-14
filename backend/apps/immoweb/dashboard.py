"""OMNIA — ImmoWeb Dashboard KPIs (real counts from MongoDB)."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from typing import List

from shared.db.connection import Database
from shared.auth.dependencies import get_current_user
from shared.models.agency import DashboardKPI

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=List[DashboardKPI])
async def get_kpis(user: dict = Depends(get_current_user)):
    """Return KPI cards for the dashboard home.

    All metrics are computed live from MongoDB, scoped to the current agency.
    """
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    agency_id = agency_ids[0] if agency_ids else None

    members_count = 0
    invites_count = 0
    properties_active = 0
    leads_open = 0
    matches_week = 0
    visits_week = 0

    if agency_id:
        members_count = await db.users.count_documents(
            {"agency_ids": agency_id, "is_active": True}
        )
        invites_count = await db.agency_invites.count_documents(
            {"agency_id": agency_id, "status": "pending"}
        )
        properties_active = await db.properties.count_documents(
            {"agency_id": agency_id, "status": "active"}
        )
        # M3.S4 leads (from B2C contact, valuator, mortgage, API v1)
        leads_open = await db.leads.count_documents(
            {"agency_id": agency_id, "status": {"$in": ["new", "contacted"]}}
        )
        # M2.S3 matches: computed on-read, so we look at the audit log of last 7 days.
        # Fallback: count clients marked "active" that have at least one property match cached.
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        matches_week = await db.match_audit.count_documents(
            {"agency_id": agency_id, "created_at": {"$gte": since}}
        )
        # M3.S3 visits (calendar events of type=visit within 7 days ahead)
        soon = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        now_iso = datetime.now(timezone.utc).isoformat()
        visits_week = await db.calendar_events.count_documents(
            {"agency_id": agency_id, "event_type": "visit",
             "start_at": {"$gte": now_iso, "$lte": soon}}
        )

    kpis: List[DashboardKPI] = [
        DashboardKPI(
            key="properties_active",
            label="Immobili attivi",
            value=properties_active,
            icon="home",
            locked=False,
        ),
        DashboardKPI(
            key="leads_open",
            label="Lead aperti",
            value=leads_open,
            icon="user-plus",
            locked=False,
        ),
        DashboardKPI(
            key="matches_week",
            label="Nuovi match (7gg)",
            value=matches_week,
            icon="sparkles",
            locked=False,
        ),
        DashboardKPI(
            key="visits_week",
            label="Visite (7gg)",
            value=visits_week,
            icon="calendar",
            locked=False,
        ),
        DashboardKPI(
            key="members_active",
            label="Collaboratori",
            value=members_count,
            icon="users",
            locked=False,
        ),
        DashboardKPI(
            key="invites_pending",
            label="Inviti pendenti",
            value=invites_count,
            icon="mail",
            locked=False,
        ),
    ]
    return kpis
