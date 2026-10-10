"""S5 — soldi onesti: self-serve ≠ Stripe; Legal no edge free."""
from __future__ import annotations

import asyncio
import os

import pytest
from fastapi import HTTPException


def test_self_serve_default_off(monkeypatch):
    monkeypatch.delenv("OMNIA_SELF_SERVE_ENABLED", raising=False)
    from shared.billing.self_serve import is_self_serve_enabled, guard_self_serve

    assert is_self_serve_enabled() is False
    with pytest.raises(HTTPException) as ei:
        guard_self_serve()
    assert ei.value.status_code == 503
    assert ei.value.detail["code"] == "self_serve_blocked"


def test_self_serve_on(monkeypatch):
    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "true")
    from shared.billing import self_serve as ss

    assert ss.is_self_serve_enabled() is True
    ss.guard_self_serve()  # no raise


def test_plans_exposes_self_serve_flag():
    from apps.billing import routes as br

    out = asyncio.run(br.list_plans())
    assert "self_serve_enabled" in out
    assert out["self_serve_enabled"] is (
        (os.environ.get("OMNIA_SELF_SERVE_ENABLED") or "").lower() == "true"
    )


def test_legal_edge_requires_agency():
    from apps.immoweb.al_legal import router as legal

    user = {
        "id": "u-edge",
        "role": "agent",
        "account_type": "b2b",
        "agency_ids": [],
        "active_agency_id": None,
    }

    async def _run():
        with pytest.raises(HTTPException) as ei:
            await legal._ensure_legal_payment(user)
        assert ei.value.status_code == 403
        assert ei.value.detail["code"] == "active_agency_required"

    asyncio.run(_run())


def test_legal_agency_included_no_debit():
    """D-119 — CRM con agency: incluso, zero crediti."""
    from apps.immoweb.al_legal import router as legal

    user = {
        "id": "u-agency",
        "role": "admin",
        "account_type": "b2b",
        "agency_ids": ["demo-agency-001"],
        "active_agency_id": "demo-agency-001",
    }

    async def _run():
        out = await legal._ensure_legal_payment(user)
        assert out["rail"] == "agency_included"
        assert out["credits_charged"] == 0
        assert out["agency_id"] == "demo-agency-001"

    asyncio.run(_run())
