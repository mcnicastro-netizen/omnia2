"""OMNIA — Daily archive backup (D-085 · D-105 · O0 design).

Copies Mongo key collections + local media into BACKUP_ROOT/YYYY-MM-DD
and purges folders older than BACKUP_RETENTION_DAYS (default 30 as-is;
target hot ≤7g in O0 design — change via env when migrating).

Status in MANIFEST: OK | PARTIAL | FAILED (D-105).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BACKUP_ROOT = Path(os.environ.get("BACKUP_ROOT") or "/workspace/backend/.backups")
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS") or "30")
MEDIA_ROOT = Path(os.environ.get("LOCAL_STORAGE_ROOT") or "/workspace/backend/.media")

# Collections that restore an agency archive + portale B2C (P-046)
_COLLECTIONS = [
    "agencies",
    "users",
    "properties",
    "clients",
    "client_requests",
    "activities",
    "leads",
    "subscriptions",
    "credit_wallets",
    "credit_ledger",
    "api_keys",
    "groups",
    "publishing_connections",
    # Portale B2C / privacy / UGC (P-046)
    "b2c_purchases",
    "b2c_visura_orders",
    "consent_events",
    "favorites",
    "saved_searches",
    "al_legal_audit",
    "listing_inquiries",
]


def _status_from_report(report: Dict[str, Any]) -> str:
    """D-105 — OK / PARTIAL / FAILED."""
    coll_errors = [
        k for k, v in (report.get("collections") or {}).items()
        if isinstance(v, dict) and v.get("error")
    ]
    media_err = bool(report.get("media_error"))
    media_ok = bool(report.get("media_copied")) or not MEDIA_ROOT.exists()
    if not coll_errors and not media_err and media_ok and report.get("ok"):
        return "OK"
    if coll_errors and len(coll_errors) >= len(_COLLECTIONS):
        return "FAILED"
    if coll_errors or media_err or not report.get("ok"):
        return "PARTIAL"
    return "OK"


def read_latest_backup_health() -> Dict[str, Any]:
    """Read newest MANIFEST.json under BACKUP_ROOT for Founder Ops (D-105)."""
    if not BACKUP_ROOT.exists():
        return {
            "status": "MISSING",
            "day": None,
            "created_at": None,
            "path": str(BACKUP_ROOT),
            "message": "Nessuna cartella backup",
        }
    days = sorted(
        (
            p for p in BACKUP_ROOT.iterdir()
            if p.is_dir() and (p / "MANIFEST.json").exists()
        ),
        key=lambda p: p.name,
        reverse=True,
    )
    if not days:
        return {
            "status": "MISSING",
            "day": None,
            "created_at": None,
            "path": str(BACKUP_ROOT),
            "message": "Nessun MANIFEST.json",
        }
    latest = days[0]
    try:
        meta = json.loads((latest / "MANIFEST.json").read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {
            "status": "FAILED",
            "day": latest.name,
            "created_at": None,
            "path": str(latest),
            "message": f"MANIFEST illeggibile: {e}",
        }
    report = meta.get("report") or {}
    status = meta.get("status") or _status_from_report(report)
    return {
        "status": status,
        "day": report.get("day") or latest.name,
        "created_at": meta.get("created_at"),
        "path": str(latest),
        "media_copied": report.get("media_copied"),
        "collections": report.get("collections"),
        "retention_days": meta.get("retention_days") or BACKUP_RETENTION_DAYS,
        "message": None if status == "OK" else f"Ultimo bak {status}",
    }


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

    status = _status_from_report(report)
    report["status"] = status
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "retention_days": BACKUP_RETENTION_DAYS,
        "status": status,
        "report": report,
    }
    (dest / "MANIFEST.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report["purged"] = _purge_old_backups()

    # D-105 — alert Founder Ops when bak not OK
    if status != "OK":
        try:
            from shared.ops_alerts import record_alert
            await record_alert(
                kind="backup",
                severity="error" if status == "FAILED" else "warning",
                message=f"Backup giornaliero {status} ({day})",
                meta={"day": day, "status": status, "path": str(dest)},
            )
        except Exception:  # noqa: BLE001
            logger.exception("backup ops_alert failed")

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
