"""QC: fail if public portal inventory is empty (P-001 / D-118).

Counts documents matching immocloud public_portal._base_filter().
Exit 0 when match_base_filter > 0, else exit 1.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env", override=True)

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from apps.immocloud.public_portal import _base_filter  # noqa: E402


async def main() -> int:
    mongo_url = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
    db_name = os.environ.get("DB_NAME", "omnia")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    flt = _base_filter()
    n = await db.properties.count_documents(flt)
    sample = await db.properties.find(flt, {"_id": 0, "id": 1, "visibility": 1, "city": 1}).limit(5).to_list(5)
    client.close()
    print(f"match_base_filter={n} sample_ids={[s.get('id') for s in sample]}")
    if n <= 0:
        print("FAIL: public portal inventory empty (P-001)", file=sys.stderr)
        return 1
    print("OK: public portal has listable inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
