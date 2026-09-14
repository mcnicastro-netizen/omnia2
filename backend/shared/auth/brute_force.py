"""OMNIA — Brute force protection for /auth/login."""
from datetime import datetime, timezone, timedelta
from shared.db.connection import Database

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


async def _identifier(email: str, ip: str) -> str:
    return f"{(ip or 'unknown').lower()}:{email.lower().strip()}"


async def is_locked(email: str, ip: str) -> bool:
    db = Database.get()
    doc = await db.login_attempts.find_one({"identifier": await _identifier(email, ip)})
    if not doc:
        return False
    if doc.get("count", 0) < MAX_ATTEMPTS:
        return False
    last = doc.get("last_attempt")
    if not last:
        return False
    if isinstance(last, str):
        last = datetime.fromisoformat(last)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    unlock_at = last + timedelta(minutes=LOCKOUT_MINUTES)
    return datetime.now(timezone.utc) < unlock_at


async def register_failed_attempt(email: str, ip: str) -> None:
    db = Database.get()
    ident = await _identifier(email, ip)
    await db.login_attempts.update_one(
        {"identifier": ident},
        {
            "$inc": {"count": 1},
            "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()},
        },
        upsert=True,
    )


async def clear_attempts(email: str, ip: str) -> None:
    db = Database.get()
    await db.login_attempts.delete_one({"identifier": await _identifier(email, ip)})
