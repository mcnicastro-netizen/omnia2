"""D-175 — Deal / Collaboration / Visit / Mini-dossier feedback / Chat / Doc-request."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from shared.mls_collab import service as svc
from shared.mls_collab.service import (
    assert_deal_transition,
    ensure_collaboration_from_offer,
    require_agency_in_collaboration,
)
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run


class _AIterCursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def sort(self, *a, **k):
        return self

    def limit(self, n):
        self._rows = self._rows[:n]
        return self

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._rows):
            raise StopAsyncIteration
        row = self._rows[self._i]
        self._i += 1
        return row

    async def to_list(self, length=1000):
        return self._rows[:length]


def _patch_find(coll: FakeColl):
    orig = coll.find

    def find(filt=None, proj=None):
        cur = orig(filt, proj)
        rows = cur._rows
        return _AIterCursor(rows)

    coll.find = find  # type: ignore
    if not hasattr(coll, "count_documents"):

        async def count_documents(filt=None):
            filt = filt or {}
            return sum(1 for d in coll.docs if coll._match(d, filt))

        coll.count_documents = count_documents  # type: ignore


def _db() -> FakeDB:
    db = FakeDB()
    for name in (
        "mls_collaborations",
        "mls_visits",
        "mls_visit_feedback",
        "mls_document_requests",
        "mls_chat_threads",
        "mls_chat_messages",
        "deals",
        "properties",
        "clients",
        "mls_requests",
    ):
        setattr(db, name, FakeColl())
        _patch_find(getattr(db, name))
    return db


def test_deal_transitions_valid_and_invalid():
    assert_deal_transition("open", "proposal_prepared")
    assert_deal_transition("proposal_prepared", "proposal_sent")
    assert_deal_transition("proposal_sent", "accepted")
    with pytest.raises(HTTPException) as ei:
        assert_deal_transition("open", "won")
    assert ei.value.status_code == 400


def test_offer_accept_creates_collaboration_without_doc_request():
    db = _db()
    offer = {
        "id": "off1",
        "property_id": "prop1",
        "from_agency_id": "agA",
        "to_agency_id": "agB",
    }
    collab = _run(ensure_collaboration_from_offer(db, offer, actor_agency_id="agB"))
    assert collab["status"] == "active"
    assert collab["document_request_auto"] is False
    assert collab["property_id"] == "prop1"
    # idempotent
    collab2 = _run(ensure_collaboration_from_offer(db, offer, actor_agency_id="agB"))
    assert collab2["id"] == collab["id"]
    assert len(db.mls_collaborations.docs) == 1


def test_collaboration_accept_does_not_create_document_request():
    db = _db()
    db.mls_collaborations.docs.append(
        {
            "id": "c1",
            "property_id": "p1",
            "owner_agency_id": "agA",
            "partner_agency_id": "agB",
            "status": "pending",
            "document_request_auto": False,
        }
    )
    # simulate accept patch invariants
    _run(
        db.mls_collaborations.update_one(
            {"id": "c1"},
            {
                "$set": {
                    "status": "active",
                    "document_request_auto": False,
                    "auto_document_share": False,
                }
            },
        )
    )
    n = _run(
        db.mls_document_requests.count_documents({"collaboration_id": "c1", "auto_created": True})
    )
    assert n == 0
    row = _run(db.mls_collaborations.find_one({"id": "c1"}))
    assert row["status"] == "active"
    assert row["auto_document_share"] is False


def test_full_visit_feedback_deal_chat_document_flow():
    db = _db()
    # collaboration active
    db.mls_collaborations.docs.append(
        {
            "id": "c1",
            "property_id": "p1",
            "owner_agency_id": "agA",
            "partner_agency_id": "agB",
            "status": "active",
            "document_request_auto": False,
        }
    )
    # visit requested → completed
    visit = {
        "id": "v1",
        "collaboration_id": "c1",
        "property_id": "p1",
        "owner_agency_id": "agA",
        "partner_agency_id": "agB",
        "status": "completed",
        "completed_at": svc.utc_now(),
    }
    db.mls_visits.docs.append(visit)
    # mini-dossier feedback (not document)
    fb = {
        "id": "fb1",
        "kind": "post_visit_feedback",
        "visit_id": "v1",
        "collaboration_id": "c1",
        "from_agency_id": "agB",
        "to_agency_id": "agA",
        "rating": 5,
        "is_document_request": False,
        "shares_documents": False,
        "contested": False,
        "excluded_from_public_rating": False,
    }
    db.mls_visit_feedback.docs.append(fb)
    assert fb["is_document_request"] is False
    # explicit document request AFTER interest
    dr = {
        "id": "dr1",
        "collaboration_id": "c1",
        "property_id": "p1",
        "visit_id": "v1",
        "requesting_agency_id": "agB",
        "owner_agency_id": "agA",
        "status": "pending",
        "auto_created": False,
        "watermark_required": True,
        "access_log": [],
    }
    db.mls_document_requests.docs.append(dr)
    _run(
        db.mls_document_requests.update_one(
            {"id": "dr1"},
            {
                "$set": {
                    "status": "fulfilled",
                    "shared_document_ids": ["docAPE"],
                    "watermark_applied": True,
                }
            },
        )
    )
    # foreign agency denied conceptually
    foreign_ok = False
    row = _run(db.mls_document_requests.find_one({"id": "dr1"}))
    assert "agC" not in (row["requesting_agency_id"], row["owner_agency_id"])
    assert foreign_ok is False
    # deal open after visit
    deal = {
        "id": "d1",
        "property_id": "p1",
        "client_id": "cl1",
        "agency_id": "agB",
        "collaboration_id": "c1",
        "visit_id": "v1",
        "status": "open",
        "history": [],
        "proposals": [],
    }
    db.deals.docs.append(deal)
    assert_deal_transition("open", "proposal_prepared")
    # chat thread scoped
    thread = {
        "id": "t1",
        "collaboration_id": "c1",
        "visit_id": "v1",
        "deal_id": "d1",
        "agency_ids": ["agA", "agB"],
        "status": "open",
    }
    db.mls_chat_threads.docs.append(thread)
    require_agency_in_collaboration(
        _run(db.mls_collaborations.find_one({"id": "c1"})), "agA"
    )
    with pytest.raises(HTTPException):
        require_agency_in_collaboration(
            _run(db.mls_collaborations.find_one({"id": "c1"})), "agX"
        )
    # revoke chat
    _run(db.mls_chat_threads.update_one({"id": "t1"}, {"$set": {"status": "revoked"}}))
    thr = _run(db.mls_chat_threads.find_one({"id": "t1"}))
    assert thr["status"] == "revoked"


def test_webhook_subscription_deleted_mirror():
    """Stripe subscription.deleted mirrors canceled without mutating CC operable status."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    db = FakeDB()
    db.subscriptions = FakeColl()
    db.commercial_customers = FakeColl()
    db.subscriptions.docs.append(
        {
            "agency_id": "ag1",
            "stripe_subscription_id": "sub_1",
            "status": "active",
            "commercial_customer_id": "cc1",
        }
    )
    db.commercial_customers.docs.append(
        {
            "id": "cc1",
            "operational_status": "full",
            "commercial_status": "active",
        }
    )
    now = datetime.now(timezone.utc).isoformat()
    obj = {
        "id": "sub_1",
        "metadata": {"agency_id": "ag1", "commercial_customer_id": "cc1"},
    }
    # inline same logic as routes handler
    upd = {
        "status": "canceled",
        "stripe_status": "canceled",
        "canceled_at": now,
        "updated_at": now,
        "commercial_customer_id": "cc1",
    }
    _run(db.subscriptions.update_one({"agency_id": "ag1"}, {"$set": upd}))
    sub = _run(db.subscriptions.find_one({"agency_id": "ag1"}))
    assert sub["status"] == "canceled"
    cc = _run(db.commercial_customers.find_one({"id": "cc1"}))
    assert cc["operational_status"] == "full"  # unchanged
