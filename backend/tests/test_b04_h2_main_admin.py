"""B04-H2 residual — Main Admin commercial binding (D01–D12)."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run, _seed_cc_agency


def _seed_user(db: FakeDB, *, user_id: str, role: str, verified=True, active=True):
    db.users = getattr(db, "users", FakeColl())
    db.users.docs.append(
        {
            "id": user_id,
            "email": f"{user_id}@x.it",
            "role": role,
            "email_verified": verified,
            "is_active": active,
        }
    )


def _patch_event_coll(db: FakeDB):
    db.commercial_main_admin_events = FakeColl()
    db.commercial_main_admin_transfers = FakeColl()
    db.notifications = FakeColl()
    if not hasattr(db, "users"):
        db.users = FakeColl()
    # FakeDB getattr for dynamic coll names used as db[EVENT_COLL]
    db.__getitem__ = lambda key: getattr(db, key)  # type: ignore


class _DBProxy:
    """Support db.users and db['commercial_main_admin_events']."""

    def __init__(self, fake: FakeDB):
        self._f = fake
        if not hasattr(fake, "users"):
            fake.users = FakeColl()
        if not hasattr(fake, "commercial_main_admin_events"):
            fake.commercial_main_admin_events = FakeColl()
        if not hasattr(fake, "commercial_main_admin_transfers"):
            fake.commercial_main_admin_transfers = FakeColl()
        if not hasattr(fake, "notifications"):
            fake.notifications = FakeColl()

    def __getattr__(self, name):
        return getattr(self._f, name)

    def __getitem__(self, name):
        if not hasattr(self._f, name):
            setattr(self._f, name, FakeColl())
        return getattr(self._f, name)


def test_nominate_ops_only():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="ops", role="super_admin")
    db = _DBProxy(raw)

    with pytest.raises(HTTPException) as ei:
        _run(
            mas.nominate_main_admin(
                db,
                commercial_customer_id="cc1",
                new_user_id="u_ma",
                actor={"id": "hacker", "role": "agency_admin"},
            )
        )
    assert ei.value.status_code == 403

    out = _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
            reason="ops_nominate",
        )
    )
    assert out["main_admin_user_id"] == "u_ma"
    events = db["commercial_main_admin_events"].docs
    assert any(e["event_type"] == "nominate" for e in events)


def test_agency_admin_denied_wallet_central():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_branch_admin_role", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    branch_admin_user = {
        "id": "u_branch_admin_role",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
    }
    with pytest.raises(HTTPException) as ei:
        _run(mas.assert_is_main_admin_of(db, branch_admin_user, "cc1"))
    assert ei.value.detail["error"] == "not_main_admin"


def test_main_admin_allowed():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    user = {
        "id": "u_ma",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
    }
    cc = _run(mas.assert_is_main_admin_of(db, user, "cc1", for_mutation=True))
    assert cc["id"] == "cc1"


def test_unassigned_and_other_cc_denied():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw, cc_id="cc1", agency_id="ag1")
    _seed_cc_agency(raw, cc_id="cc2", agency_id="ag2")
    _seed_user(raw, user_id="u1", role="agency_admin")
    db = _DBProxy(raw)
    user = {"id": "u1", "role": "agency_admin", "email_verified": True, "is_active": True}
    with pytest.raises(HTTPException) as ei:
        _run(mas.assert_is_main_admin_of(db, user, "cc1"))
    assert ei.value.detail["error"] == "main_admin_unassigned"

    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u1",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    with pytest.raises(HTTPException) as ei2:
        _run(mas.assert_is_main_admin_of(db, user, "cc2"))
    assert ei2.value.detail["error"] == "main_admin_unassigned" or ei2.value.detail["error"] == "not_main_admin"


def test_suspended_and_unverified_blocked():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    for u in (
        {"id": "u_ma", "role": "agency_admin", "email_verified": False, "is_active": True},
        {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": False},
        {"id": "u_ma", "role": "agency_admin", "email_verified": True},  # is_active missing
        {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": None},
    ):
        with pytest.raises(HTTPException) as ei:
            _run(mas.assert_is_main_admin_of(db, u, "cc1"))
        assert ei.value.detail["error"] == "account_not_eligible"


def test_user_is_eligible_requires_explicit_active_true():
    from shared.billing import main_admin_service as mas

    assert mas.user_is_eligible_main_admin(
        {"id": "u", "is_active": True, "email_verified": True}
    )
    assert not mas.user_is_eligible_main_admin(
        {"id": "u", "is_active": False, "email_verified": True}
    )
    assert not mas.user_is_eligible_main_admin(
        {"id": "u", "is_active": None, "email_verified": True}
    )
    assert not mas.user_is_eligible_main_admin(
        {"id": "u", "email_verified": True}
    )
    assert not mas.user_is_eligible_main_admin(None)


def test_ceased_blocks_mutation():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw, status="ceased")
    raw.commercial_customers.docs[0]["operational_status"] = "closed_readonly"
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    db = _DBProxy(raw)
    # force nominate even on ceased for test
    raw.commercial_customers.docs[0]["main_admin_user_id"] = "u_ma"
    user = {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": True}
    with pytest.raises(HTTPException) as ei:
        _run(mas.assert_is_main_admin_of(db, user, "cc1", for_mutation=True))
    assert ei.value.detail["error"] == "cc_not_operable"


def test_transfer_propose_accept_and_token_replay():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_new", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    actor = {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": True}
    prop = _run(
        mas.propose_transfer(
            db,
            commercial_customer_id="cc1",
            to_user_id="u_new",
            actor=actor,
        )
    )
    assert prop["status"] == "pending"
    token = prop["accept_token"]
    new_actor = {"id": "u_new", "role": "agency_admin", "email_verified": True, "is_active": True}
    ok = _run(
        mas.accept_transfer(
            db, transfer_id=prop["id"], token=token, actor=new_actor
        )
    )
    assert ok["main_admin_user_id"] == "u_new"
    # replay
    with pytest.raises(HTTPException) as ei:
        _run(
            mas.accept_transfer(
                db, transfer_id=prop["id"], token=token, actor=new_actor
            )
        )
    assert ei.value.status_code == 409


def test_transfer_expired_and_concurrent_accept():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_new", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    actor = {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": True}
    prop = _run(
        mas.propose_transfer(
            db, commercial_customer_id="cc1", to_user_id="u_new", actor=actor
        )
    )
    # expire
    db["commercial_main_admin_transfers"].docs[0]["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).isoformat()
    new_actor = {"id": "u_new", "role": "agency_admin", "email_verified": True, "is_active": True}
    with pytest.raises(HTTPException) as ei:
        _run(
            mas.accept_transfer(
                db,
                transfer_id=prop["id"],
                token=prop["accept_token"],
                actor=new_actor,
            )
        )
    assert ei.value.status_code == 409


def test_super_admin_emergency_requires_reason():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    db = _DBProxy(raw)
    ops = {"id": "ops", "role": "super_admin", "email_verified": True, "is_active": True}
    with pytest.raises(HTTPException) as ei:
        _run(
            mas.assert_super_admin_emergency_mutate(
                db, ops, "cc1", reason="short"
            )
        )
    assert ei.value.status_code == 400
    _run(
        mas.assert_super_admin_emergency_mutate(
            db,
            ops,
            "cc1",
            reason="lockout recovery allocate",
            organization_id="ag1",
            amount=10,
            operation="allocate",
        )
    )
    assert any(
        e["event_type"] == "super_admin_emergency"
        for e in db["commercial_main_admin_events"].docs
    )


def test_h1_revoke_still_bound_to_cc(monkeypatch):
    """H1 regression via service after Main Admin nominate."""
    from shared.billing import credit_wallet_service as cws
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw, cc_id="ccA", agency_id="agA")
    _seed_cc_agency(raw, cc_id="ccB", agency_id="agB")
    db = _DBProxy(raw)
    _run(
        cws.grant_lot(
            db,
            commercial_customer_id="ccB",
            amount=20,
            origin="t",
            reason="t",
            idempotency_key="h1r",
            allocate_to_organization_id="agB",
        )
    )
    alloc_id = db.credit_allocations.docs[0]["id"]
    with pytest.raises(HTTPException) as ei:
        _run(
            cws.revoke_allocation(
                db,
                allocation_id=alloc_id,
                commercial_customer_id="ccA",
                reason="x",
            )
        )
    assert ei.value.status_code == 404
    assert db.credit_allocations.docs[0]["remaining_qty"] == 20


def test_route_allocate_denies_agency_admin_without_binding(monkeypatch):
    from apps.billing import routes as billing_routes
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_filiale", role="agency_admin")
    db = _DBProxy(raw)

    class _DB:
        @staticmethod
        def get():
            return db

    monkeypatch.setattr(billing_routes, "Database", _DB)
    monkeypatch.setattr(
        billing_routes, "optional_agency_id", lambda user: user.get("active_agency_id")
    )
    user = {
        "id": "u_filiale",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
        "active_agency_id": "ag1",
    }
    with pytest.raises(HTTPException) as ei:
        _run(
            billing_routes.allocate_wallet_credits(
                {"organization_id": "ag1", "amount": 5},
                user=user,
            )
        )
    assert ei.value.status_code == 403


def test_d02_explicit_cc_wins_over_active_agency():
    """Main Admin of multiple CC can target CC-B even if agency maps to CC-A."""
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw, cc_id="ccA", agency_id="agA")
    _seed_cc_agency(raw, cc_id="ccB", agency_id="agB")
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    db = _DBProxy(raw)
    ops = {"id": "ops", "role": "super_admin"}
    _run(
        mas.nominate_main_admin(
            db, commercial_customer_id="ccA", new_user_id="u_ma", actor=ops
        )
    )
    _run(
        mas.nominate_main_admin(
            db, commercial_customer_id="ccB", new_user_id="u_ma", actor=ops
        )
    )
    user = {
        "id": "u_ma",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
    }
    resolved = _run(
        mas.resolve_wallet_cc_id(
            db,
            user,
            agency_id="agA",
            commercial_customer_id="ccB",
        )
    )
    assert resolved == "ccB"
    cc = _run(mas.assert_is_main_admin_of(db, user, "ccB", for_mutation=True))
    assert cc["id"] == "ccB"


def test_d08_cabina_failure_cancels_transfer_and_raises():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_new", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )

    async def _boom(doc):
        raise RuntimeError("cabina_down")

    db.notifications.insert_one = _boom  # type: ignore
    actor = {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": True}
    with pytest.raises(HTTPException) as ei:
        _run(
            mas.propose_transfer(
                db, commercial_customer_id="cc1", to_user_id="u_new", actor=actor
            )
        )
    assert ei.value.status_code == 503
    assert ei.value.detail["error"] == "cabina_notify_failed"
    transfers = db["commercial_main_admin_transfers"].docs
    assert len(transfers) == 1
    assert transfers[0]["status"] == "cancelled"
    assert transfers[0].get("cancel_reason") == "cabina_notify_failed"
    notify_events = [
        e
        for e in db["commercial_main_admin_events"].docs
        if e["event_type"] == "transfer_notify"
    ]
    assert notify_events and notify_events[-1]["outcome"] == "failed"


def test_d08_cabina_success_writes_inbox():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_new", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    actor = {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": True}
    prop = _run(
        mas.propose_transfer(
            db, commercial_customer_id="cc1", to_user_id="u_new", actor=actor
        )
    )
    assert prop["cabina_outcome"] == "sent"
    assert prop["status"] == "pending"
    assert any(n.get("type") == "main_admin_transfer" for n in db.notifications.docs)
    ok_events = [
        e
        for e in db["commercial_main_admin_events"].docs
        if e["event_type"] == "transfer_notify" and e["outcome"] == "success"
    ]
    assert ok_events and ok_events[-1]["meta"].get("cabina_outcome") == "sent"


def test_d10_double_accept_second_fails_binding_coherent():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_new", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    actor = {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": True}
    prop = _run(
        mas.propose_transfer(
            db, commercial_customer_id="cc1", to_user_id="u_new", actor=actor
        )
    )
    new_actor = {
        "id": "u_new",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
    }
    ok = _run(
        mas.accept_transfer(
            db, transfer_id=prop["id"], token=prop["accept_token"], actor=new_actor
        )
    )
    assert ok["main_admin_user_id"] == "u_new"
    with pytest.raises(HTTPException) as ei:
        _run(
            mas.accept_transfer(
                db, transfer_id=prop["id"], token=prop["accept_token"], actor=new_actor
            )
        )
    assert ei.value.status_code == 409
    cc = _run(mas.get_commercial_customer(db, "cc1"))
    assert cc["main_admin_user_id"] == "u_new"
    tr = db["commercial_main_admin_transfers"].docs[0]
    assert tr["status"] == "accepted"


def test_d10_accept_compensates_if_transfer_claim_lost():
    """If binding wins but transfer claim loses, restore previous MA (no orphan accepted)."""
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_new", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    actor = {"id": "u_ma", "role": "agency_admin", "email_verified": True, "is_active": True}
    prop = _run(
        mas.propose_transfer(
            db, commercial_customer_id="cc1", to_user_id="u_new", actor=actor
        )
    )

    real_claim = db["commercial_main_admin_transfers"].find_one_and_update

    async def _claim_always_none(filt, update, return_document=None, upsert=False):
        if filt.get("status") == "pending" and filt.get("id") == prop["id"]:
            return None
        return await real_claim(filt, update, return_document=return_document, upsert=upsert)

    db["commercial_main_admin_transfers"].find_one_and_update = _claim_always_none  # type: ignore
    new_actor = {
        "id": "u_new",
        "role": "agency_admin",
        "email_verified": True,
        "is_active": True,
    }
    with pytest.raises(HTTPException) as ei:
        _run(
            mas.accept_transfer(
                db, transfer_id=prop["id"], token=prop["accept_token"], actor=new_actor
            )
        )
    assert ei.value.status_code == 409
    cc = _run(mas.get_commercial_customer(db, "cc1"))
    assert cc["main_admin_user_id"] == "u_ma"
    tr = db["commercial_main_admin_transfers"].docs[0]
    assert tr["status"] == "pending"


def test_ops_replace_requires_force():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u1", role="agency_admin")
    _seed_user(raw, user_id="u2", role="agency_admin")
    db = _DBProxy(raw)
    ops = {"id": "ops", "role": "super_admin"}
    _run(
        mas.nominate_main_admin(
            db, commercial_customer_id="cc1", new_user_id="u1", actor=ops
        )
    )
    with pytest.raises(HTTPException) as ei:
        _run(
            mas.nominate_main_admin(
                db, commercial_customer_id="cc1", new_user_id="u2", actor=ops
            )
        )
    assert ei.value.status_code == 409
    with pytest.raises(HTTPException) as ei2:
        _run(
            mas.nominate_main_admin(
                db,
                commercial_customer_id="cc1",
                new_user_id="u2",
                actor=ops,
                force=True,
                reason="short",
            )
        )
    assert ei2.value.status_code == 400
    out = _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u2",
            actor=ops,
            force=True,
            reason="emergency lockout replace",
        )
    )
    assert out["main_admin_user_id"] == "u2"
    assert any(
        e["event_type"] == "ops_replace" for e in db["commercial_main_admin_events"].docs
    )


def test_mc043_bind_initial_main_admin_if_vacant():
    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_owner", role="agency_admin")
    db = _DBProxy(raw)
    assert raw.commercial_customers.docs[0].get("main_admin_user_id") in (None, "")
    out = _run(
        mas.bind_initial_main_admin_if_vacant(
            db, commercial_customer_id="cc1", user_id="u_owner"
        )
    )
    assert out["main_admin_user_id"] == "u_owner"
    # second call does not overwrite
    _seed_user(raw, user_id="u_other", role="agency_admin")
    out2 = _run(
        mas.bind_initial_main_admin_if_vacant(
            db, commercial_customer_id="cc1", user_id="u_other"
        )
    )
    assert out2 is None
    assert _run(mas.get_commercial_customer(db, "cc1"))["main_admin_user_id"] == "u_owner"


def test_mc041_expire_due_transfers_job():
    from datetime import datetime, timedelta, timezone

    from shared.billing import main_admin_service as mas

    raw = FakeDB()
    _seed_cc_agency(raw)
    _seed_user(raw, user_id="u_ma", role="agency_admin")
    _seed_user(raw, user_id="u_new", role="agency_admin")
    db = _DBProxy(raw)
    _run(
        mas.nominate_main_admin(
            db,
            commercial_customer_id="cc1",
            new_user_id="u_ma",
            actor={"id": "ops", "role": "super_admin"},
        )
    )
    prop = _run(
        mas.propose_transfer(
            db,
            commercial_customer_id="cc1",
            to_user_id="u_new",
            actor={
                "id": "u_ma",
                "role": "agency_admin",
                "email_verified": True,
                "is_active": True,
            },
        )
    )
    db["commercial_main_admin_transfers"].docs[0]["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    ).isoformat()
    report = _run(mas.expire_due_transfers(db))
    assert report["scanned"] >= 1
    assert report["expired"] >= 1
    assert db["commercial_main_admin_transfers"].docs[0]["status"] == "expired"
    assert prop["id"]
