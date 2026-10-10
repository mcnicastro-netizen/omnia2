"""S4 — un contratto di visibilità pubblica portale / brand."""
from __future__ import annotations

from shared.db.public_visibility import (
    brand_site_filter,
    intentional_deltas,
    portal_listing_filter,
    public_surface_base,
)
from apps.immocloud.public_portal import _base_filter


def _flatten_and(flt: dict) -> dict:
    """Merge $and parts into one dict for assertions (trash $or stays nested)."""
    out: dict = {}
    parts = flt.get("$and") or [flt]
    for part in parts:
        if not isinstance(part, dict):
            continue
        for k, v in part.items():
            if k == "$or":
                out.setdefault("$or", v)
            else:
                out[k] = v
    return out


def test_public_surface_shared_keys():
    base = public_surface_base()
    assert base["status"] == "active"
    assert base["visibility"] == "public"
    assert base["moderation_status"] == {"$nin": ["pending", "rejected"]}


def test_portal_filter_includes_surface_plus_deltas():
    flat = _flatten_and(portal_listing_filter())
    assert flat["visibility"] == "public"
    assert flat["is_listed_on_immobilcloud"] == {"$ne": False}
    assert flat["privacy_level"] == {"$nin": ["L3", "L4"]}
    assert "$or" in flat  # not trashed


def test_brand_filter_shares_surface_not_portal_only():
    flat = _flatten_and(brand_site_filter("demo-agency-001"))
    assert flat["agency_id"] == "demo-agency-001"
    assert flat["visibility"] == "public"
    assert flat["moderation_status"] == {"$nin": ["pending", "rejected"]}
    assert "is_listed_on_immobilcloud" not in flat
    assert "privacy_level" not in flat
    assert "$or" in flat


def test_portal_base_filter_delegates_to_sot():
    assert _base_filter() == portal_listing_filter()


def test_intentional_deltas_documented():
    d = intentional_deltas()
    assert "is_listed_on_immobilcloud" in d
    assert "privacy_level_L3_L4" in d
