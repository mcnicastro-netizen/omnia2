"""OMNIA — Refresh-token server-side store (L12: revoca al logout)."""
from datetime import datetime, timezone

from shared.db.connection import Database
from shared.auth.jwt_tokens import decode_token


async def store_refresh(token: str) -> None:
    payload = decode_token(token) or {}
    jti = payload.get("jti")
    if not jti:
        return
    db = Database.get()
    now = datetime.now(timezone.utc)
    await db.refresh_tokens.insert_one({
        "jti": jti,
        "user_id": payload.get("sub"),
        "expires_at": payload.get("exp"),
        "created_at": now.isoformat(),
    })
    # opportunistic cleanup of expired records
    await db.refresh_tokens.delete_many({"expires_at": {"$lt": int(now.timestamp())}})


async def is_refresh_valid(payload: dict) -> bool:
    """A refresh token is valid only if its jti is still in the store (not revoked)."""
    jti = payload.get("jti")
    if not jti:
        return False
    db = Database.get()
    return await db.refresh_tokens.find_one({"jti": jti}, {"_id": 1}) is not None


async def revoke_refresh(token: str | None) -> None:
    if not token:
        return
    payload = decode_token(token) or {}
    jti = payload.get("jti")
    if not jti:
        return
    db = Database.get()
    await db.refresh_tokens.delete_one({"jti": jti})
