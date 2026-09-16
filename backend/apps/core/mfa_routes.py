"""OMNIA — MFA (TOTP) routes under /api/auth/mfa."""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.auth.hashing import verify_password
from shared.auth.jwt_tokens import decode_token, _get_secret, JWT_ALGORITHM
from shared.auth.mfa import (
    consume_backup_code,
    decrypt_secret,
    encrypt_secret,
    generate_backup_codes,
    generate_totp_secret,
    provisioning_uri,
    qr_png_data_uri,
    verify_totp,
)
from shared.auth.session_store import store_refresh
from shared.db.connection import Database
from shared.utils.i18n import normalize_lang, t
import jwt

logger = logging.getLogger("omnia.auth.mfa")
router = APIRouter(prefix="/mfa", tags=["auth-mfa"])

MFA_CHALLENGE_MINUTES = 5


class MfaCodeBody(BaseModel):
    code: str = Field(min_length=4, max_length=16)


class MfaEnableBody(BaseModel):
    code: str = Field(min_length=6, max_length=16)


class MfaDisableBody(BaseModel):
    code: str = Field(min_length=4, max_length=16)
    password: Optional[str] = None


class MfaVerifyLoginBody(BaseModel):
    mfa_token: str = Field(min_length=20, max_length=4000)
    code: str = Field(min_length=4, max_length=16)


def create_mfa_challenge_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "type": "mfa_challenge",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=MFA_CHALLENGE_MINUTES),
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/status")
async def mfa_status(user: dict = Depends(get_current_user)):
    return {
        "enabled": bool(user.get("mfa_enabled")),
        "backup_codes_remaining": len(user.get("mfa_backup_hashes") or []),
    }


@router.post("/setup")
async def mfa_setup(user: dict = Depends(get_current_user)):
    """Start MFA enrollment — returns QR + secret. Not enabled until /enable."""
    if user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="mfa_already_enabled")
    secret = generate_totp_secret()
    enc = encrypt_secret(secret)
    db = Database.get()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"mfa_pending_secret_enc": enc, "updated_at": _now()}},
    )
    uri = provisioning_uri(secret, user["email"])
    return {
        "secret": secret,
        "otpauth_url": uri,
        "qr_data_uri": qr_png_data_uri(uri),
    }


@router.post("/enable")
async def mfa_enable(body: MfaEnableBody, user: dict = Depends(get_current_user)):
    if user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="mfa_already_enabled")
    enc = user.get("mfa_pending_secret_enc")
    if not enc:
        raise HTTPException(status_code=400, detail="mfa_setup_required")
    try:
        secret = decrypt_secret(enc)
    except Exception:
        raise HTTPException(status_code=400, detail="mfa_secret_invalid")
    if not verify_totp(secret, body.code):
        raise HTTPException(status_code=400, detail="mfa_code_invalid")

    plain_codes, hashed = generate_backup_codes(8)
    db = Database.get()
    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "mfa_enabled": True,
                "mfa_secret_enc": enc,
                "mfa_backup_hashes": hashed,
                "mfa_pending_secret_enc": None,
                "mfa_enabled_at": _now(),
                "updated_at": _now(),
            }
        },
    )
    return {
        "enabled": True,
        "backup_codes": plain_codes,
        "hint": "Salva questi codici di recupero — non verranno più mostrati.",
    }


@router.post("/disable")
async def mfa_disable(body: MfaDisableBody, user: dict = Depends(get_current_user)):
    if not user.get("mfa_enabled"):
        return {"enabled": False}
    db = Database.get()
    full = await db.users.find_one({"id": user["id"]}) or user
    pw_hash = full.get("password_hash") or ""
    is_oauth = pw_hash.startswith("!oauth:")
    if not is_oauth:
        if not body.password or not verify_password(body.password, pw_hash):
            raise HTTPException(status_code=401, detail="invalid_password")
    try:
        secret = decrypt_secret(full.get("mfa_secret_enc") or user.get("mfa_secret_enc") or "")
    except Exception:
        raise HTTPException(status_code=400, detail="mfa_secret_invalid")

    ok = verify_totp(secret, body.code)
    if not ok:
        remaining = consume_backup_code(full.get("mfa_backup_hashes") or [], body.code)
        ok = remaining is not None
    if not ok:
        raise HTTPException(status_code=400, detail="mfa_code_invalid")

    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "mfa_enabled": False,
                "mfa_secret_enc": None,
                "mfa_backup_hashes": [],
                "mfa_pending_secret_enc": None,
                "updated_at": _now(),
            }
        },
    )
    return {"enabled": False}


@router.post("/verify")
async def mfa_verify_login(
    body: MfaVerifyLoginBody,
    request: Request,
    response: Response,
    accept_language: Optional[str] = Header(None),
):
    """Complete login after password/Google when MFA is required."""
    from apps.core.auth import _public, _set_auth_cookies

    lang = normalize_lang(accept_language)
    payload = decode_token(body.mfa_token)
    if not payload or payload.get("type") != "mfa_challenge":
        raise HTTPException(status_code=401, detail=t("auth.invalid_token", lang=lang))

    db = Database.get()
    user = await db.users.find_one({"id": payload["sub"]})
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail=t("auth.invalid_credentials", lang=lang))
    if not user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="mfa_not_enabled")

    try:
        secret = decrypt_secret(user.get("mfa_secret_enc") or "")
    except Exception:
        raise HTTPException(status_code=400, detail="mfa_secret_invalid")

    ok = verify_totp(secret, body.code)
    updates = {"updated_at": _now()}
    if not ok:
        remaining = consume_backup_code(user.get("mfa_backup_hashes") or [], body.code)
        if remaining is None:
            raise HTTPException(status_code=401, detail="mfa_code_invalid")
        updates["mfa_backup_hashes"] = remaining
        ok = True
    if not ok:
        raise HTTPException(status_code=401, detail="mfa_code_invalid")

    if len(updates) > 1:
        await db.users.update_one({"id": user["id"]}, {"$set": updates})

    refresh = _set_auth_cookies(response, user["id"], user["email"], user["role"])
    await store_refresh(refresh)
    return _public(user)
