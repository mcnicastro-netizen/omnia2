"""Slice 1 — CommercialCustomer / Membership / session revoke / email gate."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _run(coro):
    # asyncio.run() — get_event_loop() fails after another test closed the loop
    # (e.g. W3 multiprocess suite).
    return asyncio.run(coro)


# -------------------- B01 — VAT + CommercialCustomer --------------------


def test_normalize_vat_strips_it_prefix():
    from shared.models.commercial_customer import normalize_vat_number

    assert normalize_vat_number("IT 01234567890") == "01234567890"
    assert normalize_vat_number("01234567890") == "01234567890"
    assert normalize_vat_number("it.01-234.567.890") == "01234567890"


def test_get_or_create_commercial_customer_reuses(monkeypatch):
    from shared.auth import commercial_customer_service as mod

    existing = {
        "id": "cc1",
        "country_code": "IT",
        "vat_number_normalized": "01234567890",
        "legal_name": "Agenzia Demo SRL",
        "customer_status": "active",
    }

    class DB:
        commercial_customers = MagicMock()
        commercial_customers.find_one = AsyncMock(return_value=existing)
        commercial_customers.insert_one = AsyncMock()

    out = _run(
        mod.get_or_create_commercial_customer(
            DB(),
            vat_number="IT01234567890",
            legal_name="Agenzia Demo SRL",
            country_code="IT",
        )
    )
    assert out["id"] == "cc1"
    DB.commercial_customers.insert_one.assert_not_called()


def test_get_or_create_commercial_customer_requires_vat():
    from shared.auth import commercial_customer_service as mod

    class DB:
        commercial_customers = MagicMock()
        commercial_customers.find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as ei:
        _run(
            mod.get_or_create_commercial_customer(
                DB(), vat_number="  ", legal_name="X", country_code="IT"
            )
        )
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "vat_required"


def test_activate_exclusive_membership_ends_previous():
    from shared.auth import membership_service as mod

    class DB:
        memberships = MagicMock()
        memberships.update_many = AsyncMock(return_value=MagicMock(modified_count=1))
        memberships.insert_one = AsyncMock()
        memberships.find_one = AsyncMock(return_value=None)
        users = MagicMock()
        users.update_one = AsyncMock()

    doc = _run(
        mod.activate_exclusive_membership(
            DB(),
            user_id="u1",
            organization_id="ag-new",
            operational_role="agent",
        )
    )
    assert doc["organization_id"] == "ag-new"
    assert doc["membership_status"] == "active"
    DB.memberships.update_many.assert_awaited()
    DB.users.update_one.assert_awaited()
    # dual-write: agency_ids replaced with single org
    call_kwargs = DB.users.update_one.await_args
    assert call_kwargs[0][1]["$set"]["agency_ids"] == ["ag-new"]
    assert call_kwargs[0][1]["$set"]["active_agency_id"] == "ag-new"


# -------------------- B03-DEC-02 — revoke sessions --------------------


def test_revoke_all_refresh_deletes_by_user():
    from shared.auth import session_store as mod

    class DB:
        users = MagicMock()
        users.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        refresh_tokens = MagicMock()
        refresh_tokens.delete_many = AsyncMock(return_value=MagicMock(deleted_count=3))

    with patch.object(mod.Database, "get", staticmethod(lambda: DB())):
        n = _run(mod.revoke_all_refresh("u1"))
    assert n == 3
    DB.refresh_tokens.delete_many.assert_awaited_with({"user_id": "u1"})
    # B14 — also clears active_session_ids / bumps epoch
    assert DB.users.update_one.await_count == 1
    args, _kwargs = DB.users.update_one.await_args
    assert args[0] == {"id": "u1"}
    assert args[1]["$set"]["active_session_ids"] == []
    assert args[1]["$inc"]["session_epoch"] == 1


def test_change_password_revokes_all_sessions(monkeypatch):
    from apps.core import auth as mod
    from shared.auth.hashing import hash_password

    user = {
        "id": "u1",
        "email": "a@x.it",
        "name": "A",
        "role": "agency_admin",
        "password_hash": hash_password("OldPass99"),
        "must_change_password": True,
        "is_active": True,
        "lang": "it",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }

    class DB:
        users = MagicMock()
        users.find_one = AsyncMock(
            side_effect=[user, {**user, "must_change_password": False}]
        )
        users.update_one = AsyncMock()

    revoke = AsyncMock(return_value=2)
    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: DB()))
    monkeypatch.setattr(mod, "revoke_all_refresh", revoke)

    body = mod.ChangePasswordBody(
        current_password="OldPass99",
        new_password="NuovaPass99",
    )
    out = _run(mod.change_password(body, user))
    assert out.get("must_change_password") is False
    revoke.assert_awaited_once_with("u1")


def test_reset_password_revokes_all_sessions(monkeypatch):
    from apps.core import auth as mod
    from shared.models.user import ResetPasswordRequest

    token_doc = {
        "token": "tok-abc-def-ghi-jkl",
        "user_id": "u42",
        "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }

    class DB:
        password_reset_tokens = MagicMock()
        password_reset_tokens.find_one = AsyncMock(return_value=token_doc)
        password_reset_tokens.update_one = AsyncMock()
        users = MagicMock()
        users.update_one = AsyncMock()

    revoke = AsyncMock(return_value=1)
    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: DB()))
    monkeypatch.setattr(mod, "revoke_all_refresh", revoke)

    req = ResetPasswordRequest(token="tok-abc-def-ghi-jkl", new_password="NuovaPass99")
    out = _run(mod.reset_password(req, accept_language="it"))
    assert out["status"] == "ok"
    revoke.assert_awaited_once_with("u42")


# -------------------- B03-DEC-01 / D-174 — email gate --------------------


def test_email_gate_blocks_unverified_agency_admin():
    from shared.auth.email_gate import assert_email_verified_for_operations

    with pytest.raises(HTTPException) as ei:
        assert_email_verified_for_operations(
            {"role": "agency_admin", "email_verified": False}
        )
    assert ei.value.status_code == 403
    assert ei.value.detail["error"] == "email_not_verified"


def test_email_gate_allows_verified_and_super_admin():
    from shared.auth.email_gate import assert_email_verified_for_operations

    assert_email_verified_for_operations(
        {"role": "agency_admin", "email_verified": True}
    )
    assert_email_verified_for_operations(
        {"role": "super_admin", "email_verified": False}
    )
    assert_email_verified_for_operations(
        {"role": "client", "email_verified": False}
    )


def test_verify_email_sets_flag(monkeypatch):
    from apps.core import auth as mod

    token_doc = {
        "token": "verify-token-abcdefghijklmnopqrstuvwxyz",
        "user_id": "u9",
        "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }

    class DB:
        email_verification_tokens = MagicMock()
        email_verification_tokens.find_one = AsyncMock(return_value=token_doc)
        email_verification_tokens.update_one = AsyncMock()
        users = MagicMock()
        users.update_one = AsyncMock()

    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: DB()))
    req = mod.VerifyEmailRequest(token="verify-token-abcdefghijklmnopqrstuvwxyz")
    out = _run(mod.verify_email(req, accept_language="it"))
    assert out["email_verified"] is True
    set_arg = DB.users.update_one.await_args[0][1]["$set"]
    assert set_arg["email_verified"] is True


def test_require_roles_applies_email_gate(monkeypatch):
    from shared.auth import dependencies as dep

    async def fake_get_current_user(request):
        return {
            "id": "u1",
            "email": "a@x.it",
            "role": "agency_admin",
            "email_verified": False,
            "is_active": True,
        }

    monkeypatch.setattr(dep, "get_current_user", fake_get_current_user)
    guard = dep.require_roles("agency_admin")
    with pytest.raises(HTTPException) as ei:
        _run(guard(MagicMock()))
    assert ei.value.status_code == 403
    assert ei.value.detail["error"] == "email_not_verified"
