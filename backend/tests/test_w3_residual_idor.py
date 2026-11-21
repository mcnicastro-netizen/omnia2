"""PRE-GTM W3 — residual IDOR: docs/chat filters + video job scope + stats."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from shared.mls_collab.service import (
    chat_thread_actor_filter,
    document_request_actor_filter,
    document_request_owner_filter,
    visit_feedback_rated_agency_filter,
)
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run


def test_document_request_owner_filter_blocks_partner_fulfill():
    db = FakeDB()
    db.mls_document_requests = FakeColl()
    db.mls_document_requests.docs.append(
        {
            "id": "dr1",
            "owner_agency_id": "agA",
            "requesting_agency_id": "agB",
            "status": "pending",
        }
    )
    r = _run(
        db.mls_document_requests.update_one(
            document_request_owner_filter("dr1", "agB"),
            {"$set": {"status": "fulfilled"}},
        )
    )
    assert r.matched_count == 0
    r2 = _run(
        db.mls_document_requests.update_one(
            document_request_owner_filter("dr1", "agA"),
            {"$set": {"status": "fulfilled"}},
        )
    )
    assert r2.matched_count == 1


def test_document_request_actor_filter_allows_partner_revoke():
    db = FakeDB()
    db.mls_document_requests = FakeColl()
    db.mls_document_requests.docs.append(
        {
            "id": "dr1",
            "owner_agency_id": "agA",
            "requesting_agency_id": "agB",
            "status": "approved",
        }
    )
    r = _run(
        db.mls_document_requests.update_one(
            document_request_actor_filter("dr1", "agC"),
            {"$set": {"status": "revoked"}},
        )
    )
    assert r.matched_count == 0
    r2 = _run(
        db.mls_document_requests.update_one(
            document_request_actor_filter("dr1", "agB"),
            {"$set": {"status": "revoked"}},
        )
    )
    assert r2.matched_count == 1


def test_chat_thread_actor_filter_outsider():
    """Mongo array-equality semantics: ``{agency_ids: aid}`` ⇒ membership."""
    flt_out = chat_thread_actor_filter("t1", "agC")
    flt_ok = chat_thread_actor_filter("t1", "agA")
    thread = {"id": "t1", "agency_ids": ["agA", "agB"], "status": "open"}

    def _mongo_array_eq(doc, filt):
        if doc.get("id") != filt.get("id"):
            return False
        aid = filt.get("agency_ids")
        return aid in (doc.get("agency_ids") or [])

    assert _mongo_array_eq(thread, flt_out) is False
    assert _mongo_array_eq(thread, flt_ok) is True


def test_visit_feedback_contest_filter():
    flt = visit_feedback_rated_agency_filter("fb1", "agA")
    assert flt == {"id": "fb1", "to_agency_id": "agA"}


def test_video_job_filter_binds_agency_and_property():
    from apps.immoweb.micro_tour_video import _video_job_filter

    flt = _video_job_filter("v1", agency_id="agA", property_id="p1")
    assert flt == {"id": "v1", "agency_id": "agA", "property_id": "p1"}
    ugc = _video_job_filter("v2", agency_id=None, property_id="p2")
    assert ugc["agency_id"] is None
    assert ugc["property_id"] == "p2"


def test_video_job_cannot_retarget_other_tenant(monkeypatch):
    """Update with wrong agency_id in scope must not match."""
    db = FakeDB()
    db.videos = FakeColl()
    db.videos.docs.append(
        {"id": "v1", "agency_id": "agA", "property_id": "p1", "status": "pending"}
    )
    from apps.immoweb.micro_tour_video import _video_job_filter

    r = _run(
        db.videos.update_one(
            _video_job_filter("v1", agency_id="agB", property_id="p1"),
            {"$set": {"status": "ready"}},
        )
    )
    assert r.matched_count == 0
    assert db.videos.docs[0]["status"] == "pending"


def test_property_stat_days_private_read_requires_owner_contract():
    """Documented contract: stats HTTP path checks owner_user_id before read."""
    import inspect
    from apps.immocloud import private_listings as pl

    src = inspect.getsource(pl.get_my_private_listing_stats)
    assert "owner_user_id" in src
    assert "get_listing_stats" in src
    assert "is_private_listing" in src
