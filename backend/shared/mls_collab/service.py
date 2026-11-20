"""Shared helpers for MLS collaboration ops (Deal, Visit, Mini-dossier feedback, Chat).

Functional rules (Founder-binding):
- Accepting collaboration ≠ document request / fascicolo share.
- Mini-dossier = post-visit feedback/rating only (not document transfer).
- Document request = explicit separate flow.
- Contextual chat only within collaboration (+ visit / deal when present).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid4())


def agency_in_collaboration(collab: dict, agency_id: str) -> bool:
    return agency_id in (
        collab.get("owner_agency_id"),
        collab.get("partner_agency_id"),
    )


def require_agency_in_collaboration(collab: dict, agency_id: str) -> None:
    if not agency_in_collaboration(collab, agency_id):
        raise HTTPException(status_code=403, detail="collaboration_forbidden")


def counterpart_agency(collab: dict, agency_id: str) -> str:
    if agency_id == collab.get("owner_agency_id"):
        return collab["partner_agency_id"]
    if agency_id == collab.get("partner_agency_id"):
        return collab["owner_agency_id"]
    raise HTTPException(status_code=403, detail="collaboration_forbidden")


async def get_collaboration(db, collaboration_id: str) -> dict:
    row = await db.mls_collaborations.find_one({"id": collaboration_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="collaboration_not_found")
    return row


async def ensure_collaboration_from_offer(db, offer: dict, *, actor_agency_id: str) -> dict:
    """Idempotent: accepting an MLS offer creates/returns property-scoped collaboration.

    Does NOT create document requests or share fascicolo.
    """
    existing = await db.mls_collaborations.find_one(
        {
            "property_id": offer["property_id"],
            "owner_agency_id": offer["from_agency_id"],
            "partner_agency_id": offer["to_agency_id"],
            "status": {"$in": ["active", "open"]},
        },
        {"_id": 0},
    )
    if existing:
        return existing
    now = utc_now()
    doc = {
        "id": new_id(),
        "property_id": offer["property_id"],
        "owner_agency_id": offer["from_agency_id"],
        "partner_agency_id": offer["to_agency_id"],
        "mls_offer_id": offer["id"],
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "activated_by_agency_id": actor_agency_id,
        "document_request_auto": False,  # explicit invariant
        "notes": "Created from MLS offer accept — no automatic document share",
    }
    await db.mls_collaborations.insert_one(doc)
    doc.pop("_id", None)
    return doc


DEAL_STATUSES = frozenset(
    {
        "open",
        "proposal_prepared",
        "proposal_sent",
        "counter",
        "accepted",
        "rejected",
        "won",
        "lost",
        "archived",
    }
)

DEAL_TRANSITIONS: dict[str, set[str]] = {
    "open": {"proposal_prepared", "lost", "archived"},
    "proposal_prepared": {"proposal_sent", "open", "lost", "archived"},
    "proposal_sent": {"counter", "accepted", "rejected", "lost", "archived"},
    "counter": {"proposal_sent", "accepted", "rejected", "lost", "archived"},
    "accepted": {"won", "lost", "archived"},
    "rejected": {"open", "archived"},
    "won": {"archived"},
    "lost": {"archived", "open"},
    "archived": set(),
}


def assert_deal_transition(current: str, new: str) -> None:
    allowed = DEAL_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_deal_transition", "from": current, "to": new},
        )


VISIT_STATUSES = frozenset(
    {"requested", "proposed", "agreed", "completed", "cancelled"}
)


def strip_id(doc: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in doc.items() if k != "_id"}


async def get_visit(db, visit_id: str) -> dict:
    row = await db.mls_visits.find_one({"id": visit_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="visit_not_found")
    return row


async def get_deal(db, deal_id: str) -> dict:
    row = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="deal_not_found")
    return row


async def get_thread(db, thread_id: str) -> dict:
    row = await db.mls_chat_threads.find_one({"id": thread_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="chat_thread_not_found")
    return row


def require_thread_access(thread: dict, agency_id: str) -> None:
    agencies = thread.get("agency_ids") or []
    if agency_id not in agencies:
        raise HTTPException(status_code=403, detail="chat_forbidden")
    if thread.get("status") == "revoked":
        raise HTTPException(status_code=403, detail="chat_revoked")
