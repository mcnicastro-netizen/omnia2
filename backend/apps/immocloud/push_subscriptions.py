"""OMNIA — B2C Web Push subscription endpoints."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.notifications.web_push import (
    delete_subscription,
    ensure_vapid_keys,
    is_push_configured,
    save_subscription,
    vapid_public_key,
)

router = APIRouter(prefix="/me/push", tags=["cloud-push"])


class PushSubscribeBody(BaseModel):
    subscription: Dict[str, Any]
    user_agent: Optional[str] = Field(default="", max_length=400)


class PushUnsubscribeBody(BaseModel):
    endpoint: Optional[str] = Field(default=None, max_length=2000)


async def _ensure_b2c(user: dict) -> None:
    if user.get("account_type") != "b2c" or user.get("role") != "client":
        raise HTTPException(status_code=403, detail="b2c_account_required")


@router.get("/vapid-public-key")
async def get_vapid_key():
    """Public key for PushManager.subscribe (no auth)."""
    if not is_push_configured():
        ensure_vapid_keys()
    if not is_push_configured():
        raise HTTPException(status_code=503, detail="push_not_configured")
    return {"public_key": vapid_public_key(), "configured": True}


@router.post("/subscribe")
async def subscribe_push(
    payload: PushSubscribeBody,
    request: Request,
    user: dict = Depends(get_current_user),
):
    await _ensure_b2c(user)
    if not is_push_configured():
        ensure_vapid_keys()
    if not is_push_configured():
        raise HTTPException(status_code=503, detail="push_not_configured")
    ua = payload.user_agent or (request.headers.get("user-agent") or "")
    try:
        sid = await save_subscription(
            user_id=user["id"],
            subscription=payload.subscription,
            user_agent=ua,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_subscription")
    # Enable push channel on user prefs
    from shared.db.connection import Database
    db = Database.get()
    await db.users.update_one(
        {"id": user["id"]},
        {"$addToSet": {"notification_channels": "push"}},
    )
    return {"ok": True, "id": sid}


@router.post("/unsubscribe")
async def unsubscribe_push(
    payload: PushUnsubscribeBody,
    user: dict = Depends(get_current_user),
):
    await _ensure_b2c(user)
    n = await delete_subscription(user_id=user["id"], endpoint=payload.endpoint)
    return {"ok": True, "deleted": n}
