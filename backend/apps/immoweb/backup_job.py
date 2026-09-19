"""OMNIA — Daily archive backup (D-085).

Copies Mongo key collections + local media into BACKUP_ROOT/YYYY-MM-DD
and purges folders older than BACKUP_RETENTION_DAYS (default 30).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

BACKUP_ROOT = Path(os.environ.get("BACKUP_ROOT") or "/workspace/backend/.backups")
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS") or "30")
MEDIA_ROOT = Path(os.environ.get("LOCAL_STORAGE_ROOT") or "/workspace/backend/.media")

# Collections that restore an agency archive
_COLLECTIONS = [
    "agencies",
    "users",
    "properties",
    "clients",
    "leads",
    "subscriptions",
    "credit_wallets",
    "credit_ledger",
    "api_keys",
    "groups",
    "publishing_connections",
]


async def run_daily_backup() -> Dict[str, Any]:
    from shared.db.connection import Database

    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dest = BACKUP_ROOT / day
    dest.mkdir(parents=True, exist_ok=True)
    db = Database.get()
    report: Dict[str, Any] = {
        "ok": True,
        "day": day,
        "path": str(dest),
        "collections": {},
        "media_copied": False,
        "purged": [],
    }

    for name in _COLLECTIONS:
        try:
            docs: List[dict] = await db[name].find({}, {"_id": 0}).to_list(100_000)
            out = dest / f"{name}.jsonl"
            with out.open("w", encoding="utf-8") as f:
                for doc in docs:
                    f.write(json.dumps(doc, ensure_ascii=False, default=str) + "\n")
            report["collections"][name] = len(docs)
        except Exception as e:
            logger.exception("backup collection %s failed: %s", name, e)
            report["collections"][name] = {"error": str(e)}
            report["ok"] = False

    # Media tree (local backend)
    media_dest = dest / "media"
    try:
        if MEDIA_ROOT.exists():
            if media_dest.exists():
                shutil.rmtree(media_dest)
            shutil.copytree(MEDIA_ROOT, media_dest, dirs_exist_ok=True)
            report["media_copied"] = True
            report["media_bytes"] = sum(
                p.stat().st_size for p in media_dest.rglob("*") if p.is_file()
            )
    except Exception as e:
        logger.exception("backup media failed: %s", e)
        report["media_error"] = str(e)
        report["ok"] = False

    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "retention_days": BACKUP_RETENTION_DAYS,
        "report": report,
    }
    (dest / "MANIFEST.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report["purged"] = _purge_old_backups()
    return report


def _purge_old_backups() -> List[str]:
    if not BACKUP_ROOT.exists():
        return []
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=BACKUP_RETENTION_DAYS)
    purged = []
    for child in BACKUP_ROOT.iterdir():
        if not child.is_dir():
            continue
        try:
            day = datetime.strptime(child.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        if day < cutoff:
            shutil.rmtree(child, ignore_errors=True)
            purged.append(child.name)
    return purged
