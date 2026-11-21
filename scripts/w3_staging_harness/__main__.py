"""CLI entry: python -m scripts.w3_staging_harness [--mode local|staging]."""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Allow `python -m scripts.w3_staging_harness` from repo root
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.w3_staging_harness.config import HarnessConfig  # noqa: E402
from scripts.w3_staging_harness.preflight import run_preflight  # noqa: E402


ENTRY_CRITERIA = [
    {
        "id": "EC-1",
        "text": "Local W3 + D-175 regression green (unit/FakeDB + HTTP Mongo)",
        "local_check": "pytest W3 suites",
    },
    {
        "id": "EC-2",
        "text": "No locally reproducible W3 vulnerability left open without documented external blocker",
        "local_check": "OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md",
    },
    {
        "id": "EC-3",
        "text": "Staging env expectations documented (URLs, Mongo, JWT, replicas, Stripe test, Resend)",
        "local_check": "scripts/w3_staging_harness/config.py EXPECTATIONS",
    },
    {
        "id": "EC-4",
        "text": "Harness preflight includes session revocation (access+refresh)",
        "local_check": "preflight.check_session_revocation_local",
    },
    {
        "id": "EC-5",
        "text": "Synthetic data prefix + cleanup-only-tagged-docs policy",
        "local_check": "w3stg-<run_id>",
    },
    {
        "id": "EC-6",
        "text": "Remote-only items listed separately (replicas, L5, T22, B8 multi-replica)",
        "local_check": "report § staging-only",
    },
    {
        "id": "EC-7",
        "text": "B14 immediate access JWT invalidation proven multi-process locally",
        "local_check": "test_w3_multiprocess_local.py",
    },
]


def build_report(cfg: HarnessConfig, preflight: dict) -> dict:
    return {
        "harness_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": cfg.run_id,
        "mode": cfg.mode,
        "preflight": preflight,
        "entry_criteria": ENTRY_CRITERIA,
        "scenarios_planned": [
            "dual_cc_isolation",
            "branch_admin_wallet_deny",
            "cc_spoof_deny",
            "membership_revoke",
            "deal_mls_outsider",
            "document_chat_outsider",
            "video_private_deny",
            "session_revocation_access_jwt",
            "session_revocation_refresh",
            "session_across_local_processes",
        ],
        "staging_only_verifications": [
            "Railway multi-replica instance_id diversity",
            "B8 provider kill across replicas",
            "L5 Resend evidence",
            "T22 Mongo staging procedure",
            "Stripe webhook end-to-end test mode",
            "Vercel↔Railway CORS/cookie domain",
        ],
        "verdict": preflight.get("verdict", "BLOCKED"),
        "verdict_notes": {
            "PASS": "local checks including B14 session revocation succeeded",
            "FAIL": "one or more local checks failed",
            "BLOCKED": "requires staging opt-in or remote-only dependency",
        },
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="OMNIA W3 Staging Harness")
    p.add_argument("--mode", choices=["local", "staging"], default="local")
    p.add_argument(
        "--json-out",
        default="",
        help="Write full report JSON to path",
    )
    args = p.parse_args(argv)
    cfg = HarnessConfig(mode=args.mode, run_id=f"w3stg-{uuid.uuid4().hex[:10]}")
    preflight = run_preflight(cfg)
    report = build_report(cfg, preflight)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    out = args.json_out
    if not out:
        art = Path("/opt/cursor/artifacts")
        if art.is_dir():
            out = str(art / f"w3_staging_harness_{cfg.mode}_{cfg.run_id}.json")
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"\n# wrote {out}", file=sys.stderr)
    # Local cycle must never silently claim staging PASS
    if cfg.mode == "staging" and not cfg.allow_staging:
        return 2
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
