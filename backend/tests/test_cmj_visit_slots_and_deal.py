"""CMJ — visite ≥3 slot, label collab, continuità visita→Deal, deny dopo revoca."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from apps.immoweb import collaborations as collab_mod
from apps.immoweb import deals as deals_mod
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run
from tests.test_d175_deal_collab_chat import _patch_find

SLOTS3 = ["2026-12-10T10:00", "2026-12-10T14:00", "2026-12-10T16:00"]


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
    db.agencies.docs.extend(
        [
            {"id": "agA", "mls_enabled": True, "display_name": "Agenzia Alfa"},
            {"id": "agB", "mls_enabled": True, "display_name": "Agenzia Beta"},
        ]
    )
    db.properties.docs.append(
        {
            "id": "p1",
            "agency_id": "agA",
            "title": "Villa Lago",
            "address": "Via Roma 1",
            "city": "Como",
            "visibility": "public",
            "mls_shared": True,
        }
    )
    db.clients.docs.append({"id": "cl1", "agency_id": "agB", "name": "Mario", "surname": "Rossi"})

    async def agency_from_user(user):
        return user["agency_id"]

    with patch("apps.immoweb.collaborations.Database", _DB), patch(
        "apps.immoweb.deals.Database", _DB
    ), patch("apps.immoweb.collaborations._agency_id", agency_from_user), patch(
        "apps.immoweb.deals._agency_id", agency_from_user
    ):
        yield db


def _active_collab(harness):
    created = _run(
        collab_mod.create_collaboration_request(
            collab_mod.CollaborationCreate(property_id="p1", partner_agency_id="agB"),
            _user("agB"),
        )
    )
    _run(
        collab_mod.respond_collaboration(
            created["id"],
            collab_mod.CollaborationAction(action="accept"),
            _user("agA"),
        )
    )
    return created


@pytest.mark.parametrize(
    "slots,detail_key",
    [
        ([], "proposed_slots_min"),
        (["2026-12-10T10:00"], "proposed_slots_min"),
        (["2026-12-10T10:00", "2026-12-10T14:00"], "proposed_slots_min"),
    ],
)
def test_cmj_visit_rejects_fewer_than_three_slots(harness, slots, detail_key):
    collab = _active_collab(harness)
    with pytest.raises(HTTPException) as ei:
        _run(
            collab_mod.request_visit(
                collab_mod.VisitCreate(collaboration_id=collab["id"], proposed_slots=slots),
                _user("agB"),
            )
        )
    assert ei.value.status_code == 400
    detail = ei.value.detail
    if isinstance(detail, dict):
        assert detail.get("error") == detail_key
    else:
        assert detail_key in str(detail)


def test_cmj_visit_rejects_duplicates(harness):
    collab = _active_collab(harness)
    slots = ["2026-12-10T10:00", "2026-12-10T14:00", "2026-12-10T10:00"]
    with pytest.raises(HTTPException) as ei:
        _run(
            collab_mod.request_visit(
                collab_mod.VisitCreate(collaboration_id=collab["id"], proposed_slots=slots),
                _user("agB"),
            )
        )
    assert ei.value.status_code == 400
    assert ei.value.detail == "proposed_slots_duplicate"


def test_cmj_visit_rejects_blank_malformed_as_too_few(harness):
    collab = _active_collab(harness)
    with pytest.raises(HTTPException) as ei:
        _run(
            collab_mod.request_visit(
                collab_mod.VisitCreate(
                    collaboration_id=collab["id"],
                    proposed_slots=["  ", "2026-12-10T10:00", ""],
                ),
                _user("agB"),
            )
        )
    assert ei.value.status_code == 400


def test_cmj_visit_accepts_three_slots_and_agree(harness):
    collab = _active_collab(harness)
    visit = _run(
        collab_mod.request_visit(
            collab_mod.VisitCreate(collaboration_id=collab["id"], proposed_slots=SLOTS3),
            _user("agB"),
        )
    )
    assert visit["status"] == "requested"
    assert len(visit["proposed_slots"]) == 3
    assert visit.get("property_label") == "Villa Lago"

    with pytest.raises(HTTPException) as ei:
        _run(
            collab_mod.update_visit(
                visit["id"],
                collab_mod.VisitUpdate(status="agreed"),
                _user("agA"),
            )
        )
    assert ei.value.detail == "agreed_slot_required"

    with pytest.raises(HTTPException) as ei2:
        _run(
            collab_mod.update_visit(
                visit["id"],
                collab_mod.VisitUpdate(status="agreed", agreed_slot="2099-01-01T00:00"),
                _user("agA"),
            )
        )
    assert ei2.value.detail == "agreed_slot_not_in_proposed"

    agreed = _run(
        collab_mod.update_visit(
            visit["id"],
            collab_mod.VisitUpdate(status="agreed", agreed_slot=SLOTS3[1]),
            _user("agA"),
        )
    )
    assert agreed["status"] == "agreed"
    assert agreed["agreed_slot"] == SLOTS3[1]


def test_cmj_collab_list_enriched_labels(harness):
    _active_collab(harness)
    listed = _run(collab_mod.list_collaborations(status=None, user=_user("agB")))
    assert listed["items"]
    row = listed["items"][0]
    assert row["property_label"] == "Villa Lago"
    assert "Alfa" in (row.get("counterpart_agency_label") or "")
    assert row.get("viewer_role") == "partner"


def test_cmj_visit_to_deal_continuity_and_idempotency(harness):
    collab = _active_collab(harness)
    visit = _run(
        collab_mod.request_visit(
            collab_mod.VisitCreate(collaboration_id=collab["id"], proposed_slots=SLOTS3),
            _user("agB"),
        )
    )
    _run(
        collab_mod.update_visit(
            visit["id"],
            collab_mod.VisitUpdate(status="agreed", agreed_slot=SLOTS3[0]),
            _user("agA"),
        )
    )
    completed = _run(
        collab_mod.update_visit(
            visit["id"],
            collab_mod.VisitUpdate(status="completed"),
            _user("agB"),
        )
    )
    assert completed["status"] == "completed"

    deal1 = _run(
        deals_mod.open_deal(
            deals_mod.DealCreate(
                property_id="p1",
                client_id="cl1",
                collaboration_id=collab["id"],
                visit_id=visit["id"],
            ),
            _user("agB"),
        )
    )
    assert deal1["property_title"] == "Villa Lago"
    assert deal1["visit_id"] == visit["id"]

    deal2 = _run(
        deals_mod.open_deal(
            deals_mod.DealCreate(
                property_id="p1",
                client_id="cl1",
                collaboration_id=collab["id"],
                visit_id=visit["id"],
            ),
            _user("agB"),
        )
    )
    assert deal2["id"] == deal1["id"]
    assert len(harness.deals.docs) == 1


def test_cmj_deal_rejects_foreign_client(harness):
    collab = _active_collab(harness)
    harness.clients.docs.append({"id": "clX", "agency_id": "agA", "name": "Altro", "surname": "X"})
    with pytest.raises(HTTPException) as ei:
        _run(
            deals_mod.open_deal(
                deals_mod.DealCreate(
                    property_id="p1",
                    client_id="clX",
                    collaboration_id=collab["id"],
                ),
                _user("agB"),
            )
        )
    assert ei.value.status_code == 404


def test_cmj_revoked_blocks_new_visit(harness):
    collab = _active_collab(harness)
    _run(
        collab_mod.respond_collaboration(
            collab["id"],
            collab_mod.CollaborationAction(action="revoke"),
            _user("agA"),
        )
    )
    with pytest.raises(HTTPException) as ei:
        _run(
            collab_mod.request_visit(
                collab_mod.VisitCreate(collaboration_id=collab["id"], proposed_slots=SLOTS3),
                _user("agB"),
            )
        )
    assert ei.value.status_code in (400, 403)
