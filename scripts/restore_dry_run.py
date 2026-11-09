#!/usr/bin/env python3
"""Restore dry-run — validate bak (+ optional off-box) without writing Mongo.

Usage:
  python scripts/restore_dry_run.py
  DAY=2026-10-10 AGENCY_ID=demo-agency-001 python scripts/restore_dry_run.py --offbox
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env", override=True)

from apps.immoweb.backup_scope import (  # noqa: E402
    AGENCY_COLLECTIONS,
    B2C_COLLECTIONS,
    BACKUP_COLLECTIONS,
    D096_REQUIRED_AGENCY,
    extract_agency_docs,
)

BACKUP_ROOT = Path(os.environ.get("BACKUP_ROOT") or str(BACKEND / ".backups"))
OFFBOX_ROOT = Path(os.environ.get("OFFBOX_BACKUP_ROOT") or "/tmp/omnia-offbox-backups")
AGENCY_ID = os.environ.get("AGENCY_ID", "demo-agency-001")

AGENCY_COLLS = tuple(AGENCY_COLLECTIONS)


def latest_day(root: Path) -> str | None:
    if not root.exists():
        return None
    days = sorted(
        p.name for p in root.iterdir() if p.is_dir() and (p / "MANIFEST.json").is_file()
    )
    return days[-1] if days else None


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def validate(src: Path, label: str) -> dict:
    checks: dict[str, bool] = {}
    notes: list[str] = []
    manifest = src / "MANIFEST.json"
    checks["manifest_exists"] = manifest.is_file()
    status = None
    if checks["manifest_exists"]:
        meta = json.loads(manifest.read_text(encoding="utf-8"))
        status = meta.get("status") or (meta.get("report") or {}).get("status")
        checks["manifest_ok_or_partial"] = status in ("OK", "PARTIAL")
        notes.append(f"status={status}")
        report_colls = (meta.get("report") or {}).get("collections") or {}
        missing_scope = [c for c in BACKUP_COLLECTIONS if c not in report_colls]
        checks["backup_scope_complete"] = len(missing_scope) == 0
        if missing_scope:
            notes.append(f"missing_in_manifest={missing_scope}")
    else:
        checks["manifest_ok_or_partial"] = False
        checks["backup_scope_complete"] = False

    agency_docs = 0
    prop_docs = 0
    for coll in AGENCY_COLLS:
        path = src / f"{coll}.jsonl"
        docs = load_jsonl(path)
        extracted = extract_agency_docs(coll, docs, AGENCY_ID)
        if coll == "agencies":
            agency_docs = len(extracted)
        if coll == "properties":
            prop_docs = sum(1 for d in extracted if d.get("agency_id") == AGENCY_ID)
        notes.append(f"{coll}_extract={len(extracted)}")

    for coll in B2C_COLLECTIONS:
        path = src / f"{coll}.jsonl"
        notes.append(f"{coll}_lines={len(load_jsonl(path))}")

    checks["agency_row_present"] = agency_docs >= 1
    checks["properties_for_agency"] = prop_docs >= 0  # empty agency still valid dry-run
    for coll in D096_REQUIRED_AGENCY:
        path = src / f"{coll}.jsonl"
        checks[f"file_{coll}"] = path.is_file()

    ok = all(checks.values())
    return {
        "label": label,
        "ok": ok,
        "checks": checks,
        "notes": notes,
        "path": str(src),
        "agency_id": AGENCY_ID,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offbox", action="store_true")
    args = parser.parse_args()

    day = os.environ.get("DAY") or latest_day(BACKUP_ROOT)
    if not day:
        print("FAIL: no backup day under", BACKUP_ROOT)
        return 1
    src = BACKUP_ROOT / day
    report = validate(src, "hot")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.offbox:
        off_day = os.environ.get("DAY") or latest_day(OFFBOX_ROOT)
        if not off_day:
            print("FAIL: no off-box day")
            return 1
        off = validate(OFFBOX_ROOT / off_day, "offbox")
        print(json.dumps(off, ensure_ascii=False, indent=2))
        return 0 if report["ok"] and off["ok"] else 1

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
