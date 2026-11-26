"""A4 — integrated MongoDB dual-agency check (dedicated DB, non-prod).

Uses local mongod on 127.0.0.1:27017 and a unique DB name; drops it after.
Calls MLS handlers with TenantAwareDatabase wrapping the real Motor DB.
Skips cleanly if Mongo is unreachable.
"""
from __future__ import annotations

import os
import uuid
from unittest.mock import patch

import pytest
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from shared.db.tenant_guard import (
    TenantAwareDatabase,
    set_current_role,
    set_tenant_enforce,
    tenant_bypass,
)
from shared.db.connection import set_current_agency_id
from tests.test_b04ii_wallet_ledger import _run

MONGO_URL = os.environ.get("A4_TEST_MONGO_URL", "mongodb://127.0.0.1:27017")


def _mongo_ok() -> bool:
    try:
        MongoClient(MONGO_URL, serverSelectionTimeoutMS=1500).admin.command("ping")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _mongo_ok(), reason="local mongod not reachable")


@pytest.fixture
def mongo_harness():
    from motor.motor_asyncio import AsyncIOMotorClient
    from apps.immoweb import mls as mls_mod

    db_name = f"omnia_a4_sec_{uuid.uuid4().hex[:10]}"
    sync = MongoClient(MONGO_URL, serverSelectionTimeoutMS=2500)
    sync.drop_database(db_name)

    motor = AsyncIOMotorClient(MONGO_URL)
    raw = motor[db_name]
    tenant = TenantAwareDatabase(raw)

    class _DB:
        @classmethod
        def get(cls):
            return tenant

        @classmethod
        def get_raw(cls):
            return raw

    # Seed via sync for simplicity
    sdb = sync[db_name]
    sdb.agencies.insert_many(
        [
            {"id": "agA", "mls_enabled": True, "mls_province": "CT", "province_sigla": "CT", "name": "A"},
            {"id": "agB", "mls_enabled": True, "mls_province": "CT", "province_sigla": "CT", "name": "B"},
            {"id": "agOff", "mls_enabled": False, "mls_province": "CT", "name": "Off"},
        ]
    )
    sdb.properties.insert_many(
        [
            {
                "id": "pA",
                "agency_id": "agA",
                "title": "A Share",
                "city": "Catania",
                "province_sigla": "CT",
                "visibility": "public",
                "mls_shared": True,
                "status": "active",
                "price": 1,
                "created_at": "2026-03-01T00:00:00+00:00",
            },
            {
                "id": "pB",
                "agency_id": "agB",
                "title": "B Share",
                "city": "Catania",
                "province_sigla": "CT",
                "visibility": "public",
                "mls_shared": True,
                "status": "active",
                "price": 2,
                "created_at": "2026-03-02T00:00:00+00:00",
            },
            {
                "id": "pBpriv",
                "agency_id": "agB",
                "title": "B Private",
                "city": "Catania",
                "province_sigla": "CT",
                "visibility": "private",
                "mls_shared": True,
                "status": "active",
                "created_at": "2026-03-03T00:00:00+00:00",
            },
        ]
    )
    sdb.clients.insert_one({"id": "clA", "agency_id": "agA", "name": "C", "surname": "A"})

    def agency_from_user(user):
        return user["agency_id"]

    async def ensure_idx(d):
        return None

    set_tenant_enforce(True)
    set_current_role("agency_admin")
    tenant_bypass(False)

    with patch("apps.immoweb.mls.Database", _DB), patch(
        "apps.immoweb.mls._agency_id", agency_from_user
    ), patch("apps.immoweb.mls.ensure_mls_indexes", ensure_idx), patch(
        "apps.immoweb.properties.Database", _DB
    ):
        yield {"raw": raw, "sync": sdb, "mls": mls_mod, "db_name": db_name, "motor": motor}

    set_tenant_enforce(False)
    set_current_agency_id(None)
    set_current_role(None)
    tenant_bypass(False)
    sync.drop_database(db_name)
    motor.close()
    sync.close()


def _user(aid):
    return {"id": f"u-{aid}", "role": "agency_admin", "agency_id": aid, "sub": f"u-{aid}"}


def test_mongo_inventory_national_sees_partner(mongo_harness):
    mls = mongo_harness["mls"]
    set_current_agency_id("agA")
    out = _run(mls.my_mls_inventory(scope="national", limit=50, skip=0, user=_user("agA")))
    ids = {i["id"] for i in out["items"]}
    assert "pB" in ids
    assert "pA" not in ids
    assert "pBpriv" not in ids


def test_mongo_dashboard_disabled_zeros_network(mongo_harness):
    mls = mongo_harness["mls"]
    set_current_agency_id("agOff")
    dash = _run(mls.mls_dashboard(_user("agOff")))
    assert dash["mls_enabled"] is False
    assert dash["network"]["national_listings"] == 0
    assert dash["network"]["local_listings"] == 0
    assert dash["network"]["agencies"] == 0


def test_mongo_dashboard_enabled_network(mongo_harness):
    mls = mongo_harness["mls"]
    set_current_agency_id("agA")
    dash = _run(mls.mls_dashboard(_user("agA")))
    assert dash["network"]["national_listings"] >= 1


def test_mongo_public_search(mongo_harness):
    mls = mongo_harness["mls"]
    set_current_agency_id(None)
    out = _run(
        mls.public_network_search(
            province=None, city=None, operation=None,
            price_min=None, price_max=None, limit=50, skip=0,
        )
    )
    ids = {i["id"] for i in out["items"]}
    assert "pA" in ids and "pB" in ids
    assert "pBpriv" not in ids
    assert all("agency_id" not in i for i in out["items"])


def test_mongo_crm_get_foreign_404(mongo_harness):
    from apps.immoweb import properties as props_mod
    from fastapi import HTTPException

    set_current_agency_id("agA")

    async def req_agency(user):
        return user["agency_id"]

    with patch("apps.immoweb.properties._require_agency", req_agency):
        with pytest.raises(HTTPException) as ei:
            _run(props_mod.get_property("pB", _user("agA")))
    assert ei.value.status_code == 404
