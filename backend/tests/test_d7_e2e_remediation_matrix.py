"""D7 PRE-C remediation matrix T01–T22 (local only — no staging I/O).

No test in this file is claimed as staging-verified. L5 is not executed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.d7_e2e import config
from scripts.d7_e2e.email_gate import assess_email_no_send, run_email_gate
from scripts.d7_e2e.email_proof import inventory_email_send_paths, prove_no_send_local
from scripts.d7_e2e.inventory import CreatedInventory, reconcile_by_correlation
from scripts.d7_e2e.seed import _delete_by_ids, _scoped_cleanup, post_cleanup_verify


# ---------- Fake Mongo ----------


class FakeColl:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def insert_one(self, doc):
        self.docs.append(dict(doc))

    def insert_many(self, docs):
        for d in docs:
            self.insert_one(d)

    def find_one(self, flt, proj=None):
        for d in self.docs:
            if _match(d, flt):
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    def find(self, flt, proj=None):
        return [_match_proj(d, proj) for d in self.docs if _match(d, flt)]

    def delete_many(self, flt):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not _match(d, flt)]

        class R:
            deleted_count = before - len(self.docs)

        return R()

    def count_documents(self, flt):
        return sum(1 for d in self.docs if _match(d, flt))

    def update_one(self, flt, upd):
        for d in self.docs:
            if _match(d, flt):
                if "$set" in upd:
                    d.update(upd["$set"])
                return


def _match_proj(d, proj):
    if not proj:
        return {k: v for k, v in d.items() if k != "_id"}
    out = {}
    for k, keep in proj.items():
        if keep and k in d:
            out[k] = d[k]
    return out


def _match(doc, flt):
    if not flt:
        return True
    for k, v in flt.items():
        if k == "id" and isinstance(v, dict) and "$in" in v:
            if doc.get("id") not in v["$in"]:
                return False
            continue
        if isinstance(v, dict) and "$ne" in v:
            if doc.get(k) == v["$ne"]:
                return False
            continue
        # dotted meta.invite_id
        if "." in k:
            cur = doc
            ok = True
            for part in k.split("."):
                if not isinstance(cur, dict) or part not in cur:
                    ok = False
                    break
                cur = cur[part]
            if not ok or cur != v:
                return False
            continue
        if doc.get(k) != v:
            return False
    return True


class FakeDB:
    def __init__(self):
        self.cols = {}

    def __getitem__(self, name):
        return self.cols.setdefault(name, FakeColl())

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self[name]

    def list_collection_names(self):
        return list(self.cols.keys())


# ---------- T01–T05 intents / pending ----------


def test_T01_crash_after_create_before_register_reconcile(tmp_path):
    """T01: intent orphan → reconcile single match → register."""
    rid = "20261121T120000Z_t01aaaa"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(
        step="T3.create_collab",
        collection="mls_collaborations",
        correlation={"message": f"D7R2 collab {rid}", "property_id": "p1"},
    )
    # Simulate server created doc without register
    db = FakeDB()
    db["mls_collaborations"].insert_one(
        {"id": "c-orphan-1", "message": f"D7R2 collab {rid}", "property_id": "p1"}
    )
    inv.mark_orphan_suspected(iid, http_status=201)
    matches = reconcile_by_correlation(
        db, "mls_collaborations", {"message": f"D7R2 collab {rid}", "property_id": "p1"}
    )
    assert matches == ["c-orphan-1"]
    status = inv.reconcile_intent(iid, matches)
    assert status == "reconciled"
    assert "c-orphan-1" in inv.all_ids()["mls_collaborations"]
    assert inv.certification_ok()


# ---------- DEF-01 zero-match must not unlock CLEAN ----------


def test_DEF01_zero_match_uncertain_blocks_clean(tmp_path):
    rid = "20261121T120000Z_def01aa"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(step="x", collection="deals", correlation={"notes": "n"})
    inv.mark_orphan_suspected(iid)
    status = inv.reconcile_intent(iid, [])
    assert status == "uncertain"
    assert inv.has_uncertain()
    assert not inv.certification_ok()
    rec = next(r for r in inv.as_dict()["intents"] if r["intent_id"] == iid)
    assert rec["status"] == "orphan_unconfirmed"
    out = _scoped_cleanup(FakeDB(), rid, inventory=inv)
    assert out["classification"] == "DIRTY"


def test_DEF01_invisible_resource_not_deleted(tmp_path):
    """Resource exists in DB but reconcile query returns 0 → no delete, no CLEAN."""
    rid = "20261121T120000Z_def01bb"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(
        step="x", collection="deals", correlation={"notes": "unique-lag"}
    )
    inv.mark_orphan_suspected(iid)
    db = FakeDB()
    # Created under different field than correlation → invisible to reconcile
    db["deals"].insert_one({"id": "hidden-1", "notes": "other"})
    assert inv.reconcile_intent(iid, []) == "uncertain"
    out = _scoped_cleanup(db, rid, inventory=inv)
    assert db["deals"].find_one({"id": "hidden-1"})
    assert out["classification"] == "DIRTY"
    assert "deals" not in inv.all_ids() or "hidden-1" not in inv.all_ids().get("deals", [])


def test_DEF01_retry_then_single_match_reconciles(tmp_path):
    rid = "20261121T120000Z_def01cc"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(step="x", collection="deals", correlation={"notes": "n"})
    assert inv.reconcile_intent(iid, []) == "uncertain"
    assert not inv.certification_ok()
    assert inv.reconcile_intent(iid, ["deal-1"]) == "reconciled"
    assert inv.certification_ok()
    assert inv.all_ids()["deals"] == ["deal-1"]


def test_DEF01_retry_ambiguous_uncertain_no_delete(tmp_path):
    rid = "20261121T120000Z_def01dd"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(step="x", collection="deals", correlation={"notes": "n"})
    assert inv.reconcile_intent(iid, ["a", "b"]) == "uncertain"
    db = FakeDB()
    db["deals"].insert_one({"id": "a"})
    db["deals"].insert_one({"id": "b"})
    out = _scoped_cleanup(db, rid, inventory=inv)
    assert out["classification"] == "DIRTY"
    assert db["deals"].count_documents({}) == 2


def test_DEF01_retries_exhausted_still_dirty(tmp_path):
    rid = "20261121T120000Z_def01ee"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(step="x", collection="deals", correlation={"notes": "n"})
    for _ in range(CreatedInventory.MAX_RECONCILE_RETRIES):
        assert inv.reconcile_intent(iid, []) == "uncertain"
    rec = next(r for r in inv.as_dict()["intents"] if r["intent_id"] == iid)
    assert rec["status"] == "reconcile_exhausted"
    assert not inv.certification_ok()
    out = _scoped_cleanup(FakeDB(), rid, inventory=inv)
    assert out["classification"] == "DIRTY"
    # Idempotent cleanup while uncertain
    out2 = _scoped_cleanup(FakeDB(), rid, inventory=inv)
    assert out2["classification"] == "DIRTY"


def test_T02_timeout_reconcile_required_for_clean(tmp_path):
    rid = "20261121T120000Z_t02bbbb"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(
        step="T3.open_deal",
        collection="deals",
        correlation={"notes": f"D7R2 deal {rid}"},
    )
    inv.mark_orphan_suspected(iid)
    assert not inv.certification_ok()
    # without reconcile → cleanup DIRTY
    db = FakeDB()
    out = _scoped_cleanup(db, rid, inventory=inv)
    assert out["classification"] == "DIRTY"


def test_T03_response_without_id_marks_orphan(tmp_path):
    rid = "20261121T120000Z_t03cccc"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(step="x", collection="deals", correlation={"notes": "n"})
    inv.mark_orphan_suspected(iid, http_status=201)
    assert inv.open_intents()
    assert "deals" not in inv.all_ids() or not inv.all_ids().get("deals")


def test_T04_mid_flush_pending_parsed_on_cleanup(tmp_path):
    rid = "20261121T120000Z_t04dddd"
    inv = CreatedInventory(tmp_path, rid)
    # Simulate crash after first flush: pending has key, by_collection empty
    inv._data["pending"] = ["deals:deal-pending-1"]
    inv._flush()
    db = FakeDB()
    db["deals"].insert_one({"id": "deal-pending-1", "notes": "x"})
    out = _scoped_cleanup(db, rid, inventory=CreatedInventory(tmp_path, rid))
    assert out.get("pending:deals") == 1
    assert db["deals"].count_documents({}) == 0
    assert out["classification"] == "DIRTY"  # pending note


def test_T05_pending_blocks_clean_cert(tmp_path):
    rid = "20261121T120000Z_t05eeee"
    inv = CreatedInventory(tmp_path, rid)
    inv._data["pending"] = ["deals:x"]
    inv._flush()
    assert not inv.certification_ok()
    out = _scoped_cleanup(FakeDB(), rid, inventory=inv)
    assert out["classification"] == "DIRTY"
    assert "pending_unflushed_ids_present" in out["_notes"]


# ---------- T06–T08 cleanup ----------


def test_T06_cleanup_idempotent(tmp_path):
    rid = "20261121T120000Z_t06ffff"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("deals", "d1", source="t")
    db = FakeDB()
    db["deals"].insert_one({"id": "d1"})
    r1 = _scoped_cleanup(db, rid, inventory=inv)
    r2 = _scoped_cleanup(db, rid, inventory=inv)
    assert r1["inv:deals"] == 1
    assert r2["inv:deals"] == 0
    assert r1["classification"] == "CLEAN"
    assert r2["classification"] == "CLEAN"


def test_T07_cleanup_spares_foreign_ids(tmp_path):
    rid = "20261121T120000Z_t07gggg"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("deals", "mine", source="t")
    db = FakeDB()
    db["deals"].insert_one({"id": "mine"})
    db["deals"].insert_one({"id": "foreign"})
    _scoped_cleanup(db, rid, inventory=inv)
    assert db["deals"].find_one({"id": "foreign"})
    assert db["deals"].find_one({"id": "mine"}) is None


def test_T08_ambiguous_reconcile_uncertain_no_delete(tmp_path):
    rid = "20261121T120000Z_t08hhhh"
    inv = CreatedInventory(tmp_path, rid)
    iid = inv.open_intent(
        step="x",
        collection="deals",
        correlation={"notes": "same"},
    )
    status = inv.reconcile_intent(iid, ["a", "b"])
    assert status == "uncertain"
    assert inv.has_uncertain()
    db = FakeDB()
    db["deals"].insert_one({"id": "a"})
    db["deals"].insert_one({"id": "b"})
    out = _scoped_cleanup(db, rid, inventory=inv)
    assert out["classification"] == "DIRTY"
    # neither deleted via inventory (not registered)
    assert db["deals"].count_documents({}) == 2


# ---------- T09–T14 invite side effects / preexisting ----------


def test_T09_T10_membership_notification_in_inventory_and_cleanup(tmp_path):
    rid = "20261121T120000Z_t09iiii"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("memberships", "m1", source="T4")
    inv.register("notifications", "n1", source="T4")
    assert "memberships" in config.SIDE_EFFECT_COLLECTIONS
    db = FakeDB()
    db["memberships"].insert_one({"id": "m1"})
    db["notifications"].insert_one({"id": "n1"})
    out = _scoped_cleanup(db, rid, inventory=inv)
    assert out["inv:memberships"] == 1
    assert out["inv:notifications"] == 1
    assert db["memberships"].count_documents({}) == 0


def test_T11_created_by_run_user_deleted(tmp_path):
    rid = "20261121T120000Z_t11jjjj"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("users", "u-new", source="T4", created_by_run=True)
    db = FakeDB()
    db["users"].insert_one({"id": "u-new"})
    _scoped_cleanup(db, rid, inventory=inv)
    assert db["users"].count_documents({}) == 0


def test_T12_preexisting_user_not_deleted(tmp_path):
    rid = "20261121T120000Z_t12kkkk"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("users", "u-old", source="T4", created_by_run=False)
    db = FakeDB()
    db["users"].insert_one({"id": "u-old", "email": "exists@example.com"})
    out = _scoped_cleanup(db, rid, inventory=inv)
    assert db["users"].find_one({"id": "u-old"})
    assert any("skip_preexisting_user" in n for n in out.get("_notes", []))


def test_T13_register_idempotent_same_invite_id(tmp_path):
    rid = "20261121T120000Z_t13llll"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("agency_invites", "inv1", source="create")
    inv.register("agency_invites", "inv1", source="refresh")
    assert inv.all_ids()["agency_invites"] == ["inv1"]


def test_T14_open_intent_mid_saga_dirty(tmp_path):
    rid = "20261121T120000Z_t14mmmm"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("users", "u1", created_by_run=True)
    inv.open_intent(step="membership", collection="memberships", correlation={"user_id": "u1"})
    assert not inv.certification_ok()
    out = _scoped_cleanup(FakeDB(), rid, inventory=inv)
    assert out["classification"] == "DIRTY"


# ---------- T15–T21 email ----------


def test_T15_force_hold_persists_in_process():
    from shared.security import circuit as circuit_mod

    circuit_mod.clear_hold("resend")
    circuit_mod.force_hold("resend", "t15")
    assert circuit_mod.is_held("resend")
    # simulate reload of holds via force_hold again (load_holds path)
    circuit_mod.force_hold("resend", "t15-reload")
    assert circuit_mod.is_held("resend")
    circuit_mod.clear_hold("resend")


def test_T16_circuit_open_alone_not_gate_pass():
    a = assess_email_no_send(
        api_vars={"RESEND_API_KEY": "re_xxx", "OMNIA_ENV": "staging"},
        health_body={"message": {"circuits": {"resend": {"open": True, "held": False}}}},
    )
    assert a["ok"] is False
    assert a["mode"] is None
    assert "health_circuits_resend_open_not_durable" in a["reasons"]


def test_T16b_held_still_gate_pass():
    a = assess_email_no_send(
        api_vars={"RESEND_API_KEY": "re_xxx"},
        health_body={"message": {"circuits": {"resend": {"held": True, "open": True}}}},
    )
    assert a["ok"] is True
    assert a["mode"] == "killed"


def test_T17_dogfood_nonempty_allowlist_blocked():
    a = assess_email_no_send(
        api_vars={
            "RESEND_API_KEY": "re_xxx",
            "OMNIA_ENV": "dogfood",
            "OMNIA_EMAIL_ALLOWLIST": "a@example.com",
        },
    )
    assert a["ok"] is False


def test_T18_key_present_no_hold_blocked():
    a = assess_email_no_send(
        api_vars={"RESEND_API_KEY": "re_xxx", "OMNIA_ENV": "staging"},
        health_body={"message": {"circuits": {}}},
    )
    assert a["ok"] is False


def test_T19_email_path_inventory():
    paths = inventory_email_send_paths()
    assert paths
    assert any(p["transport"] == "resend.Emails.send" for p in paths)


def test_T20_gate_missing_token_blocked(monkeypatch):
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
    monkeypatch.delenv("RAILWAY_TOKEN", raising=False)
    # api_vars=None → would fetch if token present; without token → BLOCKED
    out = run_email_gate(skip_network=False, api_vars=None)
    assert out["classification"] == "BLOCKED"
    # Explicit empty injection must not trigger remote fetch; mock mode may PASS
    out2 = run_email_gate(skip_network=True, api_vars={})
    assert out2["classification"] == "PASS"
    assert out2["assessment"]["mode"] == "mock"


def test_T21_no_send_l3_l4_spy(tmp_path):
    evidence = prove_no_send_local(run_path=tmp_path)
    assert evidence["ok"] is True
    assert evidence["l5"] == "pending_staging_not_executed"
    for att in evidence["attempts"]:
        assert att["status"] == "killed"
        assert att["transport_calls"] == 0
    assert (tmp_path / "email_send_evidence.json").exists()


# ---------- T22 dual-run isolation ----------


def test_T22_dual_run_isolation(tmp_path):
    """T22 FakeDB: cleanup A must not touch B — includes memberships/notifications."""
    rid_a = "20261121T120000Z_t22aaaA"
    rid_b = "20261121T120000Z_t22aaaB"
    path_a = tmp_path / "a"
    path_b = tmp_path / "b"
    path_a.mkdir()
    path_b.mkdir()
    inv_a = CreatedInventory(path_a, rid_a)
    inv_b = CreatedInventory(path_b, rid_b)
    inv_a.register("deals", "deal-a", source="A")
    inv_a.register("mls_collaborations", "col-a", source="A")
    inv_a.register("memberships", "mem-a", source="A")
    inv_a.register("notifications", "not-a", source="A")
    inv_a.register("users", "user-a", source="A", created_by_run=True)
    inv_b.register("deals", "deal-b", source="B")
    inv_b.register("mls_collaborations", "col-b", source="B")
    inv_b.register("memberships", "mem-b", source="B")
    inv_b.register("notifications", "not-b", source="B")
    inv_b.register("users", "user-b", source="B", created_by_run=True)

    db = FakeDB()
    for coll, aid, bid in (
        ("deals", "deal-a", "deal-b"),
        ("mls_collaborations", "col-a", "col-b"),
        ("memberships", "mem-a", "mem-b"),
        ("notifications", "not-a", "not-b"),
        ("users", "user-a", "user-b"),
    ):
        db[coll].insert_one({"id": aid, config.RUN_TAG_FIELD: rid_a})
        db[coll].insert_one({"id": bid, config.RUN_TAG_FIELD: rid_b})
    # Foreign untagged — must survive (not inventoriable by email)
    db["users"].insert_one({"id": "foreign", "email": "x@example.com"})

    def _snap_b():
        return {
            c: sorted(
                d["id"]
                for d in db[c].docs
                if d["id"].endswith("-b") or d["id"] == "foreign"
            )
            for c in (
                "deals",
                "mls_collaborations",
                "memberships",
                "notifications",
                "users",
            )
        }

    snap_b_before = _snap_b()
    out_a = _scoped_cleanup(db, rid_a, inventory=inv_a)
    assert out_a["classification"] == "CLEAN"
    for cid in ("deal-b", "col-b", "mem-b", "not-b", "user-b", "foreign"):
        coll = {
            "deal-b": "deals",
            "col-b": "mls_collaborations",
            "mem-b": "memberships",
            "not-b": "notifications",
            "user-b": "users",
            "foreign": "users",
        }[cid]
        assert db[coll].find_one({"id": cid}), cid
    for cid, coll in (
        ("deal-a", "deals"),
        ("col-a", "mls_collaborations"),
        ("mem-a", "memberships"),
        ("not-a", "notifications"),
        ("user-a", "users"),
    ):
        assert db[coll].find_one({"id": cid}) is None
    assert snap_b_before == _snap_b()
    out_a2 = _scoped_cleanup(db, rid_a, inventory=inv_a)
    assert out_a2.get("inv:deals", 0) == 0
    assert db["memberships"].find_one({"id": "mem-b"})


def test_T22_unattributable_side_effect_blocks_clean(tmp_path):
    rid_a = "20261121T120000Z_t22uncA"
    inv = CreatedInventory(tmp_path, rid_a)
    inv.register("deals", "deal-a")
    inv._append_uncertain(
        {
            "collection": "notifications",
            "reason": "side_effect_unattributable",
            "candidate_ids": [],
            "ts": "t",
        }
    )
    db = FakeDB()
    db["deals"].insert_one({"id": "deal-a"})
    db["notifications"].insert_one({"id": "mystery", "email": "a@b.c"})
    out = _scoped_cleanup(db, rid_a, inventory=inv)
    assert out["classification"] == "DIRTY"
    # mystery not in inventory → not deleted
    assert db["notifications"].find_one({"id": "mystery"})


def test_T22_staging_contract_shape():
    """Contract checklist for future Mongo staging T22 (not executed remotely)."""
    required = {
        "preflight_db",
        "run_ids_disjoint",
        "snapshot_before",
        "inventory_a",
        "inventory_b",
        "memberships",
        "notifications",
        "cleanup_a_only",
        "compare_b",
        "residual_a",
        "cleanup_a_idempotent",
        "evidence_json",
        "pass_fail_blocked",
    }
    from scripts.d7_e2e.t22_staging_procedure import STAGING_T22_CONTRACT

    assert required <= set(STAGING_T22_CONTRACT.keys())
    assert STAGING_T22_CONTRACT["executed"] is False


def test_post_cleanup_verify_clean(tmp_path):
    rid = "20261121T120000Z_pcvvvv"
    inv = CreatedInventory(tmp_path, rid)
    inv.register("deals", "d1")
    db = FakeDB()
    db["deals"].insert_one({"id": "d1"})
    _scoped_cleanup(db, rid, inventory=inv)
    v = post_cleanup_verify(db, rid, inv)
    assert v["ok"] is True
    assert v["classification"] == "CLEAN"
