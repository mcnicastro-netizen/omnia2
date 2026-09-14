"""Google Sign-In (GIS ID token) for OMNIA.

Flow:
  1. FE loads Google Identity Services with our GOOGLE_CLIENT_ID
  2. User picks Google account → FE receives ID token (JWT)
  3. FE POSTs token to /api/auth/google
  4. Backend verifies token with Google, upserts user, sets session cookies

Env:
  GOOGLE_CLIENT_ID   — required to enable (Web client ID from Google Cloud Console)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from shared.auth.session_store import store_refresh
from shared.db.connection import Database
from shared.email import send_email
from shared.utils.i18n import normalize_lang, t

logger = logging.getLogger("omnia.auth.google")
router = APIRouter(tags=["auth-google"])

GOOGLE_CLIENT_ID = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
OAUTH_PASSWORD_SENTINEL = "!oauth:google"


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20, max_length=8000)
    lang: Optional[str] = None


def google_enabled() -> bool:
    return bool(GOOGLE_CLIENT_ID)


def _verify_google_id_token(credential: str) -> Dict[str, Any]:
    """Verify GIS ID token; raises HTTPException on failure."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="google_auth_not_configured")
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
    except ImportError as e:
        logger.exception("google-auth missing")
        raise HTTPException(status_code=503, detail="google_auth_library_missing") from e

    try:
        info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except ValueError as e:
        logger.warning("Google ID token invalid: %s", e)
        raise HTTPException(status_code=401, detail="google_token_invalid") from e

    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(status_code=401, detail="google_token_invalid_issuer")
    if not info.get("email"):
        raise HTTPException(status_code=400, detail="google_email_missing")
    if not info.get("email_verified"):
        raise HTTPException(status_code=400, detail="google_email_not_verified")
    return info


@router.get("/google/config")
async def google_config():
    """Public: FE uses this to show/hide the Google button."""
    return {
        "enabled": google_enabled(),
        "client_id": GOOGLE_CLIENT_ID if google_enabled() else None,
    }


@router.post("/google")
async def google_login(
    req: GoogleLoginRequest,
    request: Request,
    response: Response,
    accept_language: Optional[str] = Header(None),
):
    """Login / register with Google ID token; sets the same cookies as password login."""
    # Import cookie helpers from auth module (same package)
    from apps.core.auth import _public, _set_auth_cookies

    lang = normalize_lang(req.lang or accept_language)
    info = _verify_google_id_token(req.credential)

    email = str(info["email"]).lower().strip()
    google_sub = str(info.get("sub") or "")
    name = (info.get("name") or info.get("given_name") or email.split("@")[0] or "Utente").strip()[:120]
    picture = info.get("picture")

    db = Database.get()
    user = await db.users.find_one({"email": email})
    now = datetime.now(timezone.utc).isoformat()
    created = False

    if user is None:
        # New user via Google → public role "client" (same as register; agency via onboarding)
        doc = {
            "id": str(uuid4()),
            "email": email,
            "password_hash": f"{OAUTH_PASSWORD_SENTINEL}:{google_sub}",
            "name": name,
            "role": "client",
            "lang": lang,
            "agency_ids": [],
            "is_active": True,
            "account_type": "b2b",
            "intents": [],
            "notification_channels": ["email"],
            "email_verified": True,
            "auth_providers": ["google"],
            "google_sub": google_sub,
            "avatar_url": picture,
            "created_at": now,
            "updated_at": now,
        }
        await db.users.insert_one(doc)
        user = doc
        created = True
        frontend = os.environ.get("FRONTEND_URL", "")
        try:
            await send_email(
                to=email,
                template="welcome",
                lang=lang,
                variables={"name": name, "role": "client", "login_url": f"{frontend}/{lang}/login"},
            )
        except Exception as e:
            logger.warning("Welcome email (Google) failed: %s", e)
    else:
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail=t("auth.account_disabled", lang=lang))
        patch: Dict[str, Any] = {
            "updated_at": now,
            "email_verified": True,
        }
        providers = list(user.get("auth_providers") or [])
        if "google" not in providers:
            providers.append("google")
            patch["auth_providers"] = providers
        if google_sub and not user.get("google_sub"):
            patch["google_sub"] = google_sub
        if picture and not user.get("avatar_url"):
            patch["avatar_url"] = picture
        # If account was password-only, keep password; just link Google
        if (user.get("password_hash") or "").startswith(OAUTH_PASSWORD_SENTINEL) and google_sub:
            patch["password_hash"] = f"{OAUTH_PASSWORD_SENTINEL}:{google_sub}"
        if patch:
            await db.users.update_one({"id": user["id"]}, {"$set": patch})
            user = {**user, **patch}

    refresh = _set_auth_cookies(response, user["id"], email, user["role"])
    await store_refresh(refresh)
    out = _public(user)
    out["google_linked"] = True
    out["created"] = created
    return out
