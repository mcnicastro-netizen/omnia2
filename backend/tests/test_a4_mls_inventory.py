"""A4 — MLS inventory cross-tenant under tenant enforce (FakeDB).

Proves GET /app/mls/inventory scope=local|national returns other agencies'
shareable listings when using get_raw, and that CRM property access stays
tenant-scoped. Also covers public network search and dashboard network counts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from apps.immoweb import mls as mls_mod
from apps.immoweb import properties as props_mod
from shared.db.tenant_guard import (
    TenantCollection,
    _inject_filter,
    set_current_role,
    set_tenant_enforce,
    tenant_bypass,
)
from shared.db.connection import set_current_agency_id
from tests.test_b04ii_wallet_ledger import _run


class FakeCursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def sort(self, *args, **kwargs):
        key = args[0] if args else "created_at"
        reverse = False
        if len(args) > 1 and args[1] == -1:
            reverse = True
        if isinstance(key, list):
            key = key[0][0] if key else "created_at"
        self._rows = sorted(self._rows, key=lambda r: r.get(key) or "", reverse=reverse)
        return self

    def skip(self, n):
        self._rows = self._rows[int(n) :]
        return self

    def limit(self, n):
        self._rows = self._rows[: int(n)]
        return self

    async def to_list(self, length=1000):
        return list(self._rows)[:length]

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._rows):
            raise StopAsyncIteration
        row = self._rows[self._i]
        self._i += 1
        return row


class FakeColl:
    """Minimal Motor-like collection with $and/$or/$ne/$in for MLS filters."""

    def __init__(self):
        self.docs: list[dict] = []
        self.last_find_filter: Optional[dict] = None
        self.last_count_filter: Optional[dict] = None

    def _match(self, doc, filt: dict) -> bool:
        for k, v in (filt or {}).items():
            if k == "$and":
                if not all(self._match(doc, c) for c in v):
                    return False
                continue
            if k == "$or":
                if not any(self._match(doc, c) for c in v):
                    return False
                continue
            if isinstance(v, dict):
                val = doc.get(k)
                if "$ne" in v and val == v["$ne"]:
                    return False
                if "$in" in v and val not in v["$in"]:
                    return False
                if "$nin" in v:
                    if isinstance(val, list):
                        if any(x in v["$nin"] for x in val):
                            return False
                    elif val is not None and val in v["$nin"]:
                        return False
                if "$exists" in v:
                    exists = k in doc and doc.get(k) is not None
                    if bool(v["$exists"]) != exists:
                        return False
                if "$gte" in v and not (val is not None and val >= v["$gte"]):
                    return False
                if "$lte" in v and not (val is not None and val <= v["$lte"]):
                    return False
                if "$regex" in v:
                    import re

                    if val is None or re.search(v["$regex"], str(val), re.I if v.get("$options") == "i" else 0) is None:
                        return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    def find(self, filt=None, proj=None):
        try:
            self.last_find_filter = deepcopy(filt or {})
        except TypeError:
            self.last_find_filter = dict(filt or {})
        rows = [deepcopy(d) for d in self.docs if self._match(d, filt or {})]
        if proj:
            keep = {k for k, flag in proj.items() if flag}
            if keep:
                rows = [{k: r[k] for k in r if k in keep or k == "id"} for r in rows]
        return FakeCursor(rows)

    async def find_one(self, filt=None, proj=None):
        rows = await self.find(filt or {}, proj).to_list(1)
        return rows[0] if rows else None

    async def count_documents(self, filt=None):
        try:
            self.last_count_filter = deepcopy(filt or {})
        except TypeError:
            self.last_count_filter = dict(filt or {})
        return len([d for d in self.docs if self._match(d, filt or {})])

    def aggregate(self, pipeline, *args, **kwargs):
        match = {}
        for stage in pipeline or []:
            if isinstance(stage, dict) and "$match" in stage:
                match = stage["$match"]
                break
        rows = [deepcopy(d) for d in self.docs if self._match(d, match)]
        return FakeCursor(rows)

    async def insert_one(self, doc):
        self.docs.append(deepcopy(doc))

    async def update_one(self, filt, update, upsert=False):
        return type("U", (), {"matched_count": 0, "modified_count": 0})()


class FakeDB:
    def __init__(self):
        self.properties = FakeColl()
        self.agencies = FakeColl()
        self.mls_partners = FakeColl()
        self.mls_requests = FakeColl()
        self.mls_events = FakeColl()
        self.clients = FakeColl()

    def __getattr__(self, item):
        if item.startswith("_"):
            raise AttributeError(item)
        coll = FakeColl()
        setattr(self, item, coll)
        return coll


class _DB:
    _inst = None
    _raw = None

    @classmethod
    def get(cls):
        # Simulate tenant proxy for properties only
        return TenantAwareFake(cls._inst)

    @classmethod
    def get_raw(cls):
        return cls._raw or cls._inst


class TenantAwareFake:
    """Mirrors TenantAwareDatabase: properties go through inject when enforce on."""

    def __init__(self, db: FakeDB):
        self._db = db

    def __getattr__(self, item):
        coll = getattr(self._db, item)
        if item == "properties":
            return TenantCollection(coll)
        return coll


def _user(agency_id="agA", role="agency_admin", uid="u1"):
    return {"id": uid, "role": role, "agency_id": agency_id, "sub": uid, "active_agency_id": agency_id}


def _seed_props(db: FakeDB):
    db.agencies.docs.extend(
        [
            {"id": "agA", "mls_enabled": True, "mls_province": "CT", "province_sigla": "CT", "name": "A"},
            {"id": "agB", "mls_enabled": True, "mls_province": "CT", "province_sigla": "CT", "name": "B"},
            {"id": "agC", "mls_enabled": True, "mls_province": "RM", "province_sigla": "RM", "name": "C"},
            {"id": "agOff", "mls_enabled": False, "mls_province": "CT", "name": "Off"},
        ]
    )
    db.properties.docs.extend(
        [
            {
                "id": "pA-share",
                "agency_id": "agA",
                "title": "Villa A share",
                "city": "Catania",
                "province_sigla": "CT",
                "visibility": "public",
                "mls_shared": True,
                "status": "active",
                "operation": "sale",
                "price": 100000,
                "created_at": "2026-01-02T00:00:00+00:00",
            },
            {
                "id": "pB-share",
                "agency_id": "agB",
                "title": "Villa B share",
                "city": "Catania",
                "province_sigla": "CT",
                "visibility": "public",
                "mls_shared": True,
                "status": "active",
                "operation": "sale",
                "price": 200000,
                "created_at": "2026-01-03T00:00:00+00:00",
            },
            {
                "id": "pB-private",
                "agency_id": "agB",
                "title": "Villa B private",
                "city": "Catania",
                "province_sigla": "CT",
                "visibility": "private",
                "mls_shared": True,
                "status": "active",
                "created_at": "2026-01-04T00:00:00+00:00",
            },
            {
                "id": "pB-noshare",
                "agency_id": "agB",
                "title": "Villa B noshare",
                "city": "Catania",
                "province_sigla": "CT",
                "visibility": "public",
                "mls_shared": False,
                "status": "active",
                "created_at": "2026-01-05T00:00:00+00:00",
            },
            {
                "id": "pB-b2c",
                "agency_id": "agB",
                "title": "Villa B b2c",
                "city": "Catania",
                "province_sigla": "CT",
                "visibility": "public",
                "mls_shared": True,
                "is_private_listing": True,
                "status": "active",
                "created_at": "2026-01-06T00:00:00+00:00",
            },
            {
                "id": "pC-rome",
                "agency_id": "agC",
                "title": "Appartamento Roma",
                "city": "Roma",
                "province_sigla": "RM",
                "visibility": "mls_only",
                "mls_shared": True,
                "status": "active",
                "operation": "sale",
                "price": 300000,
                "created_at": "2026-01-07T00:00:00+00:00",
            },
            {
                "id": "pB-other",
                "agency_id": "agB",
                "title": "Villa B second",
                "city": "Belpasso",
                "province_sigla": "CT",
                "visibility": "public",
                "mls_shared": True,
                "status": "active",
                "created_at": "2026-01-08T00:00:00+00:00",
            },
        ]
    )
    db.clients.docs.append({"id": "clA", "agency_id": "agA", "name": "Cliente", "surname": "A"})


@pytest.fixture
def harness():
    db = FakeDB()
    _seed_props(db)
    _DB._inst = db
    _DB._raw = db

    def agency_from_user(user):
        return user["agency_id"]

    async def ensure_idx(d):
        return None

    # Enforce tenant like /api/app/*
    set_tenant_enforce(True)
    set_current_role("agency_admin")
    tenant_bypass(False)

    with patch("apps.immoweb.mls.Database", _DB), patch(
        "apps.immoweb.mls._agency_id", agency_from_user
    ), patch("apps.immoweb.mls.ensure_mls_indexes", ensure_idx), patch(
        "apps.immoweb.properties.Database", _DB
    ):
        yield db

    set_tenant_enforce(False)
    set_current_agency_id(None)
    set_current_role(None)
    tenant_bypass(False)


def test_inject_collapses_ne_filter_defect_reproduction():
    """Baseline: tenant inject rewrites agency_id $ne → caller (root cause A4)."""
    set_tenant_enforce(True)
    set_current_role("agency_admin")
    set_current_agency_id("agA")
    tenant_bypass(False)
    before = {"agency_id": {"$ne": "agA"}, "mls_shared": {"$ne": False}}
    after = _inject_filter(dict(before))
    assert after["agency_id"] == "agA"
    set_tenant_enforce(False)
    set_current_agency_id(None)


def test_mine_inventory_own_shareable(harness):
    set_current_agency_id("agA")
    out = _run(mls_mod.my_mls_inventory(scope="mine", limit=24, skip=0, user=_user("agA")))
    ids = {i["id"] for i in out["items"]}
    assert "pA-share" in ids
    assert "pB-share" not in ids
    assert out["total"] >= 1
    # Query must pin own agency (explicit), not inject collapse of $ne
    assert harness.properties.last_count_filter is not None
    # with_not_trashed wraps in $and
    blob = str(harness.properties.last_count_filter)
    assert "agA" in blob
    assert "pB-share" not in ids


def test_national_sees_other_shareable_not_private_or_noshare(harness):
    set_current_agency_id("agA")
    out = _run(mls_mod.my_mls_inventory(scope="national", limit=50, skip=0, user=_user("agA")))
    ids = {i["id"] for i in out["items"]}
    assert "pB-share" in ids
    assert "pB-other" in ids
    assert "pC-rome" in ids
    assert "pA-share" not in ids  # own excluded by $ne
    assert "pB-private" not in ids
    assert "pB-noshare" not in ids
    assert "pB-b2c" not in ids
    # Prove filter still has $ne caller (not collapsed to agA equality)
    flt = harness.properties.last_find_filter or harness.properties.last_count_filter
    assert flt is not None
    # Flatten $and
    parts = flt.get("$and", [flt])
    agency_clause = None
    for p in parts:
        if isinstance(p, dict) and "agency_id" in p:
            agency_clause = p["agency_id"]
            break
    assert agency_clause == {"$ne": "agA"}


def test_local_filters_province(harness):
    set_current_agency_id("agA")
    out = _run(mls_mod.my_mls_inventory(scope="local", limit=50, skip=0, user=_user("agA")))
    ids = {i["id"] for i in out["items"]}
    assert "pB-share" in ids
    assert "pC-rome" not in ids  # RM excluded from CT local


def test_mls_disabled_denied(harness):
    set_current_agency_id("agOff")
    with pytest.raises(HTTPException) as ei:
        _run(mls_mod.my_mls_inventory(scope="national", limit=24, skip=0, user=_user("agOff")))
    assert ei.value.status_code == 403
    assert ei.value.detail == "mls_not_enabled"


def test_pagination_no_duplicates(harness):
    set_current_agency_id("agA")
    page1 = _run(mls_mod.my_mls_inventory(scope="national", limit=1, skip=0, user=_user("agA")))
    page2 = _run(mls_mod.my_mls_inventory(scope="national", limit=1, skip=1, user=_user("agA")))
    assert page1["total"] >= 2
    assert len(page1["items"]) == 1
    assert len(page2["items"]) == 1
    assert page1["items"][0]["id"] != page2["items"][0]["id"]


def test_empty_results_ok(harness):
    # Remove all foreign shareable
    harness.properties.docs = [
        d for d in harness.properties.docs if d["agency_id"] == "agA"
    ]
    set_current_agency_id("agA")
    out = _run(mls_mod.my_mls_inventory(scope="national", limit=24, skip=0, user=_user("agA")))
    assert out["total"] == 0
    assert out["items"] == []


def test_agency_b_mine_no_contamination(harness):
    set_current_agency_id("agB")
    out = _run(mls_mod.my_mls_inventory(scope="mine", limit=50, skip=0, user=_user("agB")))
    ids = {i["id"] for i in out["items"]}
    assert "pB-share" in ids
    assert "pA-share" not in ids


def test_two_agencies_national_distinct(harness):
    set_current_agency_id("agA")
    a = _run(mls_mod.my_mls_inventory(scope="national", limit=50, skip=0, user=_user("agA")))
    set_current_agency_id("agB")
    b = _run(mls_mod.my_mls_inventory(scope="national", limit=50, skip=0, user=_user("agB")))
    a_ids = {i["id"] for i in a["items"]}
    b_ids = {i["id"] for i in b["items"]}
    assert "pB-share" in a_ids and "pA-share" not in a_ids
    assert "pA-share" in b_ids and "pB-share" not in b_ids


def test_dashboard_network_counts_use_raw(harness):
    set_current_agency_id("agA")
    dash = _run(mls_mod.mls_dashboard(_user("agA")))
    assert dash["mine"]["shared"] >= 1
    assert dash["network"]["local_listings"] >= 1  # B shareable CT
    assert dash["network"]["national_listings"] >= 2  # B + C


def test_public_search_returns_network(harness):
    # No agency context — would TenantContextRequired on tenant proxy
    set_current_agency_id(None)
    out = _run(
        mls_mod.public_network_search(
            province=None,
            city=None,
            operation=None,
            price_min=None,
            price_max=None,
            limit=50,
            skip=0,
        )
    )
    ids = {i["id"] for i in out["items"]}
    assert "pA-share" in ids
    assert "pB-share" in ids
    assert "pB-private" not in ids
    assert out["total"] >= 2


async def _require_agency_patch(user):
    return user["agency_id"]


def test_crm_list_stays_tenant_scoped(harness):
    """CRM property find under tenant inject must NOT leak B listings to A."""
    set_current_agency_id("agA")
    tenant_props = TenantCollection(harness.properties)
    rows = _run(tenant_props.find({"title": {"$regex": "Villa", "$options": "i"}}).to_list(50))
    # Inject forces agency_id=agA — B shareable must not appear
    ids = {r["id"] for r in rows}
    assert "pA-share" in ids
    assert "pB-share" not in ids


def test_crm_get_foreign_404(harness):
    set_current_agency_id("agA")

    async def req_agency(user):
        return user["agency_id"]

    with patch("apps.immoweb.properties._require_agency", req_agency):
        with pytest.raises(HTTPException) as ei:
            _run(props_mod.get_property("pB-share", _user("agA")))
    assert ei.value.status_code == 404
    assert ei.value.detail == "property_not_found"


def test_scope_literal_contract():
    import typing

    hints = typing.get_type_hints(mls_mod.my_mls_inventory)
    scope = hints.get("scope")
    assert typing.get_args(scope) == ("mine", "local", "national") or set(
        typing.get_args(scope)
    ) == {"mine", "local", "national"}
