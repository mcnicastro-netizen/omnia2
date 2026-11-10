"""D-157: payment gate + credential issue on activate."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from apps.immoweb import founder_ops as fo


def test_activate_blocks_without_payment(monkeypatch):
    agency = {
        "id": "ag-pay-1",
        "slug": "demo",
        "display_name": "Demo",
        "owner_id": "u1",
        "activation_status": "pending",
        "kyc": {"status": "verified"},
        "preferred_plan_tier": "pro",
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
            db.subscriptions = _Coll()
            db.payment_transactions = type(
                "T",
                (),
                {"find_one": AsyncMock(return_value=None)},
            )()
            return db

    monkeypatch.setattr(fo, "Database", FakeDatabase)

    with patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(
            return_value={"ok": True, "agency_id": "ag-pay-1", "agency": agency}
        ),
    ), patch(
        "shared.auth.agency_credentials.agency_payment_ok",
        new=AsyncMock(return_value=False),
    ):
        with pytest.raises(HTTPException) as ei:
            asyncio.run(
                fo.ops_activate_agency(
                    fo.ActivateAgencyBody(
                        agency_id="ag-pay-1",
                        grant_plan=False,
                        send_email=False,
                        wipe_crm=False,
                        require_kyc_verified=True,
                        require_payment=True,
                        issue_login_credential=False,
                    ),
                    user={"id": "founder", "email": "f@x.it", "role": "super_admin"},
                )
            )
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "payment_required"


def test_issue_login_credential_sets_password(monkeypatch):
    from shared.auth import agency_credentials as ac
    from shared.auth.hashing import verify_password

    stored = {}

    class _Keys:
        async def insert_one(self, doc):
            stored["key_doc"] = doc

    class _Users:
        async def update_one(self, q, upd):
            stored["user_set"] = upd.get("$set") or {}

    class FakeDatabase:
        @staticmethod
        def get():
            db = type("DB", (), {})()
            db.api_keys = _Keys()
            db.users = _Users()
            return db

    monkeypatch.setattr(ac, "Database", FakeDatabase)
    out = asyncio.run(
        ac.issue_login_api_credential(
            user_id="u1", agency_id="a1", name="test", issued_by="ops"
        )
    )
    assert out["ok"] is True
    assert out["key"].startswith("omk_live_")
    assert stored["user_set"].get("must_change_password") is True
    assert verify_password(out["key"], stored["user_set"]["password_hash"])
