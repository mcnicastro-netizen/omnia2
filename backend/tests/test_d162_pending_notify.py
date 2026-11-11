"""D-162 — agency_pending solo dopo KYC + pagamento."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


class _Agencies:
    def __init__(self, doc):
        self.doc = dict(doc)

    async def find_one(self, q, *a, **k):
        if q.get("id") == self.doc.get("id"):
            return dict(self.doc)
        return None

    async def update_one(self, q, upd, *a, **k):
        if "$set" in upd:
            self.doc.update(upd["$set"])
        return SimpleNamespace(modified_count=1)


class _Users:
    def __init__(self, user):
        self.user = dict(user)

    async def find_one(self, q, *a, **k):
        if q.get("id") == self.user.get("id"):
            return dict(self.user)
        return None


class _DB:
    def __init__(self, agency, user):
        self.agencies = _Agencies(agency)
        self.users = _Users(user)
        self.subscriptions = MagicMock()
        self.payment_transactions = MagicMock()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_pending_notify_skips_without_kyc():
    from shared.auth import agency_pending_notify as mod

    agency = {
        "id": "ag-1",
        "display_name": "Test",
        "activation_status": "pending",
        "owner_id": "u-1",
        "preferred_plan_tier": "pro",
        "kyc": {"checklist": {"visura_camerale": False, "id_titolare": False}, "documents": []},
    }
    user = {"id": "u-1", "email": "t@example.com", "name": "T", "lang": "it"}
    db = _DB(agency, user)

    out = _run(mod.maybe_send_agency_pending_ready(db, "ag-1"))
    assert out.get("skipped") == "kyc_incomplete"


def test_pending_notify_sends_when_ready(monkeypatch):
    from shared.auth import agency_pending_notify as mod
    import shared.auth.agency_credentials as creds

    agency = {
        "id": "ag-2",
        "display_name": "Test Ready",
        "activation_status": "pending",
        "owner_id": "u-2",
        "preferred_plan_tier": "pro",
        "kyc": {
            "checklist": {"visura_camerale": True, "id_titolare": True},
            "documents": [
                {"doc_type": "visura_camerale"},
                {"doc_type": "documento_identita"},
            ],
        },
    }
    user = {"id": "u-2", "email": "ready@example.com", "name": "Ready", "lang": "it"}
    db = _DB(agency, user)
    monkeypatch.setattr(creds, "agency_payment_ok", AsyncMock(return_value=True))

    send = AsyncMock(return_value={"id": "mock", "status": "mock"})
    monkeypatch.setitem(
        __import__("sys").modules,
        "shared.email.client",
        SimpleNamespace(send_email=send),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "shared.public_base",
        SimpleNamespace(get_public_base_url=lambda: "https://example.com"),
    )

    out = _run(mod.maybe_send_agency_pending_ready(db, "ag-2"))
    assert out.get("ok") is True
    assert out.get("status") == "mock"
    send.assert_awaited_once()
    assert db.agencies.doc.get("pending_notify_sent_at")

    # idempotent
    out2 = _run(mod.maybe_send_agency_pending_ready(db, "ag-2"))
    assert out2.get("skipped") == "already_sent"
    assert send.await_count == 1
