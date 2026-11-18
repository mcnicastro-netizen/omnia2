"""MC-042 — CC non operativo: deny wallet operativo; whitelist sola lettura documenti.

Enforcement backend (no UI). Conservazione dati ≠ diritti operativi.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi import HTTPException

from tests.test_b04ii_wallet_ledger import FakeDB, FakeColl, _run, _seed_cc_agency


def _seed_user(db, *, user_id="u_ma", role="agency_admin"):
    if not hasattr(db, "users"):
        db.users = FakeColl()
    db.users.docs.append(
        {
            "id": user_id,
            "role": role,
            "email_verified": True,
            "is_active": True,
            "email": f"{user_id}@test.it",
        }
    )


def _make_ceased(db, cc_id="cc1"):
    for d in db.commercial_customers.docs:
        if d["id"] == cc_id:
            d["commercial_status"] = "ceased"
            d["operational_status"] = "closed_readonly"
            return d
    raise AssertionError("cc missing")


def _grant(db, *, cc_id="cc1", agency_id="ag1", amount=50, key="g"):
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


# --------------- Predicate / central gate ----------------------------


def test_mc042_predicates_align_read_and_mutation():
    from shared.billing.main_admin_service import (
        cc_allows_wallet_admin_read,
        cc_allows_wallet_mutation,
        cc_is_wallet_operable,
    )

    active = {"commercial_status": "active", "operational_status": "full"}
    ceased = {"commercial_status": "ceased", "operational_status": "closed_readonly"}
    none_op = {"commercial_status": "pre_activation", "operational_status": "none"}

    assert cc_is_wallet_operable(active)
    assert cc_allows_wallet_admin_read(active) is True
    assert cc_allows_wallet_mutation(active) is True

    assert not cc_is_wallet_operable(ceased)
    assert cc_allows_wallet_admin_read(ceased) is False
    assert cc_allows_wallet_mutation(ceased) is False

    assert not cc_is_wallet_operable(none_op)
    assert cc_allows_wallet_admin_read(None) is False


def test_mc042_assert_cc_wallet_operable_denies_ceased():
    from shared.billing import main_admin_service as mas

    db = FakeDB()
    _seed_cc_agency(db)
    _make_ceased(db)
    with pytest.raises(HTTPException) as ei:
        _run(mas.assert_cc_wallet_operable(db, "cc1", operation="wallet_read"))
    assert ei.value.status_code == 403
    assert ei.value.detail["error"] == "cc_not_operable"
    events = db["commercial_main_admin_events"].docs
    assert any(e.get("reason") == "cc_not_operable" for e in events)


def test_mc042_main_admin_identity_still_ok_on_ceased_without_wallet_gate():
    """Nomine conservate: assert identità senza require_wallet_operable."""
    from shared.billing import main_admin_service as mas

    db = FakeDB()
    _seed_cc_agency(db)
    _seed_user(db)
    db.commercial_customers.docs[0]["main_admin_user_id"] = "u_ma"
    _make_ceased(db)
    user = {
        "id": "u_ma",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
    }
    cc = _run(mas.assert_is_main_admin_of(db, user, "cc1", for_mutation=False))
    assert cc["id"] == "cc1"
    with pytest.raises(HTTPException) as ei:
        _run(
            mas.assert_is_main_admin_of(
                db, user, "cc1", for_mutation=False, require_wallet_operable=True
            )
        )
    assert ei.value.detail["error"] == "cc_not_operable"


# --------------- Service: allocate / revoke / spend ------------------


def test_mc042_allocate_denied_when_ceased():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=30,
            origin="t",
            reason="t",
            idempotency_key="pre",
        )
    )
    _make_ceased(db)
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.allocate_credits(
                db,
                commercial_customer_id="cc1",
                organization_id="ag1",
                amount=10,
            )
        )
    assert ei.value.status_code == 403
    assert ei.value.detail["error"] == "cc_not_operable"
    assert len(db.credit_allocations.docs) == 0


def test_mc042_revoke_denied_when_ceased_no_mutation():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    alloc_id = _grant(db, amount=20, key="rev-pre")
    before = db.credit_allocations.docs[0]["remaining_qty"]
    ledger_n = len(db.cc_credit_ledger.docs)
    _make_ceased(db)
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.revoke_allocation(
                db,
                allocation_id=alloc_id,
                commercial_customer_id="cc1",
                reason="x",
            )
        )
    assert ei.value.status_code == 403
    assert db.credit_allocations.docs[0]["remaining_qty"] == before
    assert len(db.cc_credit_ledger.docs) == ledger_n


def test_mc042_debit_blocked_when_ceased():
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    _grant(db, amount=15, key="deb")
    _make_ceased(db)
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.debit_for_organization(
                db, organization_id="ag1", amount=1, reason="spend"
            )
        )
    assert ei.value.status_code == 402
    assert ei.value.detail["error"] == "credits_not_spendable"


def test_mc042_debit_blocked_closed_readonly_even_if_status_active():
    """Defense: operational envelope closed_readonly blocca spend."""
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    _grant(db, amount=10, key="clo")
    db.commercial_customers.docs[0]["operational_status"] = "closed_readonly"
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.debit_for_organization(
                db, organization_id="ag1", amount=1, reason="spend"
            )
        )
    assert ei.value.detail["error"] == "credits_not_spendable"


# --------------- Routes: GET wallet / org / subscription -------------


def test_mc042_get_central_wallet_denied_when_ceased(monkeypatch):
    from apps.billing import routes as billing_routes

    db = FakeDB()
    _seed_cc_agency(db)
    _seed_user(db)
    db.commercial_customers.docs[0]["main_admin_user_id"] = "u_ma"
    _make_ceased(db)

    class _DB:
        @staticmethod
        def get():
            return db

    monkeypatch.setattr(billing_routes, "Database", _DB)
    monkeypatch.setattr(billing_routes, "optional_agency_id", lambda u: "ag1")

    user = {
        "id": "u_ma",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
        "active_agency_id": "ag1",
    }
    with pytest.raises(HTTPException) as ei:
        _run(billing_routes.get_central_wallet(user=user))
    assert ei.value.status_code == 403
    assert ei.value.detail["error"] == "cc_not_operable"


def test_mc042_super_admin_read_also_denied_when_ceased(monkeypatch):
    from apps.billing import routes as billing_routes

    db = FakeDB()
    _seed_cc_agency(db)
    _make_ceased(db)

    class _DB:
        @staticmethod
        def get():
            return db

    monkeypatch.setattr(billing_routes, "Database", _DB)
    monkeypatch.setattr(billing_routes, "optional_agency_id", lambda u: "ag1")

    user = {
        "id": "ops",
        "role": "super_admin",
        "email_verified": True,
        "is_active": True,
        "active_agency_id": "ag1",
    }
    with pytest.raises(HTTPException) as ei:
        _run(billing_routes.get_central_wallet(user=user))
    assert ei.value.detail["error"] == "cc_not_operable"


def test_mc042_org_wallet_denied_when_ceased(monkeypatch):
    from apps.billing import routes as billing_routes

    db = FakeDB()
    _seed_cc_agency(db)
    _grant(db, amount=7, key="org")
    _make_ceased(db)

    class _DB:
        @staticmethod
        def get():
            return db

    monkeypatch.setattr(billing_routes, "Database", _DB)
    monkeypatch.setattr(
        billing_routes, "require_agency", lambda user: user["active_agency_id"]
    )

    with pytest.raises(HTTPException) as ei:
        _run(
            billing_routes.get_org_wallet(
                user={"id": "u", "role": "branch_admin", "active_agency_id": "ag1"}
            )
        )
    assert ei.value.status_code == 403
    assert ei.value.detail["error"] == "cc_not_operable"


def test_mc042_org_wallet_ok_when_active(monkeypatch):
    from apps.billing import routes as billing_routes

    db = FakeDB()
    _seed_cc_agency(db)
    _grant(db, amount=7, key="orgok")

    class _DB:
        @staticmethod
        def get():
            return db

    monkeypatch.setattr(billing_routes, "Database", _DB)
    monkeypatch.setattr(
        billing_routes, "require_agency", lambda user: user["active_agency_id"]
    )

    out = _run(
        billing_routes.get_org_wallet(
            user={"id": "u", "role": "branch_admin", "active_agency_id": "ag1"}
        )
    )
    assert out["spendable"] == 7


def test_mc042_subscription_redacts_wallet_when_ceased(monkeypatch):
    from apps.billing import routes as billing_routes

    db = FakeDB()
    _seed_cc_agency(db)
    db.credit_wallets.docs.append({"agency_id": "ag1", "balance": 99})
    db.subscriptions = FakeColl()
    db.subscriptions.docs.append({"agency_id": "ag1", "status": "canceled"})
    _make_ceased(db)

    class _DB:
        @staticmethod
        def get():
            return db

    monkeypatch.setattr(billing_routes, "Database", _DB)
    monkeypatch.setattr(billing_routes, "optional_agency_id", lambda u: "ag1")

    out = _run(
        billing_routes.get_subscription(
            user={"id": "u", "role": "agency_admin", "active_agency_id": "ag1"}
        )
    )
    assert out["wallet"].get("redacted") is True
    assert "balance" not in out["wallet"] or out["wallet"].get("balance") is None
    assert out["counters"]["credits"].get("redacted") is True
    assert out["commercial_customer"]["commercial_status"] == "ceased"
    assert out["subscription"]["status"] == "canceled"


def test_mc042_allocate_route_denied(monkeypatch):
    from apps.billing import routes as billing_routes
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db)
    _seed_user(db)
    db.commercial_customers.docs[0]["main_admin_user_id"] = "u_ma"
    _run(
        mod.grant_lot(
            db,
            commercial_customer_id="cc1",
            amount=40,
            origin="t",
            reason="t",
            idempotency_key="ar",
        )
    )
    _make_ceased(db)

    class _DB:
        @staticmethod
        def get():
            return db

    monkeypatch.setattr(billing_routes, "Database", _DB)
    monkeypatch.setattr(billing_routes, "optional_agency_id", lambda u: "ag1")

    user = {
        "id": "u_ma",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
        "active_agency_id": "ag1",
    }
    with pytest.raises(HTTPException) as ei:
        _run(
            billing_routes.allocate_wallet_credits(
                payload={"organization_id": "ag1", "amount": 5},
                user=user,
            )
        )
    assert ei.value.detail["error"] == "cc_not_operable"


def test_mc042_h1_cross_tenant_revoke_still_404():
    """Regressione isolamento: cross-tenant resta 404, non vira in cc_not_operable."""
    from shared.billing import credit_wallet_service as mod

    db = FakeDB()
    _seed_cc_agency(db, cc_id="ccVictim", agency_id="agVictim")
    _seed_cc_agency(db, cc_id="ccAttacker", agency_id="agAttacker")
    victim_alloc = _grant(
        db, cc_id="ccVictim", agency_id="agVictim", amount=40, key="vic2"
    )
    with pytest.raises(HTTPException) as ei:
        _run(
            mod.revoke_allocation(
                db,
                allocation_id=victim_alloc,
                commercial_customer_id="ccAttacker",
                reason="attack",
            )
        )
    assert ei.value.status_code == 404
    assert ei.value.detail["error"] == "allocation_not_found"


def test_mc042_no_customer_closure_billing_doc_routes():
    """DISCREPANZA documentata: nessun endpoint CC chiusura/fatture cliente."""
    from apps.billing import routes as billing_routes

    names = [
        n
        for n, _ in inspect.getmembers(billing_routes, inspect.iscoroutinefunction)
    ]
    forbidden_guesses = {
        "list_closure_documents",
        "get_closure_document",
        "list_customer_invoices",
        "get_customer_invoice",
        "download_invoice",
    }
    assert forbidden_guesses.isdisjoint(set(names))
