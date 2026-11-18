"""R-03 — allocate concorrenti non devono over-allocare lo stesso lotto."""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from tests.test_b04ii_wallet_ledger import FakeDB, _run, _seed_cc_agency


def test_r03_concurrent_allocate_no_overallocation():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    db.agencies.docs.append(
        {
            "id": "ag2",
            "commercial_customer_id": "cc1",
            "name": "Org 2",
        }
    )
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=10,
            origin="test",
            reason="seed",
            idempotency_key="r03-seed",
        )
    )
    lot = db.credit_lots.docs[0]
    assert lot.get("unallocated_qty") == 10

    async def _race():
        return await asyncio.gather(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag1",
                amount=10,
                reason="a1",
            ),
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag2",
                amount=10,
                reason="a2",
            ),
            return_exceptions=True,
        )

    results = _run(_race())
    oks = [r for r in results if not isinstance(r, BaseException)]
    errs = [r for r in results if isinstance(r, HTTPException)]
    assert len(oks) == 1, results
    assert len(errs) == 1
    assert errs[0].status_code == 409
    assert errs[0].detail["error"] == "insufficient_unallocated_credits"

    total_alloc = sum(int(a.get("remaining_qty") or 0) for a in db.credit_allocations.docs)
    assert total_alloc == 10
    assert int(db.credit_lots.docs[0].get("unallocated_qty") or 0) == 0
    w = _run(mod._refresh_wallet_balances(db, "cc1"))
    assert w["balance_unallocated"] == 0
    assert w["balance_total"] == 10


def test_r03_revoke_restores_unallocated_for_reallocate():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=5,
            origin="test",
            reason="seed",
            allocate_to_organization_id="ag1",
            idempotency_key="r03-rev",
        )
    )
    assert int(db.credit_lots.docs[0].get("unallocated_qty") or 0) == 0
    alloc_id = db.credit_allocations.docs[0]["id"]
    _run(
        mod.revoke_allocation(
            db,
            allocation_id=alloc_id,
            commercial_customer_id="cc1",
            reason="back",
        )
    )
    assert int(db.credit_lots.docs[0].get("unallocated_qty") or 0) == 5
    created = _run(
        mod.allocate_credits(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            amount=5,
            reason="again",
        )
    )
    assert sum(a["remaining_qty"] for a in created) == 5
    assert int(db.credit_lots.docs[0].get("unallocated_qty") or 0) == 0


def test_r03_legacy_lot_backfill_unallocated_qty():
    """Lotti senza campo unallocated_qty: backfill poi claim."""
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    wallet = _run(mod.ensure_wallet(db, "cc1"))
    db.credit_lots.docs.append(
        {
            "id": "legacy-lot",
            "commercial_customer_id": "cc1",
            "wallet_id": wallet["id"],
            "origin": "legacy",
            "original_qty": 7,
            "remaining_qty": 7,
            # no unallocated_qty
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    )
    created = _run(
        mod.allocate_credits(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            amount=7,
            reason="legacy",
        )
    )
    assert sum(a["remaining_qty"] for a in created) == 7
    assert "unallocated_qty" in db.credit_lots.docs[0]
    assert int(db.credit_lots.docs[0]["unallocated_qty"]) == 0
