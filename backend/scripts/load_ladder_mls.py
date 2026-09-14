#!/usr/bin/env python3
"""OMNIA load ladder — seed MLS agencies at 10/50/500/1000/5000/10000 and time public search.

Usage (from backend/ with venv + Mongo up):
  python scripts/load_ladder_mls.py --tier 10
  python scripts/load_ladder_mls.py --tier 50
  python scripts/load_ladder_mls.py --all

Designed for ≥10k agency target (D-072). Does not require HTTP auth: calls seed helpers in-process.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

TIERS = [10, 50, 500, 1000, 5000, 10000]


async def run_tier(n: int, props: int, province: str) -> dict:
    from shared.db.connection import Database
    from apps.immoweb.mls import seed_mls_network, SeedBody, ensure_mls_indexes, public_network_search

    Database.connect()
    db = Database.get()
    await ensure_mls_indexes(db)
    user = {
        "id": "ladder-super",
        "role": "super_admin",
        "agency_ids": ["seed-caller"],
        "active_agency_id": "seed-caller",
    }
    if not await db.agencies.find_one({"id": "seed-caller"}):
        await db.agencies.insert_one(
            {"id": "seed-caller", "name": "Caller", "slug": "caller", "mls_enabled": True, "_seed": True}
        )

    t0 = time.perf_counter()
    # Cap properties_per_agency for huge tiers to keep runtime sane
    ppa = props if n <= 1000 else max(1, min(props, 2))
    seed = await seed_mls_network(
        SeedBody(agencies=min(n, 1000), properties_per_agency=ppa, province_sigla=province),
        user,
    )
    # For tiers >1000 seed endpoint caps at 1000 per call — loop batches
    created = seed["created_agencies"]
    if n > 1000:
        remaining = n - 1000
        batch = 1000
        base = 1000
        while remaining > 0:
            take = min(batch, remaining)
            # unique ids via province suffix shift using fake province codes is hard;
            # use multiple seed calls with different province for extra volume
            prov = "RM" if remaining % 2 else "MI"
            extra = await seed_mls_network(
                SeedBody(agencies=take, properties_per_agency=ppa, province_sigla=prov),
                user,
            )
            created += extra["created_agencies"]
            remaining -= take
            base += take
    t_seed = time.perf_counter() - t0

    t1 = time.perf_counter()
    result = await public_network_search(province=province, limit=24, skip=0)
    t_search = time.perf_counter() - t1

    total_ag = await db.agencies.count_documents({"mls_enabled": True})
    total_listings = await db.properties.count_documents(
        {"visibility": {"$in": ["public", "mls_only"]}, "status": {"$ne": "deleted"}}
    )
    return {
        "tier_requested": n,
        "seed_created_agencies": created,
        "seed_seconds": round(t_seed, 3),
        "search_seconds": round(t_search, 3),
        "search_total": result.get("total"),
        "db_mls_agencies": total_ag,
        "db_shared_listings": total_listings,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, choices=TIERS, help="Single ladder step")
    ap.add_argument("--all", action="store_true", help="Run all tiers sequentially (heavy)")
    ap.add_argument("--props", type=int, default=3, help="Properties per agency")
    ap.add_argument("--province", default="CT")
    args = ap.parse_args()
    tiers = TIERS if args.all else [args.tier or 10]
    for n in tiers:
        print(f"=== LADDER {n} ===")
        out = asyncio.run(run_tier(n, args.props, args.province))
        print(out)


if __name__ == "__main__":
    main()
