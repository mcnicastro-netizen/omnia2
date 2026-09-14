"""OMNIA — Admin user seeding at startup."""
import os
import logging
from datetime import datetime, timezone

from shared.db.connection import Database
from shared.auth.hashing import hash_password, verify_password
from shared.models.user import UserInDB

logger = logging.getLogger(__name__)


async def seed_admin() -> None:
    """Create or update the super_admin user from .env credentials."""
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
        )
        await db.users.insert_one(admin.model_dump())
        logger.info("✅ Admin user created: %s", email)
        return

    if not verify_password(password, existing["password_hash"]):
        await db.users.update_one(
            {"email": email},
            {"$set": {
                "password_hash": hash_password(password),
                "role": "super_admin",
                "is_active": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        logger.info("✅ Admin password updated for: %s", email)
    else:
        logger.info("Admin already exists and password matches: %s", email)
