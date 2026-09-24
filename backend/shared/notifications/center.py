"""OMNIA — In-app notification center helpers (A-017).

Persists per-user inbox rows in Mongo `notifications`.
Email prefs (A-021) remain orthogonal: in-app always records; email still gated.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from shared.db.connection import Database

logger = logging.getLogger("omnia.notifications")

# Stable type keys used by UI + emitters
TYPE_LEAD_NEW = "lead_new"
TYPE_INVITE_ACCEPTED = "invite_accepted"
TYPE_SAVED_SEARCH = "saved_search_match"
TYPE_MATCH_NEW = "match_new"  # reserved (matches are on-read; no emitter v1)
TYPE_FAVORITE_DROP = "favorite_price_drop"
TYPE_FAVORITE_ENDED = "favorite_listing_ended"  # D-093 / A-030 sold|rented|withdrawn
TYPE_LISTING_INQUIRY = "listing_inquiry"  # B2C private seller contact form

KNOWN_TYPES = (
    TYPE_LEAD_NEW,
    TYPE_INVITE_ACCEPTED,
    TYPE_SAVED_SEARCH,
    TYPE_MATCH_NEW,
    TYPE_FAVORITE_DROP,
    TYPE_FAVORITE_ENDED,
    TYPE_LISTING_INQUIRY,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def create_notification(
    *,
    user_id: str,
    type: str,
    title: str,
    body: str = "",
    link: Optional[str] = None,
    agency_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Insert one inbox notification for `user_id`. Never raises to callers."""
    if not user_id:
        return {}
    doc = {
        "id": str(uuid4()),
        "user_id": user_id,
        "agency_id": agency_id,
        "type": type if type in KNOWN_TYPES else type,
        "title": (title or "").strip()[:200],
        "body": (body or "").strip()[:1000],
        "link": link,
        "meta": meta or {},
        "read": False,
        "created_at": _now_iso(),
        "read_at": None,
    }
    try:
        db = Database.get()
        await db.notifications.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    except Exception as e:  # noqa: BLE001 — never break business flow
        logger.warning("create_notification failed user=%s type=%s: %s", user_id, type, e)
        return {}


async def notify_users(
    user_ids: Iterable[str],
    *,
    type: str,
    title: str,
    body: str = "",
    link: Optional[str] = None,
    agency_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> int:
    """Notify unique user ids. Returns count of successful inserts."""
    seen = set()
    n = 0
    for uid in user_ids:
        if not uid or uid in seen:
            continue
        seen.add(uid)
        doc = await create_notification(
            user_id=uid,
            type=type,
            title=title,
            body=body,
            link=link,
            agency_id=agency_id,
            meta=meta,
        )
        if doc:
            n += 1
    return n


async def resolve_agency_owner_and_admins(agency_id: str) -> List[str]:
    """Owner + agency_admin / branch_admin / group_admin members of the agency."""
    if not agency_id:
        return []
    db = Database.get()
    ids: List[str] = []
    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0, "owner_id": 1})
    if agency and agency.get("owner_id"):
        ids.append(agency["owner_id"])
    cursor = db.users.find(
        {
            "agency_ids": agency_id,
            "is_active": {"$ne": False},
            "role": {"$in": ["agency_admin", "branch_admin", "group_admin", "super_admin"]},
        },
        {"_id": 0, "id": 1},
    )
    async for u in cursor:
        if u.get("id"):
            ids.append(u["id"])
    # unique preserve order
    out: List[str] = []
    seen = set()
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


async def resolve_lead_recipients(
    agency_id: str,
    listing_agent_id: Optional[str] = None,
) -> List[str]:
    """Prefer listing agent; always include owner/admins so inbox is never empty."""
    recipients: List[str] = []
    if listing_agent_id:
        recipients.append(listing_agent_id)
    admins = await resolve_agency_owner_and_admins(agency_id)
    recipients.extend(admins)
    out: List[str] = []
    seen = set()
    for i in recipients:
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


def serialize_notification(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "type": doc.get("type"),
        "title": doc.get("title"),
        "body": doc.get("body") or "",
        "link": doc.get("link"),
        "agency_id": doc.get("agency_id"),
        "meta": doc.get("meta") or {},
        "read": bool(doc.get("read")),
        "created_at": doc.get("created_at"),
        "read_at": doc.get("read_at"),
    }
