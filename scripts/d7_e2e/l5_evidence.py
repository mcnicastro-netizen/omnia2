"""L5 evidence template — local preparation only (no remote I/O, no email send).

Future staging mandate will fill this structure with real timestamps, health
attestations, and provider read-only exports. This module never calls Resend,
Railway, or staging HTTP.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_l5_evidence_skeleton(
    *,
    run_id: str,
    run_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Create an empty L5 evidence document ready for staging fill-in."""
    evidence = {
        "level": "L5",
        "status": "NOT_EXECUTED",
        "run_id": run_id,
        "window": {"t0_utc": None, "t1_utc": None},
        "code_sha": None,
        "b8_attest": {
            "instances": [],  # [{instance_id, held, flag_killed, error}]
            "replica_count_declared": None,
            "post_restart": False,
            "ok": None,
        },
        "application": {
            "gate_mode": None,
            "invite_or_probe_status": None,
            "log_kill_line_present": None,
        },
        "transport": {
            "invoked": None,  # must be False for PASS
            "note": "Staging cannot spy transport; use logs + provider",
        },
        "provider": {
            "source": None,  # dashboard|api_list
            "delivery_count_in_window": None,
            "correlated": None,
        },
        "pass_criteria": [
            "b8_attest.ok is True for all declared replicas",
            "application shows killed/blocked",
            "provider.delivery_count_in_window == 0",
            "timestamps correlate with run window",
        ],
        "prepared_at": _now(),
        "executed_at": None,
    }
    if run_path is not None:
        p = Path(run_path) / "email_send_evidence_l5.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        evidence["path"] = str(p)
    return evidence
