"""A-007 — soft-read created_at/updated_at (S1-BIS A2) + structural skip."""
from __future__ import annotations

import logging

import pytest

from apps.immoweb.properties import (
    _serialize_property_list_items,
    _to_list_item,
)


def _base(**overrides):
    doc = {
        "id": "p1",
        "title": "Bilocale Milano",
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
    }
    doc.update(overrides)
    return doc


def test_t7_1_both_timestamps_present_unchanged():
    item = _to_list_item(_base())
    assert item is not None
    assert item["created_at"] == "2026-01-01T00:00:00+00:00"
    assert item["updated_at"] == "2026-01-02T00:00:00+00:00"
    flags = item["listing_flags"] or []
    assert "missing_created_at" not in flags
    assert "missing_updated_at" not in flags


def test_t7_2_missing_created_at_empty_string_and_flag():
    doc = _base()
    del doc["created_at"]
    item = _to_list_item(doc)
    assert item is not None
    assert item["created_at"] == ""
    assert item["updated_at"] == "2026-01-02T00:00:00+00:00"
    assert "missing_created_at" in (item["listing_flags"] or [])
    assert "missing_updated_at" not in (item["listing_flags"] or [])
    # no cross-fill
    assert item["created_at"] != item["updated_at"]


def test_t7_3_missing_updated_at_empty_string_and_flag():
    doc = _base()
    del doc["updated_at"]
    item = _to_list_item(doc)
    assert item is not None
    assert item["updated_at"] == ""
    assert item["created_at"] == "2026-01-01T00:00:00+00:00"
    assert "missing_updated_at" in (item["listing_flags"] or [])
    assert "missing_created_at" not in (item["listing_flags"] or [])


def test_t7_4_both_timestamps_missing():
    doc = _base()
    del doc["created_at"]
    del doc["updated_at"]
    item = _to_list_item(doc)
    assert item is not None
    assert item["created_at"] == ""
    assert item["updated_at"] == ""
    flags = item["listing_flags"] or []
    assert "missing_created_at" in flags
    assert "missing_updated_at" in flags


def test_t7_5_empty_string_and_none_treated_as_missing():
    item = _to_list_item(_base(created_at="", updated_at=None))
    assert item is not None
    assert item["created_at"] == ""
    assert item["updated_at"] == ""
    flags = item["listing_flags"] or []
    assert "missing_created_at" in flags
    assert "missing_updated_at" in flags


def test_t7_6_no_invented_or_cross_fill_timestamps():
    doc = _base()
    del doc["created_at"]
    item = _to_list_item(doc)
    assert item["created_at"] == ""
    assert "1970" not in item["created_at"]
    assert item["created_at"] != doc["updated_at"]


def test_t7_7_page_with_incomplete_records_no_keyerror():
    """Mixed page: complete + missing dates + structural invalid — no crash."""
    docs = [
        _base(id="ok"),
        _base(id="no-c"),  # will delete created_at below
        _base(id="no-u"),
        {"title": "Orphan title only"},  # no id → skip
        {"id": "no-title"},  # no title → skip
    ]
    del docs[1]["created_at"]
    del docs[2]["updated_at"]
    items = _serialize_property_list_items(docs)
    assert len(items) == 3
    by_id = {i["id"]: i for i in items}
    assert by_id["ok"]["created_at"] and by_id["ok"]["updated_at"]
    assert by_id["no-c"]["created_at"] == ""
    assert "missing_created_at" in (by_id["no-c"]["listing_flags"] or [])
    assert by_id["no-u"]["updated_at"] == ""
    assert "missing_updated_at" in (by_id["no-u"]["listing_flags"] or [])
    assert "Orphan" not in {i["title"] for i in items}
    assert "no-title" not in by_id


def test_t7_sort_keys_still_readable_without_crash_for_created_desc_fields():
    """Serializer does not crash when sort field missing (sort itself is Mongo-side)."""
    doc = _base()
    del doc["created_at"]
    item = _to_list_item(doc)
    assert item is not None
    # Field present as empty str — consumers can sort client-side without KeyError
    assert isinstance(item["created_at"], str)


def test_t7_structural_missing_id_or_title_returns_none_and_logs(caplog):
    assert _to_list_item({"title": "Solo titolo"}) is None
    assert _to_list_item({"id": "x"}) is None
    assert _to_list_item({"id": "  ", "title": "T"}) is None
    assert _to_list_item({"id": "x", "title": "  "}) is None
    with caplog.at_level(logging.WARNING):
        items = _serialize_property_list_items(
            [{"title": "Solo"}, {"id": "ok", "title": "Ok", "created_at": "a", "updated_at": "b"}]
        )
    assert len(items) == 1
    assert items[0]["id"] == "ok"
    assert any("property_list_item_skipped" in r.message for r in caplog.records)


def test_a034_regression_flags_still_work():
    item = _to_list_item(
        _base(
            last_price_drop={"drop_eur": 10000, "drop_pct": 5, "at": "2026-01-02"},
            _no_match=True,
            listing_agent_name="Marco",
        )
    )
    assert item is not None
    assert "price_drop" in (item["listing_flags"] or [])
    assert "no_match" in (item["listing_flags"] or [])
    assert item["listing_agent_name"] == "Marco"
