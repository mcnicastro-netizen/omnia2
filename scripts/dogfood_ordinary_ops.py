#!/usr/bin/env python3
"""D-175 C3 — Ordinary clone/wipe/restore/migrate CLI (permanent = DENY)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from shared.dogfood.ordinary_ops import (  # noqa: E402
    ordinary_clone_allowed,
    ordinary_migrate_destructive_allowed,
    ordinary_restore_allowed,
    ordinary_wipe_allowed,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("op", choices=["clone", "wipe", "restore", "migrate_destructive"])
    ap.add_argument("--uri", default="mongodb://127.0.0.1:27018/")
    ap.add_argument("--db", required=True, help="Target DB name")
    args = ap.parse_args()

    if args.op == "clone":
        r = ordinary_clone_allowed(source_uri=args.uri, target_db=args.db)
    elif args.op == "wipe":
        r = ordinary_wipe_allowed(uri=args.uri, db_name=args.db)
    elif args.op == "restore":
        r = ordinary_restore_allowed(uri=args.uri, target_db=args.db)
    else:
        r = ordinary_migrate_destructive_allowed(uri=args.uri, db_name=args.db)

    print(json.dumps(r, indent=2))
    return 0 if r.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
