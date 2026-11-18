"""MC-042 v2 lockout + MC-054 day-8 option B + MC-055…059 deroga."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from tests.test_b04_h2_main_admin import _DBProxy, _patch_event_coll, _seed_user
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run, _seed_cc_agency


def _req(path: str):
    return SimpleNamespace(url=SimpleNamespace(path=path))


def test_wallet_operable_denies_suspended_and_billing_only():
    from shared.billing.main_admin_service import cc_is_wallet_operable

    assert not cc_is_wallet_operable(
        {"commercial_status": "suspended", "operational_status": "billing_only"}
    )
    assert not cc_is_wallet_operable(
        {"commercial_status": "active", "operational_status": "billing_only"}
    )
    assert cc_is_wallet_operable(
        {"commercial_status": "active", "operational_status": "full"}
    )


def test_login_denied_when_ceased():
    from shared.billing.commercial_access import assert_user_login_allowed

    raw = FakeDB()
    _seed_cc_agency(raw, status="ceased")
    raw.commercial_customers.docs[0]["operational_status"] = "closed_readonly"
    _seed_user(raw, user_id="u1", role="agency_admin")
    db = _DBProxy(raw)
    user = {
        "id": "u1",
        "role": "agency_admin",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    with pytest.raises(HTTPException) as ei:
        _run(assert_user_login_allowed(db, user))
    assert ei.value.status_code == 403
    assert ei.value.detail["error"] == "commercial_customer_ceased"


def test_login_allowed_for_super_admin_even_if_ceased_agency():
    from shared.billing.commercial_access import assert_user_login_allowed

    raw = FakeDB()
    _seed_cc_agency(raw, status="ceased")
    db = _DBProxy(raw)
    _run(assert_user_login_allowed(db, {"id": "ops", "role": "super_admin"}))


def test_suspended_collaborator_denied_all_paths():
    from shared.billing.commercial_access import enforce_commercial_access

    raw = FakeDB()
    _seed_cc_agency(raw, status="suspended")
    raw.commercial_customers.docs[0]["operational_status"] = "billing_only"
    raw.commercial_customers.docs[0]["main_admin_user_id"] = "u_ma"
    db = _DBProxy(raw)
    collab = {
        "id": "u_collab",
        "role": "agent",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    with pytest.raises(HTTPException) as ei:
        _run(enforce_commercial_access(db, collab, _req("/api/billing/subscription")))
    assert ei.value.detail["error"] == "commercial_customer_suspended"


def test_suspended_main_admin_billing_only_paths():
    from shared.billing.commercial_access import enforce_commercial_access

    raw = FakeDB()
    _seed_cc_agency(raw, status="suspended")
    raw.commercial_customers.docs[0]["operational_status"] = "billing_only"
    raw.commercial_customers.docs[0]["main_admin_user_id"] = "u_ma"
    db = _DBProxy(raw)
    ma = {
        "id": "u_ma",
        "role": "agency_admin",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    _run(enforce_commercial_access(db, ma, _req("/api/billing/portal")))
    _run(enforce_commercial_access(db, ma, _req("/api/auth/me")))
    with pytest.raises(HTTPException) as ei:
        _run(enforce_commercial_access(db, ma, _req("/api/crm/contacts")))
    assert ei.value.detail["error"] == "commercial_customer_suspended_billing_only"


def test_deroga_restores_access_and_wallet(monkeypatch):
    from shared.billing import main_admin_service as mas
    from shared.billing import commercial_access as ca

    raw = FakeDB()
    _seed_cc_agency(raw, status="suspended")
    raw.commercial_customers.docs[0]["operational_status"] = "billing_only"
    raw.commercial_customers.docs[0]["main_admin_user_id"] = "u_ma"
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _patch_event_coll(raw)
    db = _DBProxy(raw)

    monkeypatch.setattr(
        "shared.email.send_email",
        AsyncMock(return_value={"id": "m1", "status": "mock"}),
        raising=False,
    )
    monkeypatch.setattr(
        ca,
        "send_email",
        AsyncMock(return_value={"id": "m1", "status": "mock"}),
        raising=False,
    )

    # Patch import path used inside grant
    import shared.email as email_mod

    monkeypatch.setattr(
        email_mod,
        "send_email",
        AsyncMock(return_value={"id": "m1", "status": "mock"}),
    )

    deroga = _run(
        ca.grant_reactivation_deroga(
            db,
            commercial_customer_id="cc1",
            actor={"id": "ops", "role": "super_admin", "email": "ops@x.it"},
            reason="cliente storico in attesa bonifico",
            amount_due=199.0,
            duration_hours=48,
        )
    )
    assert deroga["status"] == "active"

    ma = {
        "id": "u_ma",
        "role": "agency_admin",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    # Full path OK under deroga
    _run(ca.enforce_commercial_access(db, ma, _req("/api/crm/contacts")))
    # Wallet operable via assert (deroga bypass)
    out = _run(mas.assert_cc_wallet_operable(db, "cc1"))
    assert out["id"] == "cc1"


def test_expire_deroga_resuspends():
    from shared.billing import commercial_access as ca

    raw = FakeDB()
    _seed_cc_agency(raw, status="active")
    db = _DBProxy(raw)
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    db[ca.DEROGA_COLL].docs.append(
        {
            "id": "d1",
            "commercial_customer_id": "cc1",
            "status": "active",
            "ends_at": past,
            "starts_at": past,
        }
    )
    report = _run(ca.expire_due_deroghe(db))
    assert report["expired"] == 1
    cc = raw.commercial_customers.docs[0]
    assert cc["commercial_status"] == "suspended"
    assert cc["operational_status"] == "billing_only"
    assert db[ca.DEROGA_COLL].docs[0]["status"] == "expired"


def test_reactivate_on_full_payment_closes_deroga():
    from shared.billing import commercial_access as ca

    raw = FakeDB()
    _seed_cc_agency(raw, status="suspended")
    raw.commercial_customers.docs[0]["operational_status"] = "billing_only"
    raw.invoices = FakeColl()
    db = _DBProxy(raw)
    # invoice appena pagata — esclusa dal check; nessun altro insoluto
    db.invoices.docs.append(
        {
            "id": "inv_paid",
            "agency_id": "ag1",
            "stripe_invoice_id": "in_paid_now",
            "status": "paid",
            "amount_due": 100.0,
            "amount_paid": 100.0,
        }
    )
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    db[ca.DEROGA_COLL].docs.append(
        {
            "id": "d2",
            "commercial_customer_id": "cc1",
            "status": "active",
            "ends_at": future,
        }
    )
    out = _run(
        ca.reactivate_cc_on_full_payment(
            db, "cc1", exclude_stripe_invoice_id="in_paid_now"
        )
    )
    assert out["ok"] is True
    cc = raw.commercial_customers.docs[0]
    assert cc["commercial_status"] == "active"
    assert cc["operational_status"] == "full"
    assert db[ca.DEROGA_COLL].docs[0]["status"] == "closed_paid"


def test_reactivate_blocked_when_other_invoice_open():
    """MC-055 — pagamento parziale / altro insoluto → nessuna riattivazione."""
    from shared.billing import commercial_access as ca

    raw = FakeDB()
    _seed_cc_agency(raw, status="suspended")
    raw.commercial_customers.docs[0]["operational_status"] = "billing_only"
    raw.invoices = FakeColl()
    db = _DBProxy(raw)
    db.invoices.docs.append(
        {
            "id": "inv1",
            "agency_id": "ag1",
            "stripe_invoice_id": "in_just_paid",
            "status": "paid",
            "amount_due": 50.0,
            "amount_paid": 50.0,
        }
    )
    db.invoices.docs.append(
        {
            "id": "inv2",
            "agency_id": "ag1",
            "stripe_invoice_id": "in_still_open",
            "status": "open",
            "amount_due": 80.0,
            "amount_paid": 0.0,
        }
    )
    out = _run(
        ca.reactivate_cc_on_full_payment(
            db, "cc1", exclude_stripe_invoice_id="in_just_paid"
        )
    )
    assert out["ok"] is False
    assert out["skipped"] == "outstanding_balance"
    assert out["outstanding_count"] >= 1
    cc = raw.commercial_customers.docs[0]
    assert cc["commercial_status"] == "suspended"


def test_day8_suspension_from_past_due():
    from shared.billing import commercial_access as ca

    raw = FakeDB()
    _seed_cc_agency(raw, status="active")
    raw.commercial_customers.docs[0]["operational_status"] = "full"
    old = (datetime.now(timezone.utc) - timedelta(days=9)).isoformat()
    raw.subscriptions = getattr(raw, "subscriptions", None) or type(raw.agencies)()
    # FakeDB may not have subscriptions — create via proxy
    db = _DBProxy(raw)
    db.subscriptions.docs.append(
        {
            "id": "sub1",
            "agency_id": "ag1",
            "commercial_customer_id": "cc1",
            "status": "past_due",
            "payment_failed_at": old,
        }
    )
    report = _run(ca.apply_day8_suspensions(db, grace_days=8))
    assert report["applied"] == 1
    cc = raw.commercial_customers.docs[0]
    assert cc["commercial_status"] == "suspended"
    assert cc["operational_status"] == "billing_only"


def test_billing_recovery_path_helper():
    from shared.billing.commercial_access import is_billing_recovery_path

    assert is_billing_recovery_path("/api/billing/portal")
    assert is_billing_recovery_path("/billing/checkout")
    assert not is_billing_recovery_path("/api/billing/credits/purchase")
    assert not is_billing_recovery_path("/api/crm/leads")
