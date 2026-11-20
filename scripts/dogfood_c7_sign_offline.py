#!/usr/bin/env python3
"""D-175 C7 — Offline Founder signer (Ed25519 pure).

Run ONLY where the private key lives (Founder machine / offline vault).
Never place the private key under the Dogfood repo or dogfood/secrets.

Usage:
  backend/.venv/bin/python scripts/dogfood_c7_sign_offline.py \\
    --private-key /secure/path/c7_founder.priv \\
    --unsigned dogfood/sessions/unsigned_checkpoints/<id>.json \\
    --out /tmp/checkpoint.sig
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

from shared.dogfood.checkpoint import checkpoint_message  # noqa: E402
from shared.dogfood.session_registry import RegistryError  # noqa: E402


def load_raw_private_key(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) == 32:
        return data
    text = data.decode("utf-8")
    # allow comment lines
    hex_line = ""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        hex_line = s.replace(" ", "")
        break
    if len(hex_line) == 64 and all(c in "0123456789abcdefABCDEF" for c in hex_line):
        return bytes.fromhex(hex_line)
    raise RegistryError("private_key_format_unrecognized")


def main() -> int:
    ap = argparse.ArgumentParser(description="OMNIA C7 offline checkpoint signer")
    ap.add_argument("--private-key", required=True, type=Path)
    ap.add_argument("--unsigned", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    seed = load_raw_private_key(args.private_key)
    if len(seed) != 32:
        raise SystemExit("private_key_must_be_32_bytes")
    payload = json.loads(args.unsigned.read_text(encoding="utf-8"))
    msg = checkpoint_message(payload)
    sig = Ed25519PrivateKey.from_private_bytes(seed).sign(msg)
    args.out.write_text(sig.hex() + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "sig_path": str(args.out), "sig_len": len(sig)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
