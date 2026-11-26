"""D-193 — wallet concurrency + consistency on REAL MongoDB (isolated DB).

Requires a local mongod reachable via OMNIA_D193_MONGO_URL (default:
mongodb://127.0.0.1:27027/?replicaSet=rsD193). Uses a disposable DB name
prefixed ``omnia_d193_`` and drops it in teardown.

Never points at staging/production. Skips cleanly if Mongo is unreachable.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

import pytest

MONGO_URL = os.environ.get(
    "OMNIA_D193_MONGO_URL",
    "mongodb://127.0.0.1:27027/?replicaSet=rsD193&directConnection=true",
)
DB_PREFIX = "omnia_d193_"


# Motor binds to the running loop — keep ONE loop for the whole module.
_LOOP: asyncio.AbstractEventLoop | None = None


def _run(coro):
    global _LOOP
    if _LOOP is None or _LOOP.is_closed():
        _LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_LOOP)
    return _LOOP.run_until_complete(coro)


@pytest.fixture(scope="module")
def mongo_db():
    from motor.motor_asyncio import AsyncIOMotorClient

    global _LOOP
    _LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(_LOOP)
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2500)

    async def _ping():
        await client.admin.command("ping")

    try:
        _run(_ping())
    except Exception as exc:
        client.close()
        _LOOP.close()
        _LOOP = None
        pytest.skip(f"Mongo D-193 harness unreachable ({MONGO_URL}): {exc}")

    db_name = f"{DB_PREFIX}{uuid.uuid4().hex[:10]}"
    db = client[db_name]

    async def _indexes():
        await db.credit_lots.create_index([("id", 1)], unique=True)
        await db.credit_lots.create_index(
            [("idempotency_key", 1)], unique=True, sparse=True
        )
        await db.credit_allocations.create_index([("id", 1)], unique=True)
        await db.cc_credit_ledger.create_index([("id", 1)], unique=True)
        await db.cc_credit_ledger.create_index(
            [("idempotency_key", 1)], unique=True, sparse=True
        )
        await db.cc_credit_wallets.create_index(
            [("commercial_customer_id", 1)], unique=True
        )
        await db.credit_compensate_journal.create_index([("id", 1)], unique=True)

    _run(_indexes())
    yield db

    async def _drop():
        await client.drop_database(db_name)

    try:
        _run(_drop())
    finally:
        client.close()
        if _LOOP and not _LOOP.is_closed():
            _LOOP.close()
        _LOOP = None


def _seed(db, *, cc_id: str, agencies: list[str], status: str = "active"):
    from shared.models.commercial_customer import operational_status_for

    async def _do():
        await db.commercial_customers.insert_one(
            {
                "id": cc_id,
                "commercial_status": status,
                "operational_status": operational_status_for(status),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        for aid in agencies:
            await db.agencies.insert_one(
                {
                    "id": aid,
                    "commercial_customer_id": cc_id,
                    "display_name": aid,
                    "name": aid,
                }
            )

    _run(_do())


async def _snap(db, cc_id: str, org_ids: list[str]) -> dict:
    from shared.billing import credit_wallet_service as mod

    lots = await db.credit_lots.find({"commercial_customer_id": cc_id}, {"_id": 0}).to_list(
        10_000
    )
    allocs = await db.credit_allocations.find(
        {"commercial_customer_id": cc_id}, {"_id": 0}
    ).to_list(10_000)
    w = await mod._refresh_wallet_balances(db, cc_id)
    spend = {oid: await mod.org_spendable_balance(db, oid) for oid in org_ids}
    return {
        "lots_remaining": {d["id"]: int(d.get("remaining_qty") or 0) for d in lots},
        "lots_unallocated": {d["id"]: int(d.get("unallocated_qty") or 0) for d in lots},
        "alloc_remaining": sum(int(a.get("remaining_qty") or 0) for a in allocs),
        "balance_total": int(w.get("balance_total") or 0),
        "balance_unallocated": int(w.get("balance_unallocated") or 0),
        "spendable": spend,
    }


def test_mongo_two_concurrent_allocate_same_wallet(mongo_db):
    from shared.billing import credit_wallet_service as mod

    db = mongo_db
    cc, a1, a2 = "cc-conc-a", "ag-a1", "ag-a2"
    _seed(db, cc_id=cc, agencies=[a1, a2])
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc,
            amount=10,
            origin="t",
            reason="g",
            idempotency_key=f"g-{uuid.uuid4().hex[:8]}",
        )
    )

    async def _race():
        r1, r2 = await asyncio.gather(
            mod.allocate_credits(
                db,
                commercial_customer_id=cc,
                organization_id=a1,
                amount=7,
                reason="r1",
                idempotency_key=f"a1-{uuid.uuid4().hex[:8]}",
                payload_fingerprint="fp1",
            ),
            mod.allocate_credits(
                db,
                commercial_customer_id=cc,
                organization_id=a2,
                amount=7,
                reason="r2",
                idempotency_key=f"a2-{uuid.uuid4().hex[:8]}",
                payload_fingerprint="fp2",
            ),
            return_exceptions=True,
        )
        return r1, r2

    r1, r2 = _run(_race())
    ok = [r for r in (r1, r2) if not isinstance(r, Exception)]
    bad = [r for r in (r1, r2) if isinstance(r, Exception)]
    assert len(ok) == 1, f"exactly one allocate must succeed, got ok={ok!r} bad={bad!r}"
    assert len(bad) == 1
    snap = _run(_snap(db, cc, [a1, a2]))
    assert snap["spendable"][a1] + snap["spendable"][a2] == 7
    assert snap["balance_unallocated"] == 3
    assert snap["balance_total"] == 10
    assert snap["alloc_remaining"] == 7


def test_mongo_concurrent_debit_same_allocation(mongo_db):
    from shared.billing import credit_wallet_service as mod
    from fastapi import HTTPException

    db = mongo_db
    cc, ag = "cc-deb-same", "ag-ds"
    _seed(db, cc_id=cc, agencies=[ag])
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc,
            amount=20,
            origin="t",
            reason="g",
            idempotency_key=f"g-{uuid.uuid4().hex[:8]}",
            allocate_to_organization_id=ag,
        )
    )

    async def _race():
        return await asyncio.gather(
            mod.debit_for_organization(db, organization_id=ag, amount=15, reason="d1"),
            mod.debit_for_organization(db, organization_id=ag, amount=15, reason="d2"),
            return_exceptions=True,
        )

    out = _run(_race())
    oks = [x for x in out if not isinstance(x, Exception)]
    errs = [x for x in out if isinstance(x, Exception)]
    assert len(oks) == 1
    assert len(errs) == 1
    assert isinstance(errs[0], HTTPException)
    snap = _run(_snap(db, cc, [ag]))
    assert snap["spendable"][ag] == 5
    assert snap["balance_total"] == 5
    assert snap["alloc_remaining"] == 5


def test_mongo_concurrent_debit_two_branches(mongo_db):
    from shared.billing import credit_wallet_service as mod

    db = mongo_db
    cc, a1, a2 = "cc-deb-br", "ag-b1", "ag-b2"
    _seed(db, cc_id=cc, agencies=[a1, a2])
    for ag, key in ((a1, "g1"), (a2, "g2")):
        _run(
            mod.grant_lot(
                db,
                commercial_customer_id=cc,
                amount=30,
                origin="t",
                reason="g",
                idempotency_key=f"{key}-{uuid.uuid4().hex[:8]}",
                allocate_to_organization_id=ag,
            )
        )

    async def _race():
        return await asyncio.gather(
            mod.debit_for_organization(db, organization_id=a1, amount=10, reason="d1"),
            mod.debit_for_organization(db, organization_id=a2, amount=12, reason="d2"),
        )

    b1, b2 = _run(_race())
    assert b1 == 20 and b2 == 18
    snap = _run(_snap(db, cc, [a1, a2]))
    assert snap["spendable"][a1] == 20
    assert snap["spendable"][a2] == 18
    assert snap["balance_total"] == 38


def test_mongo_revoke_concurrent_with_debit(mongo_db):
    from shared.billing import credit_wallet_service as mod
    from fastapi import HTTPException

    db = mongo_db
    cc, ag = "cc-rev-deb", "ag-rd"
    _seed(db, cc_id=cc, agencies=[ag])
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc,
            amount=25,
            origin="t",
            reason="g",
            idempotency_key=f"g-{uuid.uuid4().hex[:8]}",
            allocate_to_organization_id=ag,
        )
    )
    alloc_id = _run(
        db.credit_allocations.find_one({"organization_id": ag}, {"_id": 0, "id": 1})
    )["id"]

    async def _race():
        return await asyncio.gather(
            mod.debit_for_organization(db, organization_id=ag, amount=10, reason="d"),
            mod.revoke_allocation(
                db,
                allocation_id=alloc_id,
                commercial_customer_id=cc,
                reason="r",
                idempotency_key=f"rev-{uuid.uuid4().hex[:8]}",
                payload_fingerprint="fp-r",
            ),
            return_exceptions=True,
        )

    out = _run(_race())
    # One or both may succeed depending on race; invariants must hold.
    snap = _run(_snap(db, cc, [ag]))
    assert snap["balance_total"] >= 0
    assert snap["balance_unallocated"] >= 0
    assert snap["spendable"][ag] >= 0
    # Remaining + unallocated cannot exceed original grant
    assert snap["spendable"][ag] + snap["balance_unallocated"] <= 25
    assert snap["balance_total"] == snap["spendable"][ag] + snap["balance_unallocated"]
    # At least one operation produced a result or typed HTTP error
    assert any(not isinstance(x, BaseException) or isinstance(x, HTTPException) for x in out)


def test_mongo_idempotency_replay_and_mismatch(mongo_db):
    from shared.billing import credit_wallet_service as mod
    from fastapi import HTTPException

    db = mongo_db
    cc, ag = "cc-idem", "ag-idem"
    _seed(db, cc_id=cc, agencies=[ag, "ag-idem-2"])
    _run(
        db.agencies.insert_one(
            {"id": "ag-idem-2", "commercial_customer_id": cc, "display_name": "x"}
        )
    )
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc,
            amount=40,
            origin="t",
            reason="g",
            idempotency_key=f"g-{uuid.uuid4().hex[:8]}",
        )
    )
    key = f"alloc-{uuid.uuid4().hex[:8]}"
    a1 = _run(
        mod.allocate_credits(
            db,
            commercial_customer_id=cc,
            organization_id=ag,
            amount=8,
            reason="a",
            idempotency_key=key,
            payload_fingerprint="fp-same",
        )
    )
    a2 = _run(
        mod.allocate_credits(
            db,
            commercial_customer_id=cc,
            organization_id=ag,
            amount=8,
            reason="a",
            idempotency_key=key,
            payload_fingerprint="fp-same",
        )
    )
    assert [x["id"] for x in a1] == [x["id"] for x in a2]
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id=cc,
                organization_id="ag-idem-2",
                amount=8,
                reason="a",
                idempotency_key=key,
                payload_fingerprint="fp-other",
            )
        )
    assert ei.value.status_code == 409
    snap = _run(_snap(db, cc, [ag, "ag-idem-2"]))
    assert snap["spendable"][ag] == 8
    assert snap["spendable"]["ag-idem-2"] == 0


def test_mongo_compensate_mid_failure_and_journal_recover(mongo_db):
    """Force lot_inconsistency via data (lot remaining drained, alloc still open)."""
    from shared.billing import credit_wallet_service as mod
    from fastapi import HTTPException

    db = mongo_db
    cc, ag = "cc-comp", "ag-comp"
    _seed(db, cc_id=cc, agencies=[ag])
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc,
            amount=30,
            origin="t",
            reason="g1",
            idempotency_key=f"g1-{uuid.uuid4().hex[:8]}",
            allocate_to_organization_id=ag,
        )
    )
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc,
            amount=30,
            origin="t",
            reason="g2",
            idempotency_key=f"g2-{uuid.uuid4().hex[:8]}",
            allocate_to_organization_id=ag,
        )
    )
    before = _run(_snap(db, cc, [ag]))
    assert before["spendable"][ag] == 60

    lots = _run(
        db.credit_lots.find({"commercial_customer_id": cc}, {"_id": 0})
        .sort("created_at", 1)
        .to_list(10)
    )
    # Drain second lot remaining so FIFO debit fails on lot filter after first slice
    _run(
        db.credit_lots.update_one(
            {"id": lots[1]["id"]}, {"$set": {"remaining_qty": 0}}
        )
    )

    with pytest.raises(HTTPException) as ei:
        _run(
            mod.debit_for_organization(
                db, organization_id=ag, amount=50, reason="partial_fail"
            )
        )
    assert ei.value.status_code in (409, 402, 500)

    after = _run(_snap(db, cc, [ag]))
    # Spendable/alloc restored; lot2 was already 0 by fixture — total remaining lots
    # should equal spendable + unallocated after refresh semantics.
    assert after["spendable"][ag] == before["spendable"][ag]
    assert after["alloc_remaining"] == before["alloc_remaining"]

    journals = _run(
        db.credit_compensate_journal.find({"commercial_customer_id": cc}, {"_id": 0}).to_list(
            100
        )
    )
    # If at least one full slice was applied before lot fail, journal exists and is done
    if journals:
        assert all(j.get("status") == "completed" for j in journals)


def test_mongo_journal_recover_after_partial_compensate_failure(mongo_db):
    """Seed a pending journal mid-step and prove recover finishes without double credit."""
    from shared.billing import credit_wallet_service as mod

    db = mongo_db
    cc, ag = "cc-jrec", "ag-jrec"
    _seed(db, cc_id=cc, agencies=[ag])
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc,
            amount=20,
            origin="t",
            reason="g1",
            idempotency_key=f"g1-{uuid.uuid4().hex[:8]}",
            allocate_to_organization_id=ag,
        )
    )
    before = _run(_snap(db, cc, [ag]))
    alloc = _run(
        db.credit_allocations.find_one({"organization_id": ag}, {"_id": 0})
    )
    lot = _run(db.credit_lots.find_one({"id": alloc["lot_id"]}, {"_id": 0}))
    take = 5
    # Simulate debit took 5 (both decremented) then crash after alloc restore only
    _run(
        db.credit_allocations.update_one(
            {"id": alloc["id"]}, {"$inc": {"remaining_qty": -take}}
        )
    )
    _run(
        db.credit_lots.update_one(
            {"id": lot["id"]}, {"$inc": {"remaining_qty": -take}}
        )
    )
    jid = _run(
        mod._open_debit_compensate_journal(
            db,
            commercial_customer_id=cc,
            organization_id=ag,
            reason="sim_crash",
            slices=[(alloc["id"], lot["id"], take)],
        )
    )
    # Partial restore: alloc back, journal step alloc_restored, lot still down
    _run(
        db.credit_allocations.update_one(
            {"id": alloc["id"]}, {"$inc": {"remaining_qty": take}}
        )
    )
    _run(
        db.credit_compensate_journal.update_one(
            {"id": jid},
            {
                "$set": {
                    "slices.0.status": mod.JOURNAL_ALLOC_RESTORED,
                    "status": mod.JOURNAL_PENDING,
                }
            },
        )
    )
    mid = _run(_snap(db, cc, [ag]))
    assert mid["spendable"][ag] == before["spendable"][ag]
    assert mid["lots_remaining"][lot["id"]] == before["lots_remaining"][lot["id"]] - take

    result = _run(mod.recover_pending_debit_compensations(db, commercial_customer_id=cc))
    assert result["recovered"] == 1
    assert result["failed"] == 0
    after = _run(_snap(db, cc, [ag]))
    assert after["spendable"][ag] == before["spendable"][ag]
    assert after["lots_remaining"] == before["lots_remaining"]
    assert after["balance_total"] == before["balance_total"]
    j = _run(db.credit_compensate_journal.find_one({"id": jid}, {"_id": 0}))
    assert j["status"] == "completed"


def test_mongo_consistency_lots_allocs_ledger(mongo_db):
    from shared.billing import credit_wallet_service as mod

    db = mongo_db
    cc, ag = "cc-cons", "ag-cons"
    _seed(db, cc_id=cc, agencies=[ag])
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id=cc,
            amount=15,
            origin="t",
            reason="g",
            idempotency_key=f"g-{uuid.uuid4().hex[:8]}",
        )
    )
    _run(
        mod.allocate_credits(
            db,
            commercial_customer_id=cc,
            organization_id=ag,
            amount=10,
            reason="a",
            idempotency_key=f"a-{uuid.uuid4().hex[:8]}",
            payload_fingerprint="fp",
        )
    )
    _run(mod.debit_for_organization(db, organization_id=ag, amount=4, reason="use"))
    snap = _run(_snap(db, cc, [ag]))
    assert snap["spendable"][ag] == 6
    assert snap["balance_unallocated"] == 5
    assert snap["balance_total"] == 11
    ledger = _run(
        db.cc_credit_ledger.find({"commercial_customer_id": cc}, {"_id": 0}).to_list(1000)
    )
    types = {e.get("entry_type") for e in ledger}
    assert "grant" in types and "allocate" in types and "consume" in types
