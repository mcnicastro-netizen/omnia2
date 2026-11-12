"""D-166 — contatori scadenze / crediti + reminder idempotenti."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from shared.billing.counters import (
    days_until,
    run_billing_reminders,
    subscription_counter,
    wallet_counter,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_subscription_counter_days_left():
    end = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    c = subscription_counter(
        {"status": "active", "tier": "pro", "current_period_end": end}
    )
    assert c["has_subscription"] is True
    assert c["days_left"] in (4, 5)
    assert c["renewal_due_soon"] is True


def test_wallet_low(monkeypatch):
    monkeypatch.setenv("OMNIA_CREDITS_LOW_THRESHOLD", "100")
    assert wallet_counter({"balance": 50})["low"] is True
    assert wallet_counter({"balance": 100})["low"] is False


def test_days_until_none():
    assert days_until(None) is None


def test_run_billing_reminders_sends_once(monkeypatch):
    end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    sub = {
        "agency_id": "ag1",
        "status": "active",
        "tier": "pro",
        "current_period_end": end,
        "renewal_reminders_sent": {},
    }
    agency = {
        "id": "ag1",
        "display_name": "Demo",
        "slug": "demo",
        "owner_id": "u1",
        "contact": {"email": "a@example.com"},
    }
    user = {"id": "u1", "email": "a@example.com", "name": "Ada", "lang": "it"}
    wallet = {"agency_id": "ag1", "balance": 10}

    class _Subs:
        def find(self, *a, **k):
            return SimpleNamespace(to_list=AsyncMock(return_value=[dict(sub)]))

        async def update_one(self, *a, **k):
            return SimpleNamespace(modified_count=1)

    class _Ag:
        async def find_one(self, q, *a, **k):
            return dict(agency) if q.get("id") == "ag1" else None

    class _Users:
        async def find_one(self, q, *a, **k):
            return dict(user)

    class _Wallets:
        def find(self, *a, **k):
            return SimpleNamespace(to_list=AsyncMock(return_value=[dict(wallet)]))

        async def update_one(self, *a, **k):
            return SimpleNamespace(modified_count=1)

    db = SimpleNamespace(
        subscriptions=_Subs(),
        agencies=_Ag(),
        users=_Users(),
        credit_wallets=_Wallets(),
    )

    send = AsyncMock(return_value={"status": "mock"})
    monkeypatch.setattr("shared.email.client.send_email", send)
    monkeypatch.setattr(
        "shared.ops_alerts.record_alert", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        "shared.email.portal_links.get_public_base_url",
        lambda: "https://example.com",
    )
    monkeypatch.setattr(
        "shared.public_base.get_public_base_url", lambda: "https://example.com"
    )
    left = subscription_counter(sub)["days_left"]
    monkeypatch.setenv("OMNIA_SUB_REMINDER_DAYS", str(left))
    monkeypatch.setenv("OMNIA_CREDITS_LOW_THRESHOLD", "50")

    out = _run(run_billing_reminders(db))
    assert out["renewal_emails"] >= 1
    assert out["credits_alerts"] >= 1
    assert send.await_count >= 2
