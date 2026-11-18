"""MC-045 / H3 — allocate solo a Organization linkate al CommercialCustomer."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from tests.test_b04_h2_main_admin import _DBProxy, _seed_user
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run, _seed_cc_agency


def _snapshot(db: FakeDB) -> dict:
    return {
        "lots": [dict(x) for x in db.credit_lots.docs],
        "allocs": [dict(x) for x in db.credit_allocations.docs],
        "ledger": [dict(x) for x in db.cc_credit_ledger.docs],
        "wallets": [dict(x) for x in db.cc_credit_wallets.docs],
    }


def test_h3_allocate_same_cc_allowed():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=20,
            origin="t",
            reason="t",
            idempotency_key="h3ok",
        )
    )
    before_ledger = len(db.cc_credit_ledger.docs)
    created = _run(
        mod.allocate_credits(
            db,
            commercial_customer_id="cc1",
            organization_id="ag1",
            amount=7,
        )
    )
    assert len(created) >= 1
    assert sum(int(a["remaining_qty"]) for a in created) == 7
    assert len(db.credit_allocations.docs) >= 1
    assert len(db.cc_credit_ledger.docs) > before_ledger
    assert _run(mod.org_spendable_balance(db, "ag1")) == 7


def test_h3_allocate_unlinked_org_denied_no_mutation():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    db.agencies.docs.append({"id": "ag_orphan", "display_name": "No CC"})
    # no commercial_customer_id
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=15,
            origin="t",
            reason="t",
            idempotency_key="h3ul",
        )
    )
    snap = _snapshot(db)
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag_orphan",
                amount=5,
            )
        )
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "organization_not_linked_to_cc"
    assert _snapshot(db) == snap


def test_h3_allocate_null_link_denied():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    db.agencies.docs.append(
        {"id": "ag_null", "commercial_customer_id": None, "display_name": "Null"}
    )
    db.agencies.docs.append(
        {"id": "ag_empty", "commercial_customer_id": "  ", "display_name": "Empty"}
    )
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=10,
            origin="t",
            reason="t",
            idempotency_key="h3null",
        )
    )
    snap = _snapshot(db)
    for oid in ("ag_null", "ag_empty"):
        with pytest.raises(HTTPException) as ei:
            _run(
                mod.allocate_credits(
                    db,
                    commercial_customer_id="cc1",
                    organization_id=oid,
                    amount=1,
                )
            )
        assert ei.value.detail["error"] == "organization_not_linked_to_cc"
    assert _snapshot(db) == snap


def test_h3_allocate_missing_org_denied_no_mutation():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=10,
            origin="t",
            reason="t",
            idempotency_key="h3miss",
        )
    )
    snap = _snapshot(db)
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag_does_not_exist",
                amount=3,
            )
        )
    assert ei.value.status_code == 404
    assert ei.value.detail["error"] == "organization_not_found"
    assert _snapshot(db) == snap


def test_h3_allocate_other_cc_denied_no_mutation():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    db.agencies.docs.append({"id": "ag2", "commercial_customer_id": "ccOTHER"})
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=10,
            origin="t",
            reason="t",
            idempotency_key="h3x",
        )
    )
    snap = _snapshot(db)
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag2",
                amount=4,
            )
        )
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "cross_vat_transfer_forbidden"
    assert _snapshot(db) == snap


def test_h3_grant_lot_auto_allocate_respects_link():
    """Percorso alternativo grant_lot → allocate: check link prima del grant."""
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    db.agencies.docs.append({"id": "ag_bad"})
    snap = _snapshot(db)
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.grant_lot(
                db,
                commercial_customer_id="cc1",
                amount=8,
                origin="t",
                reason="t",
                idempotency_key="h3grant",
                allocate_to_organization_id="ag_bad",
            )
        )
    assert ei.value.detail["error"] == "organization_not_linked_to_cc"
    assert _snapshot(db) == snap


def test_h3_insufficient_unallocated_no_partial():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="cc1", agency_id="ag1")
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=5,
            origin="t",
            reason="t",
            idempotency_key="h3ins",
        )
    )
    snap = _snapshot(db)
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag1",
                amount=99,
            )
        )
    assert ei.value.status_code == 409
    assert ei.value.detail["error"] == "insufficient_unallocated_credits"
    # rollback: no leftover allocations from failed call
    assert len(db.credit_allocations.docs) == len(snap["allocs"])


def test_h3_route_allocate_denies_non_main_admin(monkeypatch):
    from apps.billing import routes as billing_routes
    from shared.billing import main_admin_service as mas
    from shared.db.connection import Database

    raw = FakeDB()
    _seed_cc_agency(raw, cc_id="cc1", agency_id="ag1")
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_other", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    monkeypatch.setattr(Database, "get", staticmethod(lambda: db))
    user = {
        "id": "u_other",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    with pytest.raises(HTTPException) as ei:
        _run(
            billing_routes.allocate_wallet_credits(
                {"organization_id": "ag1", "amount": 1},
                user,
            )
        )
    assert ei.value.status_code == 403
