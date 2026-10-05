"""Seed idempotente agenzia Nicastroimmobiliare (cliente-1 dogfood).

Crea agenzia ufficiale + titolare agency_admin (NON demo-agency-001).
Brand assistito da palette/logo del sito reale (A-037 non chiude ancora URL→demo).
Safe to re-run. Non richiede API: parla a Mongo direttamente.
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

from shared.auth.hashing import hash_password  # noqa: E402

NOW = datetime.now(timezone.utc).isoformat()

NICASTRO_AGENCY_ID = "nicastro-agency-001"
NICASTRO_SLUG = "nicastroimmobiliare"
NICASTRO_ADMIN_EMAIL = os.environ.get(
    "NICASTRO_ADMIN_EMAIL", "titolare@nicastroimmobiliare.it"
).lower()
NICASTRO_ADMIN_PASSWORD = os.environ.get(
    "NICASTRO_ADMIN_PASSWORD", "NicastroDemo2026!"
)
NICASTRO_ADMIN_USER_ID = "nicastro-admin-001"

# Palette assistita da https://www.nicastroimmobiliare.it/ (crawl 2026-10-05)
PRIMARY = "#BC4F08"
ACCENT = "#3DB04B"
LOGO_URL = "https://media.agestaweb.it/siti/02427/public/foto/logo.jpg"
SITE_URL = "https://www.nicastroimmobiliare.it/"

PROPERTIES = [
    {
        "id": "nicastro-prop-ct-01",
        "title": "Trilocale luminoso — Centro Catania",
        "description": (
            "Appartamento ristrutturato nel cuore di Catania, doppi servizi, "
            "balcone su via pedonale. Ideale per famiglia o investimento."
        ),
        "property_type": "appartamento",
        "operation": "sale",
        "status": "active",
        "city": "Catania",
        "province": "CT",
        "postal_code": "95131",
        "zone": "Centro",
        "address": "Via Etnea 210",
        "price": 285000,
        "surface_sqm": 95,
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
        "id": "nicastro-prop-ct-02",
        "title": "Villa indipendente — San Giovanni la Punta",
        "description": (
            "Villa con giardino e garage, zona residenziale silenziosa, "
            "vista Etna. Quattro camere, due bagni, cucina abitabile."
        ),
        "property_type": "villa",
        "operation": "sale",
        "status": "active",
        "city": "San Giovanni la Punta",
        "province": "CT",
        "postal_code": "95037",
        "zone": "Centro",
        "address": "Via Roma 18",
        "price": 420000,
        "surface_sqm": 180,
        "rooms": 5,
        "bedrooms": 4,
        "bathrooms": 2,
        "energy": {"energy_class": "D", "heating": "autonomo"},
        "features": {"giardino": True, "box_auto": True, "posto_auto": True},
        "privacy_level": "L2",
        "is_listed_on_immobilcloud": True,
    },
    {
        "id": "nicastro-prop-ct-03",
        "title": "Bilocale arredato — Cibali",
        "description": (
            "Appartamento pronto all'uso, vicino allo stadio e ai mezzi. "
            "Adatto a studenti o giovani coppie."
        ),
        "property_type": "appartamento",
        "operation": "rent",
        "status": "active",
        "city": "Catania",
        "province": "CT",
        "postal_code": "95123",
        "zone": "Cibali",
        "address": "Via Gabriele D'Annunzio 44",
        "rent_monthly": 650,
        "condo_fees": 50,
        "surface_sqm": 55,
        "rooms": 2,
        "bedrooms": 1,
        "bathrooms": 1,
        "floor": 2,
        "furnished": "arredato",
        "energy": {"energy_class": "E", "heating": "autonomo"},
        "features": {"arredato": True, "ascensore": True},
        "privacy_level": "L2",
        "is_listed_on_immobilcloud": True,
    },
    {
        "id": "nicastro-prop-ct-04",
        "title": "Attico panoramico — Ognina",
        "description": (
            "Attico con terrazzo abitabile e vista mare. "
            "Finiture di pregio, posto auto condominiale."
        ),
        "property_type": "attico",
        "operation": "sale",
        "status": "active",
        "city": "Catania",
        "province": "CT",
        "postal_code": "95126",
        "zone": "Ognina",
        "address": "Via Messina 120",
        "price": 510000,
        "surface_sqm": 120,
        "rooms": 4,
        "bedrooms": 2,
        "bathrooms": 2,
        "floor": 6,
        "energy": {"energy_class": "B", "heating": "autonomo"},
        "features": {"terrazza": True, "ascensore": True, "posto_auto": True, "vista_mare": True},
        "privacy_level": "L2",
        "is_listed_on_immobilcloud": True,
    },
]

CLIENTS = [
    {
        "id": "nicastro-cli-buyer-01",
        "name": "Sara",
        "surname": "Puglisi",
        "email": "sara.puglisi.demo@omniaecosystem.it",
        "phone": "+39 340 1112233",
        "client_type": "buyer",
        "status": "qualified",
        "source": "Nicastro demo seed",
        "gdpr_consent": True,
        "preferences": {
            "operation": "sale",
            "property_types": ["appartamento"],
            "cities": ["Catania"],
            "price_max": 320000,
            "rooms_min": 3,
        },
    },
    {
        "id": "nicastro-cli-seller-01",
        "name": "Giuseppe",
        "surname": "Romano",
        "email": "giuseppe.romano.demo@omniaecosystem.it",
        "phone": "+39 340 4455667",
        "client_type": "seller",
        "status": "negotiating",
        "source": "Nicastro demo seed",
        "gdpr_consent": True,
        "notes": "Proprietario villa San Giovanni la Punta.",
    },
    {
        "id": "nicastro-cli-tenant-01",
        "name": "Elena",
        "surname": "Costa",
        "email": "elena.costa.demo@omniaecosystem.it",
        "phone": "+39 340 7788990",
        "client_type": "tenant",
        "status": "new",
        "source": "Nicastro demo seed",
        "gdpr_consent": True,
        "preferences": {
            "operation": "rent",
            "property_types": ["appartamento", "bilocale"],
            "cities": ["Catania"],
            "price_max": 700,
        },
    },
]


async def _ensure_agency(db) -> None:
    existing = await db.agencies.find_one({"id": NICASTRO_AGENCY_ID})
    agency_doc = {
        "id": NICASTRO_AGENCY_ID,
        "slug": NICASTRO_SLUG,
        "display_name": "Nicastroimmobiliare",
        "name": "Nicastroimmobiliare",
        "fiscal": {
            "legal_name": "Nicastro Immobiliare di M.M.C. Nicastro",
            "vat_number": None,
            "fiscal_code": None,
        },
        "address": {
            "street": None,
            "city": "Catania",
            "province": "CT",
            "postal_code": None,
            "country": "IT",
        },
        "contact": {
            "email": NICASTRO_ADMIN_EMAIL,
            "phone": None,
            "website": SITE_URL,
        },
        "branding": {
            "logo_url": LOGO_URL,
            "primary_color": PRIMARY,
            "accent_color": ACCENT,
            "tagline": "La tua casa in Sicilia",
        },
        "website": {
            "mode": "omnia_template",
            "external_url": SITE_URL,
            "template_id": "classic",
            "custom_domain": "www.nicastroimmobiliare.it",
            "custom_domain_status": None,
            "extracted_profile": {
                "source_url": SITE_URL,
                "palette": {
                    "primary": PRIMARY,
                    "accent": ACCENT,
                    "neutral_dark": "#2B2B2B",
                    "neutral_light": "#F4F4F4",
                },
                "voice": {"tone": "professionale", "tagline_guess": "La tua casa in Sicilia"},
                "logo_hint": {"url": LOGO_URL, "alt": "Nicastroimmobiliare"},
                "confidence": 70,
                "assisted": True,
                "note": "A-037: estrazione assistita (crawl CSS), non auto-clone sito",
            },
            "theme_config": {
                "theme_id": "classic",
                "palette": {
                    "primary": PRIMARY,
                    "accent": ACCENT,
                    "neutral_dark": "#2B2B2B",
                    "neutral_light": "#F4F4F4",
                },
                "logo_url": LOGO_URL,
                "tagline": "La tua casa in Sicilia",
            },
        },
        "plan": "pro",
        "plan_type": "turnkey",
        "owner_id": NICASTRO_ADMIN_USER_ID,
        "is_active": True,
        "onboarding_completed": True,
        "domain_sovereignty_confirmed": True,
        "domain_sovereignty_confirmed_at": NOW,
        "existing_domain": "nicastroimmobiliare.it",
        "updated_at": NOW,
    }
    if existing:
        await db.agencies.update_one({"id": NICASTRO_AGENCY_ID}, {"$set": agency_doc})
    else:
        agency_doc["created_at"] = NOW
        await db.agencies.insert_one(agency_doc)


async def _ensure_admin(db) -> None:
    existing = await db.users.find_one({"email": NICASTRO_ADMIN_EMAIL})
    user_doc = {
        "id": NICASTRO_ADMIN_USER_ID,
        "email": NICASTRO_ADMIN_EMAIL,
        "password_hash": hash_password(NICASTRO_ADMIN_PASSWORD),
        "name": "Marco Nicastro",
        "role": "agency_admin",
        "lang": "it",
        "agency_ids": [NICASTRO_AGENCY_ID],
        "active_agency_id": NICASTRO_AGENCY_ID,
        "account_type": "b2b",
        "is_active": True,
        "updated_at": NOW,
    }
    if existing:
        # Preserve id if already set differently; keep stable password refresh
        updates = {
            "password_hash": hash_password(NICASTRO_ADMIN_PASSWORD),
            "name": "Marco Nicastro",
            "role": "agency_admin",
            "agency_ids": [NICASTRO_AGENCY_ID],
            "active_agency_id": NICASTRO_AGENCY_ID,
            "is_active": True,
            "account_type": "b2b",
            "updated_at": NOW,
        }
        await db.users.update_one({"email": NICASTRO_ADMIN_EMAIL}, {"$set": updates})
    else:
        user_doc["created_at"] = NOW
        await db.users.insert_one(user_doc)


async def _upsert(col, doc: dict) -> None:
    doc = {**doc, "agency_id": NICASTRO_AGENCY_ID, "updated_at": NOW}
    doc.setdefault("created_at", NOW)
    existing = await col.find_one({"id": doc["id"]})
    if existing:
        await col.update_one({"id": doc["id"]}, {"$set": doc})
    else:
        await col.insert_one(doc)


def _want_fixtures(argv: list[str]) -> bool:
    if "--with-fixtures" in argv:
        return True
    if "--identity-only" in argv:
        return False
    flag = (os.environ.get("NICASTRO_SKIP_FIXTURES") or "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return False
    return True  # default: seed demo listings unless agency flag says otherwise


async def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    mongo_url = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    db_name = os.environ.get("DB_NAME", "omnia")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    await _ensure_agency(db)
    await _ensure_admin(db)

    agency = await db.agencies.find_one(
        {"id": NICASTRO_AGENCY_ID},
        {"_id": 0, "slug": 1, "display_name": 1, "dogfood_skip_fixtures": 1},
    )
    force_fixtures = "--with-fixtures" in argv
    skip_by_env = not _want_fixtures(argv) and not force_fixtures
    skip_by_agency = bool(agency.get("dogfood_skip_fixtures")) and not force_fixtures
    seeded_fixtures = 0
    if skip_by_env or skip_by_agency:
        print(
            f"nicastro seed identity-only (skip fixtures) "
            f"agency_flag={bool(agency.get('dogfood_skip_fixtures'))} "
            f"env_skip={skip_by_env}"
        )
    else:
        for prop in PROPERTIES:
            await _upsert(db.properties, prop)
        for cli in CLIENTS:
            await _upsert(db.clients, cli)
        seeded_fixtures = len(PROPERTIES)

    admin = await db.users.find_one({"email": NICASTRO_ADMIN_EMAIL}, {"_id": 0, "email": 1, "role": 1})
    n_props = await db.properties.count_documents({"agency_id": NICASTRO_AGENCY_ID})
    n_cli = await db.clients.count_documents({"agency_id": NICASTRO_AGENCY_ID})
    print(
        f"nicastro seed OK agency={NICASTRO_AGENCY_ID} slug={agency.get('slug')} "
        f"properties={n_props} clients={n_cli} fixtures_written={seeded_fixtures} "
        f"admin={admin.get('email')} role={admin.get('role')}"
    )
    print(f"LOGIN email={NICASTRO_ADMIN_EMAIL} password={NICASTRO_ADMIN_PASSWORD}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
