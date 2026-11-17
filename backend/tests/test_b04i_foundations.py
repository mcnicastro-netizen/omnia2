"""B04-I — CommercialCustomer↔Stripe Customer, catalog snapshot, OMNIA states."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# -------------------- DES-03 catalog / snapshot --------------------


def test_catalog_version_id_stable():
    from shared.billing.plan_catalog import (
        CATALOG_VERSION_ID,
        published_catalog_document,
        snapshot_commercial_terms,
    )

    doc = published_catalog_document()
    assert doc["id"] == CATALOG_VERSION_ID
    assert doc["immutable"] is True
    assert "launch" in doc["phases"] and "post_traction" in doc["phases"]
    assert doc["phases"]["launch"]["plans"]["starter"]["price_monthly"] == 49.0
    assert doc["phases"]["post_traction"]["plans"]["starter"]["price_monthly"] == 79.0

    snap = snapshot_commercial_terms(
        tier="pro", billing_cycle="monthly", pricing_phase="launch"
    )
    assert snap["catalog_version_id"] == CATALOG_VERSION_ID
    assert snap["tier"] == "pro"
    assert snap["price_eur"] == 99.0
    assert snap["max_properties"] == 200


def test_ensure_plan_catalog_version_inserts_once():
    from shared.billing import plan_catalog as mod

    inserted = {}

    class DB:
        plan_catalog_versions = MagicMock()
        plan_catalog_versions.find_one = AsyncMock(side_effect=[None, None])
        plan_catalog_versions.insert_one = AsyncMock(
            side_effect=lambda d: inserted.update(d)
        )

    out = _run(mod.ensure_plan_catalog_version(DB()))
    assert out["id"] == mod.CATALOG_VERSION_ID
    DB.plan_catalog_versions.insert_one.assert_called_once()

    # second call finds existing
    existing = {"id": mod.CATALOG_VERSION_ID, "immutable": True}
    DB.plan_catalog_versions.find_one = AsyncMock(return_value=existing)
    out2 = _run(mod.ensure_plan_catalog_version(DB()))
    assert out2["id"] == mod.CATALOG_VERSION_ID


def test_founder_phase_window():
    from shared.billing.plan_catalog import resolve_pricing_phase_for_customer

    assert resolve_pricing_phase_for_customer(first_paid_activated_at=None) == "launch"
    recent = datetime.now(timezone.utc).isoformat()
    assert resolve_pricing_phase_for_customer(first_paid_activated_at=recent) == "launch"
    old = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    assert resolve_pricing_phase_for_customer(first_paid_activated_at=old) == "post_traction"


# -------------------- DES-02 operational mapping --------------------


def test_operational_status_matrix():
    from shared.models.commercial_customer import operational_status_for

    assert operational_status_for("pre_activation") == "none"
    assert operational_status_for("active") == "full"
    assert operational_status_for("cancel_pending") == "full"
    assert operational_status_for("grace") == "full"
    assert operational_status_for("suspended") == "billing_only"
    assert operational_status_for("ceased") == "closed_readonly"


# -------------------- DES-01 Stripe Customer reuse --------------------


def test_get_or_create_stripe_customer_reuses_existing():
    from shared.billing import stripe_customer_service as mod

    cc = {"id": "cc1", "stripe_customer_id": "cus_EXISTING", "legal_name": "Demo"}

    class DB:
        commercial_customers = MagicMock()

    with patch.object(mod.stripe, "Customer") as Cust:
        out = _run(mod.get_or_create_stripe_customer(DB(), cc, email="a@b.it"))
        assert out == "cus_EXISTING"
        Cust.create.assert_not_called()


def test_get_or_create_stripe_customer_creates_and_binds():
    from shared.billing import stripe_customer_service as mod

    cc = {
        "id": "cc2",
        "stripe_customer_id": None,
        "legal_name": "Demo SRL",
        "vat_number_normalized": "01234567890",
        "country_code": "IT",
    }
    created = MagicMock(id="cus_NEW")

    class DB:
        commercial_customers = MagicMock()
        commercial_customers.find_one_and_update = AsyncMock(
            return_value={**cc, "stripe_customer_id": "cus_NEW"}
        )

    with patch.object(mod.stripe, "Customer") as Cust:
        Cust.create.return_value = created
        out = _run(mod.get_or_create_stripe_customer(DB(), cc, email="a@b.it"))
        assert out == "cus_NEW"
        Cust.create.assert_called_once()
        meta = Cust.create.call_args.kwargs["metadata"]
        assert meta["commercial_customer_id"] == "cc2"


def test_resolve_commercial_customer_requires_vat_when_unlinked():
    from shared.billing import stripe_customer_service as mod

    class DB:
        agencies = MagicMock()
        agencies.find_one = AsyncMock(
            return_value={
                "id": "ag1",
                "display_name": "X",
                "fiscal": {"legal_name": "X", "vat_number": None},
                "commercial_customer_id": None,
            }
        )

    with pytest.raises(HTTPException) as ei:
        _run(mod.resolve_commercial_customer_for_agency(DB(), "ag1"))
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "commercial_customer_required"


def test_mark_first_paid_activation_sets_founder_window():
    from shared.billing import stripe_customer_service as mod

    stored = {
        "id": "cc3",
        "commercial_status": "pre_activation",
        "operational_status": "none",
    }

    class DB:
        commercial_customers = MagicMock()
        commercial_customers.find_one = AsyncMock(
            side_effect=[
                dict(stored),  # initial
                {  # final read
                    **stored,
                    "first_paid_activated_at": "2026-11-17T00:00:00+00:00",
                    "founder_period_ends_at": "2027-11-17T00:00:00+00:00",
                    "commercial_status": "active",
                    "operational_status": "full",
                },
            ]
        )
        commercial_customers.update_one = AsyncMock()

    out = _run(mod.mark_first_paid_activation(DB(), "cc3"))
    assert out["commercial_status"] == "active"
    assert out["operational_status"] == "full"
    assert out.get("first_paid_activated_at")
    assert DB.commercial_customers.update_one.await_count >= 1
