"""Off-box backup mirror (pre-demo ≥8).

After a hot bak under BACKUP_ROOT, copy the day folder to OFFBOX_BACKUP_ROOT
(external disk / NFS / second volume in prod). Cloud default: /tmp/omnia-offbox-backups.

Not a substitute for object-storage DR — proves a second copy exists and is readable.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("omnia.offbox_backup")

BACKUP_ROOT = Path(os.environ.get("BACKUP_ROOT") or "/workspace/backend/.backups")
OFFBOX_ROOT = Path(
    os.environ.get("OFFBOX_BACKUP_ROOT") or "/tmp/omnia-offbox-backups"
)


def sync_day_to_offbox(day: str, *, src_root: Optional[Path] = None) -> Dict[str, Any]:
    """Copy BACKUP_ROOT/day → OFFBOX_ROOT/day. Returns report dict."""
    src = (src_root or BACKUP_ROOT) / day
    dest = OFFBOX_ROOT / day
    report: Dict[str, Any] = {
        "ok": False,
        "day": day,
        "src": str(src),
        "dest": str(dest),
        "offbox_root": str(OFFBOX_ROOT),
    }
    if not src.is_dir():
        report["error"] = "src_missing"
        return report
    manifest_path = src / "MANIFEST.json"
    if not manifest_path.is_file():
        report["error"] = "manifest_missing"
        return report
    try:
        meta = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        report["error"] = f"manifest_unreadable:{e}"
        return report
    status = meta.get("status") or (meta.get("report") or {}).get("status")
    report["manifest_status"] = status
    if status not in ("OK", "PARTIAL"):
        report["error"] = f"status_not_copyable:{status}"
        return report

    OFFBOX_ROOT.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    try:
        shutil.copytree(src, dest, symlinks=False, ignore_dangling_symlinks=True)
    except Exception as e:  # noqa: BLE001
        logger.exception("offbox copy failed day=%s", day)
        report["error"] = str(e)[:300]
        return report

    # Verify dest MANIFEST + file count
    dest_m = dest / "MANIFEST.json"
    if not dest_m.is_file():
        report["error"] = "dest_manifest_missing"
        return report
    n_files = sum(1 for p in dest.rglob("*") if p.is_file())
    report["ok"] = True
    report["files"] = n_files
    report["bytes"] = sum(p.stat().st_size for p in dest.rglob("*") if p.is_file())
    return report


def latest_offbox_day() -> Optional[str]:
    if not OFFBOX_ROOT.exists():
        return None
    days = sorted(
        p.name
        for p in OFFBOX_ROOT.iterdir()
        if p.is_dir() and (p / "MANIFEST.json").is_file()
    )
    return days[-1] if days else None


def read_offbox_health() -> Dict[str, Any]:
    day = latest_offbox_day()
    if not day:
        return {
            "status": "MISSING",
            "path": str(OFFBOX_ROOT),
            "message": "Nessuna copia off-box",
        }
    meta = {}
    try:
        meta = json.loads((OFFBOX_ROOT / day / "MANIFEST.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    return {
        "status": meta.get("status") or "UNKNOWN",
        "day": day,
        "path": str(OFFBOX_ROOT / day),
        "offbox_root": str(OFFBOX_ROOT),
        "created_at": meta.get("created_at"),
    }
