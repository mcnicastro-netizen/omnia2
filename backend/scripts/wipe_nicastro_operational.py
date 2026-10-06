"""Svuota i dati operativi demo di Nicastroimmobiliare (cliente-1).

 Tiene: agenzia, titolare, brand/tema, API key / widget, wallet crediti.
 Cancella: immobili, clienti, richieste e satelliti con agency_id.
 Imposta dogfood_skip_fixtures=true così seed_nicastro_agency.py
 NON reinserisce i 4 immobili CT / 3 clienti al prossimo boot.

 SOLO nicastro-agency-001. Non tocca demo-agency-001.
"""
from __future__ import annotations

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

NICASTRO_AGENCY_ID = "nicastro-agency-001"
NOW = datetime.now(timezone.utc).isoformat()

# Identità / integrazioni da NON cancellare
KEEP_COLLECTIONS = {
    "agencies",
    "users",
    "api_keys",
    "api_credit_ledger",
    "credit_transactions",
    "subscriptions",
    "publishing_catalog",
    "mls_network",
    "hal_knowledge_chunks",
    "hal_knowledge_meta",
    "hal_knowledge_sessions",
}


async def wipe(db) -> dict:
    agency = await db.agencies.find_one({"id": NICASTRO_AGENCY_ID})
    if not agency:
        raise SystemExit(f"agency {NICASTRO_AGENCY_ID} not found — abort")

    report: dict = {"agency_id": NICASTRO_AGENCY_ID, "deleted": {}, "kept": {}}
    names = await db.list_collection_names()

    for name in sorted(names):
        if name in KEEP_COLLECTIONS:
            kept = await db[name].count_documents({"agency_id": NICASTRO_AGENCY_ID})
            if name == "agencies":
                kept = 1
            if name == "users":
                kept = await db.users.count_documents({"agency_ids": NICASTRO_AGENCY_ID})
            report["kept"][name] = kept
            continue
        n = await db[name].count_documents({"agency_id": NICASTRO_AGENCY_ID})
        if n:
            res = await db[name].delete_many({"agency_id": NICASTRO_AGENCY_ID})
            report["deleted"][name] = res.deleted_count

    # Flag: seed identity-only da ora in poi
    await db.agencies.update_one(
        {"id": NICASTRO_AGENCY_ID},
        {
            "$set": {
                "dogfood_skip_fixtures": True,
                "dogfood_cleared_at": NOW,
                "updated_at": NOW,
            }
        },
    )
    report["dogfood_skip_fixtures"] = True
    report["cleared_at"] = NOW
    return report


async def main() -> None:
    mongo_url = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    db_name = os.environ.get("DB_NAME", "omnia")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    report = await wipe(db)
    props = await db.properties.count_documents({"agency_id": NICASTRO_AGENCY_ID})
    clients = await db.clients.count_documents({"agency_id": NICASTRO_AGENCY_ID})
    reqs = await db.client_requests.count_documents({"agency_id": NICASTRO_AGENCY_ID})
    demo_props = await db.properties.count_documents({"agency_id": "demo-agency-001"})
    print(
        f"nicastro wipe OK deleted={report['deleted']} "
        f"left properties={props} clients={clients} requests={reqs} "
        f"skip_fixtures=true demo-agency-001 properties untouched={demo_props}"
    )
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
