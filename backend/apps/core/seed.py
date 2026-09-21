"""OMNIA — Admin + demo agency seeding at startup."""
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

    Also ensures demo agency + demo admin exist, and attaches the Founder
    super_admin to the demo agency when they have no agency yet (needed for
    billing/properties smoke and founder Ops).
    """
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        logger.warning("ADMIN_EMAIL / ADMIN_PASSWORD not set — skipping seed")
        return

    db = Database.get()
    email = email.lower().strip()
    existing = await db.users.find_one({"email": email})

    if existing is None:
        admin = UserInDB(
            email=email,
            password_hash=hash_password(password),
            name="Super Admin",
            role="super_admin",
            lang="it",
            agency_ids=[DEMO_AGENCY_ID],
            active_agency_id=DEMO_AGENCY_ID,
        )
        await db.users.insert_one(admin.model_dump())
        logger.info("✅ Admin user created: %s", email)
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
        # Attach demo agency if Founder has none (billing/CRM require agency_id)
        if not (existing.get("agency_ids") or []):
            updates["agency_ids"] = [DEMO_AGENCY_ID]
            updates["active_agency_id"] = DEMO_AGENCY_ID
            logger.info("Admin attached to demo agency %s", DEMO_AGENCY_ID)
        await db.users.update_one({"email": email}, {"$set": updates})

    await _ensure_demo_agency(db)
    await _ensure_demo_admin(db)
