"""OMNIA — human-readable public codes for B2C clients and private listings.

Format (Idealista-like short refs, not UUIDs):
  Client:  OM-C-A7K2M9
  Listing: OM-L-X3F9Q2

Alphabet avoids ambiguous 0/O/1/I.
"""
from __future__ import annotations

import secrets
from typing import Optional

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_public_code(kind: str, *, length: int = 6) -> str:
    kind = (kind or "").strip().lower()
    prefix = {"client": "OM-C", "listing": "OM-L", "c": "OM-C", "l": "OM-L"}.get(kind, "OM-X")
    body = "".join(secrets.choice(_ALPHABET) for _ in range(max(4, min(length, 10))))
    return f"{prefix}-{body}"


async def ensure_unique_code(
    db,
    *,
    collection: str,
    field: str,
    kind: str,
    query_extra: Optional[dict] = None,
    attempts: int = 8,
) -> str:
    """Allocate a unique code in Mongo (retry on rare collision)."""
    extra = query_extra or {}
    for _ in range(attempts):
        code = generate_public_code(kind)
        hit = await db[collection].find_one({field: code, **extra}, {"_id": 1})
        if not hit:
            return code
    # Extremely unlikely fallback
    return generate_public_code(kind, length=8)


async def ensure_client_code(db, user_id: str) -> Optional[str]:
    if not user_id:
        return None
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "client_code": 1, "account_type": 1})
    if not user:
        return None
    existing = (user.get("client_code") or "").strip()
    if existing:
        return existing
    code = await ensure_unique_code(db, collection="users", field="client_code", kind="client")
    await db.users.update_one(
        {"id": user_id, "$or": [{"client_code": {"$exists": False}}, {"client_code": None}, {"client_code": ""}]},
        {"$set": {"client_code": code}},
    )
    refreshed = await db.users.find_one({"id": user_id}, {"_id": 0, "client_code": 1})
    return (refreshed or {}).get("client_code") or code


async def ensure_listing_code(db, listing_id: str) -> Optional[str]:
    if not listing_id:
        return None
    prop = await db.properties.find_one(
        {"id": listing_id},
        {"_id": 0, "reference_code": 1, "is_private_listing": 1},
    )
    if not prop:
        return None
    existing = (prop.get("reference_code") or "").strip()
    if existing:
        return existing
    code = await ensure_unique_code(db, collection="properties", field="reference_code", kind="listing")
    await db.properties.update_one(
        {
            "id": listing_id,
            "$or": [
                {"reference_code": {"$exists": False}},
                {"reference_code": None},
                {"reference_code": ""},
            ],
        },
        {"$set": {"reference_code": code}},
    )
    refreshed = await db.properties.find_one({"id": listing_id}, {"_id": 0, "reference_code": 1})
    return (refreshed or {}).get("reference_code") or code
