"""Sprint 4 · GAP #1 · Migrazione foto Base64 → Emergent Object Storage.

Usage (dry-run):
    cd /app/backend && python -m scripts.migrate_photos_to_objstore --dry-run

Usage (apply):
    cd /app/backend && python -m scripts.migrate_photos_to_objstore

Scans `properties.photos[].url` for `data:image/...;base64,...` URIs, uploads
each to Object Storage under `omnia/properties/{prop_id}/{photo_id}.{ext}`,
and rewrites the URL in-place to `/api/media/{path}`.

Idempotent: skips photos whose URL already starts with `/api/media/`.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from shared.storage import put_object, init_storage, ObjStoreError  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("migrate_photos")

DATA_URI_RE = re.compile(r"^data:image/(?P<mime>jpeg|jpg|png|webp);base64,(?P<b64>.+)$", re.IGNORECASE)
_EXT = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "webp": "webp"}


async def main(dry_run: bool) -> int:
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    if not dry_run:
        init_storage()

    scanned = 0
    migrated = 0
    skipped = 0
    errors = 0

    cursor = db.properties.find({"photos.0": {"$exists": True}}, {"id": 1, "photos": 1})
    async for doc in cursor:
        pid = doc["id"]
        photos = list(doc.get("photos") or [])
        changed = False
        for p in photos:
            url = p.get("url") or ""
            scanned += 1
            if not url.startswith("data:"):
                skipped += 1
                continue
            m = DATA_URI_RE.match(url)
            if not m:
                skipped += 1
                continue
            mime = m.group("mime").lower()
            ext = _EXT[mime]
            try:
                data = base64.b64decode(m.group("b64"))
            except Exception as e:
                log.warning("prop=%s photo=%s decode fail: %s", pid, p.get("id"), e)
                errors += 1
                continue
            photo_id = p.get("id") or f"legacy-{migrated}"
            storage_path = f"omnia/properties/{pid}/{photo_id}.{ext}"
            if dry_run:
                log.info("[DRY] would upload prop=%s photo=%s bytes=%d → %s",
                         pid, photo_id, len(data), storage_path)
            else:
                try:
                    put_object(storage_path, data, f"image/{'jpeg' if ext == 'jpg' else ext}")
                    p["url"] = f"/api/media/{storage_path}"
                    changed = True
                    log.info("prop=%s photo=%s → %s (bytes=%d)",
                             pid, photo_id, p["url"], len(data))
                except ObjStoreError as e:
                    log.error("prop=%s photo=%s UPLOAD FAILED: %s", pid, photo_id, e)
                    errors += 1
                    continue
            migrated += 1
        if changed and not dry_run:
            await db.properties.update_one({"id": pid}, {"$set": {"photos": photos}})

    log.info(
        "DONE · scanned=%d migrated=%d skipped=%d errors=%d dry_run=%s",
        scanned, migrated, skipped, errors, dry_run,
    )
    client.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.exit(asyncio.run(main(dry_run=args.dry_run)))
