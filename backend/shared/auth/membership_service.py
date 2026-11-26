"""Membership helpers — B01-DEC-03 / B03-DEC-03: una sola Membership operativa attiva."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from shared.models.membership import MembershipInDB

OPERATIONAL_ROLES = frozenset(
    {"agency_admin", "agent", "branch_admin", "branch_agent", "group_admin"}
)


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
    actor_user_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    reason: str = "membership_activate",
) -> dict:
    """End any active membership, then create one active membership for organization_id.

    Also syncs legacy users.agency_ids / active_agency_id / users.role (dual-write).
    """
    if operational_role not in OPERATIONAL_ROLES:
        raise ValueError(f"invalid_operational_role:{operational_role}")

    prev = await get_active_membership(db, user_id)
    prev_role = (prev or {}).get("operational_role")
    prev_org = (prev or {}).get("organization_id")

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

    from shared.auth.security_audit import record_security_event

    await record_security_event(
        db,
        event="membership_activated",
        actor_user_id=actor_user_id or user_id,
        actor_role=actor_role,
        target_user_id=user_id,
        organization_id=organization_id,
        detail={
            "reason": reason,
            "operational_role": operational_role,
            "previous_role": prev_role,
            "previous_organization_id": prev_org,
        },
    )
    return doc


async def set_operational_role(
    db,
    *,
    user_id: str,
    organization_id: str,
    operational_role: str,
    actor_user_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    reason: str = "role_change",
    revoke_sessions: bool = True,
) -> dict:
    """Change role on the active membership for organization_id + dual-write users.role.

    Revokes all sessions by default (B14) so privilege changes take effect immediately.
    """
    if operational_role not in OPERATIONAL_ROLES:
        raise ValueError(f"invalid_operational_role:{operational_role}")

    mem = await db.memberships.find_one(
        {
            "user_id": user_id,
            "organization_id": organization_id,
            "membership_status": "active",
        },
        {"_id": 0},
    )
    if not mem:
        raise LookupError("active_membership_not_found")

    prev_role = mem.get("operational_role")
    now = _now()
    await db.memberships.update_one(
        {"id": mem["id"]},
        {"$set": {"operational_role": operational_role, "updated_at": now}},
    )
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": operational_role, "updated_at": now}},
    )

    from shared.auth.security_audit import record_security_event

    await record_security_event(
        db,
        event="role_changed",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target_user_id=user_id,
        organization_id=organization_id,
        detail={
            "reason": reason,
            "previous_role": prev_role,
            "new_role": operational_role,
            "sessions_revoked": bool(revoke_sessions),
        },
    )

    if revoke_sessions and prev_role != operational_role:
        from shared.auth.session_store import revoke_all_sessions

        await revoke_all_sessions(user_id, reason=f"role_change:{prev_role}->{operational_role}")

    updated = {**mem, "operational_role": operational_role, "updated_at": now}
    return updated


async def suspend_membership(
    db,
    *,
    user_id: str,
    organization_id: str,
    actor_user_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    reason: str = "membership_suspend",
) -> int:
    """Suspend active membership for org; mark user inactive; revoke sessions."""
    now = _now()
    result = await db.memberships.update_many(
        {
            "user_id": user_id,
            "organization_id": organization_id,
            "membership_status": "active",
        },
        {
            "$set": {
                "membership_status": "suspended",
                "updated_at": now,
                "suspended_at": now,
                "suspend_reason": reason,
            }
        },
    )
    modified = int(getattr(result, "modified_count", 0) or 0)
    if modified:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"is_active": False, "updated_at": now}},
        )
        from shared.auth.security_audit import record_security_event
        from shared.auth.session_store import revoke_all_sessions

        await record_security_event(
            db,
            event="membership_suspended",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target_user_id=user_id,
            organization_id=organization_id,
            detail={"reason": reason},
        )
        await revoke_all_sessions(user_id, reason="membership_suspend")
    return modified


async def unsuspend_membership(
    db,
    *,
    user_id: str,
    organization_id: str,
    actor_user_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    reason: str = "membership_unsuspend",
) -> int:
    """Reactivate a suspended membership and re-enable the user account."""
    now = _now()
    # Ensure exclusive: end any other active memberships first.
    await end_active_memberships(db, user_id)
    result = await db.memberships.update_many(
        {
            "user_id": user_id,
            "organization_id": organization_id,
            "membership_status": "suspended",
        },
        {
            "$set": {
                "membership_status": "active",
                "updated_at": now,
                "unsuspended_at": now,
            },
            "$unset": {"suspend_reason": "", "suspended_at": ""},
        },
    )
    modified = int(getattr(result, "modified_count", 0) or 0)
    if modified:
        mem = await get_active_membership(db, user_id)
        op_role = (mem or {}).get("operational_role") or "agent"
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "is_active": True,
                    "agency_ids": [organization_id],
                    "active_agency_id": organization_id,
                    "role": op_role,
                    "updated_at": now,
                }
            },
        )
        from shared.auth.security_audit import record_security_event

        await record_security_event(
            db,
            event="membership_unsuspended",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target_user_id=user_id,
            organization_id=organization_id,
            detail={"reason": reason, "operational_role": op_role},
        )
    return modified


async def get_active_membership(db, user_id: str) -> Optional[dict]:
    return await db.memberships.find_one(
        {"user_id": user_id, "membership_status": "active"},
        {"_id": 0},
    )


async def get_suspended_membership(db, user_id: str) -> Optional[dict]:
    return await db.memberships.find_one(
        {"user_id": user_id, "membership_status": "suspended"},
        {"_id": 0},
    )
