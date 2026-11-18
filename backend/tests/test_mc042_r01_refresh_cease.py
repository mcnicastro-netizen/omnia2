"""MC-042 v2 / R-01 — nessun refresh/sessione autonoma post-cessazione."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from tests.test_b04_h2_main_admin import _DBProxy, _seed_user
from tests.test_b04ii_wallet_ledger import FakeDB, _run, _seed_cc_agency


def test_r01_login_gate_blocks_ceased_user():
    """Stesso gate usato da /auth/refresh (assert_user_login_allowed)."""
    from shared.billing.commercial_access import assert_user_login_allowed

    raw = FakeDB()
    _seed_cc_agency(raw, status="ceased")
    raw.commercial_customers.docs[0]["operational_status"] = "closed_readonly"
    _seed_user(raw, user_id="u1", role="agency_admin")
    db = _DBProxy(raw)
    user = {
        "id": "u1",
        "role": "agency_admin",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    with pytest.raises(HTTPException) as ei:
        _run(assert_user_login_allowed(db, user))
    assert ei.value.detail["error"] == "commercial_customer_ceased"


def test_r01_set_ceased_revokes_member_sessions(monkeypatch):
    from shared.billing import commercial_access as ca

    raw = FakeDB()
    _seed_cc_agency(raw, status="active")
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_other", role="agent")
    # membership
    raw.users.docs[0]["agency_ids"] = ["ag1"]
    raw.users.docs[1]["agency_ids"] = ["ag1"]
    _seed_user(raw, user_id="ops", role="super_admin")
    raw.users.docs[2]["agency_ids"] = ["ag1"]
    db = _DBProxy(raw)

    calls: list[str] = []

    async def fake_revoke(uid: str):
        calls.append(uid)
        return 1

    monkeypatch.setattr(
        "shared.auth.session_store.revoke_all_refresh",
        fake_revoke,
    )

    out = _run(
        ca.set_commercial_status(
            db,
            "cc1",
            commercial_status="ceased",
            actor_user_id="ops",
            reason="r01_test",
        )
    )
    assert out["commercial_status"] == "ceased"
    assert out["operational_status"] == "closed_readonly"
    assert "u_ma" in calls
    assert "u_other" in calls
    assert "ops" not in calls  # super_admin skipped


def test_r01_refresh_handler_invokes_login_gate(monkeypatch):
    """Il handler /auth/refresh deve chiamare assert_user_login_allowed."""
    from apps.core import auth as auth_mod
    from starlette.requests import Request
    from starlette.responses import Response

    called = {"n": 0}

    async def fake_assert(db, user):
        called["n"] += 1
        raise HTTPException(status_code=403, detail={"error": "commercial_customer_ceased"})

    monkeypatch.setattr(
        "shared.billing.commercial_access.assert_user_login_allowed",
        fake_assert,
    )
    monkeypatch.setattr(
        auth_mod,
        "decode_token",
        lambda t: {"type": "refresh", "sub": "u1", "jti": "j1"},
    )
    monkeypatch.setattr(auth_mod, "is_refresh_valid", AsyncMock(return_value=True))

    class _FakeUsers:
        async def find_one(self, *a, **k):
            return {
                "id": "u1",
                "email": "u1@x.it",
                "role": "agency_admin",
                "is_active": True,
                "agency_ids": ["ag1"],
                "active_agency_id": "ag1",
            }

    class _FakeDB:
        users = _FakeUsers()

    monkeypatch.setattr(auth_mod.Database, "get", staticmethod(lambda: _FakeDB()))

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/refresh",
        "headers": [(b"cookie", b"refresh_token=tok")],
        "query_string": b"",
    }
    req = Request(scope)
    # starlette Request.cookies needs more setup — set via monkeypatch on get
    monkeypatch.setattr(
        type(req),
        "cookies",
        property(lambda self: {"refresh_token": "tok"}),
    )
    resp = Response()
    with pytest.raises(HTTPException) as ei:
        _run(auth_mod.refresh(req, resp, accept_language="it"))
    assert ei.value.status_code == 403
    assert called["n"] == 1
