"""D-160 — no premature B2B email; change-password clears must_change_password."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_agency_register_no_email(monkeypatch):
    from apps.core import auth as mod
    from shared.models.user import RegisterRequest

    send = AsyncMock()

    class DummyDB:
        users = MagicMock()
        users.find_one = AsyncMock(return_value=None)
        users.insert_one = AsyncMock()
        password_reset_tokens = MagicMock()
        password_reset_tokens.insert_one = AsyncMock()

    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: DummyDB()))
    monkeypatch.setattr(mod, "store_refresh", AsyncMock())
    monkeypatch.setattr(mod, "send_email", send)
    monkeypatch.setattr(mod, "_set_auth_cookies", lambda *a, **k: "refresh")
    monkeypatch.setattr(
        "shared.privacy.consent_log.log_consent", AsyncMock(), raising=False
    )

    req = RegisterRequest(
        email="agenzia@example.com",
        name="Titolare",
        role="client",
        password="TempPass99",
        domain_sovereignty_confirmed=True,
        preferred_plan="pro",
    )
    out = _run(mod.register(req, MagicMock(), MagicMock(), accept_language="it"))
    assert out.get("email") == "agenzia@example.com"
    assert out.get("must_change_password") is False
    send.assert_not_called()
    DummyDB.password_reset_tokens.insert_one.assert_not_called()


def test_change_password_ok(monkeypatch):
    from apps.core import auth as mod
    from shared.auth.hashing import hash_password

    user = {
        "id": "u1",
        "email": "a@x.it",
        "name": "A",
        "role": "agency_admin",
        "password_hash": hash_password("omnia_old_key_xxxx"),
        "must_change_password": True,
        "is_active": True,
        "lang": "it",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }

    class DB:
        users = MagicMock()
        users.find_one = AsyncMock(side_effect=[user, {**user, "must_change_password": False}])
        users.update_one = AsyncMock()

    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: DB()))
    body = mod.ChangePasswordBody(
        current_password="omnia_old_key_xxxx",
        new_password="NuovaPass99",
    )
    out = _run(mod.change_password(body, user))
    assert out.get("must_change_password") is False
    DB.users.update_one.assert_awaited()


def test_change_password_wrong_current(monkeypatch):
    from apps.core import auth as mod
    from shared.auth.hashing import hash_password

    user = {
        "id": "u1",
        "email": "a@x.it",
        "name": "A",
        "role": "agency_admin",
        "password_hash": hash_password("right"),
        "must_change_password": True,
        "is_active": True,
        "lang": "it",
    }

    class DB:
        users = MagicMock()
        users.find_one = AsyncMock(return_value=user)
        users.update_one = AsyncMock()

    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: DB()))
    body = mod.ChangePasswordBody(current_password="wrong", new_password="NuovaPass99")
    with pytest.raises(HTTPException) as ei:
        _run(mod.change_password(body, user))
    assert ei.value.status_code == 400
    assert ei.value.detail == "current_password_wrong"
