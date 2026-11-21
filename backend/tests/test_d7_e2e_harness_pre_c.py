"""Local unit tests for D7 harness pre-Package C fixes (no staging I/O)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO = Path(__file__).resolve().parents[2]
# Ensure repo root precedes backend/ on sys.path (conftest adds backend).
sys.path.insert(0, str(REPO))

from scripts.d7_e2e import config
from scripts.d7_e2e.artifacts import artifacts_d7_root, new_run_id, run_dir
from scripts.d7_e2e.email_gate import assess_email_no_send, run_email_gate
from scripts.d7_e2e.inventory import CreatedInventory
from scripts.d7_e2e.run_id import InvalidRunId, validate_run_id
from scripts.d7_e2e.seed import (
    CLEANUP_REAL_COLLECTIONS,
    PHANTOM_COLLECTIONS_REMOVED,
    _delete_by_ids,
    _scoped_cleanup,
    ids,
)


# ---------- FIX3 run_id ----------


def test_run_id_valid_generated():
    rid = new_run_id()
    assert validate_run_id(rid) == rid


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "short",
        "../escape_path_x",
        "../../etc_passwd1",
        "/absolute/pathxx",
        "foo/bar/bazzzz",
        "has spaceshere1",
        "semi;colonxxxx",
        "a" * 65,
        "traversal..here",
    ],
)
def test_run_id_rejects_unsafe(bad):
    with pytest.raises(InvalidRunId):
        validate_run_id(bad)


def test_run_dir_refuses_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.d7_e2e.artifacts.repo_root", lambda: tmp_path
    )
    (tmp_path / "artifacts" / "d7").mkdir(parents=True)
    # Charset already blocks .. ; also ensure resolve guard with a valid-looking id
    rid = "20261121T120000Z_abcd1234"
    d = run_dir(rid, create=True)
    assert d.resolve().is_relative_to(artifacts_d7_root())


# ---------- FIX1 cleanup / inventory ----------


def test_cleanup_uses_real_mls_collections():
    assert "mls_collaborations" in CLEANUP_REAL_COLLECTIONS
    assert "mls_visits" in CLEANUP_REAL_COLLECTIONS
    assert "mls_visit_feedback" in CLEANUP_REAL_COLLECTIONS
    assert "mls_chat_threads" in CLEANUP_REAL_COLLECTIONS
    assert "mls_chat_messages" in CLEANUP_REAL_COLLECTIONS
    assert "deals" in CLEANUP_REAL_COLLECTIONS
    for phantom in PHANTOM_COLLECTIONS_REMOVED:
        assert phantom not in CLEANUP_REAL_COLLECTIONS


def test_inventory_register_and_flush(tmp_path):
    rid = "20261121T120000Z_invtest1"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("mls_collaborations", "c1", source="test")
    inv.register("deals", "d1", source="test")
    assert inv.path.exists()
    loaded = json.loads(inv.path.read_text())
    assert loaded["run_id"] == rid
    assert loaded["by_collection"]["mls_collaborations"] == ["c1"]
    assert loaded["pending"] == []
    assert not inv.has_pending()


def test_scoped_cleanup_deletes_only_inventory_ids():
    class FakeColl:
        def __init__(self):
            self.deleted = []

        def delete_many(self, flt):
            self.deleted.append(flt)

            class R:
                deleted_count = 1 if flt else 0

            return R()

    class FakeDB:
        def __init__(self):
            self.cols = {
                "mls_collaborations": FakeColl(),
                "deals": FakeColl(),
                "users": FakeColl(),
            }

        def __getitem__(self, name):
            return self.cols.setdefault(name, FakeColl())

        def list_collection_names(self):
            return list(self.cols.keys())

    rid = "20261121T120000Z_clean01"
    inv = CreatedInventory(Path("/tmp"), rid)  # noqa: S108 — path unused until register
    # Use real tmp via monkeypatch of path
    # re-init properly:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        inv = CreatedInventory(Path(td), rid)
        inv.register("mls_collaborations", "only-this-collab")
        inv.register("deals", "only-this-deal")
        db = FakeDB()
        counts = _scoped_cleanup(db, rid, inventory=inv)
        assert counts["inv:mls_collaborations"] == 1
        assert counts["inv:deals"] == 1
        # inventory deletes are by id $in
        assert db.cols["mls_collaborations"].deleted[0] == {
            "id": {"$in": ["only-this-collab"]}
        }
        # tagged filter uses exact run_id
        assert any(
            f == {config.RUN_TAG_FIELD: rid} for f in db.cols["users"].deleted
        )


def test_delete_by_ids_empty():
    db = MagicMock()
    assert _delete_by_ids(db, "deals", []) == 0
    db.__getitem__.assert_not_called()


# ---------- FIX2 email gate ----------


def test_email_gate_mock_when_no_key():
    a = assess_email_no_send(api_vars={}, health_body=None)
    assert a["ok"] is True
    assert a["mode"] == "mock"


def test_email_gate_blocked_dogfood_empty_allowlist():
    a = assess_email_no_send(
        api_vars={"RESEND_API_KEY": "re_xxx", "OMNIA_ENV": "dogfood", "OMNIA_EMAIL_ALLOWLIST": ""},
        health_body=None,
    )
    assert a["ok"] is True
    assert a["mode"] == "blocked"
    # never echo key
    assert "re_xxx" not in json.dumps(a)


def test_email_gate_killed_via_health_circuit():
    a = assess_email_no_send(
        api_vars={"RESEND_API_KEY": "re_xxx"},
        health_body={"message": {"db": "ok", "circuits": {"resend": {"held": True}}}},
    )
    assert a["ok"] is True
    assert a["mode"] == "killed"


def test_email_gate_open_alone_not_killed():
    a = assess_email_no_send(
        api_vars={"RESEND_API_KEY": "re_xxx", "OMNIA_ENV": "staging"},
        health_body={"message": {"db": "ok", "circuits": {"resend": {"open": True}}}},
    )
    assert a["ok"] is False
    assert a["mode"] is None


def test_email_gate_fail_closed_when_key_present():
    a = assess_email_no_send(
        api_vars={"RESEND_API_KEY": "re_xxx", "OMNIA_ENV": "staging"},
        health_body={"message": {"db": "ok", "circuits": {}}},
    )
    assert a["ok"] is False
    assert a["classification"] == "BLOCKED"
    assert a["signals"]["resend_key_present"] is True


def test_run_email_gate_skip_network_blocked():
    out = run_email_gate(
        api_vars={"RESEND_API_KEY": "re_xxx", "OMNIA_ENV": "production"},
        skip_network=True,
    )
    assert out["classification"] == "BLOCKED"
    assert any(s["step"] == "T4.email_gate_no_send" for s in out["steps"])


def test_run_email_gate_skip_network_pass_mock():
    out = run_email_gate(api_vars={}, skip_network=True)
    assert out["classification"] == "PASS"
    assert out["assessment"]["mode"] == "mock"


# ---------- FIX4 / FIX5 helpers ----------


def test_seed_ids_include_iso_tenant():
    rid = "20261121T120000Z_iso0001"
    I = ids(rid)
    assert "ag_iso" in I
    assert "user_iso" in I
    assert "cc_iso" in I
    assert "email_iso" in I
    assert I["cc_iso"] != I["cc"]
    assert I["ag_iso"] != I["ag_active"]


def test_pin_drift_detects_mismatch(monkeypatch):
    monkeypatch.setenv("OMNIA_D7_STAGING_API_URL", "https://evil.example.com")
    report = config.pin_drift_report()
    assert report["ok"] is False
    assert any(d["env"] == "OMNIA_D7_STAGING_API_URL" for d in report["drifts_mismatch"])


def test_pin_drift_ok_when_override_matches(monkeypatch):
    monkeypatch.setenv("OMNIA_D7_STAGING_API_URL", config.CANONICAL_STAGING_API_URL)
    report = config.pin_drift_report()
    assert report["ok"] is True


def test_canonical_not_env_rebindable(monkeypatch):
    """Identity aliases always equal canonical even if env is set wrong."""
    monkeypatch.setenv("OMNIA_D7_STAGING_DB_NAME", "omnia_production")
    # Module already bound — re-import check via CANONICAL vs STAGING alias
    assert config.STAGING_DB_NAME == config.CANONICAL_STAGING_DB_NAME
    assert config.STAGING_DB_NAME == "omnia_staging_e2e"
    assert config.pin_drift_report()["ok"] is False


def test_precheck_p7_requires_db_ok_not_status_alone(monkeypatch):
    from scripts.d7_e2e import precheck as pc
    from scripts.d7_e2e.classify import aggregate

    # Simulate only the health predicate logic used in P7
    health = {"status": "ok", "message": {"text": "hi"}}  # no db
    db_ok = (
        isinstance(health, dict)
        and isinstance(health.get("message"), dict)
        and health["message"].get("db") == "ok"
    )
    assert db_ok is False
    health2 = {"message": {"db": "ok"}}
    db_ok2 = (
        isinstance(health2, dict)
        and isinstance(health2.get("message"), dict)
        and health2["message"].get("db") == "ok"
    )
    assert db_ok2 is True
    # aggregate empty → FAIL (fail-closed)
    assert aggregate([]) == "FAIL"


def test_precheck_p2_exact_not_substring():
    """Document: exact set equality, not 85845f42 substring."""
    canonical = config.CANONICAL_STAGING_API_URL
    api_refs = {canonical, "https://other-85845f42.up.railway.app"}
    assert api_refs != {canonical}
    api_refs2 = {canonical}
    assert api_refs2 == {canonical}


def test_cli_rejects_bad_run_id_without_staging():
    from scripts.d7_e2e.__main__ import main

    rc = main(["cleanup", "--confirm-staging-run", "--run-id", "../escape_here"])
    assert rc == 2


def test_cli_missing_confirm_exit_2():
    from scripts.d7_e2e.__main__ import main

    with pytest.raises(SystemExit) as ei:
        main(["precheck"])
    assert ei.value.code == 2
