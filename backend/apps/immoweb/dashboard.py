"""OMNIA — ImmoWeb Dashboard KPIs + cockpit «Oggi» (A-028a)."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from typing import Any, Dict, List, Optional

from shared.db.connection import Database
from shared.auth.dependencies import get_current_user
from shared.models.agency import DashboardKPI

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_PROP_SAMPLE = {
    "_id": 0,
    "id": 1,
    "title": 1,
    "reference_code": 1,
    "status": 1,
    "city": 1,
    "updated_at": 1,
}
_CLIENT_SAMPLE = {
    "_id": 0,
    "id": 1,
    "name": 1,
    "surname": 1,
    "phone": 1,
    "client_type": 1,
    "status": 1,
    "updated_at": 1,
}
_NO_PHOTOS = {
    "$or": [
        {"photos": {"$exists": False}},
        {"photos": None},
        {"photos": {"$size": 0}},
    ]
}
_WEAK_DESC = {
    "$or": [
        {"description": {"$exists": False}},
        {"description": None},
        {"description": ""},
        {"description": {"$regex": r"^.{0,40}$"}},
    ]
}


def _agency_id(user: dict) -> Optional[str]:
    agency_ids = user.get("agency_ids") or []
    return agency_ids[0] if agency_ids else None


def _prop_label(doc: dict) -> str:
    return (doc.get("title") or doc.get("reference_code") or doc.get("id") or "Immobile")[:80]


def _client_label(doc: dict) -> str:
    name = " ".join(x for x in [doc.get("name"), doc.get("surname")] if x).strip()
    return name or doc.get("id") or "Cliente"


@router.get("/kpis", response_model=List[DashboardKPI])
async def get_kpis(user: dict = Depends(get_current_user)):
    """Return KPI cards for the dashboard home.

    All metrics are computed live from MongoDB, scoped to the current agency.
    """
    db = Database.get()
    agency_id = _agency_id(user)

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
        # Coda lavoro: richieste aperte (preferite); fallback lead grezzi
        requests_open = await db.client_requests.count_documents(
            {
                "agency_id": agency_id,
                "status": {"$in": ["open", "matched", "negotiating"]},
            }
        )
        leads_raw = await db.leads.count_documents(
            {"agency_id": agency_id, "status": {"$in": ["new", "contacted"]}}
        )
        leads_open = requests_open if requests_open else leads_raw
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
            label="Richieste aperte",
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


@router.get("/today")
async def get_today(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Cockpit «Oggi» — actionable work queues (A-028a).

    Cheap Mongo counts + small samples only. Never runs agency-wide match fan-out.
    """
    db = Database.get()
    agency_id = _agency_id(user)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    day_end = (now + timedelta(days=1)).isoformat()
    week_end = (now + timedelta(days=7)).isoformat()
    since_week = (now - timedelta(days=7)).isoformat()

    actions: List[Dict[str, Any]] = []
    recent: List[Dict[str, Any]] = []

    if not agency_id:
        return {
            "generated_at": now_iso,
            "agency_id": None,
            "actions": [],
            "recent": [],
            "summary": {"action_groups": 0, "total_items": 0},
        }

    base_prop = {"agency_id": agency_id}

    # —— Immobili senza foto (active + draft) ——
    q_no_photos = {**base_prop, "status": {"$in": ["active", "draft"]}, **_NO_PHOTOS}
    n_no_photos = await db.properties.count_documents(q_no_photos)
    if n_no_photos:
        samples = await db.properties.find(q_no_photos, _PROP_SAMPLE).sort("updated_at", -1).limit(5).to_list(5)
        actions.append(
            {
                "id": "props_no_photos",
                "kind": "property",
                "priority": 1,
                "title_key": "dashboard.today_no_photos",
                "title": "Immobili senza foto",
                "count": n_no_photos,
                "href": "/app/properties",
                "cta_key": "dashboard.today_cta_properties",
                "cta": "Apri immobili",
                "items": [
                    {
                        "id": d["id"],
                        "label": _prop_label(d),
                        "meta": d.get("city") or d.get("status") or "",
                        "href": f"/app/properties/{d['id']}",
                        "reason_key": "dashboard.today_reason_no_photos",
                        "reason": "Mancano le foto",
                    }
                    for d in samples
                    if d.get("id")
                ],
            }
        )

    # —— Bozze da completare ——
    q_draft = {**base_prop, "status": "draft"}
    n_draft = await db.properties.count_documents(q_draft)
    if n_draft:
        samples = await db.properties.find(q_draft, _PROP_SAMPLE).sort("updated_at", -1).limit(5).to_list(5)
        actions.append(
            {
                "id": "props_draft",
                "kind": "property",
                "priority": 2,
                "title_key": "dashboard.today_drafts",
                "title": "Bozze da completare",
                "count": n_draft,
                "href": "/app/properties?status=draft",
                "cta_key": "dashboard.today_cta_drafts",
                "cta": "Apri bozze",
                "items": [
                    {
                        "id": d["id"],
                        "label": _prop_label(d),
                        "meta": d.get("city") or "draft",
                        "href": f"/app/properties/{d['id']}",
                        "reason_key": "dashboard.today_reason_draft",
                        "reason": "Ancora in bozza",
                    }
                    for d in samples
                    if d.get("id")
                ],
            }
        )

    # —— Annunci attivi con testo debole (ma con foto: coda distinta da no_photos) ——
    q_weak = {
        **base_prop,
        "status": "active",
        "photos.0": {"$exists": True},
        **_WEAK_DESC,
    }
    n_weak = await db.properties.count_documents(q_weak)
    if n_weak:
        samples = await db.properties.find(q_weak, _PROP_SAMPLE).sort("updated_at", -1).limit(5).to_list(5)
        actions.append(
            {
                "id": "props_weak_copy",
                "kind": "property",
                "priority": 3,
                "title_key": "dashboard.today_weak_copy",
                "title": "Annunci da migliorare",
                "count": n_weak,
                "href": "/app/properties?status=active",
                "cta_key": "dashboard.today_cta_improve",
                "cta": "Apri e migliora",
                "items": [
                    {
                        "id": d["id"],
                        "label": _prop_label(d),
                        "meta": d.get("city") or "",
                        "href": f"/app/properties/{d['id']}",
                        "reason_key": "dashboard.today_reason_weak_copy",
                        "reason": "Descrizione assente o troppo corta",
                    }
                    for d in samples
                    if d.get("id")
                ],
            }
        )

    # —— Clienti da riprendere (searchers recent / new) — no match fan-out ——
    q_clients = {
        "agency_id": agency_id,
        "client_type": {"$in": ["buyer", "tenant", "investor"]},
        "status": {"$in": ["new", "active", "hot", "contacted"]},
    }
    n_clients = await db.clients.count_documents(q_clients)
    if n_clients:
        samples = await db.clients.find(q_clients, _CLIENT_SAMPLE).sort("updated_at", -1).limit(5).to_list(5)
        actions.append(
            {
                "id": "clients_follow",
                "kind": "client",
                "priority": 4,
                "title_key": "dashboard.today_clients",
                "title": "Clienti da riprendere",
                "count": n_clients,
                "href": "/app/clients?bucket=to_call_today",
                "cta_key": "dashboard.today_cta_clients",
                "cta": "Apri clienti smart",
                "items": [
                    {
                        "id": d["id"],
                        "label": _client_label(d),
                        "meta": d.get("phone") or d.get("client_type") or "",
                        "href": f"/app/clients/{d['id']}",
                        "reason_key": "dashboard.today_reason_client",
                        "reason": "Acquirente / cercatore da seguire",
                    }
                    for d in samples
                    if d.get("id")
                ],
            }
        )

    # —— Richieste aperte (coda lavoro; lead grezzi confluiscono qui) ——
    q_requests = {
        "agency_id": agency_id,
        "status": {"$in": ["open", "matched", "negotiating"]},
    }
    n_requests = await db.client_requests.count_documents(q_requests)
    if n_requests:
        req_proj = {
            "_id": 0, "id": 1, "title": 1, "request_type": 1,
            "status": 1, "source": 1, "client_id": 1,
        }
        samples = await db.client_requests.find(q_requests, req_proj).sort(
            "updated_at", -1
        ).limit(5).to_list(5)
        actions.append(
            {
                "id": "requests_open",
                "kind": "request",
                "priority": 5,
                "title_key": "dashboard.today_requests",
                "title": "Richieste aperte",
                "count": n_requests,
                "href": "/app/requests",
                "cta_key": "dashboard.today_cta_requests",
                "cta": "Apri richieste",
                "items": [
                    {
                        "id": d.get("id"),
                        "label": d.get("title") or d.get("id") or "Richiesta",
                        "meta": d.get("request_type") or d.get("status") or "",
                        "href": f"/app/requests/{d['id']}" if d.get("id") else "/app/requests",
                        "reason_key": "dashboard.today_reason_request",
                        "reason": "Richiesta da lavorare / matchare",
                    }
                    for d in samples
                ],
            }
        )
    else:
        # Fallback: lead grezzi non ancora migrati a richieste
        q_leads = {"agency_id": agency_id, "status": {"$in": ["new", "contacted"]}}
        n_leads = await db.leads.count_documents(q_leads)
        if n_leads:
            lead_proj = {"_id": 0, "id": 1, "name": 1, "email": 1, "source": 1, "status": 1}
            samples = await db.leads.find(q_leads, lead_proj).sort("created_at", -1).limit(5).to_list(5)
            actions.append(
                {
                    "id": "leads_open",
                    "kind": "lead",
                    "priority": 5,
                    "title_key": "dashboard.today_leads",
                    "title": "Lead aperti",
                    "count": n_leads,
                    "href": "/app/requests",
                    "cta_key": "dashboard.today_cta_leads",
                    "cta": "Vedi richieste",
                    "items": [
                        {
                            "id": d.get("id"),
                            "label": d.get("name") or d.get("email") or d.get("id") or "Lead",
                            "meta": d.get("source") or d.get("status") or "",
                            "href": "/app/requests",
                            "reason_key": "dashboard.today_reason_lead",
                            "reason": "Lead da contattare / trasformare in richiesta",
                        }
                        for d in samples
                    ],
                }
            )

    # —— Visite oggi / prossimi 7gg ——
    q_visits_today = {
        "agency_id": agency_id,
        "event_type": "visit",
        "start_at": {"$gte": now_iso, "$lte": day_end},
    }
    n_visits_today = await db.calendar_events.count_documents(q_visits_today)
    q_visits_week = {
        "agency_id": agency_id,
        "event_type": "visit",
        "start_at": {"$gte": now_iso, "$lte": week_end},
    }
    n_visits_week = await db.calendar_events.count_documents(q_visits_week)
    if n_visits_today or n_visits_week:
        cal_proj = {
            "_id": 0, "id": 1, "title": 1, "start_at": 1,
            "client_id": 1, "property_id": 1, "request_id": 1,
        }
        samples = await db.calendar_events.find(
            q_visits_week if not n_visits_today else q_visits_today, cal_proj
        ).sort("start_at", 1).limit(5).to_list(5)
        actions.append(
            {
                "id": "visits",
                "kind": "visit",
                "priority": 0 if n_visits_today else 6,
                "title_key": "dashboard.today_visits" if n_visits_today else "dashboard.today_visits_week",
                "title": "Visite di oggi" if n_visits_today else "Visite (7 giorni)",
                "count": n_visits_today or n_visits_week,
                "href": "/app/properties",
                "cta_key": "dashboard.today_cta_visits",
                "cta": "Apri immobili",
                "items": [
                    {
                        "id": d.get("id"),
                        "label": d.get("title") or "Visita",
                        "meta": (d.get("start_at") or "")[:16].replace("T", " "),
                        "href": (
                            f"/app/properties/{d['property_id']}"
                            if d.get("property_id")
                            else (
                                f"/app/clients/{d['client_id']}"
                                if d.get("client_id")
                                else (
                                    f"/app/requests/{d['request_id']}"
                                    if d.get("request_id")
                                    else "/app/properties"
                                )
                            )
                        ),
                        "reason_key": "dashboard.today_reason_visit",
                        "reason": "Visita in calendario",
                    }
                    for d in samples
                ],
            }
        )

    # —— Portali non collegati ——
    n_pub = await db.publishing_connections.count_documents({"agency_id": agency_id})
    if n_pub == 0:
        actions.append(
            {
                "id": "publishing_setup",
                "kind": "publishing",
                "priority": 7,
                "title_key": "dashboard.today_publishing",
                "title": "Collega un portale",
                "count": 1,
                "href": "/app/publishing",
                "cta_key": "dashboard.today_cta_publishing",
                "cta": "Apri portali",
                "items": [
                    {
                        "id": "publishing",
                        "label": "Nessuna connessione portale attiva",
                        "meta": "publishing",
                        "href": "/app/publishing",
                        "reason_key": "dashboard.today_reason_publishing",
                        "reason": "Setup pubblicazione",
                    }
                ],
            }
        )

    # —— Inviti pendenti ——
    n_invites = await db.agency_invites.count_documents(
        {"agency_id": agency_id, "status": "pending"}
    )
    if n_invites:
        actions.append(
            {
                "id": "invites_pending",
                "kind": "team",
                "priority": 8,
                "title_key": "dashboard.today_invites",
                "title": "Inviti collaboratori in sospeso",
                "count": n_invites,
                "href": "/app/members",
                "cta_key": "dashboard.today_cta_members",
                "cta": "Apri team",
                "items": [],
            }
        )

    actions.sort(key=lambda a: (a.get("priority", 99), -(a.get("count") or 0)))

    # —— Attività recenti (lite A-018) ——
    for coll, kind, label_fn in (
        (
            db.match_audit,
            "match",
            lambda d: f"Match · {(d.get('client_id') or '')[:8]}",
        ),
        (
            db.publishing_events,
            "publishing",
            lambda d: f"Portale · {d.get('portal_id') or d.get('status') or 'sync'}",
        ),
        (
            db.al_audit,
            "hal",
            lambda d: f"HAL · {(d.get('action') or d.get('kind') or 'chat')}",
        ),
    ):
        try:
            docs = await coll.find(
                {"agency_id": agency_id, "created_at": {"$gte": since_week}},
                {"_id": 0, "id": 1, "created_at": 1, "client_id": 1, "portal_id": 1, "status": 1, "action": 1, "kind": 1},
            ).sort("created_at", -1).limit(4).to_list(4)
        except Exception:
            docs = []
        for d in docs:
            recent.append(
                {
                    "kind": kind,
                    "label": label_fn(d),
                    "at": d.get("created_at"),
                }
            )
    recent.sort(key=lambda r: r.get("at") or "", reverse=True)
    recent = recent[:8]

    total_items = sum(int(a.get("count") or 0) for a in actions)
    return {
        "generated_at": now_iso,
        "agency_id": agency_id,
        "actions": actions,
        "recent": recent,
        "summary": {
            "action_groups": len(actions),
            "total_items": total_items,
        },
    }
