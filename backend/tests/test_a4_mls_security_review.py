"""A4 security deep review — dashboard gate, public search, raw helper hygiene."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from apps.immoweb import mls as mls_mod
from shared.db.connection import set_current_agency_id
from shared.db.tenant_guard import set_current_role, set_tenant_enforce, tenant_bypass
from tests.test_a4_mls_inventory import (
    FakeDB,
    _DB,
    _run,
    _seed_props,
    _user,
)


@pytest.fixture
def harness():
    db = FakeDB()
    _seed_props(db)
    # trashed shareable that must never appear
    db.properties.docs.append(
        {
            "id": "pB-trashed",
            "agency_id": "agB",
            "title": "Trashed share",
            "city": "Catania",
            "province_sigla": "CT",
            "visibility": "public",
            "mls_shared": True,
            "status": "active",
            "deleted_at": "2026-01-01T00:00:00+00:00",
            "created_at": "2026-01-09T00:00:00+00:00",
            "owner_email": "secret@example.com",
            "owner_phone": "+39000",
        }
    )
    _DB._inst = db
    _DB._raw = db

    def agency_from_user(user):
        return user["agency_id"]

    async def ensure_idx(d):
        return None

    set_tenant_enforce(True)
    set_current_role("agency_admin")
    tenant_bypass(False)

    with patch("apps.immoweb.mls.Database", _DB), patch(
        "apps.immoweb.mls._agency_id", agency_from_user
    ), patch("apps.immoweb.mls.ensure_mls_indexes", ensure_idx):
        yield db

    set_tenant_enforce(False)
    set_current_agency_id(None)
    set_current_role(None)
    tenant_bypass(False)


def test_dashboard_mls_enabled_exposes_network_counts(harness):
    set_current_agency_id("agA")
    dash = _run(mls_mod.mls_dashboard(_user("agA")))
    assert dash["mls_enabled"] is True
    assert dash["mine"]["shared"] >= 1
    assert dash["network"]["local_listings"] >= 1
    assert dash["network"]["national_listings"] >= 2
    assert dash["network"]["agencies"] >= 1


def test_dashboard_mls_disabled_zeros_network_no_raw_leak(harness):
    """Disabled agency may see own mine counters; network cross-tenant must be 0."""
    set_current_agency_id("agOff")
    # Ensure own shareable exists for agOff
    harness.properties.docs.append(
        {
            "id": "pOff-share",
            "agency_id": "agOff",
            "title": "Off share",
            "visibility": "public",
            "mls_shared": True,
            "status": "active",
            "province_sigla": "CT",
            "created_at": "2026-02-01T00:00:00+00:00",
        }
    )
    calls = {"raw_count": 0}
    real_count = mls_mod._mls_raw_count_shareable

    async def wrapped(extra=None):
        calls["raw_count"] += 1
        return await real_count(extra)

    with patch("apps.immoweb.mls._mls_raw_count_shareable", wrapped):
        dash = _run(mls_mod.mls_dashboard(_user("agOff")))
    assert dash["mls_enabled"] is False
    assert dash["mine"]["shared"] >= 1
    assert dash["network"]["local_listings"] == 0
    assert dash["network"]["national_listings"] == 0
    assert dash["network"]["agencies"] == 0
    assert calls["raw_count"] == 0  # no cross-tenant raw when disabled


def test_public_search_unauthenticated(harness):
    set_current_agency_id(None)
    out = _run(
        mls_mod.public_network_search(
            province=None, city=None, operation=None,
            price_min=None, price_max=None, limit=50, skip=0,
        )
    )
    ids = {i["id"] for i in out["items"]}
    assert "pA-share" in ids and "pB-share" in ids
    assert "pB-private" not in ids
    assert "pB-noshare" not in ids
    assert "pB-b2c" not in ids
    assert "pB-trashed" not in ids
    for item in out["items"]:
        assert "agency_id" not in item
        assert "owner_email" not in item
        assert "owner_phone" not in item
        assert set(item.keys()) <= {
            "id", "title", "city", "province_sigla", "price",
            "operation", "property_type", "sqm", "cover_url",
        }


def test_public_search_authenticated_mls_disabled_still_public_shareable_only(harness):
    """Public contract: no auth gate — disabled agency session still sees only shareable network."""
    set_current_agency_id("agOff")
    out = _run(
        mls_mod.public_network_search(
            province=None, city=None, operation=None,
            price_min=None, price_max=None, limit=50, skip=0,
        )
    )
    ids = {i["id"] for i in out["items"]}
    assert "pB-share" in ids
    assert "pB-private" not in ids
    assert all("agency_id" not in i for i in out["items"])


def test_public_search_authenticated_mls_enabled(harness):
    set_current_agency_id("agA")
    out = _run(
        mls_mod.public_network_search(
            province="CT", city=None, operation=None,
            price_min=None, price_max=None, limit=50, skip=0,
        )
    )
    ids = {i["id"] for i in out["items"]}
    assert "pB-share" in ids
    assert "pC-rome" not in ids  # province filter


def test_public_excludes_trashed_and_private(harness):
    set_current_agency_id(None)
    out = _run(
        mls_mod.public_network_search(
            province=None, city=None, operation=None,
            price_min=None, price_max=None, limit=100, skip=0,
        )
    )
    ids = {i["id"] for i in out["items"]}
    assert "pB-trashed" not in ids
    assert "pB-private" not in ids
    assert "pB-noshare" not in ids


def test_two_agencies_dashboard_isolation(harness):
    set_current_agency_id("agA")
    a = _run(mls_mod.mls_dashboard(_user("agA")))
    set_current_agency_id("agB")
    b = _run(mls_mod.mls_dashboard(_user("agB")))
    # Each sees own mine shared; network national excludes self
    assert a["mine"]["shared"] >= 1
    assert b["mine"]["shared"] >= 1
    # Network counts differ by province/self exclusion but both > 0 when enabled
    assert a["network"]["national_listings"] >= 1
    assert b["network"]["national_listings"] >= 1


def test_raw_helper_always_applies_shareable_filters(harness):
    q = mls_mod._mls_shareable_query({"agency_id": {"$ne": "agA"}})
    assert "$and" in q
    # Flatten: shareable visibility present
    blob = str(q)
    assert "public" in blob and "mls_only" in blob
    assert "mls_shared" in blob


def test_raw_helper_not_referenced_outside_mls_module():
    """Static: CRM property modules must not import _mls_properties_raw."""
    root = Path(__file__).resolve().parents[1] / "apps" / "immoweb"
    offenders = []
    for path in root.rglob("*.py"):
        if path.name == "mls.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "_mls_properties_raw" in text or "_mls_raw_count_shareable" in text:
            offenders.append(str(path))
    assert offenders == []


def test_inventory_still_denies_disabled(harness):
    set_current_agency_id("agOff")
    with pytest.raises(HTTPException) as ei:
        _run(mls_mod.my_mls_inventory(scope="national", limit=10, skip=0, user=_user("agOff")))
    assert ei.value.status_code == 403
