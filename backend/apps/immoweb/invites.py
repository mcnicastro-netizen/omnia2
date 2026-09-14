"""OMNIA — Agency invitation routes (magic-link invite flow)."""
import os
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Response, Header

from shared.db.connection import Database
from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.hashing import hash_password
from shared.auth.jwt_tokens import (
    create_access_token,
    create_refresh_token,
    ACCESS_TOKEN_MINUTES,
    REFRESH_TOKEN_DAYS,
)
from shared.models.agency import (
    AgencyInviteInDB,
    InviteCreateRequest,
    InviteVerifyResponse,
    InviteAcceptRequest,
)
from shared.models.user import UserInDB
from shared.email import send_email
from shared.utils.i18n import normalize_lang

logger = logging.getLogger(__name__)
router = APIRouter(tags=["invites"])

INVITE_EXPIRY_DAYS = 7
ACCESS_COOKIE_MAX_AGE = ACCESS_TOKEN_MINUTES * 60
REFRESH_COOKIE_MAX_AGE = REFRESH_TOKEN_DAYS * 24 * 3600


# -------------------- CREATE INVITE (owner only) --------------------

@router.post("/agencies/me/invites", status_code=201)
async def create_invite(
    payload: InviteCreateRequest,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
    accept_language: Optional[str] = Header(None),
):
    lang = normalize_lang(accept_language)
    db = Database.get()

    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        raise HTTPException(status_code=400, detail="no_agency")
    agency_id = agency_ids[0]
    agency = await db.agencies.find_one({"id": agency_id})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")

    email = payload.email.lower().strip()

    # Block if user already in this agency
    existing_user = await db.users.find_one({"email": email})
    if existing_user and agency_id in (existing_user.get("agency_ids") or []):
        raise HTTPException(status_code=400, detail="user_already_member")

    # If a pending invite exists, refresh it instead of duplicating
    existing_invite = await db.agency_invites.find_one(
        {"agency_id": agency_id, "email": email, "status": "pending"}
    )
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS)).isoformat()

    if existing_invite:
        await db.agency_invites.update_one(
            {"id": existing_invite["id"]},
            {
                "$set": {
                    "token": token,
                    "expires_at": expires_at,
                    "name_hint": payload.name_hint,
                    "role": payload.role,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
        invite_id = existing_invite["id"]
    else:
        invite = AgencyInviteInDB(
            agency_id=agency_id,
            email=email,
            role=payload.role,
            token=token,
            expires_at=expires_at,
            invited_by=user["id"],
            name_hint=payload.name_hint,
        )
        doc = invite.model_dump()
        await db.agency_invites.insert_one(doc)
        invite_id = invite.id

    # Send magic-link email
    frontend = os.environ.get("FRONTEND_URL", "").rstrip("/")
    accept_url = f"{frontend}/{lang}/accept-invite#token={token}"
    try:
        await send_email(
            to=email,
            template="agency_invite",
            lang=lang,
            variables={
                "agency_name": agency.get("display_name", "OMNIA"),
                "inviter_name": user.get("name", "OMNIA"),
                "role_label": payload.role,
                "accept_url": accept_url,
                "expires_days": INVITE_EXPIRY_DAYS,
            },
        )
    except Exception as e:
        logger.warning("Invite email failed: %s", e)

    logger.info("Invite created: agency=%s email=%s id=%s", agency_id, email, invite_id)
    return {
        "id": invite_id,
        "email": email,
        "role": payload.role,
        "expires_at": expires_at,
        "status": "pending",
    }


# -------------------- LIST INVITES (owner only) --------------------

@router.get("/agencies/me/invites")
async def list_invites(
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        return []
    cursor = db.agency_invites.find(
        {"agency_id": agency_ids[0]},
        {"_id": 0, "token": 0},  # never leak token
    ).sort("created_at", -1)
    invites = await cursor.to_list(length=200)
    return invites


# -------------------- REVOKE INVITE --------------------

@router.delete("/agencies/me/invites/{invite_id}")
async def revoke_invite(
    invite_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        raise HTTPException(status_code=404, detail="no_agency")
    invite = await db.agency_invites.find_one({"id": invite_id})
    if not invite or invite["agency_id"] != agency_ids[0]:
        raise HTTPException(status_code=404, detail="invite_not_found")
    await db.agency_invites.update_one(
        {"id": invite_id},
        {"$set": {"status": "revoked", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"status": "ok"}


# -------------------- VERIFY TOKEN (public, by token) --------------------

@router.get("/invites/verify")
async def verify_invite(token: str):
    """Public endpoint: invitee visits accept page with ?token=... and we return invite info."""
    db = Database.get()
    invite = await db.agency_invites.find_one({"token": token})
    if not invite:
        raise HTTPException(status_code=404, detail="invite_invalid")
    if invite["status"] != "pending":
        raise HTTPException(status_code=400, detail="invite_used_or_revoked")

    expires_at = invite["expires_at"]
    if isinstance(expires_at, str):
        expires_at_dt = datetime.fromisoformat(expires_at)
    else:
        expires_at_dt = expires_at
    if expires_at_dt.tzinfo is None:
        expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= expires_at_dt:
        await db.agency_invites.update_one(
            {"id": invite["id"]}, {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=400, detail="invite_expired")

    agency = await db.agencies.find_one({"id": invite["agency_id"]})
    return InviteVerifyResponse(
        invite_id=invite["id"],
        agency_name=agency.get("display_name", "OMNIA") if agency else "OMNIA",
        role=invite["role"],
        email=invite["email"],
        expires_at=invite["expires_at"],
    )


# -------------------- ACCEPT INVITE (public, sets password) --------------------

@router.post("/invites/accept")
async def accept_invite(
    payload: InviteAcceptRequest,
    response: Response,
    accept_language: Optional[str] = Header(None),
):
    """Public: invitee sets name+password and is auto-logged in.
    Creates a new user or links existing user to the agency.
    """
    lang = normalize_lang(accept_language)
    db = Database.get()
    invite = await db.agency_invites.find_one({"token": payload.token})
    if not invite:
        raise HTTPException(status_code=404, detail="invite_invalid")
    if invite["status"] != "pending":
        raise HTTPException(status_code=400, detail="invite_used_or_revoked")

    expires_at = invite["expires_at"]
    if isinstance(expires_at, str):
        expires_at_dt = datetime.fromisoformat(expires_at)
    else:
        expires_at_dt = expires_at
    if expires_at_dt.tzinfo is None:
        expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= expires_at_dt:
        await db.agency_invites.update_one(
            {"id": invite["id"]}, {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=400, detail="invite_expired")

    email = invite["email"]
    agency_id = invite["agency_id"]
    role = invite["role"]

    user = await db.users.find_one({"email": email})
    if user:
        # Link existing user — update role only if it's an upgrade
        await db.users.update_one(
            {"id": user["id"]},
            {
                "$addToSet": {"agency_ids": agency_id},
                "$set": {
                    "name": payload.name.strip() or user["name"],
                    "password_hash": hash_password(payload.password),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    **({"role": role} if user["role"] == "client" else {}),
                },
            },
        )
        user_id = user["id"]
        user_role = role if user["role"] == "client" else user["role"]
    else:
        new_user = UserInDB(
            email=email,
            password_hash=hash_password(payload.password),
            name=payload.name.strip(),
            role=role,
            lang=lang,
            agency_ids=[agency_id],
        )
        await db.users.insert_one(new_user.model_dump())
        user_id = new_user.id
        user_role = role

    # Mark invite as accepted
    await db.agency_invites.update_one(
        {"id": invite["id"]},
        {
            "$set": {
                "status": "accepted",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    # Auto-login: set auth cookies
    access = create_access_token(user_id, email, user_role)
    refresh = create_refresh_token(user_id)
    cookie_kwargs = dict(httponly=True, secure=True, samesite="none", path="/")
    response.set_cookie("access_token", access, max_age=ACCESS_COOKIE_MAX_AGE, **cookie_kwargs)
    response.set_cookie("refresh_token", refresh, max_age=REFRESH_COOKIE_MAX_AGE, **cookie_kwargs)

    return {"status": "ok", "user_id": user_id, "role": user_role}
