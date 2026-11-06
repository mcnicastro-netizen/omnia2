"""OMNIA — Admin + optional demo agency seeding at startup."""
import os
import logging
from datetime import datetime, timezone

from shared.db.connection import Database
from shared.auth.hashing import hash_password, verify_password
from shared.models.user import UserInDB

logger = logging.getLogger(__name__)

DEMO_AGENCY_ID = "demo-agency-001"
DEMO_ADMIN_EMAIL = "demo.admin@omniaecosystem.it"
DEMO_ADMIN_PASSWORD = os.environ.get("DEMO_ADMIN_PASSWORD", "OmniaDemo2026!")

# Live first client (Founder 06-Nov-2026) — preferred attach target for super_admin.
NICASTRO_SLUG = "nicastro-immobiliare"


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in {"1", "true", "yes", "on"}


def should_seed_demo_agency() -> bool:
    """GTM sandbox demo-agency-001.

    - Explicit ``OMNIA_SEED_DEMO_AGENCY`` wins.
    - On Railway (production API): default **off** so primo cliente reale
      non viene ricreato a ogni restart (D-145).
    - Cloud / local: default **on** for dogfood GTM.
    """
    explicit = os.environ.get("OMNIA_SEED_DEMO_AGENCY")
    if explicit is not None and explicit.strip() != "":
        return _truthy(explicit)
    on_railway = bool(
        os.environ.get("RAILWAY_ENVIRONMENT")
        or os.environ.get("RAILWAY_SERVICE_NAME")
        or os.environ.get("RAILWAY_PROJECT_ID")
    )
    return not on_railway


async def _find_preferred_agency_id(db) -> str | None:
    """Prefer Nicastro (primo cliente) over demo when attaching Founder."""
    nic = await db.agencies.find_one(
        {"slug": NICASTRO_SLUG, "is_active": {"$ne": False}},
        {"_id": 0, "id": 1},
    )
    if nic and nic.get("id"):
        return nic["id"]
    nic2 = await db.agencies.find_one(
        {"name": "Nicastro Immobiliare"},
        {"_id": 0, "id": 1},
    ) or await db.agencies.find_one(
        {"display_name": "Nicastro Immobiliare"},
        {"_id": 0, "id": 1},
    )
    if nic2 and nic2.get("id"):
        return nic2["id"]
    if should_seed_demo_agency():
        return DEMO_AGENCY_ID
    other = await db.agencies.find_one(
        {"id": {"$ne": DEMO_AGENCY_ID}, "is_active": {"$ne": False}},
        {"_id": 0, "id": 1},
    )
    return (other or {}).get("id")


async def _ensure_demo_agency(db) -> None:
    existing = await db.agencies.find_one({"id": DEMO_AGENCY_ID})
    if existing:
        return
    now = datetime.now(timezone.utc).isoformat()
    await db.agencies.insert_one({
        "id": DEMO_AGENCY_ID,
        "name": "Agenzia Demo OMNIA",
        "slug": "agenzia-demo-omnia",
        "plan_type": "turnkey",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    })
    logger.info("Demo agency created: %s", DEMO_AGENCY_ID)


async def _ensure_demo_admin(db) -> None:
    email = DEMO_ADMIN_EMAIL.lower()
    existing = await db.users.find_one({"email": email})
    now = datetime.now(timezone.utc).isoformat()
    if existing is None:
        user = UserInDB(
            email=email,
            password_hash=hash_password(DEMO_ADMIN_PASSWORD),
            name="Demo Admin",
            role="agency_admin",
            lang="it",
            agency_ids=[DEMO_AGENCY_ID],
            active_agency_id=DEMO_AGENCY_ID,
            account_type="b2b",
        )
        await db.users.insert_one(user.model_dump())
        logger.info("Demo admin created: %s", email)
        return
    # Do not resurrect an erased demo admin (password_hash !erased:)
    pw = existing.get("password_hash") or ""
    if pw.startswith("!erased:") or existing.get("is_active") is False:
        logger.info("Demo admin erased/inactive — not resurrecting: %s", email)
        return
    await db.users.update_one(
        {"email": email},
        {"$set": {
            "role": "agency_admin",
            "agency_ids": [DEMO_AGENCY_ID],
            "active_agency_id": DEMO_AGENCY_ID,
            "is_active": True,
            "updated_at": now,
        }},
    )


async def seed_admin() -> None:
    """Create or update the super_admin user from .env credentials.

    Optionally ensures demo agency + demo admin (GTM sandbox). On Railway,
    demo seed is off by default (primo cliente reale = Nicastro).
    """
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        logger.warning("ADMIN_EMAIL / ADMIN_PASSWORD not set — skipping seed")
        return

    db = Database.get()
    email = email.lower().strip()
    existing = await db.users.find_one({"email": email})
    prefer = await _find_preferred_agency_id(db)
    seed_demo = should_seed_demo_agency()

    if existing is None:
        agency_ids = [prefer] if prefer else ([DEMO_AGENCY_ID] if seed_demo else [])
        admin = UserInDB(
            email=email,
            password_hash=hash_password(password),
            name="Super Admin",
            role="super_admin",
            lang="it",
            agency_ids=agency_ids,
            active_agency_id=(agency_ids[0] if agency_ids else None),
        )
        await db.users.insert_one(admin.model_dump())
        logger.info("✅ Admin user created: %s agencies=%s", email, agency_ids)
    else:
        updates = {
            "role": "super_admin",
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if not verify_password(password, existing.get("password_hash") or ""):
            updates["password_hash"] = hash_password(password)
            logger.info("✅ Admin password updated for: %s", email)
        else:
            logger.info("Admin already exists and password matches: %s", email)

        ids = list(existing.get("agency_ids") or [])
        # Drop retired demo membership when demo seed is off and Nicastro exists
        if not seed_demo and prefer and prefer != DEMO_AGENCY_ID:
            if DEMO_AGENCY_ID in ids:
                ids = [i for i in ids if i != DEMO_AGENCY_ID]
            if prefer not in ids:
                ids.append(prefer)
            updates["agency_ids"] = ids
            updates["active_agency_id"] = prefer
            logger.info("Admin membership → preferred agency %s", prefer)
        elif not ids:
            if prefer:
                updates["agency_ids"] = [prefer]
                updates["active_agency_id"] = prefer
                logger.info("Admin attached to agency %s", prefer)
            elif seed_demo:
                updates["agency_ids"] = [DEMO_AGENCY_ID]
                updates["active_agency_id"] = DEMO_AGENCY_ID
                logger.info("Admin attached to demo agency %s", DEMO_AGENCY_ID)
        elif not existing.get("active_agency_id") or existing.get("active_agency_id") not in ids:
            if prefer and prefer in (updates.get("agency_ids") or ids):
                updates["active_agency_id"] = prefer
            elif DEMO_AGENCY_ID in ids and seed_demo:
                updates["active_agency_id"] = DEMO_AGENCY_ID
            elif ids:
                updates["active_agency_id"] = ids[0]
        await db.users.update_one({"email": email}, {"$set": updates})

    if seed_demo:
        await _ensure_demo_agency(db)
        await _ensure_demo_admin(db)
    else:
        logger.info(
            "Skipping demo agency seed (OMNIA_SEED_DEMO_AGENCY off / Railway default)"
        )
