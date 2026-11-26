"""Deal — commercial opportunity lifecycle (distinct from MLS offer / matching)."""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles
from shared.db.connection import Database
from shared.mls_collab.service import (
    DEAL_STATUSES,
    allowed_deal_transitions,
    assert_deal_transition_for_actor,
    deal_actor_filter,
    deal_owner_filter,
    deal_partner_filter,
    deal_role,
    get_collaboration,
    get_deal,
    get_visit,
    new_id,
    require_agency_in_collaboration,
    require_collaboration_active,
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


class DealPartnerRespond(BaseModel):
    action: Literal["accepted", "rejected", "counter"]
    counter_amount: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, max_length=4000)


def _enrich_deal(deal: dict, aid: str) -> dict:
    out = dict(deal)
    out["role"] = deal_role(deal, aid)
    out["allowed_transitions"] = sorted(allowed_deal_transitions(deal, aid))
    return out


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
        _enrich_deal(strip_id(r), aid)
        async for r in db.deals.find(q, {"_id": 0}).sort("updated_at", -1).limit(100)
    ]
    return {"items": items}


@router.post("", status_code=201)
async def open_deal(
    body: DealCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Open a Deal.

    With collaboration_id: requires active collaboration (FIX-04). MLS partner
    may open on the shared property via get_raw after membership check.
    Without collaboration_id: own-property Deal only — does not bypass MLS
    collab/visit rules for cross-agency cases (explicit: no collaboration path).
    """
    db = Database.get()
    # get_raw class B: partner may read owner property ONLY after collab membership
    # checks below (MLS shareable / collaboration_id). Never expose raw without gate.
    raw = Database.get_raw()
    aid = await _agency_id(user)
    prop = await db.properties.find_one(
        {"id": body.property_id, "agency_id": aid},
        {"_id": 0, "id": 1, "title": 1},
    )
    partner = body.partner_agency_id
    if body.collaboration_id:
        collab = await get_collaboration(db, body.collaboration_id)
        require_agency_in_collaboration(collab, aid)
        require_collaboration_active(collab)
        if collab["property_id"] != body.property_id:
            raise HTTPException(status_code=400, detail="property_collaboration_mismatch")
        if not prop:
            prop = await raw.properties.find_one(
                {"id": body.property_id}, {"_id": 0, "id": 1, "title": 1}
            )
        partner = (
            collab["partner_agency_id"]
            if aid == collab["owner_agency_id"]
            else collab["owner_agency_id"]
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
        if body.collaboration_id and visit.get("collaboration_id") != body.collaboration_id:
            raise HTTPException(status_code=400, detail="visit_collaboration_mismatch")
        # CMJ-04: idempotency — same visit + agency + client → return existing open deal
        existing = await db.deals.find_one(
            {
                "visit_id": body.visit_id,
                "agency_id": aid,
                "client_id": body.client_id,
                "status": {"$nin": ["cancelled", "closed_lost", "closed_won"]},
            },
            {"_id": 0},
        )
        if existing:
            return _enrich_deal(existing, aid)
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
    return _enrich_deal(doc, aid)


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
    # Revoked collab must not keep Deal as a bypass channel for mutations —
    # read still allowed for history; mutations check below.
    return _enrich_deal(deal, aid)


async def _assert_deal_collab_still_active(db, deal: dict) -> None:
    cid = deal.get("collaboration_id")
    if not cid:
        return
    collab = await get_collaboration(db, cid)
    require_collaboration_active(collab)


@router.patch("/{deal_id}")
async def update_deal(
    deal_id: str,
    body: DealUpdate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    deal = await get_deal(db, deal_id)
    role = deal_role(deal, aid)
    if role is None:
        raise HTTPException(status_code=403, detail="deal_forbidden")
    await _assert_deal_collab_still_active(db, deal)
    patch: dict[str, Any] = {"updated_at": utc_now()}
    if body.notes is not None:
        if role != "owner":
            raise HTTPException(status_code=403, detail="deal_owner_only")
        patch["notes"] = body.notes
    if body.proposal_amount is not None or body.proposal_notes is not None:
        if role != "owner":
            raise HTTPException(status_code=403, detail="deal_owner_only")
        if body.proposal_amount is not None:
            patch["proposal_amount"] = body.proposal_amount
        if body.proposal_notes is not None:
            patch["proposal_notes"] = body.proposal_notes
    if body.status:
        if body.status not in DEAL_STATUSES:
            raise HTTPException(status_code=400, detail="invalid_deal_status")
        assert_deal_transition_for_actor(deal, aid, body.status)
        patch["status"] = body.status
        hist = {
            "at": utc_now(),
            "from": deal["status"],
            "to": body.status,
            "by": user.get("id") or user.get("sub"),
            "role": role,
        }
        r = await db.deals.update_one(
            deal_actor_filter(deal_id, aid),
            {"$set": patch, "$push": {"history": hist}},
        )
        if r.matched_count == 0:
            raise HTTPException(status_code=403, detail="deal_forbidden")
    else:
        r = await db.deals.update_one(deal_actor_filter(deal_id, aid), {"$set": patch})
        if r.matched_count == 0:
            raise HTTPException(status_code=403, detail="deal_forbidden")
    return _enrich_deal(await get_deal(db, deal_id), aid)


@router.post("/{deal_id}/proposals", status_code=201)
async def add_proposal(
    deal_id: str,
    body: DealProposal,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    deal = await get_deal(db, deal_id)
    if deal_role(deal, aid) != "owner":
        raise HTTPException(status_code=403, detail="deal_owner_only")
    await _assert_deal_collab_still_active(db, deal)
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
        assert_deal_transition_for_actor(deal, aid, "proposal_prepared")
        patch["status"] = "proposal_prepared"
        push["history"] = {
            "at": now,
            "from": "open",
            "to": "proposal_prepared",
            "by": user.get("id") or user.get("sub"),
            "role": "owner",
        }
    r = await db.deals.update_one(
        deal_owner_filter(deal_id, aid), {"$set": patch, "$push": push}
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=403, detail="deal_owner_only")
    return _enrich_deal(await get_deal(db, deal_id), aid)


@router.post("/{deal_id}/send-proposal")
async def send_proposal(
    deal_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    deal = await get_deal(db, deal_id)
    if deal_role(deal, aid) != "owner":
        raise HTTPException(status_code=403, detail="deal_owner_only")
    await _assert_deal_collab_still_active(db, deal)
    assert_deal_transition_for_actor(deal, aid, "proposal_sent")
    now = utc_now()
    r = await db.deals.update_one(
        deal_owner_filter(deal_id, aid),
        {
            "$set": {"status": "proposal_sent", "updated_at": now, "proposal_sent_at": now},
            "$push": {
                "history": {
                    "at": now,
                    "from": deal["status"],
                    "to": "proposal_sent",
                    "by": user.get("id") or user.get("sub"),
                    "role": "owner",
                }
            },
        },
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=403, detail="deal_owner_only")
    return _enrich_deal(await get_deal(db, deal_id), aid)


@router.post("/{deal_id}/partner-respond")
async def partner_respond_proposal(
    deal_id: str,
    body: DealPartnerRespond,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Explicit partner powers: accept / reject / counter when proposal_sent."""
    db = Database.get()
    aid = await _agency_id(user)
    deal = await get_deal(db, deal_id)
    if deal_role(deal, aid) != "partner":
        raise HTTPException(status_code=403, detail="deal_partner_only")
    await _assert_deal_collab_still_active(db, deal)
    new_status = body.action
    assert_deal_transition_for_actor(deal, aid, new_status)
    now = utc_now()
    patch: dict[str, Any] = {"status": new_status, "updated_at": now}
    push: dict[str, Any] = {
        "history": {
            "at": now,
            "from": deal["status"],
            "to": new_status,
            "by": user.get("id") or user.get("sub"),
            "role": "partner",
            "notes": body.notes,
        }
    }
    if new_status == "counter":
        if body.counter_amount is None:
            raise HTTPException(status_code=400, detail="counter_amount_required")
        patch["proposal_amount"] = body.counter_amount
        patch["proposal_notes"] = body.notes
        push["proposals"] = {
            "id": new_id(),
            "amount": body.counter_amount,
            "notes": body.notes,
            "kind": "counter",
            "created_at": now,
            "created_by_user_id": user.get("id") or user.get("sub"),
        }
    r = await db.deals.update_one(
        deal_partner_filter(deal_id, aid), {"$set": patch, "$push": push}
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=403, detail="deal_partner_only")
    return _enrich_deal(await get_deal(db, deal_id), aid)
