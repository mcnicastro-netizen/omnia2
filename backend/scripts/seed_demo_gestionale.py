"""Seed idempotente CRM demo (D-086) — agenzia + immobili + clienti.

Safe to re-run. Stable ids so Cloud Agents have clickable gestionale data.
Does not require the API: talks to Mongo directly.
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

from apps.core.seed import (  # noqa: E402
    DEMO_ADMIN_EMAIL,
    DEMO_AGENCY_ID,
    _ensure_demo_admin,
    _ensure_demo_agency,
)

NOW = datetime.now(timezone.utc).isoformat()

PROPERTIES = [
    {
        "id": "demo-prop-roma-01",
        "title": "Trilocale luminoso a Prati",
        "description": "Appartamento ristrutturato vicino al Vaticano, doppi servizi, balcone.",
        "property_type": "appartamento",
        "operation": "sale",
        "status": "active",
        "city": "Roma",
        "province": "RM",
        "postal_code": "00192",
        "zone": "Prati",
        "address": "Via Cola di Rienzo 120",
        "price": 625000,
        "surface_sqm": 98,
        "rooms": 3,
        "bedrooms": 2,
        "bathrooms": 2,
        "floor": 3,
        "energy": {"energy_class": "C", "heating": "autonomo"},
        "features": {"balcone": True, "ascensore": True, "luminoso": True},
        "privacy_level": "L2",
        "is_listed_on_immobilcloud": True,
    },
    {
        "id": "demo-prop-milano-01",
        "title": "Bilocale Isola con terrazzo",
        "description": "Open space con terrazzo, palazzo d'epoca, vicino MM Garibaldi.",
        "property_type": "appartamento",
        "operation": "sale",
        "status": "active",
        "city": "Milano",
        "province": "MI",
        "postal_code": "20159",
        "zone": "Isola",
        "address": "Via Thaon di Revel 8",
        "price": 540000,
        "surface_sqm": 68,
        "rooms": 2,
        "bedrooms": 1,
        "bathrooms": 1,
        "floor": 4,
        "energy": {"energy_class": "B", "heating": "autonomo"},
        "features": {"terrazza": True, "ascensore": True, "aria_condizionata": True},
        "privacy_level": "L2",
        "is_listed_on_immobilcloud": True,
    },
    {
        "id": "demo-prop-catania-01",
        "title": "Villa vista Etna — San Giovanni la Punta",
        "description": "Villa indipendente con giardino e garage, zona residenziale.",
        "property_type": "villa",
        "operation": "sale",
        "status": "active",
        "city": "San Giovanni la Punta",
        "province": "CT",
        "postal_code": "95037",
        "zone": "Centro",
        "address": "Via Etnea 45",
        "price": 390000,
        "surface_sqm": 180,
        "rooms": 5,
        "bedrooms": 3,
        "bathrooms": 2,
        "energy": {"energy_class": "D", "heating": "autonomo"},
        "features": {"giardino": True, "box_auto": True, "posto_auto": True},
        "privacy_level": "L2",
        "is_listed_on_immobilcloud": True,
    },
    {
        "id": "demo-prop-roma-rent-01",
        "title": "Monolocale arredato San Lorenzo",
        "description": "Adatto a studenti, palazzo con portineria, vicino La Sapienza.",
        "property_type": "monolocale",
        "operation": "rent",
        "status": "active",
        "city": "Roma",
        "province": "RM",
        "postal_code": "00185",
        "zone": "San Lorenzo",
        "address": "Via dei Sardi 18",
        "rent_monthly": 950,
        "condo_fees": 70,
        "surface_sqm": 32,
        "rooms": 1,
        "bedrooms": 0,
        "bathrooms": 1,
        "floor": 2,
        "furnished": "arredato",
        "energy": {"energy_class": "E", "heating": "centralizzato"},
        "features": {"arredato": True, "ascensore": True},
        "privacy_level": "L2",
        "is_listed_on_immobilcloud": True,
    },
]

CLIENTS = [
    {
        "id": "demo-cli-buyer-01",
        "name": "Giulia",
        "surname": "Bianchi",
        "email": "giulia.bianchi.demo@omniaecosystem.it",
        "phone": "+39 333 1001001",
        "client_type": "buyer",
        "status": "qualified",
        "source": "Demo seed",
        "gdpr_consent": True,
        "preferences": {
            "operation": "sale",
            "property_types": ["appartamento"],
            "cities": ["Roma"],
            "price_max": 700000,
            "rooms_min": 3,
        },
    },
    {
        "id": "demo-cli-buyer-02",
        "name": "Luca",
        "surname": "Ferrari",
        "email": "luca.ferrari.demo@omniaecosystem.it",
        "phone": "+39 333 2002002",
        "client_type": "buyer",
        "status": "contacted",
        "source": "Demo seed",
        "gdpr_consent": True,
        "preferences": {
            "operation": "sale",
            "property_types": ["appartamento"],
            "cities": ["Milano"],
            "price_max": 580000,
            "rooms_min": 2,
        },
    },
    {
        "id": "demo-cli-seller-01",
        "name": "Anna",
        "surname": "Russo",
        "email": "anna.russo.demo@omniaecosystem.it",
        "phone": "+39 333 3003003",
        "client_type": "seller",
        "status": "negotiating",
        "source": "Demo seed",
        "gdpr_consent": True,
        "notes": "Proprietaria del trilocale Prati (demo-prop-roma-01).",
    },
    {
        "id": "demo-cli-tenant-01",
        "name": "Marco",
        "surname": "Conti",
        "email": "marco.conti.demo@omniaecosystem.it",
        "phone": "+39 333 4004004",
        "client_type": "tenant",
        "status": "new",
        "source": "Demo seed",
        "gdpr_consent": True,
        "preferences": {
            "operation": "rent",
            "property_types": ["monolocale", "appartamento"],
            "cities": ["Roma"],
            "price_max": 1100,
        },
    },
]


async def _upsert(col, doc: dict) -> str:
    doc = {**doc, "agency_id": DEMO_AGENCY_ID, "updated_at": NOW}
    doc.setdefault("created_at", NOW)
    existing = await col.find_one({"id": doc["id"]})
    if existing:
        await col.update_one({"id": doc["id"]}, {"$set": doc})
        return "updated"
    await col.insert_one(doc)
    return "created"


async def main() -> None:
    mongo_url = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    db_name = os.environ.get("DB_NAME", "omnia")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    await _ensure_demo_agency(db)
    await db.agencies.update_one(
        {"id": DEMO_AGENCY_ID},
        {"$set": {
            "plan": "pro",
            "plan_type": "turnkey",
            "display_name": "Agenzia Demo OMNIA",
            "name": "Agenzia Demo OMNIA",
            "is_active": True,
            "updated_at": NOW,
        }},
    )
    await _ensure_demo_admin(db)

    p_ok = c_ok = 0
    for prop in PROPERTIES:
        await _upsert(db.properties, prop)
        p_ok += 1
    for cli in CLIENTS:
        await _upsert(db.clients, cli)
        c_ok += 1

    admin = await db.users.find_one({"email": DEMO_ADMIN_EMAIL.lower()})
    print(
        f"demo seed OK agency={DEMO_AGENCY_ID} "
        f"properties={p_ok} clients={c_ok} "
        f"demo_admin={'yes' if admin else 'no'}"
    )
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
