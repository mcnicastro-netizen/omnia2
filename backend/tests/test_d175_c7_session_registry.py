"""D-175 C7 — session registry, jcanonical, seal-before-recover, Ed25519 verify."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.dogfood.checkpoint import (  # noqa: E402
    build_unsigned_checkpoint,
    checkpoint_message,
    fingerprint_sha256,
    resolve_expected_fingerprint,
    verify_checkpoint_signature,
)
from shared.dogfood.jcanonical import (  # noqa: E402
    CanonicalError,
    GENESIS_PREV_HASH,
    canonical_json,
    canonical_json_bytes,
    validate_ts_utc,
)
from shared.dogfood.session_registry import (  # noqa: E402
    RegistryError,
    SessionRegistry,
    compute_event_hash,
    serialize_event_line,
)


@pytest.fixture
def sessions_tmp(tmp_path, monkeypatch):
    root = tmp_path / "dogfood"
    (root / "sessions").mkdir(parents=True)
    monkeypatch.setenv("DOGFOOD_ROOT", str(root))
    return root


def test_c7_canonical_examples_match_design():
    pre0 = {
        "actor": "system",
        "event_id": "00000000-0000-4000-8000-000000000001",
        "journal_format_version": "omnia.dogfood.journal.v1",
        "payload": {"kind": "CLEAN"},
        "prev_hash": GENESIS_PREV_HASH,
        "seq": 0,
        "session_id": "00000000-0000-4000-8000-0000000000aa",
        "ts_utc": "2026-11-20T12:00:00.000Z",
        "type": "SESSION_OPEN",
    }
    h0 = compute_event_hash(pre0)
    assert h0 == "c92113691b5a820ffe4fe09bd35fd0c839d4cd5e7a49f6abde7f4cb9acf67436"
    pre1 = {
        "actor": "system",
        "event_id": "00000000-0000-4000-8000-000000000002",
        "journal_format_version": "omnia.dogfood.journal.v1",
        "payload": {"note": "bind"},
        "prev_hash": h0,
        "seq": 1,
        "session_id": "00000000-0000-4000-8000-0000000000aa",
        "ts_utc": "2026-11-20T12:00:01.000Z",
        "type": "BINDING_ASSERTED",
    }
    h1 = compute_event_hash(pre1)
    assert h1 == "72f507718896842c050dc1077f43999c93ec46d60b89bcda67a12cb2b4337199"


def test_c7_canonical_rejects_float_and_bad_ts():
    with pytest.raises(CanonicalError):
        canonical_json({"a": 1.5})
    with pytest.raises(CanonicalError):
        validate_ts_utc("2026-11-20T12:00:00Z")  # missing ms
    with pytest.raises(CanonicalError):
        validate_ts_utc("2026-02-30T12:00:00.000Z")
    with pytest.raises(CanonicalError):
        validate_ts_utc("2026-11-20T12:00:00.000+01:00")


def test_c7_utf16_key_order_divergence():
    # U+E000 vs emoji: UTF-16 order puts emoji first
    obj = {"\ue000": 1, "\U0001f600": 2}
    text = canonical_json(obj)
    assert text.index("\U0001f600") < text.index("\ue000") or text.startswith(
        '{"\\u'
    ) or "\U0001f600" in text.encode("utf-8").decode("utf-8")
    # Ensure deterministic: emoji key sorts before U+E000 under UTF-16
    assert list(json.loads(text).keys())[0] in ("\U0001f600", "\ue000")
    keys_order = []
    # parse canonical text manually — keys appear in UTF-16 order
    # emoji UTF-16 BE starts with D83D; U+E000 is E000; D83D < E000
    assert text.index('"') >= 0
    first_key_start = 2  # after {"
    # simpler: rebuild expected
    expected = (
        '{"'
        + "\U0001f600"
        + '":2,"'
        + "\ue000"
        + '":1}'
    )
    # Our encoder does not escape non-ascii
    assert canonical_json(obj) == expected


def test_c7_open_clean_denied_when_dirty(sessions_tmp, monkeypatch, tmp_path):
    # Simulate dirty tree by mocking git_dirty
    import shared.dogfood.session_registry as sr

    monkeypatch.setattr(sr, "git_dirty", lambda cwd=None: True)
    monkeypatch.setattr(sr, "git_sha", lambda cwd=None: "a" * 40)
    monkeypatch.setattr(sr, "git_branch", lambda cwd=None: "main")
    reg = SessionRegistry(sessions_tmp)
    with pytest.raises(RegistryError, match="CLEAN_DENIED_DIRTY_TREE"):
        reg.open_session(copy_kind="CLEAN", workcopy_id="omnia_df_clean_t")


def test_c7_open_close_verify_chain(sessions_tmp, monkeypatch):
    import shared.dogfood.session_registry as sr

    monkeypatch.setattr(sr, "git_dirty", lambda cwd=None: False)
    monkeypatch.setattr(sr, "git_sha", lambda cwd=None: "b" * 40)
    monkeypatch.setattr(sr, "git_branch", lambda cwd=None: "main")
    reg = SessionRegistry(sessions_tmp)
    hdr = reg.open_session(copy_kind="CLEAN", workcopy_id="omnia_df_clean_t")
    sid = hdr["session_id"]
    assert hdr["status"] == "OPEN"
    reg.assert_binding(sid, workcopy_id="omnia_df_clean_t")
    out = reg.close_session(sid, status="COMPLETED")
    assert out["header"]["status"] == "COMPLETED"
    assert out["header"]["signature_status"] == "PENDING_SIGNATURE"
    uc = out["unsigned_checkpoint"]
    assert uc["event_count"] == uc["seq"] + 1
    assert uc["domain"] == "OMNIA_DOGFOOD_CHECKPOINT_V1"
    assert reg.verify_chain(sid)["ok"] is True


def test_c7_continuity_requires_parent(sessions_tmp, monkeypatch):
    import shared.dogfood.session_registry as sr

    monkeypatch.setattr(sr, "git_dirty", lambda cwd=None: True)  # allowed for CONT
    monkeypatch.setattr(sr, "git_sha", lambda cwd=None: "c" * 40)
    monkeypatch.setattr(sr, "git_branch", lambda cwd=None: "main")
    reg = SessionRegistry(sessions_tmp)
    with pytest.raises(RegistryError, match="CONTINUITY_REQUIRES_PARENT"):
        reg.open_session(copy_kind="CONTINUITY", workcopy_id="omnia_df_cont_t")


def test_c7_seal_before_recover_partial_tail(sessions_tmp, monkeypatch):
    import shared.dogfood.session_registry as sr

    monkeypatch.setattr(sr, "git_dirty", lambda cwd=None: False)
    monkeypatch.setattr(sr, "git_sha", lambda cwd=None: "d" * 40)
    monkeypatch.setattr(sr, "git_branch", lambda cwd=None: "main")
    reg = SessionRegistry(sessions_tmp)
    hdr = reg.open_session(copy_kind="CLEAN", workcopy_id="omnia_df_clean_r")
    sid = hdr["session_id"]
    path = reg.events_path(sid)
    # append garbage without LF → partial tail
    with open(path, "ab") as f:
        f.write(b'{"broken":')
    manifest = reg.seal_and_recover_partial_tail(sid)
    assert manifest["reason"] == "PARTIAL_TAIL"
    evid = Path(manifest["recovery_id"])
    # evidence dir exists under sessions/evidence
    evid_dir = reg.root / "evidence" / sid / manifest["recovery_id"]
    assert (evid_dir / "journal.full.bin").exists()
    assert (evid_dir / "tail.partial.bin").exists()
    assert (evid_dir / "RECOVERY_MANIFEST.json").exists()
    # original full evidence preserved
    assert (evid_dir / "journal.full.bin").stat().st_size > 0
    hdr2 = reg.load_header(sid)
    assert hdr2["status"] == "INTERRUPTED"
    assert reg.verify_chain(sid)["ok"] is True


def test_c7_ed25519_pure_sign_verify_roundtrip():
    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key().public_bytes_raw()
    payload = build_unsigned_checkpoint(
        session_id="00000000-0000-4000-8000-0000000000aa",
        seq=1,
        journal_tip_hash="a" * 64,
        closed_at="2026-11-20T12:00:02.000Z",
        final_session_status="COMPLETED",
    )
    msg = checkpoint_message(payload)
    sig = sk.sign(msg)
    verify_checkpoint_signature(
        payload,
        sig.hex(),
        raw_public_key=pk,
        expected_fingerprint=fingerprint_sha256(pk),
    )
    with pytest.raises(RegistryError, match="SIGNED_INVALID|FINGERPRINT"):
        verify_checkpoint_signature(
            payload,
            sig.hex(),
            raw_public_key=pk,
            expected_fingerprint="sha256:" + ("0" * 64),
        )


def test_c7_resolve_fingerprint_flag_env_file(tmp_path, monkeypatch):
    fp_file = tmp_path / "c7_registry_verify.fingerprint"
    fp_file.write_text("sha256:" + ("a" * 64) + "\n", encoding="utf-8")
    monkeypatch.delenv("OMNIA_C7_PUBKEY_FINGERPRINT", raising=False)
    assert resolve_expected_fingerprint(fingerprint_file=fp_file).endswith("a" * 64)
    monkeypatch.setenv("OMNIA_C7_PUBKEY_FINGERPRINT", "sha256:" + ("b" * 64))
    assert resolve_expected_fingerprint(
        env_value=os.environ.get("OMNIA_C7_PUBKEY_FINGERPRINT"),
        fingerprint_file=fp_file,
    ).endswith("b" * 64)
    assert resolve_expected_fingerprint(
        explicit="sha256:" + ("c" * 64),
        env_value="sha256:" + ("b" * 64),
        fingerprint_file=fp_file,
    ).endswith("c" * 64)


def test_c7_installed_verify_pubkey_matches_fingerprint():
    """Live Founder verify material in docs/dogfood must be self-consistent."""
    from shared.dogfood.checkpoint import default_fingerprint_path, default_pubkey_path, load_raw_pubkey

    pub_path = default_pubkey_path()
    fp_path = default_fingerprint_path()
    assert pub_path.is_file(), "c7_registry_verify.pub missing"
    assert fp_path.is_file(), "c7_registry_verify.fingerprint missing"
    raw = load_raw_pubkey(pub_path)
    assert fingerprint_sha256(raw) == fp_path.read_text(encoding="utf-8").strip()
    assert resolve_expected_fingerprint(fingerprint_file=fp_path) == fingerprint_sha256(raw)


def test_c7_rewrite_api_absent(sessions_tmp, monkeypatch):
    """Registry only exposes append — no update/delete helpers."""
    reg = SessionRegistry(sessions_tmp)
    assert not hasattr(reg, "update_event")
    assert not hasattr(reg, "delete_event")


def test_c7_binding_sha_mismatch(sessions_tmp, monkeypatch):
    import shared.dogfood.session_registry as sr

    monkeypatch.setattr(sr, "git_dirty", lambda cwd=None: False)
    monkeypatch.setattr(sr, "git_sha", lambda cwd=None: "e" * 40)
    monkeypatch.setattr(sr, "git_branch", lambda cwd=None: "main")
    reg = SessionRegistry(sessions_tmp)
    hdr = reg.open_session(copy_kind="CLEAN", workcopy_id="omnia_df_clean_b")
    monkeypatch.setattr(sr, "git_sha", lambda cwd=None: "f" * 40)
    with pytest.raises(RegistryError, match="INVALID_BINDING_SHA"):
        reg.assert_binding(hdr["session_id"])


def test_c7_sessions_dir_no_double_nest(sessions_tmp):
    nested = sessions_tmp / "sessions"
    reg = SessionRegistry(sessions_dir=nested)
    assert reg.root == nested.resolve()
    assert (reg.root / "events").is_dir()
    assert not (reg.root / "sessions" / "events").exists()


def test_c7_recover_denied_when_completed(sessions_tmp, monkeypatch):
    import shared.dogfood.session_registry as sr

    monkeypatch.setattr(sr, "git_dirty", lambda cwd=None: False)
    monkeypatch.setattr(sr, "git_sha", lambda cwd=None: "d" * 40)
    monkeypatch.setattr(sr, "git_branch", lambda cwd=None: "main")
    reg = SessionRegistry(sessions_tmp)
    hdr = reg.open_session(copy_kind="CLEAN", workcopy_id="omnia_df_clean_done")
    reg.close_session(hdr["session_id"], status="COMPLETED")
    with pytest.raises(RegistryError, match="recover_denied_status:COMPLETED"):
        reg.seal_and_recover_partial_tail(hdr["session_id"])
