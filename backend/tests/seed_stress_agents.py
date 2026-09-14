"""Seed 4 test agents directly in MongoDB for stress test M2.
Idempotent: safe to re-run.
"""
import os
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
import sys
sys.path.insert(0, "/app/backend")

from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient
from shared.auth.hashing import hash_password

AGENCY_ID = "abc7004b-04a3-414b-8197-8e0e983d0892"
PASSWORD = os.environ["OMNIA_STRESS_PASSWORD"]
EMAILS = [f"agent{i}@omniatest.re" for i in range(1, 5)]


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    pw_hash = hash_password(PASSWORD)
    now = datetime.now(timezone.utc).isoformat()

    for email in EMAILS:
        existing = await db.users.find_one({"email": email})
        if existing:
            await db.users.update_one(
                {"email": email},
                {"$set": {
                    "password_hash": pw_hash,
                    "role": "agent",
                    "agency_ids": [AGENCY_ID],
                    "is_active": True,
                    "updated_at": now,
                }},
            )
            print(f"UPDATED {email} (id={existing['id']})")
        else:
            doc = {
                "id": str(uuid4()),
                "email": email,
                "password_hash": pw_hash,
                "name": email.split("@")[0].capitalize(),
                "role": "agent",
                "lang": "it",
                "agency_ids": [AGENCY_ID],
                "is_active": True,
                "account_type": "b2b",
                "intents": [],
                "notification_channels": ["email"],
                "email_verified": True,
                "group_id": None,
                "created_at": now,
                "updated_at": now,
            }
            await db.users.insert_one(doc)
            print(f"CREATED {email} (id={doc['id']})")

    # Clear login_attempts to avoid brute-force lockouts from any prior test noise
    res = await db.login_attempts.delete_many({})
    print(f"Cleared login_attempts: {res.deleted_count}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
