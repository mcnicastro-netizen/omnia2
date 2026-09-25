"""A-034 residual harden: smart no_match/price_drop + activities week."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_property_list_item_flags_price_drop_and_no_match():
    from apps.immoweb.properties import _to_list_item

    doc = {
        "id": "p1",
        "title": "Test",
        "property_type": "appartamento",
        "operation": "sale",
        "status": "active",
        "city": "Milano",
        "price": 200000,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-02T00:00:00+00:00",
        "photos": [{"url": "/a.jpg"}, {"url": "/b.jpg"}, {"url": "/c.jpg"}],
        "description": "x" * 80,
        "energy": {"energy_class": "B"},
        "last_price_drop": {"drop_eur": 10000, "drop_pct": 5, "at": "2026-01-02"},
        "_no_match": True,
        "listing_agent_id": "u1",
        "listing_agent_name": "Marco",
    }
    item = _to_list_item(doc)
    assert "price_drop" in (item["listing_flags"] or [])
    assert "no_match" in (item["listing_flags"] or [])
    assert item["listing_agent_name"] == "Marco"
    assert item["last_price_drop"]["drop_eur"] == 10000


def test_week_window_math():
    start = datetime(2026, 9, 21, tzinfo=timezone.utc)  # Monday
    end = start + timedelta(days=6)
    assert end.strftime("%Y-%m-%d") == "2026-09-27"
