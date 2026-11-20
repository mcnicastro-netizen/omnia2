"""Deal — commercial opportunity lifecycle (distinct from MLS offer / matching)."""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles
from shared.db.connection import Database
from shared.mls_collab.service import (
    DEAL_STATUSES,
    assert_deal_transition,
    get_collaboration,
    get_deal,
    get_visit,
    new_id,
    require_agency_in_collaboration,
    strip_id,
    utc_now,
)

router = APIRouter(prefix="/deals", tags=["deals"])


async def _agency_id(user: dict) -> str:
    from shared.auth.tenant import arequire_agency

    return await arequire_agency(user)


class DealCreate(BaseModel):
    property_id: str
    client_id: str
    visit_id: Optional[str] = None
    collaboration_id: Optional[str] = None
    partner_agency_id: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=4000)


class DealUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=4000)
    proposal_amount: Optional[float] = Field(default=None, ge=0)
    proposal_notes: Optional[str] = Field(default=None, max_length=4000)


class DealProposal(BaseModel):
    amount: float = Field(..., ge=0)
    notes: Optional[str] = Field(default=None, max_length=4000)


@router.get("")
async def list_deals(
    status: Optional[str] = None,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    q: dict[str, Any] = {
        "$or": [{"agency_id": aid}, {"partner_agency_id": aid}],
    }
    if status:
        q["status"] = status
    items = [
        strip_id(r)
        async for r in db.deals.find(q, {"_id": 0}).sort("updated_at", -1).limit(100)
    ]
    return {"items": items}


@router.post("", status_code=201)
async def open_deal(
    body: DealCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    raw = Database.get_raw()
    aid = await _agency_id(user)
    prop = await db.properties.find_one(
        {"id": body.property_id, "agency_id": aid},
        {"_id": 0, "id": 1, "title": 1},
    )
    # Partner may open deal on collaboration property they don't own
    if not prop and body.collaboration_id:
        collab = await get_collaboration(db, body.collaboration_id)
        require_agency_in_collaboration(collab, aid)
        if collab["property_id"] != body.property_id:
            raise HTTPException(status_code=400, detail="property_collaboration_mismatch")
        prop = await raw.properties.find_one(
            {"id": body.property_id}, {"_id": 0, "id": 1, "title": 1}
        )
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")
    client = await db.clients.find_one(
        {"id": body.client_id, "agency_id": aid},
        {"_id": 0, "id": 1, "name": 1, "surname": 1},
    )
    if not client:
        raise HTTPException(status_code=404, detail="client_not_found")
    if body.visit_id:
        visit = await get_visit(db, body.visit_id)
        if visit.get("status") != "completed":
            raise HTTPException(status_code=400, detail="visit_not_completed")
        if aid not in (visit["owner_agency_id"], visit["partner_agency_id"]):
            raise HTTPException(status_code=403, detail="visit_forbidden")
    partner = body.partner_agency_id
    if body.collaboration_id:
        collab = await get_collaboration(db, body.collaboration_id)
        require_agency_in_collaboration(collab, aid)
        partner = collab["partner_agency_id"] if aid == collab["owner_agency_id"] else collab["owner_agency_id"]
    now = utc_now()
    doc = {
        "id": new_id(),
        "property_id": body.property_id,
        "property_title": prop.get("title"),
        "client_id": body.client_id,
        "client_label": f"{client.get('name', '')} {client.get('surname', '')}".strip(),
        "agency_id": aid,
        "partner_agency_id": partner,
        "collaboration_id": body.collaboration_id,
        "visit_id": body.visit_id,
        "status": "open",
        "notes": body.notes,
        "interest_expressed_at": now,
        "created_by_user_id": user.get("id") or user.get("sub"),
        "created_at": now,
        "updated_at": now,
        "history": [{"at": now, "to": "open", "by": user.get("id") or user.get("sub")}],
        "proposals": [],
    }
    await db.deals.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/{deal_id}")
async def get_deal_detail(
    deal_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    deal = await get_deal(db, deal_id)
    if aid not in (deal.get("agency_id"), deal.get("partner_agency_id")):
        raise HTTPException(status_code=403, detail="deal_forbidden")
    return deal


@router.patch("/{deal_id}")
async def update_deal(
    deal_id: str,
    body: DealUpdate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    deal = await get_deal(db, deal_id)
    if aid != deal.get("agency_id"):
        raise HTTPException(status_code=403, detail="deal_owner_only")
    patch: dict[str, Any] = {"updated_at": utc_now()}
    if body.notes is not None:
        patch["notes"] = body.notes
    if body.proposal_amount is not None:
        patch["proposal_amount"] = body.proposal_amount
    if body.proposal_notes is not None:
        patch["proposal_notes"] = body.proposal_notes
    if body.status:
        if body.status not in DEAL_STATUSES:
            raise HTTPException(status_code=400, detail="invalid_deal_status")
        assert_deal_transition(deal["status"], body.status)
        patch["status"] = body.status
        hist = {
            "at": utc_now(),
            "from": deal["status"],
            "to": body.status,
            "by": user.get("id") or user.get("sub"),
        }
        await db.deals.update_one(
            {"id": deal_id},
            {"$set": patch, "$push": {"history": hist}},
        )
    else:
        await db.deals.update_one({"id": deal_id}, {"$set": patch})
    return await get_deal(db, deal_id)


@router.post("/{deal_id}/proposals", status_code=201)
async def add_proposal(
    deal_id: str,
    body: DealProposal,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    deal = await get_deal(db, deal_id)
    if aid != deal.get("agency_id"):
        raise HTTPException(status_code=403, detail="deal_owner_only")
    now = utc_now()
    proposal = {
        "id": new_id(),
        "amount": body.amount,
        "notes": body.notes,
        "created_at": now,
        "created_by_user_id": user.get("id") or user.get("sub"),
    }
    patch: dict[str, Any] = {
        "proposal_amount": body.amount,
        "proposal_notes": body.notes,
        "updated_at": now,
    }
    push: dict[str, Any] = {"proposals": proposal}
    if deal["status"] == "open":
        assert_deal_transition("open", "proposal_prepared")
        patch["status"] = "proposal_prepared"
        push["history"] = {
            "at": now,
            "from": "open",
            "to": "proposal_prepared",
            "by": user.get("id") or user.get("sub"),
        }
    await db.deals.update_one({"id": deal_id}, {"$set": patch, "$push": push})
    return await get_deal(db, deal_id)


@router.post("/{deal_id}/send-proposal")
async def send_proposal(
    deal_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    deal = await get_deal(db, deal_id)
    if aid != deal.get("agency_id"):
        raise HTTPException(status_code=403, detail="deal_owner_only")
    assert_deal_transition(deal["status"], "proposal_sent")
    now = utc_now()
    await db.deals.update_one(
        {"id": deal_id},
        {
            "$set": {"status": "proposal_sent", "updated_at": now, "proposal_sent_at": now},
            "$push": {
                "history": {
                    "at": now,
                    "from": deal["status"],
                    "to": "proposal_sent",
                    "by": user.get("id") or user.get("sub"),
                }
            },
        },
    )
    return await get_deal(db, deal_id)
