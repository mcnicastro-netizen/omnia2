"""D-175 C6 — fulfillment credits/storage, claim, matching, no auto-alloc."""
from __future__ import annotations

from copy import deepcopy

import pytest

from shared.billing import checkout_fulfillment as cf
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run


def _seed_cc(db: FakeDB, *, cc_id="cc1", stripe_customer_id="cus_1", extra=0):
    db.commercial_customers = FakeColl()
    db.agencies = FakeColl()
    db.payment_transactions = FakeColl()
    db.properties = FakeColl()
    db.subscriptions = FakeColl()
    db.credit_lots = FakeColl()
    db.credit_allocations = FakeColl()
    db.cc_credit_wallets = FakeColl()
    db.cc_credit_ledger = FakeColl()
    db.commercial_customers.docs.append(
        {
            "id": cc_id,
            "legal_name": "ACME",
            "stripe_customer_id": stripe_customer_id,
            "storage_extra_gb": extra,
            "commercial_status": "active",
            "operational_status": "full",
        }
    )


def _tx(
    *,
    session_id="cs_1",
    kind="credits_topup",
    cc_id="cc1",
    agency_id=None,
    credits=400,
    storage_gb=100,
    stripe_customer_id="cus_1",
    paid=True,
):
    doc = {
        "session_id": session_id,
        "kind": kind,
        "commercial_customer_id": cc_id,
        "agency_id": agency_id,
        "stripe_customer_id": stripe_customer_id,
        "lookup_key": "pkg_400",
        "credits": credits,
        "storage_gb": storage_gb,
        "payment_status": "paid" if paid else "pending",
        "status": "completed" if paid else "initiated",
    }
    return doc


def test_c6_credits_agency_null_central_only():
    db = FakeDB()
    _seed_cc(db)
    db.payment_transactions.docs.append(_tx(agency_id=None, credits=400))

    out = _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    assert out.get("ok") is True
    assert out.get("applied") == "credits_topup"

    lots = db.credit_lots.docs
    assert len(lots) == 1
    assert lots[0]["commercial_customer_id"] == "cc1"
    assert lots[0]["original_qty"] == 400
    assert lots[0]["unallocated_qty"] == 400
    assert lots[0]["idempotency_key"] == "checkout:cs_1"
    assert db.credit_allocations.docs == []

    tx = db.payment_transactions.docs[0]
    assert tx.get("applied_at")
    assert tx.get("fulfillment_status") == cf.FULFILLMENT_APPLIED


def test_c6_credits_with_agency_no_auto_allocate():
    db = FakeDB()
    _seed_cc(db)
    db.agencies.docs.append({"id": "ag1", "commercial_customer_id": "cc1"})
    db.payment_transactions.docs.append(_tx(agency_id="ag1", credits=200))

    _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    assert len(db.credit_lots.docs) == 1
    assert db.credit_allocations.docs == []


def test_c6_credits_duplicate_idempotent():
    db = FakeDB()
    _seed_cc(db)
    db.payment_transactions.docs.append(_tx(credits=100))

    _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    assert len(db.credit_lots.docs) == 1


def test_c6_credits_cc_missing_error():
    db = FakeDB()
    _seed_cc(db)
    db.payment_transactions.docs.append(_tx(cc_id="missing_cc"))

    out = _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    assert out.get("ok") is False
    assert "commercial_customer_not_found" in (out.get("error") or "")
    assert db.credit_lots.docs == []
    assert not db.payment_transactions.docs[0].get("applied_at")
    assert db.payment_transactions.docs[0].get("fulfillment_status") == cf.FULFILLMENT_ERROR


def test_c6_agency_cc_mismatch_deny():
    db = FakeDB()
    _seed_cc(db)
    db.commercial_customers.docs.append(
        {
            "id": "cc_other",
            "stripe_customer_id": "cus_other",
            "storage_extra_gb": 0,
            "commercial_status": "active",
            "operational_status": "full",
        }
    )
    db.agencies.docs.append({"id": "ag_x", "commercial_customer_id": "cc_other"})
    db.payment_transactions.docs.append(_tx(cc_id="cc1", agency_id="ag_x"))

    out = _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    assert out.get("ok") is False
    assert "agency_cc_mismatch" in (out.get("error") or "")
    assert db.credit_lots.docs == []


def test_c6_stripe_customer_mismatch_deny():
    db = FakeDB()
    _seed_cc(db, stripe_customer_id="cus_1")
    db.payment_transactions.docs.append(_tx(stripe_customer_id="cus_OTHER"))

    out = _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    assert out.get("ok") is False
    assert "stripe_customer_mismatch" in (out.get("error") or "")


def test_c6_storage_increments_cc_not_agency():
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 0}
    )
    db.payment_transactions.docs.append(
        _tx(kind="storage_addon", agency_id=None, storage_gb=100)
    )

    out = _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    assert out.get("ok") is True
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100
    assert db.agencies.docs[0]["storage_extra_gb"] == 0


def test_c6_storage_duplicate_one_inc():
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.payment_transactions.docs.append(
        _tx(kind="storage_addon", storage_gb=100)
    )
    _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    _run(cf.apply_h4_session_side_effects(db, "cs_1"))
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100


def test_c6_routes_apply_delegates_h4(monkeypatch):
    """_apply_session_side_effects routes H4 kinds to C6 module."""
    import apps.billing.routes as routes
    import shared.billing.checkout_fulfillment as mod

    calls = []

    async def _fake(db, session_id, session_customer=None):
        calls.append(session_id)
        return {"ok": True}

    monkeypatch.setattr(mod, "apply_h4_session_side_effects", _fake)

    db = FakeDB()
    db.payment_transactions = FakeColl()
    db.payment_transactions.docs.append(_tx(kind="credits_topup"))

    class _DB:
        @staticmethod
        def get():
            return db

    monkeypatch.setattr(routes, "Database", _DB)
    _run(routes._apply_session_side_effects("cs_1"))
    assert calls == ["cs_1"]
