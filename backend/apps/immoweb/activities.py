"""OMNIA — CRM Activities / follow-up (A-028h).

Minimal task list for the agent morning loop. Not a full calendar —
cockpit «Oggi» surfaces open items due today/overdue.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database

logger = logging.getLogger("omnia.activities")
router = APIRouter(prefix="/activities", tags=["activities"])

ActivityKind = Literal["call", "visit", "follow_up", "other"]
ActivityStatus = Literal["open", "done", "cancelled"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _agency_id(user: dict) -> str:
    from shared.auth.tenant import arequire_agency
    return await arequire_agency(user)


def _strip(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "_id"}


class ActivityCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    kind: ActivityKind = "follow_up"
    due_at: Optional[str] = None  # ISO
    related_client_id: Optional[str] = None
    related_property_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


class ActivityUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    kind: Optional[ActivityKind] = None
    due_at: Optional[str] = None
    status: Optional[ActivityStatus] = None
    related_client_id: Optional[str] = None
    related_property_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


@router.get("")
async def list_activities(
    status: Optional[str] = Query("open"),
    due: Optional[str] = Query(None, description="today | overdue | all"),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    agency_id = await _agency_id(user)
    db = Database.get()
    q: Dict[str, Any] = {"agency_id": agency_id}
    if status and status != "all":
        q["status"] = status
    now = _now()
    today = now[:10]
    if due == "today":
        q["due_at"] = {"$gte": f"{today}T00:00:00", "$lte": f"{today}T23:59:59.999999+00:00"}
        # also accept date-only or any ISO starting with today
        q["due_at"] = {"$regex": f"^{today}"}
    elif due == "overdue":
        q["status"] = "open"
        q["due_at"] = {"$lt": f"{today}T00:00:00", "$ne": None}
    cursor = db.activities.find(q, {"_id": 0}).sort("due_at", 1).limit(limit)
    items = await cursor.to_list(length=limit)
    return {"items": items, "total": len(items)}


@router.post("", status_code=201)
async def create_activity(payload: ActivityCreate, user: dict = Depends(get_current_user)):
    agency_id = await _agency_id(user)
    db = Database.get()
    doc = {
        "id": str(uuid4()),
        "agency_id": agency_id,
        "title": payload.title.strip(),
        "kind": payload.kind,
        "status": "open",
        "due_at": payload.due_at,
        "related_client_id": payload.related_client_id,
        "related_property_id": payload.related_property_id,
        "notes": (payload.notes or "").strip() or None,
        "created_by": user["id"],
        "created_at": _now(),
        "updated_at": _now(),
        "completed_at": None,
    }
    await db.activities.insert_one(doc)
    return _strip(doc)


@router.patch("/{activity_id}")
async def update_activity(
    activity_id: str,
    payload: ActivityUpdate,
    user: dict = Depends(get_current_user),
):
    agency_id = await _agency_id(user)
    db = Database.get()
    existing = await db.activities.find_one(
        {"id": activity_id, "agency_id": agency_id}, {"_id": 0},
    )
    if not existing:
        raise HTTPException(status_code=404, detail="activity_not_found")
    updates = payload.model_dump(exclude_unset=True)
    updates["updated_at"] = _now()
    if updates.get("status") == "done" and existing.get("status") != "done":
        updates["completed_at"] = _now()
    if updates.get("status") == "open":
        updates["completed_at"] = None
    await db.activities.update_one(
        {"id": activity_id, "agency_id": agency_id}, {"$set": updates},
    )
    doc = await db.activities.find_one(
        {"id": activity_id, "agency_id": agency_id}, {"_id": 0},
    )
    return doc


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(activity_id: str, user: dict = Depends(get_current_user)):
    agency_id = await _agency_id(user)
    db = Database.get()
    r = await db.activities.delete_one({"id": activity_id, "agency_id": agency_id})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="activity_not_found")
    return None
