#!/usr/bin/env python3
"""Provisioning assistito piano + crediti (O6: self-serve OFF).

Uso tipico dopo onboarding nuova agenzia in dogfood:
  cd backend && .venv/bin/python scripts/grant_agency_plan.py \\
      --agency-id <id> --tier pro --credits 2000

Oppure per email titolare / slug:
  .venv/bin/python scripts/grant_agency_plan.py --email nuova@agenzia.it --tier pro
  .venv/bin/python scripts/grant_agency_plan.py --slug nicastroimmobiliare --tier pro

Non stampa segreti. Non tocca Stripe.
Preferire in prod: POST /api/app/ops/grant-agency-plan (super_admin).
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

from apps.immoweb.assisted_billing import grant_assisted_plan, resolve_agency  # noqa: E402


async def main() -> int:
    p = argparse.ArgumentParser(description="Grant plan + credits (assisted)")
    p.add_argument("--agency-id", default="")
    p.add_argument("--slug", default="")
    p.add_argument("--email", default="", help="Email titolare → active_agency_id")
    p.add_argument("--tier", default="pro", choices=["starter", "pro", "agency"])
    p.add_argument("--credits", type=int, default=2000)
    p.add_argument("--note", default="cli_assisted_grant")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    uri = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    dbn = os.environ.get("DB_NAME", "omnia")
    client = AsyncIOMotorClient(uri)
    db = client[dbn]

    resolved = await resolve_agency(
        db,
        agency_id=args.agency_id or None,
        slug=args.slug or None,
        email=args.email or None,
    )
    if not resolved.get("ok"):
        print(f"ERROR {resolved}")
        return 1

    agency = resolved["agency"]
    print(
        f"agency={agency.get('display_name') or agency.get('name')} "
        f"slug={agency.get('slug')} id={resolved['agency_id']} "
        f"→ tier={args.tier} credits+={args.credits}"
    )
    if args.dry_run:
        print("dry-run: no write")
        return 0

    out = await grant_assisted_plan(
        db,
        resolved["agency_id"],
        tier=args.tier,  # type: ignore[arg-type]
        credits=args.credits,
        reason=args.note,
        granted_by="cli",
    )
    if not out.get("ok"):
        print(f"ERROR {out}")
        return 1
    print(
        f"OK plan_tier={out.get('plan_tier')} wallet_balance={out.get('credits_balance')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
