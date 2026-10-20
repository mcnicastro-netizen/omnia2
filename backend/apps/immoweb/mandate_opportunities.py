"""Opportunità di mandato in esclusiva (D-129).

Il matching buyer↔stock resta in `matches` / `client_requests`.
Questo modulo trasforma un annuncio privato sul portale (con domanda
agenzia compatibile) in una **coda acquisizione incarico** con funnel
misurabile: new → contacted → appointment → mandate_won | lost | dismissed.

Privacy: solo dati già pubblici sull'annuncio (`contact_public` + scheda
cloud). Nessuna email proprietario nascosta, nessun lead valuator redistribuito.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.auth.tenant import arequire_agency as _agency
from shared.db.connection import Database

logger = logging.getLogger("omnia.mandate_opportunities")

COLLECTION = "mandate_opportunities"
STATUSES = ("new", "contacted", "appointment", "mandate_won", "lost", "dismissed")
OPEN_STATUSES = ("new", "contacted", "appointment")

router = APIRouter(prefix="/mandate-opportunities", tags=["mandate-opportunities"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_contact(prop: Dict[str, Any]) -> Dict[str, Any]:
    cp = prop.get("contact_public") or {}
    out: Dict[str, Any] = {
        "display_name": cp.get("display_name") or None,
        "show_phone": bool(cp.get("show_phone")),
        "show_whatsapp": bool(cp.get("show_whatsapp")),
        "show_email": bool(cp.get("show_email")),
    }
    if out["show_phone"] and cp.get("phone"):
        out["phone"] = cp["phone"]
    if out["show_whatsapp"] and cp.get("whatsapp"):
        out["whatsapp"] = cp["whatsapp"]
    # email solo se il proprietario l'ha resa pubblica sul listing
    if out["show_email"] and prop.get("email"):
        out["email"] = prop.get("email")
    return out


def _listing_snapshot(prop: Dict[str, Any]) -> Dict[str, Any]:
    photos = prop.get("photos") or []
    cover = next((x for x in photos if x.get("is_cover")), photos[0] if photos else None)
    return {
        "property_id": prop.get("id"),
        "title": prop.get("title"),
        "city": prop.get("city"),
        "zone": prop.get("zone"),
        "property_type": prop.get("property_type"),
        "operation": prop.get("operation"),
        "price": prop.get("price") or prop.get("rent_monthly"),
        "surface_sqm": prop.get("surface_sqm"),
        "rooms": prop.get("rooms"),
        "cover_photo_url": (cover or {}).get("url"),
        "cloud_path": f"/cloud/property/{prop.get('id')}" if prop.get("id") else None,
        "contact_public": _public_contact(prop),
    }


async def ensure_indexes(db) -> None:
    await db[COLLECTION].create_index(
        [("agency_id", 1), ("property_id", 1)],
        unique=True,
        name="agency_property_unique",
    )
    await db[COLLECTION].create_index([("agency_id", 1), ("status", 1), ("demand_score", -1)])
    await db[COLLECTION].create_index([("agency_id", 1), ("updated_at", -1)])


async def upsert_from_portal_match(
    db,
    *,
    agency_id: str,
    prop: Dict[str, Any],
    hits_for_agency: List[Dict[str, Any]],
) -> Optional[str]:
    """Crea/aggiorna opportunità mandato quando c'è domanda compatibile.

    `hits_for_agency` = risultati di match privato filtrati per questa agenzia.
    """
    if not agency_id or not prop.get("id") or not hits_for_agency:
        return None

    await ensure_indexes(db)
    best = max(hits_for_agency, key=lambda h: int(h.get("score") or 0))
    demand_score = int(best.get("score") or 0)
    request_ids = [h["request_id"] for h in hits_for_agency if h.get("request_id")]
    now = _now()
    snap = _listing_snapshot(prop)

    existing = await db[COLLECTION].find_one(
        {"agency_id": agency_id, "property_id": prop["id"]},
        {"_id": 0, "id": 1, "status": 1},
    )

    if existing:
        update: Dict[str, Any] = {
            "demand_score": demand_score,
            "matching_request_ids": request_ids,
            "best_request_id": best.get("request_id"),
            "listing": snap,
            "updated_at": now,
            "last_matched_at": now,
        }
        # Non riaprire opportunità chiuse automaticamente
        if existing.get("status") in OPEN_STATUSES or existing.get("status") == "new":
            pass
        await db[COLLECTION].update_one(
            {"id": existing["id"]},
            {"$set": update},
        )
        return existing["id"]

    oid = str(uuid4())
    doc = {
        "id": oid,
        "agency_id": agency_id,
        "property_id": prop["id"],
        "source": "private_listing",
        "purpose": "exclusive_mandate",
        "status": "new",
        "demand_score": demand_score,
        "matching_request_ids": request_ids,
        "best_request_id": best.get("request_id"),
        "listing": snap,
        "notes": "",
        "assigned_agent_id": best.get("assigned_agent_id"),
        "created_at": now,
        "updated_at": now,
        "last_matched_at": now,
        "status_history": [{"status": "new", "at": now, "by": "system"}],
        # Prove anti-causalità spuria: flag se l'agenzia aveva già un mandato sull'immobile
        "baseline_had_mandate": False,
    }
    await db[COLLECTION].insert_one(doc)
    return oid


async def sync_opportunities_from_hits(
    db,
    prop: Dict[str, Any],
    hits: List[Dict[str, Any]],
) -> int:
    """Raggruppa hit per agency_id e upserta opportunità."""
    by_agency: Dict[str, List[Dict[str, Any]]] = {}
    for h in hits:
        aid = h.get("agency_id")
        if not aid:
            continue
        by_agency.setdefault(aid, []).append(h)
    created_or_updated = 0
    for aid, agency_hits in by_agency.items():
        oid = await upsert_from_portal_match(
            db, agency_id=aid, prop=prop, hits_for_agency=agency_hits,
        )
        if oid:
            created_or_updated += 1
    return created_or_updated


class StatusPatch(BaseModel):
    status: str = Field(..., description="new|contacted|appointment|mandate_won|lost|dismissed")
    notes: Optional[str] = None
    assigned_agent_id: Optional[str] = None


@router.get("/proof")
async def proof_metrics(user: dict = Depends(get_current_user)):
    """Metriche di prova per i tre pilastri (agenzia corrente).

    Mandati: funnel opportunità. Portale: contatti/richieste da ImmobilCloud.
    Academy: placeholder onesto finché M6 non è codice.
    """
    agency_id = await _agency(user)
    db = Database.get()
    await ensure_indexes(db)

    since_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    since_30d = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    funnel: Dict[str, int] = {}
    for st in STATUSES:
        funnel[st] = await db[COLLECTION].count_documents(
            {"agency_id": agency_id, "status": st}
        )
    total = sum(funnel.values())
    won = funnel.get("mandate_won", 0)
    contacted = (
        funnel.get("contacted", 0)
        + funnel.get("appointment", 0)
        + won
        + funnel.get("lost", 0)
    )
    appointments = funnel.get("appointment", 0) + won + funnel.get("lost", 0)

    mandates_proof = {
        "total_opportunities": total,
        "funnel": funnel,
        "rates": {
            "contacted_of_total": round(contacted / total, 3) if total else None,
            "appointment_of_contacted": round(appointments / contacted, 3) if contacted else None,
            "mandate_of_appointment": round(won / appointments, 3) if appointments else None,
            "mandate_of_total": round(won / total, 3) if total else None,
        },
        "note": (
            "mandate_won conta solo avanzamenti espliciti in questa coda. "
            "Confrontare con mandati acquisiti fuori sistema (baseline)."
        ),
    }

    leads_7d = await db.leads.count_documents(
        {
            "agency_id": agency_id,
            "source": "ImmobilCloud",
            "created_at": {"$gte": since_7d},
        }
    )
    leads_30d = await db.leads.count_documents(
        {
            "agency_id": agency_id,
            "source": "ImmobilCloud",
            "created_at": {"$gte": since_30d},
        }
    )
    requests_7d = await db.client_requests.count_documents(
        {
            "agency_id": agency_id,
            "source": "ImmobilCloud",
            "created_at": {"$gte": since_7d},
        }
    )
    portal_proof = {
        "leads_immobilcloud_7d": leads_7d,
        "leads_immobilcloud_30d": leads_30d,
        "requests_immobilcloud_7d": requests_7d,
        "mandate_opportunities_from_portal": await db[COLLECTION].count_documents(
            {"agency_id": agency_id, "source": "private_listing"}
        ),
        "note": (
            "Contatto qualificato = lead/richiesta con source ImmobilCloud. "
            "Costo per contatto richiede piano + spesa portali esterni (non in v1)."
        ),
    }

    academy_proof = {
        "status": "not_implemented",
        "completion_rate": None,
        "placement_rate": None,
        "retention_rate": None,
        "note": "M6 congelata: nessun LMS. Non claimare formazione→produttività finché non c'è codice.",
    }

    return {
        "agency_id": agency_id,
        "generated_at": _now(),
        "pillars": {
            "portal": portal_proof,
            "academy": academy_proof,
            "mandates": mandates_proof,
        },
        "decision": "D-129",
    }


@router.get("")
async def list_opportunities(
    status: Optional[str] = Query(None),
    min_score: int = Query(50, ge=0, le=100),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """Coda opportunità mandato per l'agenzia corrente."""
    agency_id = await _agency(user)
    db = Database.get()
    await ensure_indexes(db)

    q: Dict[str, Any] = {
        "agency_id": agency_id,
        "demand_score": {"$gte": min_score},
    }
    if status:
        if status not in STATUSES:
            raise HTTPException(status_code=400, detail="invalid_status")
        q["status"] = status
    else:
        q["status"] = {"$in": list(OPEN_STATUSES)}

    items = await db[COLLECTION].find(q, {"_id": 0}).sort(
        [("demand_score", -1), ("updated_at", -1)]
    ).to_list(length=limit)

    return {
        "items": items,
        "total": len(items),
        "min_score": min_score,
        "status_filter": status or "open",
        "purpose": "exclusive_mandate",
    }


@router.patch("/{opportunity_id}")
async def patch_opportunity(
    opportunity_id: str,
    body: StatusPatch,
    user: dict = Depends(get_current_user),
):
    """Avanza il funnel acquisizione (contatto → appuntamento → mandato)."""
    if body.status not in STATUSES:
        raise HTTPException(status_code=400, detail="invalid_status")
    agency_id = await _agency(user)
    db = Database.get()
    doc = await db[COLLECTION].find_one(
        {"id": opportunity_id, "agency_id": agency_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="opportunity_not_found")

    now = _now()
    update: Dict[str, Any] = {
        "status": body.status,
        "updated_at": now,
        f"timestamps.{body.status}": now,
    }
    if body.notes is not None:
        update["notes"] = body.notes[:2000]
    if body.assigned_agent_id is not None:
        update["assigned_agent_id"] = body.assigned_agent_id

    await db[COLLECTION].update_one(
        {"id": opportunity_id, "agency_id": agency_id},
        {
            "$set": update,
            "$push": {
                "status_history": {
                    "status": body.status,
                    "at": now,
                    "by": user.get("id"),
                }
            },
        },
    )
    updated = await db[COLLECTION].find_one(
        {"id": opportunity_id}, {"_id": 0},
    )
    return {"ok": True, "item": updated}


async def count_open_for_agency(db, agency_id: str) -> int:
    return await db[COLLECTION].count_documents(
        {"agency_id": agency_id, "status": {"$in": list(OPEN_STATUSES)}}
    )


async def sample_open_for_agency(db, agency_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    return await db[COLLECTION].find(
        {"agency_id": agency_id, "status": {"$in": list(OPEN_STATUSES)}},
        {"_id": 0, "id": 1, "demand_score": 1, "status": 1, "listing": 1},
    ).sort("demand_score", -1).to_list(length=limit)
