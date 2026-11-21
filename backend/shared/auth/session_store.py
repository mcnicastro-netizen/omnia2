"""OMNIA — Server-side session SoT (B03 / B14).

Access JWTs are HS256 and otherwise stateless. To honour immediate revocation
(logout, password change, security revoke, membership revoke, CC cease) we keep
``users.active_session_ids`` + ``users.session_epoch`` in MongoDB and embed
``sid`` / ``sv`` in every access token. Validation runs on the user document
already loaded by ``get_current_user`` (no extra round-trip). Refresh tokens
remain allowlisted by ``jti`` and must share the same ``sid``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status

from shared.auth.jwt_tokens import decode_token
from shared.db.connection import Database

MAX_ACTIVE_SESSIONS = 20


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def register_session(user_id: str) -> tuple[str, int]:
    """Register a new session id on the user. Returns (sid, session_epoch)."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="session_invalid"
        )
    db = Database.get()
    sid = str(uuid4())
    now = _now_iso()
    try:
        await db.users.update_one(
            {"id": user_id},
            {
                "$push": {
                    "active_session_ids": {
                        "$each": [sid],
                        "$slice": -MAX_ACTIVE_SESSIONS,
                    }
                },
                "$set": {"updated_at": now},
            },
        )
        # Ensure epoch field exists for legacy users (idempotent).
        await db.users.update_one(
            {"id": user_id, "session_epoch": {"$exists": False}},
            {"$set": {"session_epoch": 0}},
        )
        user = await db.users.find_one(
            {"id": user_id}, {"_id": 0, "session_epoch": 1, "active_session_ids": 1}
        )
    except Exception as exc:  # noqa: BLE001
        # Fail-closed: cannot prove session registration.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="session_store_unavailable",
        ) from exc
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found"
        )
    epoch = int(user.get("session_epoch") or 0)
    return sid, epoch


async def store_refresh(token: str) -> None:
    payload = decode_token(token) or {}
    jti = payload.get("jti")
    if not jti:
        return
    db = Database.get()
    now = datetime.now(timezone.utc)
    doc = {
        "jti": jti,
        "user_id": payload.get("sub"),
        "session_id": payload.get("sid"),
        "expires_at": payload.get("exp"),
        "created_at": now.isoformat(),
    }
    await db.refresh_tokens.insert_one(doc)
    await db.refresh_tokens.delete_many({"expires_at": {"$lt": int(now.timestamp())}})


async def is_refresh_valid(payload: dict) -> bool:
    """Refresh valid only if jti is stored AND session sid is still active."""
    jti = payload.get("jti")
    if not jti:
        return False
    try:
        db = Database.get()
        row = await db.refresh_tokens.find_one({"jti": jti}, {"_id": 1, "session_id": 1})
        if not row:
            return False
        sid = payload.get("sid") or row.get("session_id")
        uid = payload.get("sub")
        if not sid or not uid:
            # Legacy refresh without sid: reject (fail-closed after B14).
            return False
        user = await db.users.find_one(
            {"id": uid}, {"_id": 0, "active_session_ids": 1, "session_epoch": 1}
        )
        if not user:
            return False
        return sid in (user.get("active_session_ids") or [])
    except Exception:  # noqa: BLE001
        return False


async def revoke_refresh(token: str | None) -> None:
    """Revoke one refresh jti and its linked access session (logout current)."""
    if not token:
        return
    payload = decode_token(token) or {}
    jti = payload.get("jti")
    sid = payload.get("sid")
    uid = payload.get("sub")
    db = Database.get()
    if jti:
        await db.refresh_tokens.delete_one({"jti": jti})
    if uid and sid:
        await revoke_session(uid, sid, reason="logout")


async def revoke_session(
    user_id: str | None,
    session_id: str | None,
    *,
    reason: str = "logout",
) -> bool:
    """Revoke a single session (access + any refresh rows with that sid)."""
    if not user_id or not session_id:
        return False
    db = Database.get()
    now = _now_iso()
    try:
        res = await db.users.update_one(
            {"id": user_id},
            {
                "$pull": {"active_session_ids": session_id},
                "$set": {
                    "updated_at": now,
                    "last_session_revoke_reason": reason,
                    "last_session_revoke_at": now,
                },
            },
        )
        await db.refresh_tokens.delete_many(
            {"user_id": user_id, "session_id": session_id}
        )
        return bool(getattr(res, "modified_count", 0) or getattr(res, "matched_count", 0))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="session_store_unavailable",
        ) from exc


async def revoke_all_refresh(user_id: str | None) -> int:
    """B03-DEC-02 / B14 — invalidate ALL sessions (access + refresh).

    Clears ``active_session_ids``, bumps ``session_epoch`` (so any JWT with the
    old ``sv`` fails even if a stale sid lingered), and deletes refresh rows.
    """
    if not user_id:
        return 0
    return await revoke_all_sessions(user_id, reason="revoke_all")


async def revoke_all_sessions(
    user_id: str | None,
    *,
    reason: str = "revoke_all",
) -> int:
    if not user_id:
        return 0
    db = Database.get()
    now = _now_iso()
    user_err: Optional[Exception] = None
    try:
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "active_session_ids": [],
                    "updated_at": now,
                    "last_session_revoke_reason": reason,
                    "last_session_revoke_at": now,
                },
                "$inc": {"session_epoch": 1},
            },
        )
    except Exception as exc:  # noqa: BLE001
        user_err = exc
    try:
        result = await db.refresh_tokens.delete_many({"user_id": user_id})
        deleted = int(getattr(result, "deleted_count", 0) or 0)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="session_store_unavailable",
        ) from exc
    if user_err is not None and deleted == 0:
        # Neither session field nor refresh rows could be cleared.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="session_store_unavailable",
        ) from user_err
    return deleted


def assert_access_session(user: dict, payload: dict) -> None:
    """Validate access JWT against Mongo-backed session state (fail-closed).

    Called after the user document is loaded — no extra Mongo round-trip.
    """
    sid = payload.get("sid")
    if not sid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="session_invalid"
        )
    active = user.get("active_session_ids")
    if not isinstance(active, list) or sid not in active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="session_revoked"
        )
    if "sv" in payload:
        try:
            sv = int(payload.get("sv"))
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="session_invalid"
            ) from exc
        epoch = int(user.get("session_epoch") or 0)
        if sv != epoch:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="session_revoked"
            )


async def issue_auth_tokens(user_id: str, email: str, role: str) -> tuple[str, str]:
    """Open a session and return (access_jwt, refresh_jwt). Persists refresh jti."""
    from shared.auth.jwt_tokens import create_access_token, create_refresh_token

    try:
        sid, epoch = await register_session(user_id)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="session_store_unavailable",
        ) from exc
    access = create_access_token(
        user_id, email, role, session_id=sid, session_epoch=epoch
    )
    refresh = create_refresh_token(user_id, session_id=sid)
    await store_refresh(refresh)
    return access, refresh


async def mint_access_for_session(
    user: dict, *, session_id: str
) -> str:
    """Issue a new access JWT for an existing (still active) session — refresh path."""
    from shared.auth.jwt_tokens import create_access_token

    sid = session_id
    if not sid or sid not in (user.get("active_session_ids") or []):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="session_revoked"
        )
    epoch = int(user.get("session_epoch") or 0)
    return create_access_token(
        user["id"],
        user["email"],
        user["role"],
        session_id=sid,
        session_epoch=epoch,
    )
