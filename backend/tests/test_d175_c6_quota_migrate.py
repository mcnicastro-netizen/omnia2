"""D-175 C6 — quota pool S3/S3-bis + migration S2."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from shared.storage import migrate_extra_to_cc as mig
from shared.storage import quota as q
from tests.test_b04ii_wallet_ledger import FakeColl, FakeDB, _run


def _base(db: FakeDB):
    db.commercial_customers = FakeColl()
    db.agencies = FakeColl()
    db.subscriptions = FakeColl()
    db.properties = FakeColl()
    db.payment_transactions = FakeColl()
    db.storage_migration_snapshots = FakeColl()


def test_c6_quota_included_once_two_orgs_pro_plus_extra():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append(
        {
            "id": "cc1",
            "storage_extra_gb": 100,
            "storage_migration_status": "migrated",
        }
    )
    db.agencies.docs.extend(
        [
            {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 0},
            {"id": "ag2", "commercial_customer_id": "cc1", "storage_extra_gb": 0},
        ]
    )
    db.subscriptions.docs.append(
        {
            "agency_id": "ag1",
            "commercial_customer_id": "cc1",
            "tier": "pro",
            "status": "active",
        }
    )
    db.properties.docs.append(
        {
            "agency_id": "ag2",
            "photos": [{"size_bytes": q.gb_to_bytes(150)}],
        }
    )

    status = _run(q.get_storage_status(db, "ag1"))
    assert status["included_plan_gb"] == 100
    assert status["extra_gb"] == 100
    assert status["quota_cc_gb"] == 200
    assert status["used_org_gb"] == 0
    assert status["used_cc_gb"] == 150.0


def test_c6_quota_starter_two_orgs_not_doubled():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append(
        {"id": "cc1", "storage_extra_gb": 0, "storage_migration_status": "migrated"}
    )
    db.agencies.docs.extend(
        [
            {"id": "ag1", "commercial_customer_id": "cc1"},
            {"id": "ag2", "commercial_customer_id": "cc1"},
        ]
    )
    db.subscriptions.docs.append(
        {
            "commercial_customer_id": "cc1",
            "agency_id": "ag1",
            "tier": "starter",
            "status": "active",
        }
    )
    st = _run(q.get_storage_status_for_cc(db, "cc1"))
    assert st["included_plan_gb"] == 30
    assert st["quota_cc_gb"] == 30


def test_c6_assert_upload_uses_pool_not_org_only():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append(
        {"id": "cc1", "storage_extra_gb": 0, "storage_migration_status": "migrated"}
    )
    db.agencies.docs.extend(
        [
            {"id": "ag1", "commercial_customer_id": "cc1"},
            {"id": "ag2", "commercial_customer_id": "cc1"},
        ]
    )
    db.subscriptions.docs.append(
        {
            "commercial_customer_id": "cc1",
            "tier": "starter",
            "status": "active",
            "agency_id": "ag1",
        }
    )
    db.properties.docs.append(
        {"agency_id": "ag2", "photos": [{"size_bytes": q.gb_to_bytes(30)}]}
    )
    with pytest.raises(HTTPException) as ei:
        _run(q.assert_can_upload(db, "ag1", incoming_bytes=1))
    assert ei.value.status_code == 413


def test_c6_migrate_dry_run_no_mutations():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append({"id": "cc1", "storage_extra_gb": 0})
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 100}
    )
    db.payment_transactions.docs.append(
        {
            "session_id": "cs_stor_1",
            "kind": "storage_addon",
            "payment_status": "paid",
            "storage_gb": 100,
            "commercial_customer_id": "cc1",
            "agency_id": "ag1",
        }
    )
    dry = _run(mig.run_migration(db, dry_run=True, cc_id="cc1"))
    assert dry["dry_run"] is True
    assert dry["migrate"] == 1
    assert db.agencies.docs[0]["storage_extra_gb"] == 100
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 0
    assert db.storage_migration_snapshots.docs == []
    assert db.commercial_customers.docs[0].get("storage_migration_status") in (
        None,
        "",
    )


def test_c6_migrate_preserves_legacy_snapshot():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append({"id": "cc1", "storage_extra_gb": 0})
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 100}
    )
    db.payment_transactions.docs.append(
        {
            "session_id": "cs_stor_1",
            "kind": "storage_addon",
            "payment_status": "paid",
            "storage_gb": 100,
            "commercial_customer_id": "cc1",
            "agency_id": "ag1",
        }
    )

    applied = _run(mig.run_migration(db, dry_run=False, cc_id="cc1"))
    assert applied["migrate"] == 1
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100
    assert db.agencies.docs[0]["storage_extra_gb"] == 0
    snaps = db.storage_migration_snapshots.docs
    assert len(snaps) == 1
    assert snaps[0]["agency_id"] == "ag1"
    assert snaps[0]["previous_storage_extra_gb"] == 100
    assert snaps[0]["transferred_gb"] == 100
    assert snaps[0]["outcome"] == "migrated"
    assert "cs_stor_1" in snaps[0]["verified_session_ids"]


def test_c6_migrate_idempotent_reapply():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append({"id": "cc1", "storage_extra_gb": 0})
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 100}
    )
    db.payment_transactions.docs.append(
        {
            "session_id": "cs_stor_1",
            "kind": "storage_addon",
            "payment_status": "paid",
            "storage_gb": 100,
            "commercial_customer_id": "cc1",
            "agency_id": "ag1",
        }
    )
    _run(mig.run_migration(db, dry_run=False, cc_id="cc1"))
    second = _run(mig.run_migration(db, dry_run=False, cc_id="cc1"))
    assert second["noop"] == 1
    assert db.commercial_customers.docs[0]["storage_extra_gb"] == 100
    # snapshots not duplicated for same outcome+previous
    assert len(db.storage_migration_snapshots.docs) == 1


def test_c6_migrate_suspend_unverified_agency_extra():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append({"id": "cc1", "storage_extra_gb": 0})
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 200}
    )
    report = _run(mig.run_migration(db, dry_run=False, cc_id="cc1"))
    assert report["suspend"] == 1
    assert db.commercial_customers.docs[0]["storage_migration_status"] == "suspended"
    assert db.agencies.docs[0]["storage_extra_gb"] == 200
    assert db.storage_migration_snapshots.docs[0]["previous_storage_extra_gb"] == 200
    assert db.storage_migration_snapshots.docs[0]["outcome"] == "suspended"


def test_c6_migrate_suspend_tx_agency_cc_mismatch():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.extend(
        [
            {"id": "cc1", "storage_extra_gb": 0},
            {"id": "cc2", "storage_extra_gb": 0},
        ]
    )
    db.agencies.docs.append(
        {"id": "ag2", "commercial_customer_id": "cc2", "storage_extra_gb": 0}
    )
    db.payment_transactions.docs.append(
        {
            "session_id": "cs_bad",
            "kind": "storage_addon",
            "payment_status": "paid",
            "storage_gb": 100,
            "commercial_customer_id": "cc1",
            "agency_id": "ag2",  # belongs to cc2
        }
    )
    report = _run(mig.run_migration(db, dry_run=True))
    assert report["cc_agency_mismatch_sessions"]
    assert report["suspend"] >= 1
    # no silent credit to cc1
    assert report["migrate"] == 0


def test_c6_migrate_discordant_session_anomaly():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append({"id": "cc1", "storage_extra_gb": 0})
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 100}
    )
    db.payment_transactions.docs.extend(
        [
            {
                "session_id": "cs_same",
                "kind": "storage_addon",
                "payment_status": "paid",
                "storage_gb": 100,
                "commercial_customer_id": "cc1",
            },
            {
                "session_id": "cs_same",
                "kind": "storage_addon",
                "payment_status": "paid",
                "storage_gb": 200,  # discordant
                "commercial_customer_id": "cc1",
            },
        ]
    )
    report = _run(mig.run_migration(db, dry_run=True, cc_id="cc1"))
    assert report["discordant_sessions"]
    assert report["suspend"] == 1
    assert report["migrate"] == 0


def test_c6_migrate_dedupe_coherent_session():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append({"id": "cc1", "storage_extra_gb": 0})
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 100}
    )
    for _ in range(2):
        db.payment_transactions.docs.append(
            {
                "session_id": "cs_same",
                "kind": "storage_addon",
                "payment_status": "paid",
                "storage_gb": 100,
                "commercial_customer_id": "cc1",
            }
        )
    row = _run(mig.classify_cc(db, "cc1"))
    assert row["status"] == "migrate"
    assert row["verifiable_gb"] == 100


def test_c6_suspended_effective_extra_not_under_quota():
    db = FakeDB()
    _base(db)
    db.commercial_customers.docs.append(
        {
            "id": "cc1",
            "storage_extra_gb": 0,
            "storage_migration_status": "suspended",
        }
    )
    db.agencies.docs.append(
        {"id": "ag1", "commercial_customer_id": "cc1", "storage_extra_gb": 100}
    )
    db.subscriptions.docs.append(
        {
            "commercial_customer_id": "cc1",
            "tier": "starter",
            "status": "active",
            "agency_id": "ag1",
        }
    )
    st = _run(q.get_storage_status_for_cc(db, "cc1"))
    assert st["extra_gb"] == 100
    assert st["quota_cc_gb"] == 130
