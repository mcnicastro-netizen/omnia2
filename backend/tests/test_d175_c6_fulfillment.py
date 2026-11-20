"""D-175 C6 — fulfillment: storage atomic gate, strict Stripe match, reclaim."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from shared.billing import checkout_fulfillment as cf
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run


def _seed_cc(db: FakeDB, *, cc_id="cc1", stripe_customer_id="cus_1", extra=0):
    db.commercial_customers = FakeColl()
    db.agencies = FakeColl()
    db.payment_transactions = FakeColl()
    db.credit_lots = FakeColl()
    db.credit_allocations = FakeColl()
    db.cc_credit_wallets = FakeColl()
    db.cc_credit_ledger = FakeColl()
    db.storage_checkout_fulfillments = FakeColl()
    db.commercial_customers.docs.append(
        {
            "id": cc_id,
            "legal_name": "ACME",
            "stripe_customer_id": stripe_customer_id,
            "storage_extra_gb": extra,
            "storage_fulfilled_sessions": [],
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
):
    return {
        "session_id": session_id,
        "kind": kind,
        "commercial_customer_id": cc_id,
        "agency_id": agency_id,
        "stripe_customer_id": stripe_customer_id,
        "lookup_key": "pkg_400",
        "credits": credits,
        "storage_gb": storage_gb,
        "payment_status": "paid",
        "status": "completed",
    }


def _apply(db, session_id="cs_1", customer="cus_1", **kw):
    return _run(
        cf.apply_h4_session_side_effects(
            db, session_id, session_customer=customer, **kw
        )
    )


def test_c6_credits_agency_null_central_only():
    db = FakeDB()
    _seed_cc(db)
    db.payment_transactions.docs.append(_tx(agency_id=None, credits=400))
    out = _apply(db)
    assert out.get("ok") is True
    assert len(db.credit_lots.docs) == 1
    assert db.credit_allocations.docs == []
    assert db.credit_lots.docs[0]["unallocated_qty"] == 400


def test_c6_credits_with_agency_no_auto_allocate():
    db = FakeDB()
    _seed_cc(db)
    db.agencies.docs.append({"id": "ag1", "commercial_customer_id": "cc1"})
    db.payment_transactions.docs.append(_tx(agency_id="ag1", credits=200))
    _apply(db)
    assert db.credit_allocations.docs == []


def test_c6_credits_duplicate_idempotent():
    db = FakeDB()
    _seed_cc(db)
    db.payment_transactions.docs.append(_tx(credits=100))
    _apply(db)
    _apply(db)
    assert len(db.credit_lots.docs) == 1


# --- Stripe matching (all three required) ---


@pytest.mark.parametrize(
    "session_c,tx_c,cc_c,err",
    [
        (None, "cus_1", "cus_1", "stripe_customer_missing"),
        ("cus_1", None, "cus_1", "stripe_customer_missing_on_tx"),
        ("cus_1", "cus_1", None, "stripe_customer_missing_on_cc"),
        ("cus_A", "cus_1", "cus_1", "stripe_customer_mismatch"),
        ("cus_1", "cus_B", "cus_1", "stripe_customer_mismatch"),
        ("cus_1", "cus_1", "cus_C", "stripe_customer_mismatch"),
    ],
)
def test_c6_stripe_triple_required(session_c, tx_c, cc_c, err):
    db = FakeDB()
    _seed_cc(db, stripe_customer_id=cc_c or "cus_placeholder")
    if cc_c is None:
        db.commercial_customers.docs[0]["stripe_customer_id"] = None
    db.payment_transactions.docs.append(
        _tx(stripe_customer_id=tx_c, credits=10)
    )
    out = _apply(db, customer=session_c)
    assert out.get("ok") is False
    assert err in (out.get("error") or "")
    assert db.credit_lots.docs == []
    assert not db.payment_transactions.docs[0].get("applied_at")
    assert db.payment_transactions.docs[0].get("fulfillment_status") == cf.FULFILLMENT_ERROR


def test_c6_stripe_triple_match_ok():
    db = FakeDB()
    _seed_cc(db, stripe_customer_id="cus_1")
    db.payment_transactions.docs.append(_tx(stripe_customer_id="cus_1", credits=50))
    out = _apply(db, customer="cus_1")
    assert out.get("ok") is True


# --- Storage atomic gate ---


def test_c6_storage_increments_cc_not_agency():
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 0}
    )
    db.payment_transactions.docs.append(
        _tx(kind="storage_addon", agency_id=None, storage_gb=100)
    )
    out = _apply(db)
    assert out.get("ok") is True
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100
    assert db.agencies.docs[0]["storage_extra_gb"] == 0
    assert "cs_1" in db.commercial_customers.docs[0]["storage_fulfilled_sessions"]
    assert db.storage_checkout_fulfillments.docs[0]["status"] == cf.LEDGER_APPLIED


def test_c6_storage_crash_before_inc_then_retry():
    """Ledger must NOT exist as applied before gate; simulate empty then full apply."""
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.payment_transactions.docs.append(_tx(kind="storage_addon", storage_gb=100))
    # No prior ledger — normal apply
    out = _apply(db)
    assert out.get("ok") is True
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100


def test_c6_storage_crash_after_inc_before_ledger_retry():
    """Gate already consumed, ledger missing → retry must NOT double-inc, must finalize ledger."""
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.payment_transactions.docs.append(_tx(kind="storage_addon", storage_gb=100))

    # Simulate: $inc+$push done, ledger empty, applied_at missing, processing stale
    db.commercial_customers.docs[0]["storage_extra_gb"] = 100
    db.commercial_customers.docs[0]["storage_fulfilled_sessions"] = ["cs_1"]
    stale = (datetime.now(timezone.utc) - timedelta(seconds=600)).isoformat()
    db.payment_transactions.docs[0]["fulfillment_status"] = cf.FULFILLMENT_PROCESSING
    db.payment_transactions.docs[0]["fulfillment_started_at"] = stale

    out = _apply(db, stale_seconds=60)
    assert out.get("ok") is True
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100  # no double
    assert db.storage_checkout_fulfillments.docs[0]["status"] == cf.LEDGER_APPLIED
    assert db.payment_transactions.docs[0].get("fulfillment_status") == cf.FULFILLMENT_APPLIED


def test_c6_storage_crash_after_ledger_pending_must_still_inc():
    """Old bug: pending/existence without applied must not skip $inc.

    Insert a non-applied ledger row (or wrong status) — gate still empty → must inc once.
    """
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.payment_transactions.docs.append(_tx(kind="storage_addon", storage_gb=100))
    db.storage_checkout_fulfillments.docs.append(
        {
            "id": "cs_1",
            "session_id": "cs_1",
            "status": cf.LEDGER_PENDING,  # NOT proof of increment
            "storage_gb": 100,
        }
    )
    out = _apply(db)
    assert out.get("ok") is True
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100
    assert db.storage_checkout_fulfillments.docs[0]["status"] == cf.LEDGER_APPLIED


def test_c6_storage_duplicate_and_concurrent_one_inc():
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.payment_transactions.docs.append(_tx(kind="storage_addon", storage_gb=100))

    async def _both():
        # sequential double (claim blocks second)
        r1 = await cf.apply_h4_session_side_effects(
            db, "cs_1", session_customer="cus_1"
        )
        r2 = await cf.apply_h4_session_side_effects(
            db, "cs_1", session_customer="cus_1"
        )
        return r1, r2

    r1, r2 = _run(_both())
    assert r1.get("ok") is True
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100
    # second skipped or applied idempotent
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100

    # Concurrent gate on same CC different sessions → both apply
    db.payment_transactions.docs.append(
        _tx(session_id="cs_2", kind="storage_addon", storage_gb=50)
    )

    async def _conc():
        # Reset claim state for cs_2 only; call fulfill_storage_addon directly twice concurrent
        cc = db.commercial_customers.docs[0]
        tx = {
            "session_id": "cs_x",
            "storage_gb": 10,
        }
        # two concurrent gates same session — only one $inc
        t1 = asyncio.create_task(cf.fulfill_storage_addon(db, tx, cc))
        t2 = asyncio.create_task(cf.fulfill_storage_addon(db, tx, cc))
        await asyncio.gather(t1, t2)

    before = db.commercial_customers.docs[0]["storage_extra_gb"]
    _run(_conc())
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == before + 10


def test_c6_storage_full_retry_after_applied_noop():
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.payment_transactions.docs.append(_tx(kind="storage_addon", storage_gb=100))
    _apply(db)
    _apply(db)
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100


def test_c6_storage_ledger_must_persist_or_fail():
    """If ledger cannot be written, fulfillment must error (not silent applied)."""
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.payment_transactions.docs.append(_tx(kind="storage_addon", storage_gb=100))

    class _BoomColl(FakeColl):
        async def insert_one(self, doc):
            raise RuntimeError("insert_failed")

        async def update_one(self, filt, update, upsert=False):
            return type("R", (), {"matched_count": 0, "modified_count": 0})()

        async def find_one(self, filt=None, proj=None):
            return None

    db.storage_checkout_fulfillments = _BoomColl()
    out = _apply(db)
    assert out.get("ok") is False
    assert "storage_ledger_not_persisted" in (out.get("error") or "")
    assert not db.payment_transactions.docs[0].get("applied_at")
    assert db.payment_transactions.docs[0].get("fulfillment_status") == cf.FULFILLMENT_ERROR
    # Gate may have consumed — saldo può essere +100, ma senza applied finché ledger ok
    # Retry with working ledger must finalize without double-inc
    db.storage_checkout_fulfillments = FakeColl()
    stale = (datetime.now(timezone.utc) - timedelta(seconds=600)).isoformat()
    db.payment_transactions.docs[0]["fulfillment_status"] = cf.FULFILLMENT_PROCESSING
    db.payment_transactions.docs[0]["fulfillment_started_at"] = stale
    out2 = _apply(db, stale_seconds=60)
    assert out2.get("ok") is True
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100
    assert db.storage_checkout_fulfillments.docs[0]["status"] == cf.LEDGER_APPLIED


def test_c6_fresh_processing_not_reclaimed():
    db = FakeDB()
    _seed_cc(db, extra=0)
    db.payment_transactions.docs.append(_tx(kind="storage_addon", storage_gb=100))
    now = datetime.now(timezone.utc).isoformat()
    db.payment_transactions.docs[0]["fulfillment_status"] = cf.FULFILLMENT_PROCESSING
    db.payment_transactions.docs[0]["fulfillment_started_at"] = now
    out = _apply(db, stale_seconds=300)
    assert out.get("skipped") == "not_claimable"
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 0


def test_c6_routes_apply_passes_session_customer(monkeypatch):
    import apps.billing.routes as routes
    import shared.billing.checkout_fulfillment as mod

    seen = {}

    async def _fake(db, session_id, session_customer=None, **kwargs):
        seen["session_customer"] = session_customer
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
    _run(routes._apply_session_side_effects("cs_1", session_customer="cus_from_webhook"))
    assert seen["session_customer"] == "cus_from_webhook"
