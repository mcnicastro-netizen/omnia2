"""D-193 — wallet remediation: debit compensate, idempotency allocate/revoke."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from tests.test_b04ii_wallet_ledger import FakeDB, FakeColl, _run, _seed_cc_agency


def _grant_alloc(db, *, cc_id: str, agency_id: str, amount: int, key: str) -> str:
    from shared.billing import credit_wallet_service as mod

    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc_id,
            amount=amount,
            origin="test",
            reason="t",
            idempotency_key=key,
            allocate_to_organization_id=agency_id,
        )
    )
    return db.credit_allocations.docs[-1]["id"]


def test_d193_compensate_restores_lot_remaining_after_lot_failure():
    """Reproduce+fix: mid-debit lot failure must restore alloc AND lot remaining_qty."""
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=50,
            origin="t",
            reason="g1",
            idempotency_key="d193-g1",
            allocate_to_organization_id="ag1",
        )
    )
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=50,
            origin="t",
            reason="g2",
            idempotency_key="d193-g2",
            allocate_to_organization_id="ag1",
        )
    )
    # Two allocations FIFO — force second lot update to fail by zeroing lot remaining
    # after first slice applied: monkeypatch find_one_and_update on lots.
    lots = db.credit_lots
    real_fau = lots.find_one_and_update
    calls = {"n": 0}

    async def flaky_lot_fau(filt, update, return_document=None, upsert=False):
        # Fail on first lot decrement attempt after allocs already decremented once
        # Strategy: let first full slice (alloc+lot) succeed; on second lot dec fail.
        is_lot_dec = "$inc" in update and "remaining_qty" in update.get("$inc", {})
        if is_lot_dec:
            calls["n"] += 1
            if calls["n"] >= 2:
                return None
        return await real_fau(filt, update, return_document=return_document, upsert=upsert)

    lots.find_one_and_update = flaky_lot_fau  # type: ignore[method-assign]

    before_lots = {d["id"]: int(d["remaining_qty"]) for d in db.credit_lots.docs}
    before_allocs = {d["id"]: int(d["remaining_qty"]) for d in db.credit_allocations.docs}
    before_spendable = _run(mod.org_spendable_balance(db, "ag1"))
    assert before_spendable == 100

    with pytest.raises(HTTPException) as ei:
        _run(
            mod.debit_for_organization(
                db, organization_id="ag1", amount=80, reason="spend_partial_fail"
            )
        )
    assert ei.value.status_code in (402, 409)

    after_lots = {d["id"]: int(d["remaining_qty"]) for d in db.credit_lots.docs}
    after_allocs = {d["id"]: int(d["remaining_qty"]) for d in db.credit_allocations.docs}
    assert after_lots == before_lots, "lot remaining must be fully restored"
    assert after_allocs == before_allocs, "allocation remaining must be fully restored"
    assert _run(mod.org_spendable_balance(db, "ag1")) == before_spendable
    w = _run(mod._refresh_wallet_balances(db, "cc1"))
    assert w["balance_total"] == 100
    # Compensate ledger entries present (full slice restore and/or alloc-only)
    comps = [e for e in db.cc_credit_ledger.docs if e.get("entry_type") == "compensate"]
    assert comps, "compensate ledger required"
    assert any(
        (c.get("meta") or {}).get("restored_lot")
        or (c.get("meta") or {}).get("restored_alloc_only")
        for c in comps
    )


def test_d193_debit_success_still_fifo_and_consistent():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=30,
            origin="t",
            reason="a",
            idempotency_key="ok1",
            allocate_to_organization_id="ag1",
        )
    )
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=20,
            origin="t",
            reason="b",
            idempotency_key="ok2",
            allocate_to_organization_id="ag1",
        )
    )
    bal = _run(
        mod.debit_for_organization(db, organization_id="ag1", amount=35, reason="use")
    )
    assert bal == 15
    assert _run(mod.org_spendable_balance(db, "ag1")) == 15
    w = _run(mod._refresh_wallet_balances(db, "cc1"))
    assert w["balance_total"] == 15
    # Oldest lot drained first
    lots = sorted(db.credit_lots.docs, key=lambda x: x["created_at"])
    assert lots[0]["remaining_qty"] == 0
    assert lots[1]["remaining_qty"] == 15


def test_d193_allocate_idempotent_replay_same_payload():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=40,
            origin="t",
            reason="g",
            idempotency_key="grant-idem",
        )
    )
    fp = "fp-alloc-1"
    a1 = _run(
        mod.allocate_credits(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            amount=10,
            reason="alloc",
            idempotency_key="alloc-key-1",
            payload_fingerprint=fp,
        )
    )
    a2 = _run(
        mod.allocate_credits(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            amount=10,
            reason="alloc",
            idempotency_key="alloc-key-1",
            payload_fingerprint=fp,
        )
    )
    assert [x["id"] for x in a1] == [x["id"] for x in a2]
    assert sum(int(a["remaining_qty"]) for a in db.credit_allocations.docs) == 10
    assert _run(mod.org_spendable_balance(db, "ag1")) == 10


def test_d193_allocate_idempotent_key_reused_different_payload_rejected():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag2")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=40,
            origin="t",
            reason="g",
            idempotency_key="grant-idem-2",
        )
    )
    _run(
        mod.allocate_credits(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            amount=5,
            reason="alloc",
            idempotency_key="alloc-key-2",
            payload_fingerprint="fp-a",
        )
    )
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag2",
                amount=5,
                reason="alloc",
                idempotency_key="alloc-key-2",
                payload_fingerprint="fp-b",
            )
        )
    assert ei.value.status_code == 409
    assert ei.value.detail["error"] == "idempotency_key_reused"
    assert _run(mod.org_spendable_balance(db, "ag1")) == 5
    assert _run(mod.org_spendable_balance(db, "ag2")) == 0


def test_d193_revoke_idempotent_and_reject_payload_mismatch():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    alloc_id = _grant_alloc(db, cc_id="cc1", agency_id="ag1", amount=12, key="rv-g")
    e1 = _run(
        mod.revoke_allocation(
            db,
            allocation_id=alloc_id,
            commercial_customer_id="cc1",
            reason="r",
            idempotency_key="rev-1",
            payload_fingerprint="fp-r",
        )
    )
    e2 = _run(
        mod.revoke_allocation(
            db,
            allocation_id=alloc_id,
            commercial_customer_id="cc1",
            reason="r",
            idempotency_key="rev-1",
            payload_fingerprint="fp-r",
        )
    )
    assert e1["id"] == e2["id"]
    assert _run(mod.org_spendable_balance(db, "ag1")) == 0
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.revoke_allocation(
                db,
                allocation_id=alloc_id,
                commercial_customer_id="cc1",
                reason="r",
                idempotency_key="rev-1",
                payload_fingerprint="fp-other",
            )
        )
    assert ei.value.status_code == 409


def test_d193_legacy_allocate_without_idempotency_key_still_works():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=8,
            origin="t",
            reason="g",
            idempotency_key="lg",
        )
    )
    created = _run(
        mod.allocate_credits(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            amount=3,
            reason="legacy",
        )
    )
    assert len(created) == 1
    assert _run(mod.org_spendable_balance(db, "ag1")) == 3


def test_d193_route_helpers_fingerprint_stable():
    from apps.billing import routes as r

    a = r._wallet_payload_fingerprint("cc", "ag", 10)
    b = r._wallet_payload_fingerprint("cc", "ag", 10)
    c = r._wallet_payload_fingerprint("cc", "ag", 11)
    assert a == b and a != c
    assert r._wallet_idempotency_key({}, None) is None
    assert r._wallet_idempotency_key({"idempotency_key": "k1"}, None) == "k1"
    assert r._wallet_idempotency_key({}, "hdr") == "hdr"


def test_d193_compensate_after_ledger_failure_restores_full_slice():
    """Failure after alloc+lot decrement (during consume ledger) must restore both."""
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=20,
            origin="t",
            reason="g",
            idempotency_key="led-g",
            allocate_to_organization_id="ag1",
        )
    )
    before_lots = {d["id"]: int(d["remaining_qty"]) for d in db.credit_lots.docs}
    before_allocs = {d["id"]: int(d["remaining_qty"]) for d in db.credit_allocations.docs}
    real_append = mod._append_ledger
    calls = {"n": 0}

    async def boom_append(*args, **kwargs):
        if kwargs.get("entry_type") == mod.ENTRY_CONSUME:
            calls["n"] += 1
            if calls["n"] >= 1:
                raise RuntimeError("ledger_write_failed")
        return await real_append(*args, **kwargs)

    mod._append_ledger = boom_append  # type: ignore[assignment]
    try:
        with pytest.raises(HTTPException) as ei:
            _run(
                mod.debit_for_organization(
                    db, organization_id="ag1", amount=5, reason="spend"
                )
            )
        assert ei.value.status_code == 500
        assert ei.value.detail["error"] == "debit_failed_compensated"
    finally:
        mod._append_ledger = real_append  # type: ignore[assignment]

    after_lots = {d["id"]: int(d["remaining_qty"]) for d in db.credit_lots.docs}
    after_allocs = {d["id"]: int(d["remaining_qty"]) for d in db.credit_allocations.docs}
    assert after_lots == before_lots
    assert after_allocs == before_allocs
    assert _run(mod.org_spendable_balance(db, "ag1")) == 20


def test_d193_concurrent_allocate_does_not_over_allocate_simulated():
    """Simulated sequential race: second allocate sees reduced unallocated (FakeDB)."""
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag2")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=10,
            origin="t",
            reason="g",
            idempotency_key="conc-g",
        )
    )
    _run(
        mod.allocate_credits(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            amount=7,
            reason="a1",
            idempotency_key="conc-a1",
            payload_fingerprint="fp1",
        )
    )
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag2",
                amount=7,
                reason="a2",
                idempotency_key="conc-a2",
                payload_fingerprint="fp2",
            )
        )
    assert ei.value.status_code == 409
    assert ei.value.detail["error"] == "insufficient_unallocated_credits"
    assert _run(mod.org_spendable_balance(db, "ag1")) == 7
    assert _run(mod.org_spendable_balance(db, "ag2")) == 0
    w = _run(mod._refresh_wallet_balances(db, "cc1"))
    assert w["balance_unallocated"] == 3
    assert w["balance_total"] == 10


def test_d193_cross_piva_allocate_rejected():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="ccA", agency_id="agA")
    _seed_cc_agency(db, cc_id="ccB", agency_id="agB")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="ccA",
            amount=15,
            origin="t",
            reason="g",
            idempotency_key="xp-g",
        )
    )
    with pytest.raises(HTTPException):
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="ccA",
                organization_id="agB",
                amount=5,
                reason="cross",
            )
        )
    assert _run(mod.org_spendable_balance(db, "agB")) == 0
    w = _run(mod._refresh_wallet_balances(db, "ccA"))
    assert w["balance_unallocated"] == 15


def test_d193_journal_recover_after_partial_compensate():
    """Compensate crash after alloc restore → recover finishes without double credit."""
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=20,
            origin="t",
            reason="g",
            idempotency_key="jr-g",
            allocate_to_organization_id="ag1",
        )
    )
    before_alloc = int(db.credit_allocations.docs[0]["remaining_qty"])
    before_lot = int(db.credit_lots.docs[0]["remaining_qty"])
    # Simulate: debit took 5, then compensate restored alloc only (journal step)
    db.credit_allocations.docs[0]["remaining_qty"] = before_alloc - 5
    db.credit_lots.docs[0]["remaining_qty"] = before_lot - 5
    alloc_id = db.credit_allocations.docs[0]["id"]
    lot_id = db.credit_lots.docs[0]["id"]
    jid = _run(
        mod._open_debit_compensate_journal(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            reason="sim",
            slices=[(alloc_id, lot_id, 5)],
        )
    )
    # Partial: alloc already restored, journal step = alloc_restored
    db.credit_allocations.docs[0]["remaining_qty"] = before_alloc
    db.credit_compensate_journal.docs[0]["slices"][0]["status"] = mod.JOURNAL_ALLOC_RESTORED
    result = _run(mod.recover_pending_debit_compensations(db, commercial_customer_id="cc1"))
    assert result["recovered"] == 1
    assert db.credit_allocations.docs[0]["remaining_qty"] == before_alloc
    assert db.credit_lots.docs[0]["remaining_qty"] == before_lot
    assert db.credit_compensate_journal.docs[0]["status"] == mod.JOURNAL_COMPLETED
    assert jid


def test_d193_wallet_admin_auth_excludes_branch_and_agent():
    from apps.billing import routes as billing_routes

    src = open(billing_routes.__file__, encoding="utf-8").read()
    start = src.index("_WALLET_ADMIN_AUTH = require_roles_exact(")
    end = src.index(")", start) + 1
    block = src[start:end]
    assert "agency_admin" in block
    assert "group_admin" in block
    assert "super_admin" in block
    assert "branch_admin" not in block
    assert '"agent"' not in block and "'agent'" not in block


def test_d193_compensate_journal_recover_endpoint_is_ops_super_only():
    import inspect
    from apps.billing import routes as billing_routes

    fn = billing_routes.recover_wallet_compensate_journal
    params = inspect.signature(fn).parameters
    user_dep = params["user"].default
    assert user_dep.dependency is billing_routes._OPS_SUPER
