"""RBAC matrix — membership role SoT, invite edges, suspend, session revoke, cross-org."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _run(coro):
    return asyncio.run(coro)


def _db_base():
    db = MagicMock()
    db.memberships = MagicMock()
    db.users = MagicMock()
    db.security_events = MagicMock()
    db.security_events.insert_one = AsyncMock()
    db.agency_invites = MagicMock()
    db.agencies = MagicMock()
    return db


# ---------- set_operational_role ----------


def test_set_operational_role_dual_write_and_audit():
    from shared.auth import membership_service as mod

    db = _db_base()
    db.memberships.find_one = AsyncMock(
        return_value={
            "id": "m1",
            "user_id": "u1",
            "organization_id": "ag1",
            "operational_role": "agency_admin",
            "membership_status": "active",
        }
    )
    db.memberships.update_one = AsyncMock()
    db.users.update_one = AsyncMock()

    with patch(
        "shared.auth.session_store.revoke_all_sessions", AsyncMock(return_value=1)
    ) as rev:
        out = _run(
            mod.set_operational_role(
                db,
                user_id="u1",
                organization_id="ag1",
                operational_role="agent",
                actor_user_id="admin",
                actor_role="agency_admin",
            )
        )
    assert out["operational_role"] == "agent"
    db.users.update_one.assert_awaited()
    assert db.users.update_one.await_args[0][1]["$set"]["role"] == "agent"
    db.security_events.insert_one.assert_awaited()
    rev.assert_awaited()


def test_set_operational_role_missing_membership():
    from shared.auth import membership_service as mod

    db = _db_base()
    db.memberships.find_one = AsyncMock(return_value=None)
    with pytest.raises(LookupError):
        _run(
            mod.set_operational_role(
                db, user_id="u1", organization_id="ag1", operational_role="agent"
            )
        )


def test_set_operational_role_rejects_invalid():
    from shared.auth import membership_service as mod

    db = _db_base()
    with pytest.raises(ValueError):
        _run(
            mod.set_operational_role(
                db, user_id="u1", organization_id="ag1", operational_role="super_admin"
            )
        )


# ---------- suspend / unsuspend ----------


def test_suspend_membership_marks_inactive_and_revokes():
    from shared.auth import membership_service as mod

    db = _db_base()
    db.memberships.update_many = AsyncMock(return_value=MagicMock(modified_count=1))
    db.users.update_one = AsyncMock()
    with patch(
        "shared.auth.session_store.revoke_all_sessions", AsyncMock(return_value=2)
    ) as rev:
        n = _run(
            mod.suspend_membership(
                db,
                user_id="u1",
                organization_id="ag1",
                actor_user_id="admin",
                actor_role="agency_admin",
            )
        )
    assert n == 1
    assert db.users.update_one.await_args[0][1]["$set"]["is_active"] is False
    rev.assert_awaited()
    db.security_events.insert_one.assert_awaited()


def test_unsuspend_membership_restores_role():
    from shared.auth import membership_service as mod

    db = _db_base()
    db.memberships.update_many = AsyncMock(return_value=MagicMock(modified_count=1))
    db.users.update_one = AsyncMock()
    db.memberships.find_one = AsyncMock(
        side_effect=[
            None,  # end_active find unused
            {
                "user_id": "u1",
                "organization_id": "ag1",
                "operational_role": "branch_admin",
                "membership_status": "active",
            },
        ]
    )
    # end_active_memberships uses update_many; unsuspend also update_many
    with patch.object(mod, "end_active_memberships", AsyncMock(return_value=0)):
        with patch.object(
            mod,
            "get_active_membership",
            AsyncMock(
                return_value={
                    "operational_role": "branch_admin",
                    "organization_id": "ag1",
                }
            ),
        ):
            n = _run(
                mod.unsuspend_membership(
                    db, user_id="u1", organization_id="ag1", actor_user_id="admin"
                )
            )
    assert n == 1
    aset = db.users.update_one.await_args[0][1]["$set"]
    assert aset["is_active"] is True
    assert aset["role"] == "branch_admin"


# ---------- get_current_user suspended ----------


def test_get_current_user_blocks_suspended_membership():
    from shared.auth import dependencies as dep

    class DB:
        users = MagicMock()
        users.find_one = AsyncMock(
            return_value={
                "id": "u1",
                "email": "a@x.it",
                "role": "agent",
                "is_active": True,
                "agency_ids": ["ag1"],
                "active_agency_id": "ag1",
            }
        )

    fake_request = MagicMock()
    with (
        patch.object(dep, "get_token_from_request", AsyncMock(return_value="tok")),
        patch.object(dep, "decode_token", return_value={"type": "access", "sub": "u1"}),
        patch.object(dep.Database, "get", staticmethod(lambda: DB())),
        patch("shared.auth.session_store.assert_access_session", lambda u, p: None),
        patch(
            "shared.auth.membership_service.get_active_membership",
            AsyncMock(return_value=None),
        ),
        patch(
            "shared.auth.membership_service.get_suspended_membership",
            AsyncMock(return_value={"organization_id": "ag1", "membership_status": "suspended"}),
        ),
    ):
        with pytest.raises(HTTPException) as ei:
            _run(dep.get_current_user(fake_request))
    assert ei.value.status_code == 403
    assert ei.value.detail == "membership_suspended"


def test_get_current_user_single_org_membership_role():
    from shared.auth import dependencies as dep

    class DB:
        users = MagicMock()
        users.find_one = AsyncMock(
            return_value={
                "id": "u1",
                "email": "a@x.it",
                "role": "agent",
                "is_active": True,
                "agency_ids": ["ag1"],
                "active_agency_id": "ag1",
            }
        )

    fake_request = MagicMock()
    with (
        patch.object(dep, "get_token_from_request", AsyncMock(return_value="tok")),
        patch.object(dep, "decode_token", return_value={"type": "access", "sub": "u1"}),
        patch.object(dep.Database, "get", staticmethod(lambda: DB())),
        patch("shared.auth.session_store.assert_access_session", lambda u, p: None),
        patch(
            "shared.auth.membership_service.get_active_membership",
            AsyncMock(
                return_value={
                    "organization_id": "ag1",
                    "operational_role": "agency_admin",
                    "membership_status": "active",
                }
            ),
        ),
        patch("shared.auth.tenant.optional_agency_id", return_value="ag1"),
        patch("shared.db.tenant_guard.set_current_role"),
        patch("shared.db.connection.set_current_agency_id"),
        patch(
            "shared.billing.commercial_access.enforce_commercial_access",
            AsyncMock(),
        ),
    ):
        user = _run(dep.get_current_user(fake_request))
    assert user["role"] == "agency_admin"
    assert user["role_source"] == "membership"


# ---------- invite verify expired / revoked ----------


def test_verify_invite_revoked():
    from apps.immoweb import invites as inv

    db = _db_base()
    db.agency_invites.find_one = AsyncMock(
        return_value={
            "id": "i1",
            "token": "t",
            "status": "revoked",
            "agency_id": "ag1",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        }
    )
    with patch.object(inv.Database, "get_raw", staticmethod(lambda: db)):
        with pytest.raises(HTTPException) as ei:
            _run(inv.verify_invite("t"))
    assert ei.value.detail == "invite_used_or_revoked"


def test_verify_invite_expired():
    from apps.immoweb import invites as inv

    db = _db_base()
    db.agency_invites.find_one = AsyncMock(
        return_value={
            "id": "i1",
            "token": "t",
            "status": "pending",
            "agency_id": "ag1",
            "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        }
    )
    db.agency_invites.update_one = AsyncMock()
    with patch.object(inv.Database, "get_raw", staticmethod(lambda: db)):
        with pytest.raises(HTTPException) as ei:
            _run(inv.verify_invite("t"))
    assert ei.value.detail == "invite_expired"
    db.agency_invites.update_one.assert_awaited()


# ---------- change_member_role HTTP guards ----------


def test_change_member_role_rejects_branch_admin_actor():
    """branch_admin must not pass require_roles_exact for role changes."""
    from shared.auth.dependencies import require_roles_exact

    guard = require_roles_exact("agency_admin", "super_admin", "group_admin")

    class DB:
        users = MagicMock()
        users.find_one = AsyncMock(
            return_value={
                "id": "u",
                "role": "branch_admin",
                "is_active": True,
                "email_verified": True,
                "agency_ids": ["ag1"],
                "active_agency_id": "ag1",
            }
        )

    req = MagicMock()
    with (
        patch("shared.auth.dependencies.get_token_from_request", AsyncMock(return_value="tok")),
        patch("shared.auth.dependencies.decode_token", return_value={"type": "access", "sub": "u"}),
        patch("shared.auth.dependencies.Database.get", staticmethod(lambda: DB())),
        patch("shared.auth.session_store.assert_access_session", lambda u, p: None),
        patch(
            "shared.auth.membership_service.get_active_membership",
            AsyncMock(
                return_value={
                    "organization_id": "ag1",
                    "operational_role": "branch_admin",
                }
            ),
        ),
        patch("shared.auth.tenant.optional_agency_id", return_value="ag1"),
        patch("shared.db.tenant_guard.set_current_role"),
        patch("shared.db.connection.set_current_agency_id"),
        patch(
            "shared.billing.commercial_access.enforce_commercial_access",
            AsyncMock(),
        ),
    ):
        with pytest.raises(HTTPException) as ei:
            _run(guard(req))
    assert ei.value.status_code == 403


def test_change_member_role_handler_owner_locked():
    from apps.immoweb import agencies as ag
    from apps.immoweb.agencies import MemberRoleBody

    db = _db_base()
    db.users.find_one = AsyncMock(return_value={"id": "owner1", "role": "agency_admin"})
    db.agencies.find_one = AsyncMock(return_value={"owner_id": "owner1"})
    db.users.count_documents = AsyncMock(return_value=2)

    actor = {
        "id": "admin2",
        "role": "agency_admin",
        "active_agency_id": "ag1",
        "agency_ids": ["ag1"],
    }
    with (
        patch.object(ag.Database, "get", staticmethod(lambda: db)),
        patch.object(ag, "require_agency", return_value="ag1"),
    ):
        with pytest.raises(HTTPException) as ei:
            _run(
                ag.change_member_role(
                    "owner1",
                    MemberRoleBody(role="agent", reason="test downgrade"),
                    user=actor,
                )
            )
    assert ei.value.detail == "owner_role_locked"


def test_change_member_role_success_calls_set_role():
    from apps.immoweb import agencies as ag
    from apps.immoweb.agencies import MemberRoleBody

    db = _db_base()
    db.users.find_one = AsyncMock(return_value={"id": "u2", "role": "agent"})
    db.agencies.find_one = AsyncMock(return_value={"owner_id": "owner1"})

    actor = {
        "id": "admin1",
        "role": "agency_admin",
        "active_agency_id": "ag1",
        "agency_ids": ["ag1"],
    }
    with (
        patch.object(ag.Database, "get", staticmethod(lambda: db)),
        patch.object(ag, "require_agency", return_value="ag1"),
        patch(
            "shared.auth.membership_service.set_operational_role",
            AsyncMock(return_value={"operational_role": "branch_agent"}),
        ) as setter,
    ):
        out = _run(
            ag.change_member_role(
                "u2",
                MemberRoleBody(role="branch_agent", reason="promote"),
                user=actor,
            )
        )
    assert out["ok"] is True
    assert out["role"] == "branch_agent"
    setter.assert_awaited()


def test_suspend_member_handler():
    from apps.immoweb import agencies as ag

    db = _db_base()
    db.users.find_one = AsyncMock(return_value={"id": "u2"})
    db.agencies.find_one = AsyncMock(return_value={"owner_id": "owner1"})
    actor = {"id": "admin1", "role": "agency_admin", "active_agency_id": "ag1"}
    with (
        patch.object(ag.Database, "get", staticmethod(lambda: db)),
        patch.object(ag, "require_agency", return_value="ag1"),
        patch(
            "shared.auth.membership_service.suspend_membership",
            AsyncMock(return_value=1),
        ) as sus,
    ):
        out = _run(ag.suspend_member("u2", user=actor))
    assert out["status"] == "suspended"
    sus.assert_awaited()


def test_cross_org_member_not_found_on_role_change():
    """Manipolazione ID: member di altra org → 404."""
    from apps.immoweb import agencies as ag
    from apps.immoweb.agencies import MemberRoleBody

    db = _db_base()
    db.users.find_one = AsyncMock(return_value=None)
    actor = {"id": "admin1", "role": "agency_admin", "active_agency_id": "ag1"}
    with (
        patch.object(ag.Database, "get", staticmethod(lambda: db)),
        patch.object(ag, "require_agency", return_value="ag1"),
    ):
        with pytest.raises(HTTPException) as ei:
            _run(
                ag.change_member_role(
                    "foreign-user",
                    MemberRoleBody(role="agent"),
                    user=actor,
                )
            )
    assert ei.value.status_code == 404
