"""Elimina demo-agency-001 (GTM sandbox) e satelliti.

 Uso:
   cd backend && .venv/bin/python scripts/wipe_demo_agency.py \\
       --attach-slug nicastro-immobiliare --grant-pro --credits 500
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env", override=True)

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from apps.immoweb.demo_retire import (  # noqa: E402
    DEMO_AGENCY_ID,
    retire_demo_and_promote_first_client,
    wipe_demo_agency,
)


async def main() -> int:
    p = argparse.ArgumentParser(description="Wipe demo-agency-001")
    p.add_argument("--attach-slug", default="", help="Attach Founder to this agency slug")
    p.add_argument("--grant-pro", action="store_true")
    p.add_argument("--credits", type=int, default=500)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    uri = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    dbn = os.environ.get("DB_NAME", "omnia")
    client = AsyncIOMotorClient(uri)
    db = client[dbn]

    exists = await db.agencies.find_one({"id": DEMO_AGENCY_ID})
    print(f"demo_agency_present={bool(exists)}")
    if args.dry_run:
        n_props = await db.properties.count_documents({"agency_id": DEMO_AGENCY_ID})
        print(f"dry-run properties={n_props} — no write")
        client.close()
        return 0

    if args.attach_slug:
        report = await retire_demo_and_promote_first_client(
            db,
            attach_slug=args.attach_slug.strip(),
            grant_pro=args.grant_pro,
            credits=args.credits,
        )
        print(f"OK {report}")
        client.close()
        return 0 if (report.get("attach") or {}).get("ok") else 1

    report = await wipe_demo_agency(db)
    print(f"wipe_demo OK {report}")
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
