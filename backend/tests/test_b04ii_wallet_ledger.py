"""B04-II — central wallet, lots, allocations, FIFO debit."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any, Optional

import pytest
from fastapi import HTTPException


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def sort(self, *args, **kwargs):
        key = args[0] if args else "created_at"
        reverse = False
        if len(args) > 1 and args[1] == -1:
            reverse = True
        if isinstance(key, list):
            # ignore complex
            key = key[0][0] if key else "created_at"
        self._rows = sorted(self._rows, key=lambda r: r.get(key) or "", reverse=reverse)
        return self

    async def to_list(self, length=1000):
        return list(self._rows)[:length]


class FakeColl:
    def __init__(self):
        self.docs: list[dict] = []

    def _match(self, doc, filt: dict) -> bool:
        for k, v in filt.items():
            if k == "$or":
                if not any(self._match(doc, clause) for clause in v):
                    return False
                continue
            if isinstance(v, dict):
                val = doc.get(k)
                if "$gte" in v and not (val is not None and val >= v["$gte"]):
                    return False
                if "$gt" in v and not (val is not None and val > v["$gt"]):
                    return False
                if "$lt" in v and not (val is not None and val < v["$lt"]):
                    return False
                if "$lte" in v and not (val is not None and val <= v["$lte"]):
                    return False
                if "$ne" in v and val == v["$ne"]:
                    return False
                if "$in" in v and val not in v["$in"]:
                    return False
                if "$nin" in v and val in v["$nin"]:
                    return False
                if "$exists" in v:
                    exists = k in doc and doc.get(k) is not None
                    if bool(v["$exists"]) != exists:
                        return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    def find(self, filt=None, proj=None):
        filt = filt or {}
        rows = [deepcopy(d) for d in self.docs if self._match(d, filt)]
        if proj:
            keep = {k for k, flag in proj.items() if flag}
            if keep:
                rows = [{k: r[k] for k in r if k in keep or k == "id"} for r in rows]
        return FakeCursor(rows)

    async def find_one(self, filt=None, proj=None):
        rows = await self.find(filt or {}, proj).to_list(1)
        return rows[0] if rows else None

    async def insert_one(self, doc):
        if any(d.get("id") and d.get("id") == doc.get("id") for d in self.docs):
            raise Exception("duplicate id")
        # unique idempotency_key sparse
        ik = doc.get("idempotency_key")
        if ik:
            if any(d.get("idempotency_key") == ik for d in self.docs):
                raise Exception("duplicate idempotency")
        self.docs.append(deepcopy(doc))
        return MagicInsert()

    async def update_one(self, filt, update, upsert=False):
        for i, d in enumerate(self.docs):
            if self._match(d, filt):
                self._apply(self.docs[i], update)
                return MagicUpdate(1)
        if upsert:
            base = {k: v for k, v in filt.items() if not str(k).startswith("$")}
            if "$setOnInsert" in update:
                base.update(update["$setOnInsert"])
            if "$set" in update:
                base.update(update["$set"])
            self.docs.append(base)
            return MagicUpdate(1)
        return MagicUpdate(0)

    async def update_many(self, filt, update):
        n = 0
        for i, d in enumerate(self.docs):
            if self._match(d, filt or {}):
                self._apply(self.docs[i], update)
                n += 1
        return MagicUpdate(n)

    async def find_one_and_update(self, filt, update, return_document=None, upsert=False):
        before = None
        for i, d in enumerate(self.docs):
            if self._match(d, filt):
                before = deepcopy(d)
                self._apply(self.docs[i], update)
                after = deepcopy(self.docs[i])
                # ReturnDocument.BEFORE vs AFTER — pymongo enum; treat truthy AFTER as after
                if return_document is not None and str(return_document).endswith("BEFORE"):
                    return before
                if return_document is False:
                    return before
                return after
        if upsert:
            base = {k: v for k, v in filt.items() if not str(k).startswith("$")}
            if "$setOnInsert" in update:
                base.update(update["$setOnInsert"])
            if "$set" in update:
                base.update(update["$set"])
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    base[k] = base.get(k, 0) + v
            self.docs.append(base)
            return deepcopy(base)
        return None

    async def delete_one(self, filt):
        for i, d in enumerate(self.docs):
            if self._match(d, filt):
                self.docs.pop(i)
                return MagicUpdate(1)
        return MagicUpdate(0)

    def _apply(self, doc, update):
        if "$set" in update:
            doc.update(update["$set"])
        if "$inc" in update:
            for k, v in update["$inc"].items():
                doc[k] = int(doc.get(k) or 0) + int(v)
        if "$setOnInsert" in update:
            pass


class MagicInsert:
    inserted_id = "x"


class MagicUpdate:
    def __init__(self, n):
        self.modified_count = n
        self.matched_count = n


class FakeDB:
    def __init__(self):
        self.cc_credit_wallets = FakeColl()
        self.credit_lots = FakeColl()
        self.credit_allocations = FakeColl()
        self.cc_credit_ledger = FakeColl()
        self.credit_wallets = FakeColl()
        self.credit_ledger = FakeColl()
        self.agencies = FakeColl()
        self.commercial_customers = FakeColl()
        self.commercial_main_admin_events = FakeColl()
        self.storage_checkout_fulfillments = FakeColl()
        self.storage_migration_snapshots = FakeColl()
        self.payment_transactions = FakeColl()
        self.properties = FakeColl()
        self.subscriptions = FakeColl()

    def __getitem__(self, name):
        if not hasattr(self, name):
            setattr(self, name, FakeColl())
        return getattr(self, name)


def _seed_cc_agency(db: FakeDB, *, cc_id="cc1", agency_id="ag1", status="active"):
    from shared.models.commercial_customer import operational_status_for

    db.commercial_customers.docs.append(
        {
            "id": cc_id,
            "commercial_status": status,
            "operational_status": operational_status_for(status),
        }
    )
    db.agencies.docs.append(
        {"id": agency_id, "commercial_customer_id": cc_id, "display_name": "Demo"}
    )


def test_grant_lot_idempotent():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    a = _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=100,
            origin="test",
            reason="t",
            idempotency_key="k1",
            allocate_to_organization_id="ag1",
        )
    )
    b = _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=100,
            origin="test",
            reason="t",
            idempotency_key="k1",
            allocate_to_organization_id="ag1",
        )
    )
    assert a["id"] == b["id"]
    assert len(db.credit_lots.docs) == 1
    assert _run(mod.org_spendable_balance(db, "ag1")) == 100


def test_allocate_rejects_cross_vat():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    db.agencies.docs.append({"id": "ag2", "commercial_customer_id": "ccOTHER"})
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=50,
            origin="test",
            reason="t",
            idempotency_key="g1",
        )
    )
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag2",
                amount=10,
            )
        )
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "cross_vat_transfer_forbidden"


def test_fifo_debit_across_two_lots():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=30,
            origin="old",
            reason="old",
            idempotency_key="old",
            allocate_to_organization_id="ag1",
        )
    )
    # Force older created_at
    db.credit_lots.docs[0]["created_at"] = "2026-01-01T00:00:00+00:00"
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=40,
            origin="new",
            reason="new",
            idempotency_key="new",
            allocate_to_organization_id="ag1",
        )
    )
    db.credit_lots.docs[1]["created_at"] = "2026-06-01T00:00:00+00:00"

    bal = _run(
        mod.debit_for_organization(
            db, organization_id="ag1", amount=40, reason="staging"
        )
    )
    assert bal == 30
    # Oldest lot fully consumed
    lots = sorted(db.credit_lots.docs, key=lambda x: x["created_at"])
    assert lots[0]["remaining_qty"] == 0
    assert lots[1]["remaining_qty"] == 30
    consumes = [e for e in db.cc_credit_ledger.docs if e["entry_type"] == "consume"]
    assert sum(-e["delta"] for e in consumes) == 40


def test_debit_blocked_when_suspended():
    """MC-054 — spend negata su suspended; grant/allocate solo a CC operable."""
    from shared.billing import credit_wallet_service as mod
    from shared.models.commercial_customer import operational_status_for

    db = FakeDB()
    _seed_cc_agency(db, status="active")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=10,
            origin="t",
            reason="t",
            idempotency_key="s1",
            allocate_to_organization_id="ag1",
        )
    )
    # Sospendi dopo il grant (wallet mutate già vietata su suspended)
    db.commercial_customers.docs[0]["commercial_status"] = "suspended"
    db.commercial_customers.docs[0]["operational_status"] = operational_status_for(
        "suspended"
    )
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.debit_for_organization(
                db, organization_id="ag1", amount=1, reason="x"
            )
        )
    assert ei.value.status_code == 402
    assert ei.value.detail["error"] == "credits_not_spendable"


def test_revoke_returns_to_unallocated():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=20,
            origin="t",
            reason="t",
            idempotency_key="r1",
            allocate_to_organization_id="ag1",
        )
    )
    alloc_id = db.credit_allocations.docs[0]["id"]
    _run(
        mod.revoke_allocation(
            db,
            allocation_id=alloc_id,
            commercial_customer_id="cc1",
            reason="rev",
        )
    )
    assert _run(mod.org_spendable_balance(db, "ag1")) == 0
    wallet = _run(mod.ensure_wallet(db, "cc1"))
    # lot remaining still 20, unallocated 20
    w2 = _run(mod._refresh_wallet_balances(db, "cc1"))
    assert w2["balance_total"] == 20
    assert w2["balance_unallocated"] == 20


def test_insufficient_debit():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=5,
            origin="t",
            reason="t",
            idempotency_key="i1",
            allocate_to_organization_id="ag1",
        )
    )
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.debit_for_organization(
                db, organization_id="ag1", amount=6, reason="x"
            )
        )
    assert ei.value.detail["error"] == "insufficient_credits"
