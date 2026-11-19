#!/usr/bin/env python3
"""D-175 C3 — Sealed emergency restore for the permanent Dogfood base.

NOT callable from ordinary runtime / clone / wipe / stack scripts.
C3 mandate: prove gates without performing destructive restore unless Founder
issues a further specific authorization.

Usage (prove gates only — default for C3):
  OMNIA_PERMANENT_UNLOCK=1 \\
  OMNIA_PERMANENT_AUTH_PHRASE='OMNIA FOUNDATION UNLOCK PERMANENT BASE' \\
  OMNIA_PERMANENT_CONFIRM_1=CONFIRM-PERMANENT-EMERGENCY \\
  OMNIA_PERMANENT_CONFIRM_2=CONFIRM-PERMANENT-EMERGENCY \\
  python3 scripts/dogfood_permanent_emergency_restore.py --prove-gates

Full restore requires --execute-restore AND all gates AND
OMNIA_PERMANENT_EXECUTE=1 — still refused in C3 unless Founder authorizes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from shared.dogfood.permanent import (  # noqa: E402
    append_emergency_audit,
    check_emergency_unlock_gates,
    emergency_audit_path,
    require_identity_or_raise,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Permanent base emergency restore (sealed)")
    ap.add_argument(
        "--prove-gates",
        action="store_true",
        help="Validate unlock/phrase/double-confirm and exit without restore",
    )
    ap.add_argument(
        "--execute-restore",
        action="store_true",
        help="Attempt destructive restore (requires OMNIA_PERMANENT_EXECUTE=1)",
    )
    args = ap.parse_args()

    # Refuse accidental invocation without explicit mode
    if not args.prove_gates and not args.execute_restore:
        append_emergency_audit(
            {"event": "invoke_denied", "reason": "mode_missing", "result": "DENY"}
        )
        print("DENY: specify --prove-gates or --execute-restore", file=sys.stderr)
        return 2

    gates = check_emergency_unlock_gates()
    if not gates["ok"]:
        append_emergency_audit(
            {
                "event": "gates_failed",
                "errors": gates["errors"],
                "result": "DENY",
                "mode": "prove" if args.prove_gates else "execute",
            }
        )
        print(json.dumps({"ok": False, "result": "DENY", "errors": gates["errors"]}, indent=2))
        return 2

    # Identity must be demonstrable
    try:
        identity = require_identity_or_raise()
    except RuntimeError as e:
        append_emergency_audit(
            {"event": "identity_missing", "error": str(e), "result": "DENY"}
        )
        print(json.dumps({"ok": False, "result": "DENY", "error": str(e)}, indent=2))
        return 2

    if args.prove_gates:
        append_emergency_audit(
            {
                "event": "prove_gates_ok",
                "instance_id": identity.get("instance_id"),
                "result": "PASS",
                "destructive": False,
            }
        )
        out = {
            "ok": True,
            "result": "PASS",
            "mode": "prove_gates",
            "destructive": False,
            "instance_id": identity.get("instance_id"),
            "audit": str(emergency_audit_path()),
            "note": "No restore performed",
        }
        print(json.dumps(out, indent=2))
        return 0

    # execute-restore path — C3 default refuse even with gates
    execute_flag = (os.environ.get("OMNIA_PERMANENT_EXECUTE") or "").strip() == "1"
    if not execute_flag:
        append_emergency_audit(
            {
                "event": "execute_refused_missing_flag",
                "instance_id": identity.get("instance_id"),
                "result": "DENY",
            }
        )
        print(
            json.dumps(
                {
                    "ok": False,
                    "result": "DENY",
                    "error": "execute_requires_OMNIA_PERMANENT_EXECUTE=1",
                    "note": "C3 forbids real destructive restore without further Founder auth",
                },
                indent=2,
            )
        )
        return 2

    append_emergency_audit(
        {
            "event": "execute_blocked_c3_policy",
            "instance_id": identity.get("instance_id"),
            "result": "DENY",
            "note": "Destructive restore implementation deferred; C3 proves gates only",
        }
    )
    print(
        json.dumps(
            {
                "ok": False,
                "result": "DENY",
                "error": "destructive_restore_not_authorized_in_c3",
            },
            indent=2,
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
