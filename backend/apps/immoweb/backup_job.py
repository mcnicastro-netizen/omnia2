"""OMNIA — Daily archive backup (D-085 · D-105 · D-114 / O0 · S2).

Copies Mongo key collections + local media into BACKUP_ROOT/YYYY-MM-DD
and purges folders older than BACKUP_RETENTION_DAYS (default **7** — O0 hot).

Media: incremental hardlink from previous day when possible (O0 preferenza),
else full copy. Unchanged files share inodes → disco ≈ live + delta, not ×N.

Status in MANIFEST: OK | PARTIAL | FAILED (D-105).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BACKUP_ROOT = Path(os.environ.get("BACKUP_ROOT") or "/workspace/backend/.backups")
# O0 / S2: hot retention ≤7g (was 30 as-is ≈32×). Override via env if needed.
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS") or "7")
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
        "media_mode": report.get("media_mode"),
        "collections": report.get("collections"),
        "retention_days": meta.get("retention_days") or BACKUP_RETENTION_DAYS,
        "message": None if status == "OK" else f"Ultimo bak {status}",
    }


def _previous_backup_media(current_day: str) -> Optional[Path]:
    """Newest day-dir before current_day that has a media/ tree."""
    if not BACKUP_ROOT.exists():
        return None
    candidates = sorted(
        (
            p for p in BACKUP_ROOT.iterdir()
            if p.is_dir()
            and p.name != current_day
            and (p / "media").is_dir()
            and len(p.name) == 10
        ),
        key=lambda p: p.name,
        reverse=True,
    )
    for p in candidates:
        if p.name < current_day:
            return p / "media"
    return None


def _same_file(a: Path, b: Path) -> bool:
    """Unchanged if size + mtime_ns match (rsync-like; no full checksum V1)."""
    try:
        sa, sb = a.stat(), b.stat()
    except OSError:
        return False
    if sa.st_size != sb.st_size:
        return False
    ma = getattr(sa, "st_mtime_ns", int(sa.st_mtime * 1_000_000_000))
    mb = getattr(sb, "st_mtime_ns", int(sb.st_mtime * 1_000_000_000))
    return ma == mb


def _hardlink_or_copy(src: Path, dest: Path, prev: Optional[Path]) -> str:
    """Prefer hardlink from prev snapshot if unchanged; else copy from src."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    if prev is not None and prev.is_file() and _same_file(src, prev):
        try:
            os.link(prev, dest)
            return "hardlink"
        except OSError:
            pass
    shutil.copy2(src, dest)
    return "copy"


def _sync_media_incremental(src_root: Path, dest_root: Path, prev_root: Optional[Path]) -> Dict[str, Any]:
    """Incremental media: hardlink unchanged from prev, copy new/changed, drop deleted."""
    stats = {
        "mode": "incremental_hardlink",
        "files_hardlinked": 0,
        "files_copied": 0,
        "files_removed": 0,
        "prev_day": prev_root.parent.name if prev_root else None,
    }
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)

    src_files: List[Path] = [p for p in src_root.rglob("*") if p.is_file()]
    for src in src_files:
        rel = src.relative_to(src_root)
        dest = dest_root / rel
        prev = (prev_root / rel) if prev_root is not None else None
        kind = _hardlink_or_copy(src, dest, prev if prev and prev.is_file() else None)
        if kind == "hardlink":
            stats["files_hardlinked"] += 1
        else:
            stats["files_copied"] += 1

    # No orphan cleanup needed: dest was rebuilt from scratch via hardlink/copy.
    # files_removed stays 0 (full rebuild of dest tree).
    return stats


def _sync_media_full(src_root: Path, dest_root: Path) -> Dict[str, Any]:
    if dest_root.exists():
        shutil.rmtree(dest_root)
    shutil.copytree(src_root, dest_root, dirs_exist_ok=True)
    n = sum(1 for p in dest_root.rglob("*") if p.is_file())
    return {
        "mode": "full_copytree",
        "files_hardlinked": 0,
        "files_copied": n,
        "files_removed": 0,
        "prev_day": None,
    }


def backup_media_tree(day: str, dest: Path) -> Tuple[Dict[str, Any], bool]:
    """Copy or incrementally snapshot MEDIA_ROOT → dest/media. Returns (stats, ok)."""
    media_dest = dest / "media"
    if not MEDIA_ROOT.exists():
        return {
            "mode": "skipped_no_media_root",
            "files_hardlinked": 0,
            "files_copied": 0,
            "files_removed": 0,
            "prev_day": None,
        }, True
    prev = _previous_backup_media(day)
    try:
        if prev is not None:
            stats = _sync_media_incremental(MEDIA_ROOT, media_dest, prev)
        else:
            stats = _sync_media_full(MEDIA_ROOT, media_dest)
        stats["media_bytes_apparent"] = sum(
            p.stat().st_size for p in media_dest.rglob("*") if p.is_file()
        )
        # Unique inode bytes ≈ real disk for this tree alone (shared across days)
        seen: set[Tuple[int, int]] = set()
        unique = 0
        for p in media_dest.rglob("*"):
            if not p.is_file():
                continue
            st = p.stat()
            key = (st.st_dev, st.st_ino)
            if key not in seen:
                seen.add(key)
                unique += st.st_size
        stats["media_bytes_unique_inodes"] = unique
        return stats, True
    except Exception as e:
        logger.exception("backup media failed: %s", e)
        return {"mode": "error", "error": str(e)}, False


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
        "media_mode": None,
        "purged": [],
        "retention_days": BACKUP_RETENTION_DAYS,
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

    media_stats, media_ok = backup_media_tree(day, dest)
    report["media_mode"] = media_stats.get("mode")
    report["media_stats"] = media_stats
    if not media_ok:
        report["media_error"] = media_stats.get("error", "media backup failed")
        report["media_copied"] = False
        report["ok"] = False
    elif media_stats.get("mode") == "skipped_no_media_root":
        report["media_copied"] = False  # root assente → OK via _status_from_report
    else:
        report["media_copied"] = True
        report["media_bytes"] = media_stats.get("media_bytes_apparent", 0)

    status = _status_from_report(report)
    report["status"] = status
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "retention_days": BACKUP_RETENTION_DAYS,
        "media_mode": report.get("media_mode"),
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
                dedupe_hours=6,
            )
        except Exception:  # noqa: BLE001
            logger.exception("backup ops_alert failed")

    # Pre-demo — second copy off-box (disk/NFS/volume). Failures alert but do not flip hot status.
    if status in ("OK", "PARTIAL"):
        try:
            from apps.immoweb.offbox_backup import sync_day_to_offbox

            off = sync_day_to_offbox(day)
            report["offbox"] = off
            if not off.get("ok"):
                from shared.ops_alerts import record_alert

                await record_alert(
                    kind="backup_offbox",
                    severity="warning",
                    message=f"Off-box bak fallito ({day}): {off.get('error')}",
                    meta=off,
                    dedupe_hours=6,
                )
        except Exception:  # noqa: BLE001
            logger.exception("offbox sync failed")
            report["offbox"] = {"ok": False, "error": "exception"}

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
