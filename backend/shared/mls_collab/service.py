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


def require_collaboration_active(collab: dict) -> None:
    if collab.get("status") != "active":
        raise HTTPException(status_code=400, detail="collaboration_not_active")


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


def assert_mls_listing_shareable(prop: dict) -> None:
    """Same gates as mls.create_offer for MLS-visible listings."""
    if prop.get("visibility") == "private" or prop.get("mls_shared") is False:
        raise HTTPException(status_code=400, detail="property_not_shared_on_mls")


async def ensure_collaboration_from_offer(db, offer: dict, *, actor_agency_id: str) -> dict:
    """Idempotent: accepting an MLS offer links to property-scoped collaboration.

    Rules:
    - active/open → return existing (no duplicate)
    - pending → return existing WITHOUT auto-activating (owner consent still required
      unless actor is owner — offer accept by partner never silently activates pending)
    - revoked/rejected → allow creating a new active collaboration from this offer
    Never creates document requests or shares fascicolo.
    """
    base_q = {
        "property_id": offer["property_id"],
        "owner_agency_id": offer["from_agency_id"],
        "partner_agency_id": offer["to_agency_id"],
    }
    existing = await db.mls_collaborations.find_one(
        {**base_q, "status": {"$in": ["active", "open", "pending"]}},
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
        "document_request_auto": False,
        "notes": "Created from MLS offer accept — no automatic document share",
        "history": [
            {
                "at": now,
                "event": "created_from_offer",
                "offer_id": offer["id"],
                "by_agency_id": actor_agency_id,
            }
        ],
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

# Who may perform which transition (role relative to deal)
OWNER_TRANSITIONS = {
    "open": {"proposal_prepared", "lost", "archived"},
    "proposal_prepared": {"proposal_sent", "open", "lost", "archived"},
    "proposal_sent": {"lost", "archived"},  # owner awaits partner response
    "counter": {"proposal_sent", "lost", "archived"},
    "accepted": {"won", "lost", "archived"},
    "rejected": {"open", "archived"},
    "won": {"archived"},
    "lost": {"archived", "open"},
    "archived": set(),
}

PARTNER_TRANSITIONS = {
    "proposal_sent": {"accepted", "rejected", "counter"},
    "counter": set(),  # partner made counter; owner must respond by re-sending
}


def deal_role(deal: dict, agency_id: str) -> Optional[str]:
    if agency_id == deal.get("agency_id"):
        return "owner"
    if agency_id == deal.get("partner_agency_id"):
        return "partner"
    return None


def allowed_deal_transitions(deal: dict, agency_id: str) -> set[str]:
    role = deal_role(deal, agency_id)
    if role == "owner":
        return set(OWNER_TRANSITIONS.get(deal.get("status"), set()))
    if role == "partner":
        return set(PARTNER_TRANSITIONS.get(deal.get("status"), set()))
    return set()


def assert_deal_transition(current: str, new: str) -> None:
    allowed = DEAL_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_deal_transition", "from": current, "to": new},
        )


def assert_deal_transition_for_actor(deal: dict, agency_id: str, new: str) -> None:
    assert_deal_transition(deal["status"], new)
    allowed = allowed_deal_transitions(deal, agency_id)
    if new not in allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "deal_transition_forbidden",
                "from": deal["status"],
                "to": new,
                "role": deal_role(deal, agency_id),
            },
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


def chat_scope_key(
    collaboration_id: str,
    *,
    visit_id: Optional[str] = None,
    deal_id: Optional[str] = None,
) -> str:
    """Canonical exact scope — absent visit/deal never collide with scoped threads."""
    v = visit_id or "-"
    d = deal_id or "-"
    return f"{collaboration_id}|v:{v}|d:{d}"


def chat_thread_scope_query(
    collaboration_id: str,
    *,
    visit_id: Optional[str] = None,
    deal_id: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "collaboration_id": collaboration_id,
        "status": "open",
        "scope_key": chat_scope_key(
            collaboration_id, visit_id=visit_id, deal_id=deal_id
        ),
    }


async def assert_document_request_accessible(db, row: dict) -> dict:
    """Deny access when request or parent collaboration is revoked."""
    if row.get("status") == "revoked":
        raise HTTPException(status_code=403, detail="document_access_revoked")
    collab = await get_collaboration(db, row["collaboration_id"])
    if collab.get("status") == "revoked":
        raise HTTPException(status_code=403, detail="document_access_revoked")
    if collab.get("status") != "active":
        raise HTTPException(status_code=403, detail="collaboration_not_active")
    return collab
