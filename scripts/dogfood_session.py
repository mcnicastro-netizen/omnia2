#!/usr/bin/env python3
"""D-175 C7 — Session registry CLI (open / bind / close / verify / attach-sig).

Does not generate Founder private keys. attach-sig only verifies + stores signature.
Prefer: backend/.venv/bin/python scripts/dogfood_session.py ...
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from shared.dogfood.jcanonical import CanonicalError  # noqa: E402
from shared.dogfood.checkpoint import (  # noqa: E402
    attach_signature,
    default_fingerprint_path,
    default_pubkey_path,
    fingerprint_sha256,
    load_raw_pubkey,
    resolve_expected_fingerprint,
)
from shared.dogfood.permanent import dogfood_root  # noqa: E402
from shared.dogfood.session_registry import (  # noqa: E402
    RegistryError,
    SessionRegistry,
)


def _reg() -> SessionRegistry:
    override = (os.environ.get("OMNIA_DOGFOOD_SESSIONS_ROOT") or "").strip()
    if override:
        # Path is the sessions tree itself (…/dogfood/sessions), not dogfood root.
        return SessionRegistry(sessions_dir=Path(override))
    return SessionRegistry(dogfood_root())


def _repo_cwd(args: argparse.Namespace) -> Path:
    raw = getattr(args, "repo_cwd", None) or os.environ.get("OMNIA_DOGFOOD_REPO_CWD")
    return Path(raw).resolve() if raw else ROOT


def cmd_open(args: argparse.Namespace) -> int:
    reg = _reg()
    hdr = reg.open_session(
        copy_kind=args.kind,
        workcopy_id=args.workcopy,
        parent_session_id=args.parent,
        catalog_version=args.catalog_version,
        executor=args.executor,
        repo_cwd=_repo_cwd(args),
        source_permanent_db=args.permanent_db,
    )
    print(json.dumps(hdr, indent=2))
    return 0


def cmd_bind(args: argparse.Namespace) -> int:
    reg = _reg()
    reg.assert_binding(
        args.session_id, repo_cwd=_repo_cwd(args), workcopy_id=args.workcopy
    )
    print(json.dumps({"ok": True, "session_id": args.session_id}))
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    reg = _reg()
    out = reg.close_session(
        args.session_id, status=args.status, actor=args.executor
    )
    print(json.dumps(out, indent=2, default=str))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    reg = _reg()
    r = reg.verify_chain(args.session_id)
    print(json.dumps(r, indent=2))
    return 0


def cmd_recover(args: argparse.Namespace) -> int:
    reg = _reg()
    m = reg.seal_and_recover_partial_tail(args.session_id)
    print(json.dumps(m, indent=2))
    return 0


def cmd_attach_sig(args: argparse.Namespace) -> int:
    reg = _reg()
    uc = (
        reg.root
        / "unsigned_checkpoints"
        / f"{args.checkpoint_id}.json"
    )
    if not uc.exists():
        raise RegistryError("unsigned_checkpoint_missing")
    payload = json.loads(uc.read_text(encoding="utf-8"))
    # Bind signature to the journal PREFIX attested by the checkpoint.
    # Tip may legitimately advance after unsigned (CHECKPOINT_UNSIGNED / SESSION_CLOSE).
    reg.verify_chain(payload["session_id"])
    events = reg.load_events(payload["session_id"])
    seq = int(payload.get("seq", -1))
    if seq < 0 or seq >= len(events):
        raise RegistryError("checkpoint_seq_out_of_range")
    if events[seq]["event_hash"] != payload.get("journal_tip_hash"):
        raise RegistryError("checkpoint_tip_hash_mismatch")
    if events[seq]["session_id"] != payload.get("session_id"):
        raise RegistryError("checkpoint_session_mismatch")
    if int(payload.get("event_count", -1)) != seq + 1:
        raise RegistryError("checkpoint_event_count_invalid")
    allowed_after = {
        "CHECKPOINT_UNSIGNED",
        "SESSION_CLOSE",
        "CHECKPOINT_SIGNED_ATTACHED",
        "SIGNATURE_STATUS",
    }
    for ev in events[seq + 1 :]:
        if ev["type"] not in allowed_after:
            raise RegistryError(f"journal_diverged_after_checkpoint:{ev['type']}")
    pub_path = Path(args.pubkey) if args.pubkey else default_pubkey_path()
    raw = load_raw_pubkey(pub_path)
    fp_file = (
        Path(args.fingerprint_file)
        if getattr(args, "fingerprint_file", None)
        else pub_path.with_suffix(".fingerprint")
    )
    fp = resolve_expected_fingerprint(
        explicit=args.fingerprint,
        env_value=os.environ.get("OMNIA_C7_PUBKEY_FINGERPRINT"),
        fingerprint_file=fp_file if fp_file.is_file() else default_fingerprint_path(),
    )
    sig_hex = Path(args.signature).read_text(encoding="utf-8").strip()
    out = attach_signature(
        reg.root,
        payload,
        sig_hex,
        raw_public_key=raw,
        expected_fingerprint=fp,
    )
    reg.append_event(
        payload["session_id"],
        type="CHECKPOINT_SIGNED_ATTACHED",
        actor="founder",
        payload={"checkpoint_id": args.checkpoint_id, "sig_path": str(out)},
    )
    hdr = reg.load_header(payload["session_id"])
    if hdr:
        hdr["signature_status"] = "SIGNED_VERIFIED"
        reg.save_header(hdr)
        reg.append_event(
            payload["session_id"],
            type="SIGNATURE_STATUS",
            actor="founder",
            payload={"to": "SIGNED_VERIFIED"},
        )
    print(json.dumps({"ok": True, "sig_path": str(out), "fingerprint": fingerprint_sha256(raw)}))
    return 0


def cmd_fingerprint(args: argparse.Namespace) -> int:
    raw = load_raw_pubkey(Path(args.pubkey))
    print(fingerprint_sha256(raw))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="D-175 C7 dogfood session registry")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("open")
    p.add_argument("--kind", choices=["CLEAN", "CONTINUITY", "clean", "continuity"], required=True)
    p.add_argument("--workcopy", required=True, help="omnia_df_clean_* or omnia_df_cont_*")
    p.add_argument("--parent", default=None)
    p.add_argument("--catalog-version", default="df-catalog-2026.11.1")
    p.add_argument("--executor", default="founder")
    p.add_argument("--permanent-db", default="omnia_df_perm_main")
    p.add_argument("--repo-cwd", default=None, help="git repo for SHA/branch/dirty checks")
    p.set_defaults(func=cmd_open)

    p = sub.add_parser("bind")
    p.add_argument("--session-id", required=True)
    p.add_argument("--workcopy", default=None)
    p.add_argument("--repo-cwd", default=None)
    p.set_defaults(func=cmd_bind)

    p = sub.add_parser("close")
    p.add_argument("--session-id", required=True)
    p.add_argument(
        "--status",
        default="COMPLETED",
        choices=["COMPLETED", "INTERRUPTED", "ABORTED", "INVALID"],
    )
    p.add_argument("--executor", default="founder")
    p.set_defaults(func=cmd_close)

    p = sub.add_parser("verify")
    p.add_argument("--session-id", required=True)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("recover-partial")
    p.add_argument("--session-id", required=True)
    p.set_defaults(func=cmd_recover)

    p = sub.add_parser("attach-sig")
    p.add_argument("--checkpoint-id", required=True)
    p.add_argument("--signature", required=True, help="path to .sig hex file")
    p.add_argument("--pubkey", default=None)
    p.add_argument("--fingerprint", default=None)
    p.add_argument(
        "--fingerprint-file",
        default=None,
        help="default: <pubkey>.fingerprint or docs/dogfood/c7_registry_verify.fingerprint",
    )
    p.set_defaults(func=cmd_attach_sig)

    p = sub.add_parser("fingerprint")
    p.add_argument("--pubkey", required=True)
    p.set_defaults(func=cmd_fingerprint)

    args = ap.parse_args()
    if getattr(args, "kind", None):
        args.kind = args.kind.upper()
    try:
        return args.func(args)
    except (RegistryError, CanonicalError) as e:
        print(f"FAIL {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
