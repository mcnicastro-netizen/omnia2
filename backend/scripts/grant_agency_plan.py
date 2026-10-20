#!/usr/bin/env python3
"""Provisioning assistito piano + crediti (O6: self-serve OFF).

Uso tipico dopo onboarding nuova agenzia in dogfood:
  cd backend && .venv/bin/python scripts/grant_agency_plan.py \\
      --agency-id <id> --tier starter --credits 500

Oppure per email titolare:
  .venv/bin/python scripts/grant_agency_plan.py --email nuova@agenzia.it --tier starter

Non stampa segreti. Non tocca Stripe.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env", override=True)

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from apps.billing.plans import get_plan  # noqa: E402

NOW = datetime.now(timezone.utc).isoformat()


async def main() -> int:
    p = argparse.ArgumentParser(description="Grant plan + credits (assisted)")
    p.add_argument("--agency-id", default="")
    p.add_argument("--email", default="", help="Email titolare → active_agency_id")
    p.add_argument("--tier", default="starter", choices=["starter", "pro", "agency"])
    p.add_argument("--credits", type=int, default=500)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    uri = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    dbn = os.environ.get("DB_NAME", "omnia")
    client = AsyncIOMotorClient(uri)
    db = client[dbn]

    agency_id = args.agency_id.strip()
    if not agency_id and args.email:
        user = await db.users.find_one({"email": args.email.strip().lower()})
        if not user:
            print(f"ERROR user_not_found email={args.email}")
            return 1
        agency_id = user.get("active_agency_id") or ((user.get("agency_ids") or [None])[0])
        if not agency_id:
            print("ERROR user_has_no_agency — completa onboarding prima")
            return 1
        print(f"user={user.get('email')} agency_id={agency_id}")

    if not agency_id:
        print("ERROR need --agency-id or --email")
        return 1

    agency = await db.agencies.find_one({"id": agency_id})
    if not agency:
        print(f"ERROR agency_not_found id={agency_id}")
        return 1

    plan = get_plan(args.tier)  # type: ignore[arg-type]
    if not plan:
        print(f"ERROR unknown_tier={args.tier}")
        return 1

    print(
        f"agency={agency.get('display_name') or agency.get('name')} "
        f"slug={agency.get('slug')} → tier={args.tier} credits+={args.credits}"
    )
    if args.dry_run:
        print("dry-run: no write")
        return 0

    await db.agencies.update_one(
        {"id": agency_id},
        {
            "$set": {
                "plan": args.tier if args.tier != "agency" else "agency",
                "plan_type": agency.get("plan_type") or "hybrid",
                "updated_at": NOW,
                "billing_assisted_at": NOW,
                "billing_assisted_tier": args.tier,
            }
        },
    )

    # Subscription mirror (billing UI)
    await db.subscriptions.update_one(
        {"agency_id": agency_id},
        {
            "$set": {
                "agency_id": agency_id,
                "plan_tier": args.tier,
                "status": "active",
                "billing_cycle": "monthly",
                "source": "assisted_provisioning",
                "updated_at": NOW,
                "activated_at": NOW,
            },
            "$setOnInsert": {"created_at": NOW},
        },
        upsert=True,
    )

    wallet = await db.credit_wallets.find_one_and_update(
        {"agency_id": agency_id},
        {
            "$inc": {"balance": max(0, args.credits)},
            "$set": {"updated_at": NOW, "last_topup_at": NOW},
            "$setOnInsert": {"agency_id": agency_id, "created_at": NOW},
        },
        upsert=True,
        return_document=True,
    )
    bal = (wallet or {}).get("balance")
    await db.credit_transactions.insert_one(
        {
            "agency_id": agency_id,
            "kind": "assisted_topup",
            "credits": args.credits,
            "balance_after": bal,
            "reason": f"assisted_grant_{args.tier}",
            "created_at": NOW,
            "ref_type": "grant_agency_plan",
        }
    )
    print(f"OK plan={args.tier} wallet_balance={bal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
