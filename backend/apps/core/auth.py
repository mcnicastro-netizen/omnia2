"""OMNIA — Auth routes (register, login, me, refresh, logout, forgot/reset password)."""
import os
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Request, Response, HTTPException, status, Header, Depends

from shared.db.connection import Database
from shared.utils.i18n import normalize_lang, t
from shared.auth.hashing import hash_password, verify_password
from shared.auth.jwt_tokens import (
    create_access_token,
    create_refresh_token,
    decode_token,
    ACCESS_TOKEN_MINUTES,
    REFRESH_TOKEN_DAYS,
)
from shared.auth.brute_force import (
    is_locked,
    register_failed_attempt,
    clear_attempts,
)
from shared.auth.dependencies import get_current_user
from shared.auth.session_store import store_refresh, is_refresh_valid, revoke_refresh
from shared.models.user import (
    UserInDB,
    UserPublic,
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from shared.email import send_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE_MAX_AGE = ACCESS_TOKEN_MINUTES * 60
REFRESH_COOKIE_MAX_AGE = REFRESH_TOKEN_DAYS * 24 * 3600

# L13 — secure cookies by default; COOKIE_SECURE=false only for local plain-HTTP dev
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"
COOKIE_SAMESITE = "none" if COOKIE_SECURE else "lax"


def _cookie_kwargs() -> dict:
    return dict(httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE, path="/")


def _set_auth_cookies(response: Response, user_id: str, email: str, role: str) -> str:
    """Set access+refresh cookies; returns the refresh token (for jti persistence)."""
    access = create_access_token(user_id, email, role)
    refresh = create_refresh_token(user_id)
    kw = _cookie_kwargs()
    response.set_cookie("access_token", access, max_age=ACCESS_COOKIE_MAX_AGE, **kw)
    response.set_cookie("refresh_token", refresh, max_age=REFRESH_COOKIE_MAX_AGE, **kw)
    return refresh


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


def _public(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "lang": user.get("lang", "it"),
        "agency_ids": user.get("agency_ids", []),
        "active_agency_id": user.get("active_agency_id"),
        "is_active": user.get("is_active", True),
        "account_type": user.get("account_type", "agent"),
        "intents": user.get("intents", []),
        "notification_channels": user.get("notification_channels", []),
        "phone": user.get("phone"),
        "group_id": user.get("group_id"),
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ---------------- REGISTER ----------------

@router.post("/register")
async def register(req: RegisterRequest, request: Request, response: Response,
                   accept_language: Optional[str] = Header(None)):
    lang = req.lang or normalize_lang(accept_language)
    db = Database.get()
    email = req.email.lower().strip()

    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail=t("auth.email_taken", lang=lang))

    # C1/S2 — public registration can never grant privileged roles.
    # agency_admin viene assegnato SOLO al completamento dell'onboarding (creazione agenzia);
    # agent SOLO via invito (accept-invite).
    _PUBLIC_ROLES = {"client", "student"}
    safe_role = req.role if req.role in _PUBLIC_ROLES else "client"

    user = UserInDB(
        email=email,
        password_hash=hash_password(req.password),
        name=req.name.strip(),
        role=safe_role,
        lang=lang,
        signup_domain_sovereignty_confirmed=bool(req.domain_sovereignty_confirmed),
        signup_existing_domain=(req.existing_domain or "").strip().lower() or None,
    )
    doc = user.model_dump()
    await db.users.insert_one(doc)

    _refresh_tok = _set_auth_cookies(response, user.id, email, user.role)
    await store_refresh(_refresh_tok)

    # Send welcome email (non-blocking; ignore failures)
    frontend = os.environ.get("FRONTEND_URL", "")
    try:
        await send_email(
            to=email,
            template="welcome",
            lang=lang,
            variables={"name": user.name, "role": user.role, "login_url": f"{frontend}/{lang}/login"},
        )
    except Exception as e:
        logger.warning("Welcome email failed: %s", e)

    return _public(doc)


# ---------------- LOGIN ----------------

@router.post("/login")
async def login(req: LoginRequest, request: Request, response: Response,
                accept_language: Optional[str] = Header(None)):
    lang = normalize_lang(accept_language)
    email = req.email.lower().strip()
    ip = _client_ip(request)

    if await is_locked(email, ip):
        raise HTTPException(status_code=429, detail=t("auth.too_many_attempts", lang=lang))

    db = Database.get()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user["password_hash"]):
        await register_failed_attempt(email, ip)
        raise HTTPException(status_code=401, detail=t("auth.invalid_credentials", lang=lang))

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail=t("auth.account_disabled", lang=lang))

    await clear_attempts(email, ip)
    _refresh_tok = _set_auth_cookies(response, user["id"], email, user["role"])
    await store_refresh(_refresh_tok)
    return _public(user)


# ---------------- ME ----------------

@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return _public(user)


# ---------------- REFRESH ----------------

@router.post("/refresh")
async def refresh(request: Request, response: Response,
                  accept_language: Optional[str] = Header(None)):
    lang = normalize_lang(accept_language)
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail=t("auth.no_refresh_token", lang=lang))

    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail=t("auth.invalid_token", lang=lang))

    # L12 — refresh valido solo se il jti non è stato revocato (logout)
    if not await is_refresh_valid(payload):
        raise HTTPException(status_code=401, detail=t("auth.invalid_token", lang=lang))

    db = Database.get()
    user = await db.users.find_one({"id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail=t("auth.user_not_found", lang=lang))
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail=t("auth.account_disabled", lang=lang))

    access = create_access_token(user["id"], user["email"], user["role"])
    response.set_cookie(
        "access_token", access,
        max_age=ACCESS_COOKIE_MAX_AGE,
        **_cookie_kwargs(),
    )
    return _public(user)


# ---------------- LOGOUT ----------------

@router.post("/logout")
async def logout(request: Request, response: Response):
    await revoke_refresh(request.cookies.get("refresh_token"))
    _clear_auth_cookies(response)
    return {"status": "ok"}


# ---------------- ACTIVE AGENCY (M5 multi-agency switcher) ----------------

@router.get("/my-agencies")
async def my_agencies(user: dict = Depends(get_current_user)):
    """List id+name of every agency the user belongs to (for the switcher)."""
    ids = user.get("agency_ids") or []
    if not ids:
        return {"items": [], "active_agency_id": None}
    db = Database.get()
    cursor = db.agencies.find({"id": {"$in": ids}}, {"_id": 0, "id": 1, "display_name": 1, "slug": 1})
    items = await cursor.to_list(length=100)
    from shared.auth.tenant import optional_agency_id
    return {"items": items, "active_agency_id": optional_agency_id(user)}


@router.post("/active-agency")
async def set_active_agency(payload: dict, user: dict = Depends(get_current_user)):
    agency_id = (payload or {}).get("agency_id")
    if not agency_id or agency_id not in (user.get("agency_ids") or []):
        raise HTTPException(status_code=403, detail="agency_not_in_memberships")
    db = Database.get()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"active_agency_id": agency_id, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"status": "ok", "active_agency_id": agency_id}


# ---------------- FORGOT PASSWORD ----------------

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest,
                          accept_language: Optional[str] = Header(None)):
    lang = normalize_lang(accept_language)
    email = req.email.lower().strip()
    db = Database.get()
    user = await db.users.find_one({"email": email})

    # Always 200 to prevent enumeration
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.password_reset_tokens.insert_one({
            "token": token,
            "user_id": user["id"],
            "expires_at": expires_at,
            "used": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        frontend = os.environ.get("FRONTEND_URL", "")
        reset_url = f"{frontend}/{lang}/reset-password?token={token}"
        logger.info("Password reset link generated for %s", email)
        try:
            await send_email(
                to=email,
                template="password_reset",
                lang=lang,
                variables={"name": user["name"], "reset_url": reset_url},
            )
        except Exception as e:
            logger.warning("Reset email failed: %s", e)

    return {"status": "ok", "message": t("auth.reset_link_sent", lang=lang)}


# ---------------- RESET PASSWORD ----------------

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest,
                         accept_language: Optional[str] = Header(None)):
    lang = normalize_lang(accept_language)
    db = Database.get()
    token_doc = await db.password_reset_tokens.find_one({"token": req.token})
    if not token_doc or token_doc.get("used"):
        raise HTTPException(status_code=400, detail=t("auth.invalid_or_used_token", lang=lang))

    expires_at = token_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= expires_at:
        raise HTTPException(status_code=400, detail=t("auth.token_expired", lang=lang))

    new_hash = hash_password(req.new_password)
    await db.users.update_one(
        {"id": token_doc["user_id"]},
        {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.password_reset_tokens.update_one(
        {"token": req.token}, {"$set": {"used": True}}
    )
    return {"status": "ok", "message": t("auth.password_updated", lang=lang)}
