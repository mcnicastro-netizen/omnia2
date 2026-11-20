"""MLS Collaboration workspace: visits, mini-dossier feedback, document requests, chat.

Does NOT auto-share fascicolo or create document requests on collaboration accept.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles
from shared.db.connection import Database
from shared.mls_collab.service import (
    VISIT_STATUSES,
    counterpart_agency,
    get_collaboration,
    get_thread,
    get_visit,
    new_id,
    require_agency_in_collaboration,
    require_thread_access,
    strip_id,
    utc_now,
)

router = APIRouter(tags=["mls-collaborations"])


async def _agency_id(user: dict) -> str:
    from shared.auth.tenant import arequire_agency

    return await arequire_agency(user)


# ── Collaboration ──────────────────────────────────────────────────────────


class CollaborationCreate(BaseModel):
    property_id: str
    partner_agency_id: str
    message: Optional[str] = Field(default=None, max_length=1000)


@router.get("/collaborations")
async def list_collaborations(
    status: Optional[str] = Query(None),
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    q: dict[str, Any] = {
        "$or": [{"owner_agency_id": aid}, {"partner_agency_id": aid}],
    }
    if status:
        q["status"] = status
    items = [
        strip_id(r)
        async for r in db.mls_collaborations.find(q, {"_id": 0}).sort("created_at", -1).limit(100)
    ]
    return {"items": items}


@router.post("/collaborations", status_code=201)
async def create_collaboration_request(
    body: CollaborationCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Partner agency requests collaboration on owner's property (MLS listing)."""
    db = Database.get()
    raw = Database.get_raw()  # cross-agency property lookup (tenant guard would hide it)
    aid = await _agency_id(user)
    if body.partner_agency_id == aid:
        # requester is partner; owner is listing agency
        pass
    prop = await raw.properties.find_one({"id": body.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")
    owner = prop.get("agency_id")
    if not owner or owner == aid:
        raise HTTPException(status_code=400, detail="must_request_other_agency_listing")
    if body.partner_agency_id != aid:
        raise HTTPException(status_code=400, detail="partner_agency_must_be_self")
    existing = await db.mls_collaborations.find_one(
        {
            "property_id": body.property_id,
            "owner_agency_id": owner,
            "partner_agency_id": aid,
            "status": {"$in": ["pending", "active"]},
        },
        {"_id": 0},
    )
    if existing:
        return existing
    now = utc_now()
    doc = {
        "id": new_id(),
        "property_id": body.property_id,
        "owner_agency_id": owner,
        "partner_agency_id": aid,
        "status": "pending",
        "message": body.message,
        "created_at": now,
        "updated_at": now,
        "requested_by_user_id": user.get("id") or user.get("sub"),
        "document_request_auto": False,
    }
    await db.mls_collaborations.insert_one(doc)
    doc.pop("_id", None)
    return doc


class CollaborationAction(BaseModel):
    action: Literal["accept", "reject", "revoke"]


@router.post("/collaborations/{collaboration_id}/respond")
async def respond_collaboration(
    collaboration_id: str,
    body: CollaborationAction,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    collab = await get_collaboration(db, collaboration_id)
    if body.action == "accept":
        if aid != collab["owner_agency_id"]:
            raise HTTPException(status_code=403, detail="only_owner_can_accept")
        if collab.get("status") != "pending":
            raise HTTPException(status_code=400, detail="not_pending")
        now = utc_now()
        await db.mls_collaborations.update_one(
            {"id": collaboration_id},
            {
                "$set": {
                    "status": "active",
                    "accepted_at": now,
                    "updated_at": now,
                    # Explicit invariants — never auto-create document pipeline
                    "document_request_auto": False,
                    "auto_document_share": False,
                }
            },
        )
        # Verify no document request was spawned
        auto_docs = await db.mls_document_requests.count_documents(
            {"collaboration_id": collaboration_id, "auto_created": True}
        )
        if auto_docs:
            raise HTTPException(status_code=500, detail="invariant_auto_document_request")
        return {"id": collaboration_id, "status": "active", "document_request_created": False}
    if body.action == "reject":
        if aid != collab["owner_agency_id"]:
            raise HTTPException(status_code=403, detail="only_owner_can_reject")
        await db.mls_collaborations.update_one(
            {"id": collaboration_id},
            {"$set": {"status": "rejected", "updated_at": utc_now()}},
        )
        return {"id": collaboration_id, "status": "rejected"}
    # revoke
    require_agency_in_collaboration(collab, aid)
    await db.mls_collaborations.update_one(
        {"id": collaboration_id},
        {"$set": {"status": "revoked", "updated_at": utc_now()}},
    )
    await db.mls_chat_threads.update_many(
        {"collaboration_id": collaboration_id},
        {"$set": {"status": "revoked", "updated_at": utc_now()}},
    )
    return {"id": collaboration_id, "status": "revoked"}


@router.get("/collaborations/{collaboration_id}")
async def get_collaboration_detail(
    collaboration_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    collab = await get_collaboration(db, collaboration_id)
    require_agency_in_collaboration(collab, aid)
    return collab


# ── Visits ─────────────────────────────────────────────────────────────────


class VisitCreate(BaseModel):
    collaboration_id: str
    proposed_slots: list[str] = Field(default_factory=list, max_length=10)
    notes: Optional[str] = Field(default=None, max_length=2000)


class VisitUpdate(BaseModel):
    status: Optional[Literal["proposed", "agreed", "completed", "cancelled"]] = None
    agreed_slot: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=2000)


@router.post("/visits", status_code=201)
async def request_visit(
    body: VisitCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    collab = await get_collaboration(db, body.collaboration_id)
    require_agency_in_collaboration(collab, aid)
    if collab.get("status") != "active":
        raise HTTPException(status_code=400, detail="collaboration_not_active")
    now = utc_now()
    doc = {
        "id": new_id(),
        "collaboration_id": collab["id"],
        "property_id": collab["property_id"],
        "owner_agency_id": collab["owner_agency_id"],
        "partner_agency_id": collab["partner_agency_id"],
        "status": "requested",
        "proposed_slots": body.proposed_slots,
        "notes": body.notes,
        "requested_by_agency_id": aid,
        "requested_by_user_id": user.get("id") or user.get("sub"),
        "created_at": now,
        "updated_at": now,
    }
    await db.mls_visits.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/visits")
async def list_visits(
    collaboration_id: Optional[str] = None,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    q: dict[str, Any] = {
        "$or": [{"owner_agency_id": aid}, {"partner_agency_id": aid}],
    }
    if collaboration_id:
        q["collaboration_id"] = collaboration_id
    items = [
        strip_id(r)
        async for r in db.mls_visits.find(q, {"_id": 0}).sort("created_at", -1).limit(100)
    ]
    return {"items": items}


@router.patch("/visits/{visit_id}")
async def update_visit(
    visit_id: str,
    body: VisitUpdate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    visit = await get_visit(db, visit_id)
    if aid not in (visit["owner_agency_id"], visit["partner_agency_id"]):
        raise HTTPException(status_code=403, detail="visit_forbidden")
    patch: dict[str, Any] = {"updated_at": utc_now()}
    if body.notes is not None:
        patch["notes"] = body.notes
    if body.agreed_slot is not None:
        patch["agreed_slot"] = body.agreed_slot
    if body.status:
        if body.status not in VISIT_STATUSES:
            raise HTTPException(status_code=400, detail="invalid_visit_status")
        patch["status"] = body.status
        if body.status == "agreed":
            patch["agreed_at"] = utc_now()
        if body.status == "completed":
            patch["completed_at"] = utc_now()
    await db.mls_visits.update_one({"id": visit_id}, {"$set": patch})
    return await get_visit(db, visit_id)


# ── Mini-dossier = post-visit feedback / rating ONLY ───────────────────────


class VisitFeedbackCreate(BaseModel):
    visit_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = Field(default=None, max_length=4000)
    contested: bool = False


@router.post("/visit-feedback", status_code=201)
async def create_visit_feedback(
    body: VisitFeedbackCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Mini-dossier post-visita: feedback/rating for agency reputation — NOT documents."""
    db = Database.get()
    aid = await _agency_id(user)
    visit = await get_visit(db, body.visit_id)
    if aid not in (visit["owner_agency_id"], visit["partner_agency_id"]):
        raise HTTPException(status_code=403, detail="visit_forbidden")
    if visit.get("status") != "completed":
        raise HTTPException(status_code=400, detail="visit_not_completed")
    collab = await get_collaboration(db, visit["collaboration_id"])
    target = counterpart_agency(collab, aid)
    now = utc_now()
    doc = {
        "id": new_id(),
        "kind": "post_visit_feedback",  # mini-dossier semantic
        "visit_id": visit["id"],
        "collaboration_id": visit["collaboration_id"],
        "property_id": visit["property_id"],
        "from_agency_id": aid,
        "to_agency_id": target,
        "rating": body.rating,
        "feedback_text": body.feedback_text,
        "contested": body.contested,
        "excluded_from_public_rating": bool(body.contested),
        "created_by_user_id": user.get("id") or user.get("sub"),
        "created_at": now,
        # Hard separation from document flows
        "is_document_request": False,
        "shares_documents": False,
    }
    await db.mls_visit_feedback.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/visit-feedback")
async def list_visit_feedback(
    visit_id: Optional[str] = None,
    collaboration_id: Optional[str] = None,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    q: dict[str, Any] = {
        "$or": [{"from_agency_id": aid}, {"to_agency_id": aid}],
    }
    if visit_id:
        q["visit_id"] = visit_id
    if collaboration_id:
        q["collaboration_id"] = collaboration_id
    items = [
        strip_id(r)
        async for r in db.mls_visit_feedback.find(q, {"_id": 0}).sort("created_at", -1).limit(100)
    ]
    return {"items": items}


# ── Explicit document request (separate from mini-dossier) ─────────────────


class DocumentRequestCreate(BaseModel):
    collaboration_id: str
    visit_id: Optional[str] = None
    deal_id: Optional[str] = None
    document_keys: list[str] = Field(default_factory=list, max_length=50)
    message: Optional[str] = Field(default=None, max_length=2000)


class DocumentRequestAction(BaseModel):
    action: Literal["approve", "reject", "fulfill", "revoke"]
    shared_document_ids: list[str] = Field(default_factory=list)


@router.post("/document-requests", status_code=201)
async def create_document_request(
    body: DocumentRequestCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    collab = await get_collaboration(db, body.collaboration_id)
    require_agency_in_collaboration(collab, aid)
    if collab.get("status") != "active":
        raise HTTPException(status_code=400, detail="collaboration_not_active")
    if body.visit_id:
        visit = await get_visit(db, body.visit_id)
        if visit["collaboration_id"] != collab["id"]:
            raise HTTPException(status_code=400, detail="visit_collaboration_mismatch")
    now = utc_now()
    doc = {
        "id": new_id(),
        "collaboration_id": collab["id"],
        "property_id": collab["property_id"],
        "visit_id": body.visit_id,
        "deal_id": body.deal_id,
        "requesting_agency_id": aid,
        "owner_agency_id": collab["owner_agency_id"],
        "status": "pending",
        "document_keys": body.document_keys,
        "message": body.message,
        "auto_created": False,
        "watermark_required": True,
        "created_by_user_id": user.get("id") or user.get("sub"),
        "created_at": now,
        "updated_at": now,
        "access_log": [],
    }
    await db.mls_document_requests.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/document-requests/{request_id}/respond")
async def respond_document_request(
    request_id: str,
    body: DocumentRequestAction,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    row = await db.mls_document_requests.find_one({"id": request_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="document_request_not_found")
    now = utc_now()
    if body.action in ("approve", "fulfill", "reject"):
        if aid != row["owner_agency_id"]:
            raise HTTPException(status_code=403, detail="only_owner_manages_documents")
        status_map = {"approve": "approved", "fulfill": "fulfilled", "reject": "rejected"}
        patch: dict[str, Any] = {
            "status": status_map[body.action],
            "updated_at": now,
            "responded_by_user_id": user.get("id") or user.get("sub"),
        }
        if body.action == "fulfill":
            patch["shared_document_ids"] = body.shared_document_ids
            patch["watermark_applied"] = True
            patch["fulfilled_at"] = now
        await db.mls_document_requests.update_one({"id": request_id}, {"$set": patch})
    elif body.action == "revoke":
        if aid not in (row["owner_agency_id"], row["requesting_agency_id"]):
            raise HTTPException(status_code=403, detail="forbidden")
        await db.mls_document_requests.update_one(
            {"id": request_id},
            {"$set": {"status": "revoked", "updated_at": now}},
        )
    return await db.mls_document_requests.find_one({"id": request_id}, {"_id": 0})


@router.get("/document-requests")
async def list_document_requests(
    collaboration_id: Optional[str] = None,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    q: dict[str, Any] = {
        "$or": [{"requesting_agency_id": aid}, {"owner_agency_id": aid}],
    }
    if collaboration_id:
        q["collaboration_id"] = collaboration_id
    items = [
        strip_id(r)
        async for r in db.mls_document_requests.find(q, {"_id": 0}).sort("created_at", -1).limit(100)
    ]
    return {"items": items}


@router.post("/document-requests/{request_id}/access")
async def log_document_access(
    request_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Trace download/view — foreign agencies denied."""
    db = Database.get()
    aid = await _agency_id(user)
    row = await db.mls_document_requests.find_one({"id": request_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="document_request_not_found")
    if row.get("status") not in ("approved", "fulfilled"):
        raise HTTPException(status_code=403, detail="documents_not_shared")
    if aid not in (row["requesting_agency_id"], row["owner_agency_id"]):
        raise HTTPException(status_code=403, detail="document_access_denied")
    if row.get("status") == "revoked":
        raise HTTPException(status_code=403, detail="document_access_revoked")
    entry = {
        "at": utc_now(),
        "agency_id": aid,
        "user_id": user.get("id") or user.get("sub"),
        "watermark": True,
    }
    await db.mls_document_requests.update_one(
        {"id": request_id},
        {"$push": {"access_log": entry}},
    )
    return {
        "ok": True,
        "watermark": True,
        "shared_document_ids": row.get("shared_document_ids") or [],
        "access": entry,
    }


# ── Contextual chat ────────────────────────────────────────────────────────


class ChatOpenBody(BaseModel):
    collaboration_id: str
    visit_id: Optional[str] = None
    deal_id: Optional[str] = None


class ChatMessageBody(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)
    attachment_document_request_id: Optional[str] = None


@router.post("/collab-chat/threads", status_code=201)
async def open_chat_thread(
    body: ChatOpenBody,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    collab = await get_collaboration(db, body.collaboration_id)
    require_agency_in_collaboration(collab, aid)
    if collab.get("status") != "active":
        raise HTTPException(status_code=400, detail="collaboration_not_active")
    if body.visit_id:
        visit = await get_visit(db, body.visit_id)
        if visit["collaboration_id"] != collab["id"]:
            raise HTTPException(status_code=400, detail="visit_collaboration_mismatch")
    q = {"collaboration_id": collab["id"], "status": "open"}
    if body.visit_id:
        q["visit_id"] = body.visit_id
    if body.deal_id:
        q["deal_id"] = body.deal_id
    existing = await db.mls_chat_threads.find_one(q, {"_id": 0})
    if existing:
        return existing
    now = utc_now()
    doc = {
        "id": new_id(),
        "collaboration_id": collab["id"],
        "property_id": collab["property_id"],
        "visit_id": body.visit_id,
        "deal_id": body.deal_id,
        "agency_ids": [collab["owner_agency_id"], collab["partner_agency_id"]],
        "status": "open",
        "created_at": now,
        "updated_at": now,
        "created_by_agency_id": aid,
    }
    await db.mls_chat_threads.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/collab-chat/threads/{thread_id}/messages")
async def list_chat_messages(
    thread_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    thread = await get_thread(db, thread_id)
    require_thread_access(thread, aid)
    items = [
        strip_id(r)
        async for r in db.mls_chat_messages.find({"thread_id": thread_id}, {"_id": 0})
        .sort("created_at", 1)
        .limit(500)
    ]
    return {"thread": thread, "items": items}


@router.post("/collab-chat/threads/{thread_id}/messages", status_code=201)
async def post_chat_message(
    thread_id: str,
    body: ChatMessageBody,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    thread = await get_thread(db, thread_id)
    require_thread_access(thread, aid)
    if body.attachment_document_request_id:
        dr = await db.mls_document_requests.find_one(
            {"id": body.attachment_document_request_id}, {"_id": 0}
        )
        if not dr or dr.get("status") not in ("approved", "fulfilled"):
            raise HTTPException(status_code=403, detail="attachment_not_authorized")
        if aid not in (dr["requesting_agency_id"], dr["owner_agency_id"]):
            raise HTTPException(status_code=403, detail="attachment_forbidden")
    now = utc_now()
    msg = {
        "id": new_id(),
        "thread_id": thread_id,
        "collaboration_id": thread["collaboration_id"],
        "sender_agency_id": aid,
        "sender_user_id": user.get("id") or user.get("sub"),
        "body": body.body,
        "attachment_document_request_id": body.attachment_document_request_id,
        "created_at": now,
    }
    await db.mls_chat_messages.insert_one(msg)
    await db.mls_chat_threads.update_one(
        {"id": thread_id}, {"$set": {"updated_at": now, "last_message_at": now}}
    )
    msg.pop("_id", None)
    return msg
