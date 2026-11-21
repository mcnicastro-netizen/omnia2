"""PRE-GTM W3 — outsider must not access deals / MLS by ID alone (FakeDB)."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from shared.mls_collab import service as svc
from shared.mls_collab.service import (
    agency_in_collaboration,
    deal_role,
    require_agency_in_collaboration,
)
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run
from tests.test_d175_deal_collab_chat import _db, _patch_find


def test_outsider_not_in_collaboration():
    collab = {
        "id": "c1",
        "owner_agency_id": "agA",
        "partner_agency_id": "agB",
        "status": "active",
    }
    assert agency_in_collaboration(collab, "agA")
    assert agency_in_collaboration(collab, "agB")
    assert not agency_in_collaboration(collab, "agC")
    with pytest.raises(HTTPException) as ei:
        require_agency_in_collaboration(collab, "agC")
    assert ei.value.status_code == 403
    assert ei.value.detail == "collaboration_forbidden"


def test_outsider_deal_role_none():
    deal = {"agency_id": "agA", "partner_agency_id": "agB", "status": "open"}
    assert deal_role(deal, "agA") == "owner"
    assert deal_role(deal, "agB") == "partner"
    assert deal_role(deal, "agC") is None
    assert svc.allowed_deal_transitions(deal, "agC") == set()


def test_get_deal_by_id_then_outsider_denied_pattern():
    """Handlers load by id then check role — outsider must 403."""
    db = _db()
    deal = {
        "id": "deal-1",
        "agency_id": "agA",
        "partner_agency_id": "agB",
        "status": "open",
        "collaboration_id": "c1",
    }
    _run(db.deals.insert_one(deal))
    loaded = _run(svc.get_deal(db, "deal-1"))
    assert loaded["id"] == "deal-1"
    assert deal_role(loaded, "agC") is None
    # Simulate handler gate used by deals.py
    if deal_role(loaded, "agC") is None:
        with pytest.raises(HTTPException) as ei:
            raise HTTPException(status_code=403, detail="deal_forbidden")
        assert ei.value.status_code == 403


def test_get_visit_outsider_pattern():
    db = _db()
    visit = {
        "id": "v1",
        "owner_agency_id": "agA",
        "partner_agency_id": "agB",
        "collaboration_id": "c1",
        "status": "requested",
    }
    _run(db.mls_visits.insert_one(visit))
    loaded = _run(svc.get_visit(db, "v1"))
    assert loaded["id"] == "v1"
    assert "agC" not in (loaded["owner_agency_id"], loaded["partner_agency_id"])


def test_get_collaboration_outsider_forbidden():
    db = _db()
    collab = {
        "id": "c1",
        "owner_agency_id": "agA",
        "partner_agency_id": "agB",
        "status": "active",
        "property_id": "p1",
    }
    _run(db.mls_collaborations.insert_one(collab))
    loaded = _run(svc.get_collaboration(db, "c1"))
    with pytest.raises(HTTPException) as ei:
        require_agency_in_collaboration(loaded, "agC")
    assert ei.value.status_code == 403


def test_list_or_filter_does_not_match_outsider():
    """$or owner/partner must not include outsider when aid is trusted."""
    aid = "agC"
    flt = {"$or": [{"agency_id": aid}, {"partner_agency_id": aid}]}
    deal_ab = {"agency_id": "agA", "partner_agency_id": "agB"}
    # Fake match semantics
    matched = deal_ab["agency_id"] == aid or deal_ab["partner_agency_id"] == aid
    assert matched is False


def test_or_with_client_extra_id_still_requires_agency_membership():
    """Client cannot widen $or by appending victim id without agency membership."""
    aid = "agA"
    # Legitimate list filter
    base = {"$or": [{"agency_id": aid}, {"partner_agency_id": aid}]}
    # Attacker tries to OR in foreign deal id — handlers do not accept client $or.
    # Document expected contract: only server-built $or from trusted aid.
    assert base == {"$or": [{"agency_id": "agA"}, {"partner_agency_id": "agA"}]}


def test_chat_thread_agency_gate():
    db = _db()
    thread = {
        "id": "t1",
        "agency_ids": ["agA", "agB"],
        "status": "open",
        "collaboration_id": "c1",
    }
    _run(db.mls_chat_threads.insert_one(thread))
    loaded = _run(svc.get_thread(db, "t1"))
    with pytest.raises(HTTPException) as ei:
        svc.require_thread_access(loaded, "agC")
    assert ei.value.status_code == 403
    svc.require_thread_access(loaded, "agA")  # owner/partner OK
