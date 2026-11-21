#!/usr/bin/env python3
"""CLI entrypoint for D7 T3/T4 harness.

Execution requires Founder authorization (package C) AND --confirm-staging-run.

Examples (DO NOT run without authorization):
  PYTHONPATH=. python -m scripts.d7_e2e precheck --confirm-staging-run
  PYTHONPATH=. python -m scripts.d7_e2e run --confirm-staging-run

This module was created under D-175 A+B authorization: implement only, do not execute.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__, config
from .artifacts import (
    append_console,
    new_run_id,
    run_dir,
    write_checksums,
    write_json,
    write_manifest,
)
from .classify import aggregate
from .precheck import run_precheck
from .seed import cleanup_run, seed
from .t3 import run_t3
from .t4 import run_t4


def _require_confirm(args: argparse.Namespace) -> None:
    if not getattr(args, "confirm_staging_run", False):
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "missing_--confirm-staging-run",
                    "message": (
                        "Mutative/staging harness requires Founder package C authorization "
                        "and the explicit --confirm-staging-run flag."
                    ),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)


def cmd_precheck(args: argparse.Namespace) -> int:
    _require_confirm(args)
    out = run_precheck()
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("classification") == "PASS" else 1


def cmd_run(args: argparse.Namespace) -> int:
    _require_confirm(args)
    run_id = args.run_id or new_run_id()
    path = run_dir(run_id, create=True)
    append_console(path, f"run_start harness={__version__} run_id={run_id}")

    pre = run_precheck()
    write_json(path / "precheck.json", pre)
    if pre.get("classification") != "PASS":
        write_manifest(
            path,
            {
                "run_id": run_id,
                "phase": "precheck",
                "classification": pre.get("classification"),
                "staging_api": config.STAGING_API_URL,
                "staging_fe": config.STAGING_FE_URL,
                "db": config.STAGING_DB_NAME,
                "historical_a6_not_sot": config.FORENSIC_A6_NOT_SOT,
            },
        )
        write_checksums(path)
        append_console(path, f"stop_precheck classification={pre.get('classification')}")
        print(json.dumps({"run_id": run_id, "stopped": "precheck", "precheck": pre}, indent=2))
        return 1

    meta = seed(run_id, path)
    secrets = json.loads((path / "secrets" / "fixtures_secrets.json").read_text())
    password = secrets["password"]

    t3 = run_t3(run_id, path, meta, password)
    t4 = run_t4(run_id, path, meta, password)

    overall = aggregate(
        [{"result": t3["classification"]}, {"result": t4["classification"]}]
    )
    # Remap: aggregate expects step dicts with PASS/FAIL/BLOCKED
    results = [t3["classification"], t4["classification"]]
    if "FAIL" in results:
        overall = "FAIL"
    elif "BLOCKED" in results:
        overall = "BLOCKED"
    elif results == ["PASS", "PASS"]:
        overall = "PASS"
    else:
        overall = "FAIL"

    write_manifest(
        path,
        {
            "run_id": run_id,
            "phase": "complete",
            "t3": t3["classification"],
            "t4": t4["classification"],
            "overall": overall,
            "staging_api": config.STAGING_API_URL,
            "staging_fe": config.STAGING_FE_URL,
            "db": config.STAGING_DB_NAME,
            "pin": config.AUTHORIZED_FE_PIN,
            "historical_a6_not_sot": config.FORENSIC_A6_NOT_SOT,
            "cleanup_done": False,
        },
    )
    if args.cleanup_after:
        counts = cleanup_run(run_id)
        write_json(path / "cleanup.json", counts)
        append_console(path, f"cleanup {counts}")

    write_checksums(path)
    append_console(path, f"run_end overall={overall}")
    print(
        json.dumps(
            {
                "run_id": run_id,
                "artifact_dir": str(path),
                "t3": t3["classification"],
                "t4": t4["classification"],
                "overall": overall,
            },
            indent=2,
        )
    )
    return 0 if overall == "PASS" else 1


def cmd_cleanup(args: argparse.Namespace) -> int:
    _require_confirm(args)
    if not args.run_id or len(args.run_id) < 12:
        print(json.dumps({"ok": False, "error": "run_id_required"}, indent=2), file=sys.stderr)
        return 2
    counts = cleanup_run(args.run_id)
    print(json.dumps({"run_id": args.run_id, "deleted": counts}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m scripts.d7_e2e")
    p.add_argument("--version", action="version", version=f"d7_e2e {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_confirm(sp):
        sp.add_argument(
            "--confirm-staging-run",
            action="store_true",
            help="Required. Affirms Founder-authorized staging execution.",
        )

    sp = sub.add_parser("precheck", help="Isolation gates only")
    add_confirm(sp)
    sp.set_defaults(func=cmd_precheck)

    sp = sub.add_parser("run", help="precheck + seed + T3 + T4")
    add_confirm(sp)
    sp.add_argument("--run-id", default="", help="Optional fixed run id (must be unique)")
    sp.add_argument(
        "--cleanup-after",
        action="store_true",
        help="Delete only docs with this run_id after tests",
    )
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("cleanup", help="Scoped cleanup by run_id only")
    add_confirm(sp)
    sp.add_argument("--run-id", required=True)
    sp.set_defaults(func=cmd_cleanup)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
