"""D-156: KYC gate Attiva + preferred plan."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from apps.immoweb import founder_ops as fo


def test_activate_blocks_without_kyc(monkeypatch):
    agency = {
        "id": "ag-kyc-1",
        "slug": "demo",
        "display_name": "Demo",
        "owner_id": "u1",
        "activation_status": "pending",
        "kyc": {"status": "incomplete", "documents": []},
        "preferred_plan_tier": "starter",
    }

    class _DB:
        async def find_one(self, *a, **k):
            return agency

        async def update_one(self, *a, **k):
            return None

    class FakeDatabase:
        @staticmethod
        def get():
            db = type("DB", (), {})()
            db.agencies = _DB()
            db.users = _DB()
            return db

    monkeypatch.setattr(fo, "Database", FakeDatabase)

    with patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(
            return_value={"ok": True, "agency_id": "ag-kyc-1", "agency": agency}
        ),
    ):
        with pytest.raises(HTTPException) as ei:
            asyncio.run(
                fo.ops_activate_agency(
                    fo.ActivateAgencyBody(
                        agency_id="ag-kyc-1",
                        grant_plan=False,
                        send_email=False,
                        wipe_crm=False,
                        require_kyc_verified=True,
                    ),
                    user={"id": "founder", "email": "f@x.it", "role": "super_admin"},
                )
            )
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "kyc_not_verified"


def test_activate_uses_preferred_plan(monkeypatch):
    agency = {
        "id": "ag-kyc-2",
        "slug": "demo2",
        "display_name": "Demo2",
        "owner_id": "u1",
        "activation_status": "pending",
        "kyc": {"status": "verified"},
        "preferred_plan_tier": "agency",
        "contact": {},
    }

    class _Coll:
        async def find_one(self, *a, **k):
            return agency

        async def update_one(self, *a, **k):
            return None

    class FakeDatabase:
        @staticmethod
        def get():
            db = type("DB", (), {})()
            db.agencies = _Coll()
            db.users = _Coll()
            return db

    monkeypatch.setattr(fo, "Database", FakeDatabase)

    grants = {}

    async def _grant(db, agency_id, *, tier, credits, reason, granted_by):
        grants["tier"] = tier
        return {"ok": True}

    with patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(
            return_value={"ok": True, "agency_id": "ag-kyc-2", "agency": agency}
        ),
    ), patch(
        "apps.immoweb.assisted_billing.grant_assisted_plan",
        new=_grant,
    ):
        out = asyncio.run(
            fo.ops_activate_agency(
                fo.ActivateAgencyBody(
                    agency_id="ag-kyc-2",
                    grant_plan=True,
                    tier=None,
                    send_email=False,
                    wipe_crm=False,
                    require_kyc_verified=True,
                    require_payment=False,
                    issue_login_credential=False,
                    credits=10,
                ),
                user={"id": "founder", "email": "f@x.it", "role": "super_admin"},
            )
        )
    assert grants.get("tier") == "agency"
    assert out.get("activation_status") == "active"
