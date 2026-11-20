"""D-175 — API handlers for collab / visit / feedback / doc-request / chat / deal (FakeDB)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from apps.immoweb import collaborations as collab_mod
from apps.immoweb import deals as deals_mod
from shared.mls_collab.service import require_thread_access
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run
from tests.test_d175_deal_collab_chat import _patch_find


def _user(agency_id="agA", role="agency_admin", uid="u1"):
    return {"id": uid, "role": role, "agency_id": agency_id, "sub": uid}


class _DB:
    _inst = None

    @classmethod
    def get(cls):
        return cls._inst

    @classmethod
    def get_raw(cls):
        return cls._inst


def _bind(db: FakeDB):
    _DB._inst = db
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
        "agencies",
        "mls_document_artifacts",
        "mls_document_distributions",
        "mls_rating_dispute_audit",
    ):
        if not hasattr(db, name) or getattr(db, name) is None:
            setattr(db, name, FakeColl())
        _patch_find(getattr(db, name))


@pytest.fixture
def harness():
    db = FakeDB()
    _bind(db)
    db.agencies = FakeColl()
    _patch_find(db.agencies)
    db.agencies.docs.extend(
        [
            {"id": "agA", "mls_enabled": True},
            {"id": "agB", "mls_enabled": True},
            {"id": "agX", "mls_enabled": True},
        ]
    )
    db.mls_document_artifacts = FakeColl()
    _patch_find(db.mls_document_artifacts)
    db.mls_document_distributions = FakeColl()
    _patch_find(db.mls_document_distributions)
    db.mls_rating_dispute_audit = FakeColl()
    _patch_find(db.mls_rating_dispute_audit)

    async def agency_from_user(user):
        return user["agency_id"]

    with patch("apps.immoweb.collaborations.Database", _DB), patch(
        "apps.immoweb.deals.Database", _DB
    ), patch("apps.immoweb.collaborations._agency_id", agency_from_user), patch(
        "apps.immoweb.deals._agency_id", agency_from_user
    ):
        yield db


def test_accept_collab_no_auto_doc_then_visit_feedback_deal_chat(harness):
    db = harness
    db.properties.docs.append(
        {
            "id": "p1",
            "agency_id": "agA",
            "title": "Villa",
            "visibility": "public",
            "mls_shared": True,
        }
    )
    db.clients.docs.append({"id": "cl1", "agency_id": "agB", "name": "Mario", "surname": "R"})

    # B requests collab
    body = collab_mod.CollaborationCreate(property_id="p1", partner_agency_id="agB")
    created = _run(collab_mod.create_collaboration_request(body, _user("agB")))
    assert created["status"] == "pending"
    assert created["document_request_auto"] is False

    # A accepts — no document request
    resp = _run(
        collab_mod.respond_collaboration(
            created["id"],
            collab_mod.CollaborationAction(action="accept"),
            _user("agA"),
        )
    )
    assert resp["status"] == "active"
    assert resp["document_request_created"] is False
    assert len(db.mls_document_requests.docs) == 0

    # Visit
    visit = _run(
        collab_mod.request_visit(
            collab_mod.VisitCreate(collaboration_id=created["id"]),
            _user("agB"),
        )
    )
    visit = _run(
        collab_mod.update_visit(
            visit["id"],
            collab_mod.VisitUpdate(status="agreed"),
            _user("agA"),
        )
    )
    visit = _run(
        collab_mod.update_visit(
            visit["id"],
            collab_mod.VisitUpdate(status="completed"),
            _user("agA"),
        )
    )
    assert visit["status"] == "completed"

    # Mini-dossier feedback
    fb = _run(
        collab_mod.create_visit_feedback(
            collab_mod.VisitFeedbackCreate(visit_id=visit["id"], rating=4, feedback_text="ok"),
            _user("agB"),
        )
    )
    assert fb["kind"] == "post_visit_feedback"
    assert fb["is_document_request"] is False
    assert fb["shares_documents"] is False

    # Explicit document request
    dr = _run(
        collab_mod.create_document_request(
            collab_mod.DocumentRequestCreate(
                collaboration_id=created["id"],
                visit_id=visit["id"],
                document_keys=["ape"],
            ),
            _user("agB"),
        )
    )
    assert dr["auto_created"] is False
    fulfilled = _run(
        collab_mod.respond_document_request(
            dr["id"],
            collab_mod.DocumentRequestAction(action="fulfill", shared_document_ids=["d1"]),
            _user("agA"),
        )
    )
    assert fulfilled["watermark_applied"] is True
    access = _run(collab_mod.log_document_access(dr["id"], _user("agB")))
    assert access["watermark"] is True
    with pytest.raises(HTTPException) as ei:
        _run(collab_mod.log_document_access(dr["id"], _user("agX")))
    assert ei.value.status_code == 403

    # Chat
    thread = _run(
        collab_mod.open_chat_thread(
            collab_mod.ChatOpenBody(collaboration_id=created["id"], visit_id=visit["id"]),
            _user("agB"),
        )
    )
    msg = _run(
        collab_mod.post_chat_message(
            thread["id"],
            collab_mod.ChatMessageBody(body="Ciao, conferma orario"),
            _user("agB"),
        )
    )
    listed = _run(collab_mod.list_chat_messages(thread["id"], _user("agA")))
    assert any(m["id"] == msg["id"] for m in listed["items"])
    with pytest.raises(HTTPException):
        _run(collab_mod.list_chat_messages(thread["id"], _user("agX")))

    # Deal
    deal = _run(
        deals_mod.open_deal(
            deals_mod.DealCreate(
                property_id="p1",
                client_id="cl1",
                visit_id=visit["id"],
                collaboration_id=created["id"],
            ),
            _user("agB"),
        )
    )
    assert deal["status"] == "open"
    deal = _run(
        deals_mod.add_proposal(
            deal["id"],
            deals_mod.DealProposal(amount=250000),
            _user("agB"),
        )
    )
    assert deal["status"] == "proposal_prepared"
    deal = _run(deals_mod.send_proposal(deal["id"], _user("agB")))
    assert deal["status"] == "proposal_sent"
    deal = _run(
        deals_mod.partner_respond_proposal(
            deal["id"],
            deals_mod.DealPartnerRespond(action="accepted"),
            _user("agA"),
        )
    )
    assert deal["status"] == "accepted"
    with pytest.raises(HTTPException):
        _run(deals_mod.get_deal_detail(deal["id"], _user("agX")))

    # Revoke collab → chat revoked
    _run(
        collab_mod.respond_collaboration(
            created["id"],
            collab_mod.CollaborationAction(action="revoke"),
            _user("agA"),
        )
    )
    thr = _run(db.mls_chat_threads.find_one({"id": thread["id"]}))
    assert thr["status"] == "revoked"
    with pytest.raises(HTTPException):
        require_thread_access(thr, "agB")


def test_h4_gate_blocks_without_sealed(monkeypatch, tmp_path):
    from shared.dogfood import perimeter as p

    monkeypatch.setenv("OMNIA_H4_PURCHASE_READY", "true")
    monkeypatch.setenv("OMNIA_H4_READY_MARKER_PATH", str(tmp_path / "missing.sealed"))
    assert p.is_h4_purchase_ready() is False
