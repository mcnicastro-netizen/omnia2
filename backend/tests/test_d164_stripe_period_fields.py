"""D-164 — Stripe subscription period su items (no AttributeError root)."""
from __future__ import annotations

from types import SimpleNamespace

from apps.billing.routes import _stripe_sub_period_iso


def test_period_from_items_when_root_missing():
    sub = SimpleNamespace(
        to_dict=lambda: {
            "status": "active",
            "customer": "cus_x",
            "items": {
                "data": [
                    {
                        "current_period_start": 1794412859,
                        "current_period_end": 1797004859,
                    }
                ]
            },
        }
    )
    start, end = _stripe_sub_period_iso(sub)
    assert start and start.startswith("2026-")
    assert end and end.startswith("2026-")


def test_period_from_root_dict():
    start, end = _stripe_sub_period_iso(
        {"current_period_start": 1700000000, "current_period_end": 1702592000}
    )
    assert start is not None and end is not None


def test_period_empty_safe():
    assert _stripe_sub_period_iso({}) == (None, None)
