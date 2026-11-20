"""MLS Collaboration workspace: visits, mini-dossier feedback, document requests, chat.

Does NOT auto-share fascicolo or create document requests on collaboration accept.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles
from shared.db.connection import Database
from shared.mls_collab.service import (
    VISIT_STATUSES,
    assert_document_request_accessible,
    assert_mls_listing_shareable,
    chat_scope_key,
    chat_thread_scope_query,
    counterpart_agency,
    get_collaboration,
    get_thread,
    get_visit,
    new_id,
    require_agency_in_collaboration,
    require_collaboration_active,
    require_thread_access,
    strip_id,
    utc_now,
)
from shared.mls_collab.watermark import apply_watermark, assert_format_supported

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
    """Partner agency requests collaboration on owner's MLS-shareable property."""
    db = Database.get()
    raw = Database.get_raw()
    aid = await _agency_id(user)
    prop = await raw.properties.find_one({"id": body.property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")
    owner = prop.get("agency_id")
    if not owner or owner == aid:
        raise HTTPException(status_code=400, detail="must_request_other_agency_listing")
    if body.partner_agency_id != aid:
        raise HTTPException(status_code=400, detail="partner_agency_must_be_self")
    # FIX-06 — same MLS gates as create_offer
    assert_mls_listing_shareable(prop)
    target = await raw.agencies.find_one(
        {"id": owner, "mls_enabled": True}, {"_id": 0, "id": 1}
    )
    if not target:
        raise HTTPException(status_code=400, detail="owner_agency_not_in_mls")
    requester = await raw.agencies.find_one(
        {"id": aid, "mls_enabled": True}, {"_id": 0, "id": 1}
    )
    if not requester:
        raise HTTPException(status_code=400, detail="requester_agency_not_in_mls")

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
        "history": [{"at": now, "event": "requested", "by_agency_id": aid}],
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
                    "document_request_auto": False,
                    "auto_document_share": False,
                },
                "$push": {"history": {"at": now, "event": "accepted", "by_agency_id": aid}},
            },
        )
        auto_docs = await db.mls_document_requests.count_documents(
            {"collaboration_id": collaboration_id, "auto_created": True}
        )
        if auto_docs:
            raise HTTPException(status_code=500, detail="invariant_auto_document_request")
        return {"id": collaboration_id, "status": "active", "document_request_created": False}
    if body.action == "reject":
        if aid != collab["owner_agency_id"]:
            raise HTTPException(status_code=403, detail="only_owner_can_reject")
        now = utc_now()
        await db.mls_collaborations.update_one(
            {"id": collaboration_id},
            {
                "$set": {"status": "rejected", "updated_at": now},
                "$push": {"history": {"at": now, "event": "rejected", "by_agency_id": aid}},
            },
        )
        return {"id": collaboration_id, "status": "rejected"}
    # FIX-03 — revoke collab + chat + document requests
    require_agency_in_collaboration(collab, aid)
    now = utc_now()
    await db.mls_collaborations.update_one(
        {"id": collaboration_id},
        {
            "$set": {"status": "revoked", "updated_at": now, "revoked_at": now},
            "$push": {"history": {"at": now, "event": "revoked", "by_agency_id": aid}},
        },
    )
    await db.mls_chat_threads.update_many(
        {"collaboration_id": collaboration_id},
        {"$set": {"status": "revoked", "updated_at": now}},
    )
    await db.mls_document_requests.update_many(
        {
            "collaboration_id": collaboration_id,
            "status": {"$in": ["pending", "approved", "fulfilled"]},
        },
        {
            "$set": {
                "status": "revoked",
                "revoked_at": now,
                "revoked_reason": "collaboration_revoked",
                "updated_at": now,
            }
        },
    )
    return {"id": collaboration_id, "status": "revoked", "document_requests_revoked": True}


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
    require_collaboration_active(collab)
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


class FeedbackContestBody(BaseModel):
    reason: str = Field(..., min_length=3, max_length=2000)


class FeedbackResolveBody(BaseModel):
    decision: Literal["uphold", "dismiss"]
    rationale: str = Field(..., min_length=3, max_length=4000)


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
    require_collaboration_active(collab)
    target = counterpart_agency(collab, aid)
    dup = await db.mls_visit_feedback.find_one(
        {"visit_id": visit["id"], "from_agency_id": aid},
        {"_id": 0, "id": 1},
    )
    if dup:
        raise HTTPException(status_code=409, detail="feedback_already_submitted")
    now = utc_now()
    doc = {
        "id": new_id(),
        "kind": "post_visit_feedback",
        "visit_id": visit["id"],
        "collaboration_id": visit["collaboration_id"],
        "property_id": visit["property_id"],
        "from_agency_id": aid,
        "to_agency_id": target,
        "rating": body.rating,
        "feedback_text": body.feedback_text,
        "contested": False,
        "contest_status": None,
        "excluded_from_public_rating": False,
        "created_by_user_id": user.get("id") or user.get("sub"),
        "created_at": now,
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


@router.post("/visit-feedback/{feedback_id}/contest")
async def contest_visit_feedback(
    feedback_id: str,
    body: FeedbackContestBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Target agency contests a rating — excluded from public aggregate until Super Admin resolves."""
    db = Database.get()
    aid = await _agency_id(user)
    row = await db.mls_visit_feedback.find_one({"id": feedback_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="feedback_not_found")
    if aid != row.get("to_agency_id"):
        raise HTTPException(status_code=403, detail="only_rated_agency_can_contest")
    if row.get("contested"):
        return row
    now = utc_now()
    await db.mls_visit_feedback.update_one(
        {"id": feedback_id},
        {
            "$set": {
                "contested": True,
                "contest_status": "open",
                "contest_reason": body.reason,
                "contested_at": now,
                "excluded_from_public_rating": True,
                "updated_at": now,
            }
        },
    )
    return await db.mls_visit_feedback.find_one({"id": feedback_id}, {"_id": 0})


@router.post("/visit-feedback/{feedback_id}/resolve")
async def resolve_visit_feedback_dispute(
    feedback_id: str,
    body: FeedbackResolveBody,
    user: dict = Depends(require_roles("super_admin")),
):
    """Super Admin only — scoped to the dispute, audited."""
    db = Database.get()
    row = await db.mls_visit_feedback.find_one({"id": feedback_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="feedback_not_found")
    if not row.get("contested") or row.get("contest_status") not in ("open", None, "pending"):
        if row.get("contest_status") in ("upheld", "dismissed"):
            return row
        raise HTTPException(status_code=400, detail="feedback_not_in_dispute")
    now = utc_now()
    if body.decision == "uphold":
        # Keep excluded (rating voided for public aggregate)
        patch = {
            "contest_status": "upheld",
            "excluded_from_public_rating": True,
            "resolved_at": now,
            "resolution_rationale": body.rationale,
            "resolved_by_user_id": user.get("id") or user.get("sub"),
            "updated_at": now,
        }
    else:
        # Dismiss contest → rating re-enters aggregate
        patch = {
            "contest_status": "dismissed",
            "contested": False,
            "excluded_from_public_rating": False,
            "resolved_at": now,
            "resolution_rationale": body.rationale,
            "resolved_by_user_id": user.get("id") or user.get("sub"),
            "updated_at": now,
        }
    await db.mls_visit_feedback.update_one({"id": feedback_id}, {"$set": patch})
    await db.mls_rating_dispute_audit.insert_one(
        {
            "id": new_id(),
            "feedback_id": feedback_id,
            "decision": body.decision,
            "rationale": body.rationale,
            "by_user_id": user.get("id") or user.get("sub"),
            "at": now,
            "to_agency_id": row.get("to_agency_id"),
            "from_agency_id": row.get("from_agency_id"),
        }
    )
    return await db.mls_visit_feedback.find_one({"id": feedback_id}, {"_id": 0})


@router.get("/agency-ratings/{agency_id}")
async def agency_public_rating(
    agency_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Aggregate only non-excluded feedback. No private history of individual ratings."""
    db = Database.get()
    cursor = db.mls_visit_feedback.find(
        {
            "to_agency_id": agency_id,
            "excluded_from_public_rating": {"$ne": True},
            "contest_status": {"$nin": ["upheld"]},
        },
        {"_id": 0, "rating": 1},
    )
    ratings = [int(r["rating"]) async for r in cursor if r.get("rating") is not None]
    if not ratings:
        return {
            "agency_id": agency_id,
            "count": 0,
            "average": None,
            "history_public": False,
        }
    return {
        "agency_id": agency_id,
        "count": len(ratings),
        "average": round(sum(ratings) / len(ratings), 2),
        "history_public": False,
    }


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
    # Optional inline artifacts for Dogfood / synthetic docs (base64 not required —
    # content stored server-side on fulfill via keys mapping to generated samples)


@router.post("/document-requests", status_code=201)
async def create_document_request(
    body: DocumentRequestCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = await _agency_id(user)
    collab = await get_collaboration(db, body.collaboration_id)
    require_agency_in_collaboration(collab, aid)
    require_collaboration_active(collab)
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
        collab = await get_collaboration(db, row["collaboration_id"])
        require_collaboration_active(collab)
        status_map = {"approve": "approved", "fulfill": "fulfilled", "reject": "rejected"}
        patch: dict[str, Any] = {
            "status": status_map[body.action],
            "updated_at": now,
            "responded_by_user_id": user.get("id") or user.get("sub"),
        }
        if body.action == "fulfill":
            shared_ids = body.shared_document_ids or list(row.get("document_keys") or []) or [
                "doc-default"
            ]
            # Persist synthetic originals (never served raw)
            for did in shared_ids:
                existing = await db.mls_document_artifacts.find_one(
                    {"id": did, "document_request_id": request_id}, {"_id": 0, "id": 1}
                )
                if existing:
                    continue
                # Default sample: small PNG (Pillow) — real watermark applied on download
                from PIL import Image, ImageDraw

                img = Image.new("RGB", (640, 360), color=(240, 240, 245))
                draw = ImageDraw.Draw(img)
                draw.text((24, 160), f"OMNIA original {did}", fill=(30, 30, 30))
                buf = __import__("io").BytesIO()
                img.save(buf, format="PNG")
                await db.mls_document_artifacts.insert_one(
                    {
                        "id": did,
                        "document_request_id": request_id,
                        "collaboration_id": row["collaboration_id"],
                        "content_type": "image/png",
                        "original_bytes": buf.getvalue(),
                        "created_at": now,
                        "is_original": True,
                    }
                )
            patch["shared_document_ids"] = shared_ids
            patch["watermark_applied"] = True  # distribution path will apply real watermark
            patch["watermark_mode"] = "content_on_download"
            patch["fulfilled_at"] = now
        await db.mls_document_requests.update_one({"id": request_id}, {"$set": patch})
    elif body.action == "revoke":
        if aid not in (row["owner_agency_id"], row["requesting_agency_id"]):
            raise HTTPException(status_code=403, detail="forbidden")
        await db.mls_document_requests.update_one(
            {"id": request_id},
            {"$set": {"status": "revoked", "updated_at": now, "revoked_at": now}},
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
    """Trace consult intent — foreign / revoked denied. Prefer /download for content."""
    db = Database.get()
    aid = await _agency_id(user)
    row = await db.mls_document_requests.find_one({"id": request_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="document_request_not_found")
    if aid not in (row["requesting_agency_id"], row["owner_agency_id"]):
        raise HTTPException(status_code=403, detail="document_access_denied")
    await assert_document_request_accessible(db, row)
    if row.get("status") not in ("approved", "fulfilled"):
        raise HTTPException(status_code=403, detail="documents_not_shared")
    entry = {
        "at": utc_now(),
        "agency_id": aid,
        "user_id": user.get("id") or user.get("sub"),
        "watermark": True,
        "action": "consult",
    }
    await db.mls_document_requests.update_one(
        {"id": request_id},
        {"$push": {"access_log": entry}},
    )
    return {
        "ok": True,
        "watermark": True,
        "watermark_mode": row.get("watermark_mode") or "content_on_download",
        "shared_document_ids": row.get("shared_document_ids") or [],
        "access": entry,
        "download_path_hint": f"/app/document-requests/{request_id}/download",
    }


@router.get("/document-requests/{request_id}/download")
async def download_watermarked_document(
    request_id: str,
    document_id: Optional[str] = Query(None),
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Serve watermarked copy only — original never returned."""
    db = Database.get()
    aid = await _agency_id(user)
    row = await db.mls_document_requests.find_one({"id": request_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="document_request_not_found")
    if aid not in (row["requesting_agency_id"], row["owner_agency_id"]):
        raise HTTPException(status_code=403, detail="document_access_denied")
    await assert_document_request_accessible(db, row)
    if row.get("status") != "fulfilled":
        raise HTTPException(status_code=403, detail="documents_not_shared")
    shared = row.get("shared_document_ids") or []
    doc_id = document_id or (shared[0] if shared else None)
    if not doc_id or doc_id not in shared:
        raise HTTPException(status_code=404, detail="document_not_in_share")
    art = await db.mls_document_artifacts.find_one(
        {"id": doc_id, "document_request_id": request_id, "is_original": True},
        {"_id": 0},
    )
    if not art or not art.get("original_bytes"):
        raise HTTPException(status_code=404, detail="artifact_missing")
    assert_format_supported(art.get("content_type") or "image/png")
    label = (
        f"OMNIA | req={request_id[:8]} | agency={aid[:8]} | "
        f"user={(user.get('id') or user.get('sub') or '')[:8]}"
    )
    wm_bytes, out_ct = apply_watermark(
        art["original_bytes"],
        content_type=art.get("content_type") or "image/png",
        label=label,
    )
    now = utc_now()
    dist_id = new_id()
    await db.mls_document_distributions.insert_one(
        {
            "id": dist_id,
            "document_request_id": request_id,
            "document_id": doc_id,
            "collaboration_id": row["collaboration_id"],
            "agency_id": aid,
            "user_id": user.get("id") or user.get("sub"),
            "content_type": out_ct,
            "bytes_len": len(wm_bytes),
            "watermark_label": label,
            "created_at": now,
        }
    )
    await db.mls_document_requests.update_one(
        {"id": request_id},
        {
            "$push": {
                "access_log": {
                    "at": now,
                    "agency_id": aid,
                    "user_id": user.get("id") or user.get("sub"),
                    "watermark": True,
                    "action": "download",
                    "distribution_id": dist_id,
                    "document_id": doc_id,
                }
            }
        },
    )
    return Response(
        content=wm_bytes,
        media_type=out_ct,
        headers={
            "Content-Disposition": f'attachment; filename="omnia-wm-{doc_id}.bin"',
            "X-OMNIA-Watermark": "1",
            "X-OMNIA-Distribution-Id": dist_id,
            "Cache-Control": "no-store",
        },
    )


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
    require_collaboration_active(collab)
    if body.visit_id:
        visit = await get_visit(db, body.visit_id)
        if visit["collaboration_id"] != collab["id"]:
            raise HTTPException(status_code=400, detail="visit_collaboration_mismatch")
    # FIX-02 — exact scope match (absent ≠ any)
    q = chat_thread_scope_query(
        collab["id"], visit_id=body.visit_id, deal_id=body.deal_id
    )
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
        "scope_key": chat_scope_key(
            collab["id"], visit_id=body.visit_id, deal_id=body.deal_id
        ),
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
    collab = await get_collaboration(db, thread["collaboration_id"])
    require_collaboration_active(collab)
    if body.attachment_document_request_id:
        dr = await db.mls_document_requests.find_one(
            {"id": body.attachment_document_request_id}, {"_id": 0}
        )
        if not dr or dr.get("status") not in ("approved", "fulfilled"):
            raise HTTPException(status_code=403, detail="attachment_not_authorized")
        if aid not in (dr["requesting_agency_id"], dr["owner_agency_id"]):
            raise HTTPException(status_code=403, detail="attachment_forbidden")
        await assert_document_request_accessible(db, dr)
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
