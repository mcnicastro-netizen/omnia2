"""OMNIA — In-app notification inbox API (A-017).

Routes under `/api/notifications` (shared B2B CRM + B2C cloud).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from shared.notifications.center import serialize_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


class MarkReadBody(BaseModel):
    ids: Optional[list[str]] = Field(default=None, description="If omitted, mark all unread")


@router.get("")
async def list_notifications(
    limit: int = Query(30, ge=1, le=100),
    unread_only: bool = Query(False),
    user: dict = Depends(get_current_user),
):
    db = Database.get()
    flt: dict = {"user_id": user["id"]}
    if unread_only:
        flt["read"] = False
    cursor = (
        db.notifications.find(flt, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
    )
    items = [serialize_notification(d) async for d in cursor]
    unread = await db.notifications.count_documents({"user_id": user["id"], "read": False})
    return {"items": items, "unread_count": unread, "total_returned": len(items)}


@router.get("/unread-count")
async def unread_count(user: dict = Depends(get_current_user)):
    db = Database.get()
    n = await db.notifications.count_documents({"user_id": user["id"], "read": False})
    return {"unread_count": n}


@router.post("/{notification_id}/read")
async def mark_one_read(notification_id: str, user: dict = Depends(get_current_user)):
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    r = await db.notifications.update_one(
        {"id": notification_id, "user_id": user["id"], "read": False},
        {"$set": {"read": True, "read_at": now}},
    )
    if r.matched_count == 0:
        # idempotent: already read or missing
        exists = await db.notifications.find_one(
            {"id": notification_id, "user_id": user["id"]}, {"_id": 0, "id": 1}
        )
        if not exists:
            raise HTTPException(status_code=404, detail="notification_not_found")
    unread = await db.notifications.count_documents({"user_id": user["id"], "read": False})
    return {"ok": True, "unread_count": unread}


@router.post("/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    r = await db.notifications.update_many(
        {"user_id": user["id"], "read": False},
        {"$set": {"read": True, "read_at": now}},
    )
    return {"ok": True, "marked": r.modified_count, "unread_count": 0}
