"""OMNIA — Orphan Object Storage GC (D-102 / Onda 7).

Compares local object keys under `omnia/` with Mongo references.
Deletes only keys older than ORPHAN_GC_MIN_AGE_HOURS (default 48) and not
referenced — avoids racing in-flight uploads.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional, Set

from shared.db.connection import Database
from shared.storage import delete_object, list_object_keys
from apps.immoweb.trash import _path_from_media_url, collect_property_blob_paths

logger = logging.getLogger("omnia.orphan_gc")

DEFAULT_MIN_AGE_HOURS = 48
DEFAULT_MAX_DELETE = 500


def _min_age_hours() -> float:
    try:
        return float(os.environ.get("ORPHAN_GC_MIN_AGE_HOURS") or DEFAULT_MIN_AGE_HOURS)
    except ValueError:
        return float(DEFAULT_MIN_AGE_HOURS)


def _add_url_or_path(refs: Set[str], value: Optional[str]) -> None:
    if not value or not isinstance(value, str):
        return
    p = _path_from_media_url(value) or value.lstrip("/")
    if p.startswith("omnia/"):
        refs.add(p)


def _walk_media_strings(node: Any, refs: Set[str]) -> None:
    """Collect omnia/ paths from nested JSON (staging variants, etc.)."""
    if isinstance(node, dict):
        for v in node.values():
            _walk_media_strings(v, refs)
    elif isinstance(node, list):
        for v in node:
            _walk_media_strings(v, refs)
    elif isinstance(node, str):
        _add_url_or_path(refs, node)


async def collect_referenced_blob_paths(db=None) -> Set[str]:
    """All Object Storage paths still referenced by live Mongo docs."""
    db = db or Database.get()
    refs: Set[str] = set()

    prop_cur = db.properties.find(
        {},
        {
            "_id": 0,
            "photos": 1,
            "videos": 1,
            "floor_plans": 1,
            "documents": 1,
            "floor_plan_url": 1,
        },
    )
    async for prop in prop_cur:
        for path in collect_property_blob_paths(prop):
            if path.startswith("omnia/"):
                refs.add(path)
        _add_url_or_path(refs, prop.get("floor_plan_url"))

    async for doc in db.modulistica_documents.find({}, {"_id": 0, "storage_path": 1}):
        _add_url_or_path(refs, doc.get("storage_path"))

    async for vid in db.videos.find(
        {}, {"_id": 0, "id": 1, "storage_path": 1, "download_url": 1}
    ):
        _add_url_or_path(refs, vid.get("storage_path"))
        _add_url_or_path(refs, vid.get("download_url"))
        if vid.get("id") and not vid.get("storage_path"):
            refs.add(f"omnia/videos/{vid['id']}.mp4")

    # Staging previews / paid variants may live only on the job doc until attach.
    async for job in db.virtual_staging_jobs.find(
        {}, {"_id": 0, "variants": 1, "source_url": 1, "photo_url": 1}
    ):
        _walk_media_strings(job, refs)

    return refs


def find_orphan_keys(
    *,
    referenced: Set[str],
    keys: Optional[List[tuple]] = None,
    min_age_hours: Optional[float] = None,
    now: Optional[float] = None,
) -> List[str]:
    """Return orphan paths older than min_age_hours."""
    min_age = _min_age_hours() if min_age_hours is None else float(min_age_hours)
    now_ts = time.time() if now is None else now
    cutoff = now_ts - (min_age * 3600)
    keys = keys if keys is not None else list_object_keys("omnia/")
    orphans: List[str] = []
    for path, mtime in keys:
        if path in referenced:
            continue
        if mtime > cutoff:
            continue
        orphans.append(path)
    return orphans


def _env_dry_run_default() -> bool:
    """ORPHAN_GC_DRY_RUN=1 forces scan-only (ops kill-switch)."""
    return (os.environ.get("ORPHAN_GC_DRY_RUN") or "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


async def run_orphan_gc(
    *,
    dry_run: Optional[bool] = None,
    max_delete: int = DEFAULT_MAX_DELETE,
    min_age_hours: Optional[float] = None,
) -> Dict[str, Any]:
    """Scan + optionally delete orphan blobs. Safe defaults for scheduler."""
    if dry_run is None:
        dry_run = _env_dry_run_default()
    db = Database.get()
    referenced = await collect_referenced_blob_paths(db)
    keys = list_object_keys("omnia/")
    orphans = find_orphan_keys(
        referenced=referenced,
        keys=keys,
        min_age_hours=min_age_hours,
    )
    to_delete = orphans[: max(0, int(max_delete))]
    deleted: List[str] = []
    errors = 0
    if not dry_run:
        for path in to_delete:
            try:
                delete_object(path)
                deleted.append(path)
            except Exception:
                errors += 1
                logger.warning("orphan_gc delete failed path=%s", path, exc_info=True)

    report = {
        "ok": errors == 0,
        "dry_run": dry_run,
        "objects_scanned": len(keys),
        "referenced": len(referenced),
        "orphans_found": len(orphans),
        "orphans_deleted": len(deleted),
        "errors": errors,
        "min_age_hours": _min_age_hours() if min_age_hours is None else float(min_age_hours),
        "sample": (deleted or orphans)[:20],
    }
    logger.info(
        "orphan_gc dry_run=%s scanned=%s orphans=%s deleted=%s errors=%s",
        dry_run,
        report["objects_scanned"],
        report["orphans_found"],
        report["orphans_deleted"],
        errors,
    )
    return report
