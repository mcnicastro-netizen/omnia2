"""OMNIA — ImmobilCloud B2C Auth (M3.S5 v1).

Public registration for B2C end-users (privati che vogliono vendere/affittare/
ricevere alert). Reuses the same JWT cookie auth as B2B but with role='client'
and account_type='b2c'. No agency_id assigned.
"""
import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field

from shared.auth.hashing import hash_password
from shared.auth.jwt_tokens import (
    create_access_token, create_refresh_token,
    ACCESS_TOKEN_MINUTES, REFRESH_TOKEN_DAYS,
)
from shared.db.connection import Database

logger = logging.getLogger("omnia.cloud_auth")
router = APIRouter(prefix="/auth", tags=["cloud-auth"])

Intent = Literal["sell", "rent_out", "get_alerts"]
Channel = Literal["email", "push"]


class CloudRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    intents: List[Intent] = Field(default_factory=list)
    notification_channels: List[Channel] = Field(default_factory=lambda: ["email"])
    lang: Optional[Literal["it", "en", "es"]] = "it"
    gdpr_consent: bool = False


@router.post("/register")
async def cloud_register(payload: CloudRegisterRequest, response: Response):
    """Register a B2C user. No email verification required for MVP — verification
    flag stays False until user clicks the link sent via Resend (handled by
    the existing /api/auth/verify-email flow if present)."""
    if not payload.gdpr_consent:
        raise HTTPException(status_code=400, detail="gdpr_consent_required")
    if not payload.intents:
        raise HTTPException(status_code=400, detail="at_least_one_intent_required")
    db = Database.get()
    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=409, detail="email_already_registered")

    now = datetime.now(timezone.utc).isoformat()
    user_id = str(uuid4())
    doc = {
        "id": user_id,
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "name": payload.name.strip(),
        "role": "client",
        "lang": payload.lang or "it",
        "agency_ids": [],
        "is_active": True,
        "account_type": "b2c",
        "intents": payload.intents,
        "notification_channels": payload.notification_channels or ["email"],
        "email_verified": False,
        "created_at": now,
        "updated_at": now,
    }
    await db.users.insert_one(doc)

    # Auto-login via cookie (same flow as standard /auth/login)
    try:
        from apps.core.auth import _cookie_kwargs, ACCESS_COOKIE_MAX_AGE, REFRESH_COOKIE_MAX_AGE
        from shared.auth.session_store import store_refresh
        access = create_access_token(user_id, doc["email"], "client")
        refresh = create_refresh_token(user_id)
        kw = _cookie_kwargs()
        response.set_cookie("access_token", access, max_age=ACCESS_COOKIE_MAX_AGE, **kw)
        response.set_cookie("refresh_token", refresh, max_age=REFRESH_COOKIE_MAX_AGE, **kw)
        await store_refresh(refresh)
    except Exception as e:
        logger.warning("cookie set failed (non-fatal): %s", e)

    return {
        "ok": True,
        "user": {
            "id": user_id, "email": doc["email"], "name": doc["name"],
            "role": "client", "account_type": "b2c",
            "intents": doc["intents"],
            "notification_channels": doc["notification_channels"],
        },
    }
