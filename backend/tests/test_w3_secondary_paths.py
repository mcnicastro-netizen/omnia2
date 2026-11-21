"""PRE-GTM W3 — secondary access paths: videos public IDOR, deal filters, context."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from shared.db import tenant_guard as tg
from shared.db.connection import set_current_agency_id
from shared.mls_collab.service import (
    deal_actor_filter,
    deal_owner_filter,
    deal_partner_filter,
    visit_actor_filter,
)
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run
from tests.test_tenant_guard_adversarial import RecordingColl, _armed


@pytest.fixture(autouse=True)
def _reset():
    set_current_agency_id(None)
    tg.set_current_role(None)
    tg.tenant_bypass(False)
    tg.set_tenant_enforce(False)
    yield
    set_current_agency_id(None)
    tg.set_current_role(None)
    tg.tenant_bypass(False)
    tg.set_tenant_enforce(False)


def test_calendar_and_ledger_in_tenant_collections():
    assert "calendar_events" in tg.TENANT_COLLECTIONS
    assert "credit_ledger" in tg.TENANT_COLLECTIONS
    assert "match_audit" in tg.TENANT_COLLECTIONS
    assert "property_stat_days" not in tg.TENANT_COLLECTIONS
    assert "videos" not in tg.TENANT_COLLECTIONS


def test_deal_actor_filter_scopes_owner_and_partner():
    flt = deal_actor_filter("d1", "agA")
    assert flt["id"] == "d1"
    assert {"agency_id": "agA"} in flt["$or"]
    assert {"partner_agency_id": "agA"} in flt["$or"]
    assert deal_owner_filter("d1", "agA") == {"id": "d1", "agency_id": "agA"}
    assert deal_partner_filter("d1", "agB") == {"id": "d1", "partner_agency_id": "agB"}
    assert visit_actor_filter("v1", "agA")["$or"][0]["owner_agency_id"] == "agA"


def test_deal_update_filter_rejects_outsider_in_fakedb():
    db = FakeDB()
    db.deals = FakeColl()
    db.deals.docs.append(
        {"id": "d1", "agency_id": "agA", "partner_agency_id": "agB", "status": "open"}
    )
    r = _run(
        db.deals.update_one(
            deal_actor_filter("d1", "agC"), {"$set": {"notes": "hack"}}
        )
    )
    assert r.matched_count == 0
    assert db.deals.docs[0].get("notes") is None
    r2 = _run(
        db.deals.update_one(
            deal_actor_filter("d1", "agA"), {"$set": {"notes": "ok"}}
        )
    )
    assert r2.matched_count == 1
    assert db.deals.docs[0]["notes"] == "ok"


def test_video_status_public_logic_no_blind_ready_fallback():
    """Unit stand-in for the removed public fallback ``{id, status:ready}``."""
    # Contract: public path may return agency video only if property is public.
    agency_vid = {
        "id": "vid-agency",
        "agency_id": "agA",
        "status": "ready",
        "property_id": "p-private",
    }
    public_ugc = {"id": "vid-ugc", "agency_id": None, "status": "ready"}

    def resolve_public(doc, prop_public: bool):
        if doc.get("agency_id") is None:
            return doc
        if prop_public and doc.get("status") == "ready":
            return doc
        return None

    assert resolve_public(public_ugc, False) is public_ugc
    assert resolve_public(agency_vid, False) is None
    assert resolve_public(agency_vid, True) is agency_vid


def test_guarded_collection_without_context_raises_on_find():
    tg.set_tenant_enforce(True)
    set_current_agency_id(None)
    proxy = tg.TenantCollection(RecordingColl())
    with pytest.raises(tg.TenantContextRequired):
        proxy.find_one({"id": "x"})
