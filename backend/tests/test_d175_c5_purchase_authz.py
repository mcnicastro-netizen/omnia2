"""D-175 C5 — Main Admin purchase authz + DENY ⇒ zero Stripe calls."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from apps.billing.models import CreditPurchaseRequest, StoragePurchaseRequest
from tests.test_b04_h2_main_admin import _DBProxy, _patch_event_coll, _seed_user
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run, _seed_cc_agency


def _seed_cc(
    db: FakeDB,
    *,
    cc_id: str = "cc1",
    ma_id: str | None = "u_ma",
    commercial_status: str = "active",
    operational_status: str = "full",
    agency_id: str = "ag1",
):
    db.commercial_customers = FakeColl()
    db.agencies = FakeColl()
    db.payment_transactions = FakeColl()
    db.commercial_customers.docs.append(
        {
            "id": cc_id,
            "legal_name": "ACME SRL",
            "vat_number_normalized": "123",
            "main_admin_user_id": ma_id,
            "commercial_status": commercial_status,
            "operational_status": operational_status,
            "stripe_customer_id": "cus_existing",
        }
    )
    db.agencies.docs.append(
        {
            "id": agency_id,
            "commercial_customer_id": cc_id,
            "display_name": "Sede",
        }
    )
    _patch_event_coll(db)


class _StripeSpies:
    def __init__(self):
        self.price_list = MagicMock(return_value=SimpleNamespace(data=[]))
        self.customer_create = MagicMock()
        self.session_create = MagicMock()
        self.get_or_create = AsyncMock(return_value="cus_new")


def _open_h4(monkeypatch, tmp_path):
    marker = tmp_path / "h4.sealed"
    marker.write_text("H4_PURCHASE_READY_V1=c6_verified_token_ok99\n", encoding="utf-8")
    monkeypatch.setenv("OMNIA_H4_READY_MARKER_PATH", str(marker))
    monkeypatch.setenv("OMNIA_H4_PURCHASE_READY", "true")
    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "true")
    monkeypatch.setenv("STRIPE_ENABLED", "true")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")


def _user(
    *,
    user_id: str = "u_ma",
    role: str = "agency_admin",
    verified: bool = True,
    active: bool = True,
    agency_ids=None,
    active_agency_id=None,
):
    return {
        "id": user_id,
        "email": f"{user_id}@x.it",
        "role": role,
        "email_verified": verified,
        "is_active": active,
        "agency_ids": agency_ids if agency_ids is not None else [],
        "active_agency_id": active_agency_id,
    }


@pytest.fixture
def spies(monkeypatch):
    s = _StripeSpies()
    import apps.billing.routes as routes
    import shared.billing.stripe_customer_service as scs

    monkeypatch.setattr(routes.stripe.Price, "list", s.price_list)
    monkeypatch.setattr(routes.stripe.Customer, "create", s.customer_create)
    monkeypatch.setattr(routes.stripe.checkout.Session, "create", s.session_create)
    monkeypatch.setattr(scs, "get_or_create_stripe_customer", s.get_or_create)
    # also patch where routes imports at call time — buy_* imports get_or_create inside
    return s


def _assert_zero_stripe(spies: _StripeSpies):
    assert spies.price_list.call_count == 0
    assert spies.customer_create.call_count == 0
    assert spies.session_create.call_count == 0
    assert spies.get_or_create.await_count == 0


def test_c5_h4_closed_zero_stripe(monkeypatch, spies):
    from apps.billing import routes as billing_routes

    monkeypatch.setenv("OMNIA_H4_PURCHASE_READY", "true")  # alone insufficient
    monkeypatch.delenv("OMNIA_H4_READY_MARKER_PATH", raising=False)
    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "true")
    monkeypatch.setenv("STRIPE_ENABLED", "true")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")

    payload = CreditPurchaseRequest(
        package_key="pkg_400", commercial_customer_id="cc1"
    )
    with pytest.raises(HTTPException) as ei:
        _run(billing_routes.buy_credits(payload, MagicMock(), _user()))
    assert ei.value.status_code == 503
    assert ei.value.detail["error"] == "h4_not_ready"
    _assert_zero_stripe(spies)


@pytest.mark.parametrize(
    "case,user,cc_kwargs,payload_cc,agency_ctx,status,err",
    [
        (
            "sa",
            _user(user_id="ops", role="super_admin"),
            {},
            "cc1",
            None,
            403,
            "sa_purchase_forbidden",
        ),
        (
            "sa_who_is_ma",
            _user(user_id="u_ma", role="super_admin"),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "sa_purchase_forbidden",
        ),
        (
            "not_ma",
            _user(user_id="u_other", role="agency_admin", agency_ids=["ag1"], active_agency_id="ag1"),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "not_main_admin",
        ),
        (
            "org_admin",
            _user(user_id="u_org", role="agency_admin", agency_ids=["ag1"], active_agency_id="ag1"),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "not_main_admin",
        ),
        (
            "collaborator",
            _user(user_id="u_agent", role="agent", agency_ids=["ag1"], active_agency_id="ag1"),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "not_main_admin",
        ),
        (
            "cc_missing_body",
            _user(user_id="u_ma", role="agency_admin"),
            {},
            "   ",
            None,
            400,
            "commercial_customer_id_required",
        ),
        (
            "cc_inexistent",
            _user(user_id="u_ma", role="agency_admin"),
            {},
            "cc_missing",
            None,
            404,
            "commercial_customer_not_found",
        ),
        (
            "cc_no_ma",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": None},
            "cc1",
            None,
            403,
            "main_admin_unassigned",
        ),
        (
            "ma_not_eligible",
            _user(user_id="u_ma", role="agency_admin", verified=False),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "account_not_eligible",
        ),
        (
            "cc_not_operable",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": "u_ma", "commercial_status": "ceased", "operational_status": "closed_readonly"},
            "cc1",
            None,
            403,
            "cc_not_operable",
        ),
        (
            "wrong_cc",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": "u_ma"},
            "cc_other",
            None,
            404,
            "commercial_customer_not_found",
        ),
        (
            "agency_mismatch",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": "u_ma"},
            "cc1",
            "ag_other",
            403,
            "agency_cc_mismatch",
        ),
    ],
)
def test_c5_deny_matrix_zero_stripe(
    monkeypatch, tmp_path, spies, case, user, cc_kwargs, payload_cc, agency_ctx, status, err
):
    from apps.billing import routes as billing_routes

    _open_h4(monkeypatch, tmp_path)
    raw = FakeDB()
    _seed_cc(raw, **cc_kwargs)
    if case == "wrong_cc":
        # only cc1 seeded; request other id
        pass
    if case == "agency_mismatch":
        raw.agencies.docs.append(
            {"id": "ag_other", "commercial_customer_id": "cc_foreign"}
        )
    db = _DBProxy(raw)

    with patch("apps.billing.routes.Database.get", return_value=db):
        payload = CreditPurchaseRequest(
            package_key="pkg_400",
            commercial_customer_id=payload_cc,
            agency_id=agency_ctx,
        )
        with pytest.raises(HTTPException) as ei:
            _run(billing_routes.buy_credits(payload, MagicMock(base_url="http://x/"), user))
    assert ei.value.status_code == status
    detail = ei.value.detail
    if isinstance(detail, dict):
        assert detail.get("error") == err
    _assert_zero_stripe(spies)


def test_c5_ma_revoked_zero_stripe(monkeypatch, tmp_path, spies):
    from apps.billing import routes as billing_routes

    _open_h4(monkeypatch, tmp_path)
    raw = FakeDB()
    _seed_cc(raw, ma_id="u_new")  # revoked from u_ma
    db = _DBProxy(raw)
    with patch("apps.billing.routes.Database.get", return_value=db):
        payload = CreditPurchaseRequest(
            package_key="pkg_400", commercial_customer_id="cc1"
        )
        with pytest.raises(HTTPException) as ei:
            _run(
                billing_routes.buy_credits(
                    payload, MagicMock(base_url="http://x/"), _user(user_id="u_ma")
                )
            )
    assert ei.value.status_code == 403
    assert ei.value.detail["error"] == "not_main_admin"
    _assert_zero_stripe(spies)


def test_c5_allow_ma_without_membership_mocks_stripe(monkeypatch, tmp_path, spies):
    from apps.billing import routes as billing_routes

    _open_h4(monkeypatch, tmp_path)
    raw = FakeDB()
    _seed_cc(raw, ma_id="u_ma")
    db = _DBProxy(raw)

    price = SimpleNamespace(id="price_1", currency="eur")
    spies.price_list.return_value = SimpleNamespace(data=[price])
    spies.get_or_create = AsyncMock(return_value="cus_existing")
    import shared.billing.stripe_customer_service as scs

    monkeypatch.setattr(scs, "get_or_create_stripe_customer", spies.get_or_create)
    spies.session_create.return_value = SimpleNamespace(
        id="cs_test_1", url="https://checkout.stripe.test/cs"
    )

    with patch("apps.billing.routes.Database.get", return_value=db):
        payload = CreditPurchaseRequest(
            package_key="pkg_400", commercial_customer_id="cc1"
        )
        # MA without agency_ids / active_agency
        out = _run(
            billing_routes.buy_credits(
                payload,
                MagicMock(base_url="http://localhost/"),
                _user(user_id="u_ma", agency_ids=[], active_agency_id=None),
            )
        )

    assert out["checkout_url"].startswith("https://checkout.stripe.test/")
    assert out["commercial_customer_id"] == "cc1"
    assert out["stripe_customer_id"] == "cus_existing"
    assert spies.price_list.call_count == 1
    assert spies.session_create.call_count == 1
    assert spies.get_or_create.await_count == 1
    assert spies.customer_create.call_count == 0  # reused existing via helper mock
    kwargs = spies.session_create.call_args.kwargs
    assert kwargs["customer"] == "cus_existing"
    assert kwargs["metadata"]["commercial_customer_id"] == "cc1"
    assert kwargs["metadata"]["kind"] == "credits_topup"
    # no customer_email binding
    assert "customer_email" not in kwargs
    tx = db.payment_transactions.docs[-1]
    assert tx["commercial_customer_id"] == "cc1"
    assert tx["stripe_customer_id"] == "cus_existing"
    assert tx.get("agency_id") in (None, "")


@pytest.mark.parametrize(
    "case,user,cc_kwargs,payload_cc,agency_ctx,status,err",
    [
        (
            "sa",
            _user(user_id="ops", role="super_admin"),
            {},
            "cc1",
            None,
            403,
            "sa_purchase_forbidden",
        ),
        (
            "sa_who_is_ma",
            _user(user_id="u_ma", role="super_admin"),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "sa_purchase_forbidden",
        ),
        (
            "not_ma",
            _user(user_id="u_other", role="agency_admin", agency_ids=["ag1"], active_agency_id="ag1"),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "not_main_admin",
        ),
        (
            "org_admin",
            _user(user_id="u_org", role="agency_admin", agency_ids=["ag1"], active_agency_id="ag1"),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "not_main_admin",
        ),
        (
            "collaborator",
            _user(user_id="u_agent", role="agent", agency_ids=["ag1"], active_agency_id="ag1"),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "not_main_admin",
        ),
        (
            "cc_missing_body",
            _user(user_id="u_ma", role="agency_admin"),
            {},
            "   ",
            None,
            400,
            "commercial_customer_id_required",
        ),
        (
            "cc_inexistent",
            _user(user_id="u_ma", role="agency_admin"),
            {},
            "cc_missing",
            None,
            404,
            "commercial_customer_not_found",
        ),
        (
            "cc_no_ma",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": None},
            "cc1",
            None,
            403,
            "main_admin_unassigned",
        ),
        (
            "ma_not_eligible",
            _user(user_id="u_ma", role="agency_admin", verified=False),
            {"ma_id": "u_ma"},
            "cc1",
            None,
            403,
            "account_not_eligible",
        ),
        (
            "cc_not_operable",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": "u_ma", "commercial_status": "ceased", "operational_status": "closed_readonly"},
            "cc1",
            None,
            403,
            "cc_not_operable",
        ),
        (
            "wrong_cc",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": "u_ma"},
            "cc_other",
            None,
            404,
            "commercial_customer_not_found",
        ),
        (
            "agency_mismatch",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": "u_ma"},
            "cc1",
            "ag_other",
            403,
            "agency_cc_mismatch",
        ),
        (
            "ma_revoked",
            _user(user_id="u_ma", role="agency_admin"),
            {"ma_id": "u_new"},
            "cc1",
            None,
            403,
            "not_main_admin",
        ),
    ],
)
def test_c5_storage_deny_matrix_zero_stripe(
    monkeypatch, tmp_path, spies, case, user, cc_kwargs, payload_cc, agency_ctx, status, err
):
    from apps.billing import routes as billing_routes

    _open_h4(monkeypatch, tmp_path)
    raw = FakeDB()
    _seed_cc(raw, **cc_kwargs)
    if case == "agency_mismatch":
        raw.agencies.docs.append(
            {"id": "ag_other", "commercial_customer_id": "cc_foreign"}
        )
    db = _DBProxy(raw)

    with patch("apps.billing.routes.Database.get", return_value=db):
        payload = StoragePurchaseRequest(
            commercial_customer_id=payload_cc,
            agency_id=agency_ctx,
        )
        with pytest.raises(HTTPException) as ei:
            _run(billing_routes.buy_storage(payload, MagicMock(base_url="http://x/"), user))
    assert ei.value.status_code == status
    detail = ei.value.detail
    if isinstance(detail, dict):
        assert detail.get("error") == err
    _assert_zero_stripe(spies)


def test_c5_storage_self_serve_off_after_ma_auth_no_stripe(monkeypatch, tmp_path, spies):
    """Self-serve OFF: MA ALLOW → soft assistito; non-MA still DENY before soft."""
    from apps.billing import routes as billing_routes

    _open_h4(monkeypatch, tmp_path)
    monkeypatch.setenv("OMNIA_SELF_SERVE_ENABLED", "false")
    raw = FakeDB()
    _seed_cc(raw, ma_id="u_ma")
    db = _DBProxy(raw)

    with patch("apps.billing.routes.Database.get", return_value=db):
        # non-MA: must DENY (not soft assistito)
        with pytest.raises(HTTPException) as ei:
            _run(
                billing_routes.buy_storage(
                    StoragePurchaseRequest(commercial_customer_id="cc1"),
                    MagicMock(base_url="http://x/"),
                    _user(
                        user_id="u_org",
                        role="agency_admin",
                        agency_ids=["ag1"],
                        active_agency_id="ag1",
                    ),
                )
            )
        assert ei.value.detail["error"] == "not_main_admin"
        _assert_zero_stripe(spies)

        # MA: soft self_serve_blocked, still zero Stripe
        out = _run(
            billing_routes.buy_storage(
                StoragePurchaseRequest(commercial_customer_id="cc1"),
                MagicMock(base_url="http://x/"),
                _user(user_id="u_ma"),
            )
        )
    assert out.get("self_serve_blocked") is True
    assert out.get("commercial_customer_id") == "cc1"
    assert "checkout_url" not in out
    _assert_zero_stripe(spies)


def test_c5_storage_stripe_off_after_ma_auth_no_stripe(monkeypatch, tmp_path, spies):
    from apps.billing import routes as billing_routes

    _open_h4(monkeypatch, tmp_path)
    monkeypatch.setenv("STRIPE_ENABLED", "false")
    raw = FakeDB()
    _seed_cc(raw, ma_id="u_ma")
    db = _DBProxy(raw)
    with patch("apps.billing.routes.Database.get", return_value=db):
        with pytest.raises(HTTPException) as ei:
            _run(
                billing_routes.buy_storage(
                    StoragePurchaseRequest(commercial_customer_id="cc1"),
                    MagicMock(base_url="http://x/"),
                    _user(user_id="ops", role="super_admin"),
                )
            )
        assert ei.value.detail["error"] == "sa_purchase_forbidden"
        _assert_zero_stripe(spies)

        out = _run(
            billing_routes.buy_storage(
                StoragePurchaseRequest(commercial_customer_id="cc1"),
                MagicMock(base_url="http://x/"),
                _user(user_id="u_ma"),
            )
        )
    assert out.get("stripe_required") is True
    assert out.get("commercial_customer_id") == "cc1"
    _assert_zero_stripe(spies)


def test_c5_storage_allow_tx_cc_no_agency_quota_write(monkeypatch, tmp_path, spies):
    from apps.billing import routes as billing_routes

    _open_h4(monkeypatch, tmp_path)
    raw = FakeDB()
    _seed_cc(raw, ma_id="u_ma")
    raw.agencies.docs[0]["storage_extra_gb"] = 0
    db = _DBProxy(raw)
    price = SimpleNamespace(id="price_s", currency="eur")
    spies.price_list.return_value = SimpleNamespace(data=[price])
    spies.get_or_create = AsyncMock(return_value="cus_existing")
    import shared.billing.stripe_customer_service as scs

    monkeypatch.setattr(scs, "get_or_create_stripe_customer", spies.get_or_create)
    spies.session_create.return_value = SimpleNamespace(
        id="cs_s1", url="https://checkout.stripe.test/s"
    )
    with patch("apps.billing.routes.Database.get", return_value=db):
        payload = StoragePurchaseRequest(commercial_customer_id="cc1")
        out = _run(
            billing_routes.buy_storage(
                payload,
                MagicMock(base_url="http://localhost/"),
                _user(user_id="u_ma"),
            )
        )
    assert out["commercial_customer_id"] == "cc1"
    assert db.agencies.docs[0]["storage_extra_gb"] == 0  # C5 does not mutate quota
    assert spies.session_create.call_args.kwargs["metadata"]["kind"] == "storage_addon"


def test_c5_crit04_sealed_fixture_org_admin_deny(monkeypatch, tmp_path, spies):
    """Sealed+env open gate but org admin still DENY with zero Stripe."""
    from apps.billing import routes as billing_routes

    _open_h4(monkeypatch, tmp_path)
    raw = FakeDB()
    _seed_cc(raw, ma_id="u_ma")
    db = _DBProxy(raw)
    with patch("apps.billing.routes.Database.get", return_value=db):
        payload = CreditPurchaseRequest(
            package_key="pkg_400", commercial_customer_id="cc1"
        )
        with pytest.raises(HTTPException) as ei:
            _run(
                billing_routes.buy_credits(
                    payload,
                    MagicMock(base_url="http://x/"),
                    _user(
                        user_id="u_org",
                        role="agency_admin",
                        agency_ids=["ag1"],
                        active_agency_id="ag1",
                    ),
                )
            )
    assert ei.value.detail["error"] == "not_main_admin"
    _assert_zero_stripe(spies)


def test_sealed_marker_not_created_in_repo():
    from pathlib import Path
    from shared.dogfood.perimeter import h4_ready_marker_path

    # default repo path must remain absent (C5 must never mint)
    default = Path(__file__).resolve().parents[2] / "dogfood" / "h4_purchase_ready.sealed"
    assert not default.is_file()
    # helper path without env override points at repo-relative default
    import os

    os.environ.pop("OMNIA_H4_READY_MARKER_PATH", None)
    os.environ.pop("DOGFOOD_ROOT", None)
    p = h4_ready_marker_path()
    assert p.name == "h4_purchase_ready.sealed"
    assert not p.is_file()
