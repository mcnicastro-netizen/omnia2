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

BACKUP_ROOT = Path(os.environ.get("BACKUP_ROOT") or str(BACKEND / ".backups"))
OFFBOX_ROOT = Path(os.environ.get("OFFBOX_BACKUP_ROOT") or "/tmp/omnia-offbox-backups")
AGENCY_ID = os.environ.get("AGENCY_ID", "demo-agency-001")

AGENCY_COLLS = (
    "agencies",
    "users",
    "properties",
    "clients",
    "client_requests",
    "activities",
    "leads",
    "subscriptions",
    "credit_wallets",
    "publishing_connections",
)


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
    else:
        checks["manifest_ok_or_partial"] = False

    agency_docs = 0
    prop_docs = 0
    for coll in AGENCY_COLLS:
        path = src / f"{coll}.jsonl"
        exists = path.is_file()
        checks[f"coll_{coll}"] = exists
        if not exists:
            continue
        docs = load_jsonl(path)
        if coll == "agencies":
            agency_docs = sum(1 for d in docs if d.get("id") == AGENCY_ID)
        if coll == "properties":
            prop_docs = sum(1 for d in docs if d.get("agency_id") == AGENCY_ID)

    checks["agency_present"] = agency_docs >= 1
    checks["properties_ge_1"] = prop_docs >= 1
    media = src / "media"
    checks["media_dir"] = media.is_dir()
    notes.append(f"agency_docs={agency_docs} props={prop_docs} label={label}")
    failed = [k for k, v in checks.items() if not v]
    return {
        "label": label,
        "src": str(src),
        "status": status,
        "checks": checks,
        "failed": failed,
        "ok": not failed,
        "notes": notes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offbox", action="store_true", help="also validate OFFBOX copy")
    ap.add_argument("--day", default=os.environ.get("DAY") or "")
    args = ap.parse_args()

    day = args.day or latest_day(BACKUP_ROOT)
    if not day:
        print("FAIL no backup day under", BACKUP_ROOT)
        return 1
    hot = validate(BACKUP_ROOT / day, "hot")
    print(json.dumps(hot, ensure_ascii=False, indent=2))
    results = [hot]
    if args.offbox:
        ob_day = args.day or latest_day(OFFBOX_ROOT) or day
        off = validate(OFFBOX_ROOT / ob_day, "offbox")
        print(json.dumps(off, ensure_ascii=False, indent=2))
        results.append(off)
    ok = all(r["ok"] for r in results)
    print(f"ESITO={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
