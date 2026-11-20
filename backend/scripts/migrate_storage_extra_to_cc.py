#!/usr/bin/env python3
"""CLI — D-175 C6 / S2 migrate agencies.storage_extra_gb → CC SoT.

Usage (from backend/, with env loaded):
  python -m scripts.migrate_storage_extra_to_cc --dry-run
  python -m scripts.migrate_storage_extra_to_cc --apply --cc-id <id>

Never use against production without Founder mandate.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys


async def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="C6 S2 storage extra migration")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", help="Write changes")
    parser.add_argument("--cc-id", default=None)
    args = parser.parse_args(argv)

    dry_run = not args.apply
    from shared.db.connection import Database
    from shared.storage.migrate_extra_to_cc import run_migration

    db = Database.get()
    report = await run_migration(db, dry_run=dry_run, cc_id=args.cc_id)
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main(sys.argv[1:])))
