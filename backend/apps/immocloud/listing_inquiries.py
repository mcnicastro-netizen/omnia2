"""OMNIA — B2C seller inquiry inbox (Idealista+ · D-138).

Private listing contacts land in `listing_inquiries`. This module lets the
seller list / filter / mark-read / archive and manage visit status — better
than Idealista's email-only private flow.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from shared.models.base import OmniaBaseModel

logger = logging.getLogger("omnia.listing_inquiries")
router = APIRouter(prefix="/me/inquiries", tags=["cloud-inquiries"])

VisitStatus = Literal["none", "requested", "accepted", "declined", "completed"]
FilterKind = Literal["all", "unread", "visits", "open", "archived"]


class InquiryPatch(OmniaBaseModel):
    read: Optional[bool] = None
    archived: Optional[bool] = None
    visit_status: Optional[VisitStatus] = None
    seller_note: Optional[str] = Field(default=None, max_length=2000)


def _ensure_b2c(user: dict) -> None:
    if user.get("account_type") != "b2c" or user.get("role") != "client":
        raise HTTPException(status_code=403, detail="b2c_account_required")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_item(doc: dict, prop: Optional[dict] = None) -> dict:
    """Shape safe for the seller UI (no internal Mongo _id)."""
    visit_requested = bool(doc.get("visit_requested"))
    visit_status = doc.get("visit_status")
    if not visit_status:
        visit_status = "requested" if visit_requested else "none"
    read_at = doc.get("read_at")
    return {
        "id": doc.get("id"),
        "property_id": doc.get("property_id"),
        "property_title": (prop or {}).get("title") or doc.get("property_title") or "Immobile",
        "property_city": (prop or {}).get("city") or doc.get("property_city"),
        "listing_code": (prop or {}).get("listing_code") or doc.get("listing_code"),
        "name": doc.get("name") or "",
        "surname": doc.get("surname") or "",
        "email": doc.get("email") or "",
        "phone": doc.get("phone") or "",
        "message": doc.get("message") or "",
        "visit_requested": visit_requested,
        "visit_status": visit_status,
        "archived": bool(doc.get("archived")),
        "read_at": read_at,
        "is_read": bool(read_at),
        "seller_note": doc.get("seller_note") or "",
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at") or doc.get("created_at"),
    }


@router.get("/summary")
async def inquiries_summary(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _ensure_b2c(user)
    db = Database.get()
    uid = user["id"]
    base = {"owner_user_id": uid}
    total = await db.listing_inquiries.count_documents(base)
    unread = await db.listing_inquiries.count_documents({
        **base,
        "archived": {"$ne": True},
        "$or": [{"read_at": None}, {"read_at": {"$exists": False}}],
    })
    # Pending visit = explicit requested, or legacy flag without a decision yet.
    visits_pending = await db.listing_inquiries.count_documents({
        **base,
        "archived": {"$ne": True},
        "$or": [
            {"visit_status": "requested"},
            {
                "visit_requested": True,
                "$or": [
                    {"visit_status": {"$exists": False}},
                    {"visit_status": None},
                    {"visit_status": "none"},
                ],
            },
        ],
    })
    return {
        "total": total,
        "unread": unread,
        "visits_pending": visits_pending,
        "open": await db.listing_inquiries.count_documents({**base, "archived": {"$ne": True}}),
    }


@router.get("")
async def list_inquiries(
    user: dict = Depends(get_current_user),
    filter: FilterKind = Query("open"),  # noqa: A002 — API name
    property_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    _ensure_b2c(user)
    db = Database.get()
    q: Dict[str, Any] = {"owner_user_id": user["id"]}
    if property_id:
        q["property_id"] = property_id
    if filter == "unread":
        q["archived"] = {"$ne": True}
        q["$or"] = [{"read_at": None}, {"read_at": {"$exists": False}}]
    elif filter == "visits":
        q["archived"] = {"$ne": True}
        q["$or"] = [
            {"visit_status": {"$in": ["requested", "accepted"]}},
            {"visit_requested": True, "visit_status": {"$in": [None, "none"]}},
            {"visit_requested": True, "visit_status": {"$exists": False}},
        ]
    elif filter == "archived":
        q["archived"] = True
    elif filter == "open":
        q["archived"] = {"$ne": True}
    # filter == "all" → no extra

    total = await db.listing_inquiries.count_documents(q)
    cursor = (
        db.listing_inquiries.find(q, {"_id": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    rows: List[dict] = await cursor.to_list(length=limit)
    pids = list({r.get("property_id") for r in rows if r.get("property_id")})
    props: Dict[str, dict] = {}
    if pids:
        async for p in db.properties.find(
            {"id": {"$in": pids}},
            {"_id": 0, "id": 1, "title": 1, "city": 1, "listing_code": 1},
        ):
            props[p["id"]] = p
    items = [_public_item(r, props.get(r.get("property_id") or "")) for r in rows]
    return {"items": items, "total": total, "limit": limit, "offset": offset, "filter": filter}


@router.patch("/{inquiry_id}")
async def patch_inquiry(
    inquiry_id: str,
    body: InquiryPatch,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    _ensure_b2c(user)
    db = Database.get()
    doc = await db.listing_inquiries.find_one(
        {"id": inquiry_id, "owner_user_id": user["id"]},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="inquiry_not_found")

    updates: Dict[str, Any] = {"updated_at": _iso_now()}
    if body.read is True:
        updates["read_at"] = _iso_now()
    elif body.read is False:
        updates["read_at"] = None
    if body.archived is not None:
        updates["archived"] = bool(body.archived)
    if body.visit_status is not None:
        allowed = {"none", "requested", "accepted", "declined", "completed"}
        if body.visit_status not in allowed:
            raise HTTPException(status_code=400, detail="invalid_visit_status")
        updates["visit_status"] = body.visit_status
        if body.visit_status != "none":
            updates["visit_requested"] = True
    if body.seller_note is not None:
        updates["seller_note"] = body.seller_note.strip()

    await db.listing_inquiries.update_one(
        {"id": inquiry_id, "owner_user_id": user["id"]},
        {"$set": updates},
    )
    fresh = await db.listing_inquiries.find_one(
        {"id": inquiry_id, "owner_user_id": user["id"]},
        {"_id": 0},
    )
    prop = None
    if fresh and fresh.get("property_id"):
        prop = await db.properties.find_one(
            {"id": fresh["property_id"]},
            {"_id": 0, "id": 1, "title": 1, "city": 1, "listing_code": 1},
        )
    return {"ok": True, "item": _public_item(fresh or doc, prop)}
