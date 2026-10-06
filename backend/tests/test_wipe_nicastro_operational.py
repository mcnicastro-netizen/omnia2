"""Safety + identity-only seed after wipe (nicastro-agency-001 only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from pymongo import MongoClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from scripts.wipe_nicastro_operational import KEEP_COLLECTIONS, NICASTRO_AGENCY_ID  # noqa: E402


def _db():
    url = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    name = os.environ.get("DB_NAME", "omnia")
    return MongoClient(url)[name]


@pytest.mark.skipif(
    os.environ.get("OMNIA_SKIP_LIVE_MONGO") == "1",
    reason="live mongo disabled",
)
def test_keep_list_never_includes_crm_inventory():
    assert "properties" not in KEEP_COLLECTIONS
    assert "clients" not in KEEP_COLLECTIONS
    assert "client_requests" not in KEEP_COLLECTIONS
    assert "agencies" in KEEP_COLLECTIONS
    assert "users" in KEEP_COLLECTIONS
    assert "api_keys" in KEEP_COLLECTIONS


@pytest.mark.skipif(
    os.environ.get("OMNIA_SKIP_LIVE_MONGO") == "1",
    reason="live mongo disabled",
)
def test_wipe_is_hardcoded_to_nicastro_only():
    assert NICASTRO_AGENCY_ID == "nicastro-agency-001"


@pytest.mark.skipif(
    os.environ.get("OMNIA_SKIP_LIVE_MONGO") == "1",
    reason="live mongo disabled",
)
def test_live_nicastro_inventory_empty_after_wipe_and_reseed():
    db = _db()
    agency = db.agencies.find_one({"id": NICASTRO_AGENCY_ID})
    if not agency:
        pytest.skip("nicastro agency not seeded in this env")
    if not agency.get("dogfood_skip_fixtures"):
        pytest.skip("wipe not applied yet (dogfood_skip_fixtures unset)")
    assert db.properties.count_documents({"agency_id": NICASTRO_AGENCY_ID}) == 0
    assert db.clients.count_documents({"agency_id": NICASTRO_AGENCY_ID}) == 0
    assert db.client_requests.count_documents({"agency_id": NICASTRO_AGENCY_ID}) == 0
    assert db.users.find_one({"email": "titolare@nicastroimmobiliare.it"})
    # sandbox demo agency must survive
    assert db.agencies.find_one({"id": "demo-agency-001"})
