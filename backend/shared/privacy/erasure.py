"""OMNIA — GDPR erasure (right to be forgotten) for the authenticated user."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from shared.db.connection import Database

logger = logging.getLogger("omnia.privacy.erasure")


async def erase_user_data(user: dict) -> Dict[str, Any]:
    """Anonymize the user and delete personal satellite data.

    Agency / property inventory owned by the agency is kept (business records),
    but the person's PII on the user document is wiped and sessions revoked.
    B2C private listings owned by the user are withdrawn and PII stripped.
    """
    db = Database.get()
    uid = user["id"]
    email = (user.get("email") or "").lower()
    now = datetime.now(timezone.utc).isoformat()
    tombstone = f"deleted-{uuid4().hex[:12]}@erased.omnia.local"
    report: Dict[str, Any] = {"user_id": uid, "deleted": {}}

    # Personal collections
    for coll, flt in (
        ("favorites", {"user_id": uid}),
        ("saved_searches", {"user_id": uid}),
        ("notifications", {"user_id": uid}),
        ("password_reset_tokens", {"user_id": uid}),
        ("refresh_tokens", {"user_id": uid}),
    ):
        try:
            r = await db[coll].delete_many(flt)
            report["deleted"][coll] = r.deleted_count
        except Exception as e:
            logger.warning("erasure %s failed: %s", coll, e)
            report["deleted"][coll] = f"error:{e}"

    # Visura / mortgage leads tied to email or user
    for coll, flt in (
        ("mortgage_leads", {"email": email}),
        ("visura_orders", {"user_id": uid}),
        ("cloud_contact_leads", {"email": email}),
        ("contact_leads", {"email": email}),
    ):
        try:
            r = await db[coll].delete_many(flt)
            report["deleted"][coll] = r.deleted_count
        except Exception as e:
            logger.warning("erasure optional %s: %s", coll, e)

    # B2C private listings: withdraw + strip owner PII
    try:
        r = await db.properties.update_many(
            {"owner_user_id": uid},
            {
                "$set": {
                    "status": "withdrawn",
                    "owner": {},
                    "contact_email": None,
                    "contact_phone": None,
                    "updated_at": now,
                    "erased_at": now,
                }
            },
        )
        report["deleted"]["properties_withdrawn"] = r.modified_count
    except Exception as e:
        logger.warning("erasure properties: %s", e)

    # Also match listings created by this user id field variants
    try:
        r = await db.properties.update_many(
            {"created_by": uid, "listing_source": {"$in": ["b2c", "private", "cloud"]}},
            {"$set": {"status": "withdrawn", "updated_at": now, "erased_at": now}},
        )
        report["deleted"]["properties_created_by"] = r.modified_count
    except Exception:
        pass

    # API keys created by this user (personal) — revoke
    try:
        r = await db.api_keys.update_many(
            {"created_by": uid},
            {"$set": {"revoked": True, "revoked_at": now}},
        )
        report["deleted"]["api_keys_revoked"] = r.modified_count
    except Exception:
        pass

    # Anonymize user document (keep id for FK integrity / audit)
    await db.users.update_one(
        {"id": uid},
        {
            "$set": {
                "email": tombstone,
                "name": "Utente eliminato",
                "phone": None,
                "password_hash": f"!erased:{uuid4().hex}",
                "is_active": False,
                "mfa_enabled": False,
                "mfa_secret_enc": None,
                "mfa_backup_hashes": [],
                "mfa_pending_secret_enc": None,
                "avatar_url": None,
                "google_sub": None,
                "auth_providers": [],
                "agency_ids": [],
                "active_agency_id": None,
                "group_id": None,
                "notification_channels": [],
                "intents": [],
                "erased_at": now,
                "updated_at": now,
            },
            "$unset": {
                "signup_existing_domain": "",
            },
        },
    )
    report["status"] = "erased"
    report["erased_at"] = now
    logger.info("GDPR erasure completed user=%s report=%s", uid, report)
    return report
