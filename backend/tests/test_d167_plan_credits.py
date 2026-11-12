"""D-167 — crediti listino da invoice Stripe + default piano (no 2000 dogfood)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from shared.billing.plan_credits import (
    grant_plan_credits_from_stripe_invoice,
    plan_included_amount,
    resolve_tier_and_cycle_from_invoice,
)


def _run(coro):
    return asyncio.run(coro)


def test_plan_included_amount_monthly_yearly():
    assert plan_included_amount("pro", "monthly") == 1200
    assert plan_included_amount("pro", "yearly") == 14400
    assert plan_included_amount("starter", "monthly") == 120


def test_resolve_tier_from_lookup_key():
    inv = {
        "id": "in_test",
        "metadata": {},
        "lines": {
            "data": [
                {"price": {"lookup_key": "pro_yearly"}},
            ]
        },
    }
    tier, cycle = resolve_tier_and_cycle_from_invoice(inv)
    assert tier == "pro"
    assert cycle == "yearly"


def test_grant_plan_credits_idempotent():
    db = MagicMock()
    db.credit_ledger = MagicMock()
    db.credit_wallets = MagicMock()
    db.subscriptions = MagicMock()

    # already granted
    db.credit_ledger.find_one = AsyncMock(
        return_value={"id": "led1", "delta": 1200}
    )
    out = _run(
        grant_plan_credits_from_stripe_invoice(
            db,
            {
                "id": "in_1",
                "billing_reason": "subscription_create",
                "metadata": {"agency_id": "ag1", "tier": "pro"},
                "lines": {"data": []},
            },
        )
    )
    assert out["ok"] is True
    assert out["skipped"] == "already_granted"

    # fresh grant (find_one: idempotency miss, then prior_plan miss)
    db.credit_ledger.find_one = AsyncMock(side_effect=[None, None])
    db.credit_ledger.insert_one = AsyncMock()
    db.credit_transactions = MagicMock()
    db.credit_transactions.find_one = AsyncMock(return_value=None)
    db.credit_wallets.find_one_and_update = AsyncMock(
        return_value={"balance": 1200}
    )
    out2 = _run(
        grant_plan_credits_from_stripe_invoice(
            db,
            {
                "id": "in_2",
                "billing_reason": "subscription_cycle",
                "metadata": {"agency_id": "ag1", "tier": "pro", "billing_cycle": "monthly"},
                "lines": {"data": []},
            },
        )
    )
    assert out2["ok"] is True
    assert out2["credits_added"] == 1200
    db.credit_ledger.insert_one.assert_awaited()


def test_grant_skips_non_subscription_billing_reason():
    db = MagicMock()
    db.credit_ledger = MagicMock()
    db.credit_ledger.find_one = AsyncMock(return_value=None)
    out = _run(
        grant_plan_credits_from_stripe_invoice(
            db,
            {
                "id": "in_pack",
                "billing_reason": "manual",
                "metadata": {"agency_id": "ag1", "tier": "pro"},
            },
        )
    )
    assert out["ok"] is False
    assert out["skipped"] == "billing_reason"
