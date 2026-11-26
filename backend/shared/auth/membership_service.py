"""Membership helpers — B01-DEC-03 / B03-DEC-03: una sola Membership operativa attiva."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from shared.models.membership import MembershipInDB


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def end_active_memberships(db, user_id: str) -> int:
    """Mark all active memberships as ended (append-only history)."""
    now = _now()
    result = await db.memberships.update_many(
        {"user_id": user_id, "membership_status": "active"},
        {
            "$set": {
                "membership_status": "ended",
                "ended_at": now,
                "valid_to": now,
                "updated_at": now,
            }
        },
    )
    return int(getattr(result, "modified_count", 0) or 0)


async def end_membership_for_organization(db, user_id: str, organization_id: str) -> int:
    """End active membership(s) for one organization only (remove_member path)."""
    now = _now()
    result = await db.memberships.update_many(
        {
            "user_id": user_id,
            "organization_id": organization_id,
            "membership_status": "active",
        },
        {
            "$set": {
                "membership_status": "ended",
                "ended_at": now,
                "valid_to": now,
                "updated_at": now,
            }
        },
    )
    return int(getattr(result, "modified_count", 0) or 0)


async def activate_exclusive_membership(
    db,
    *,
    user_id: str,
    organization_id: str,
    operational_role: str,
) -> dict:
    """End any active membership, then create one active membership for organization_id.

    Also syncs legacy users.agency_ids / active_agency_id to a single org (Slice 1 dual-write).
    """
    await end_active_memberships(db, user_id)
    now = _now()
    membership = MembershipInDB(
        id=str(uuid4()),
        user_id=user_id,
        organization_id=organization_id,
        operational_role=operational_role,  # type: ignore[arg-type]
        membership_status="active",
        valid_from=now,
    )
    doc = membership.model_dump()
    await db.memberships.insert_one(doc)
    # Dual-write legacy SoT: agency pointers + users.role aligned to membership.
    # RBAC target = operational_role per membership; users.role stays in sync to avoid drift.
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "agency_ids": [organization_id],
                "active_agency_id": organization_id,
                "role": operational_role,
                "updated_at": now,
            }
        },
    )
    return doc


async def get_active_membership(db, user_id: str) -> Optional[dict]:
    return await db.memberships.find_one(
        {"user_id": user_id, "membership_status": "active"},
        {"_id": 0},
    )
