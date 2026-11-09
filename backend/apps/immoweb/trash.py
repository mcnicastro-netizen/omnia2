"""OMNIA — Cestino (trash): lista, ripristino, eliminazione definitiva, purge.

D-095 / T-02: purge definitiva di un immobile elimina anche i blob Object Storage
associati (foto/video/documenti fascicolo), best-effort.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import arequire_agency as _require_agency
from shared.db.connection import Database
from shared.db.trash import (
    TRASH_RETENTION_DAYS,
    days_left_in_trash,
    in_trash,
    purge_cutoff_iso,
    restore_update,
)
from shared.storage import delete_object

logger = logging.getLogger("omnia.trash")
router = APIRouter(prefix="/trash", tags=["trash"])

_ADMIN = ("agency_admin", "super_admin")
_MEDIA_PREFIX = "/api/media/"


def _prop_item(doc: dict) -> dict:
    return {
        "kind": "property",
        "id": doc["id"],
        "title": doc.get("title") or "—",
        "subtitle": " · ".join(
            x for x in [
                doc.get("city") or "",
                doc.get("reference_code") or "",
                doc.get("status") or "",
            ] if x
        ),
        "deleted_at": doc.get("deleted_at"),
        "days_left": days_left_in_trash(doc.get("deleted_at")),
    }


def _client_item(doc: dict) -> dict:
    name = " ".join(x for x in [doc.get("name") or "", doc.get("surname") or ""] if x).strip() or "—"
    return {
        "kind": "client",
        "id": doc["id"],
        "title": name,
        "subtitle": " · ".join(
            x for x in [
                doc.get("email") or "",
                doc.get("phone") or "",
                doc.get("client_type") or "",
            ] if x
        ),
        "deleted_at": doc.get("deleted_at"),
        "days_left": days_left_in_trash(doc.get("deleted_at")),
    }


def _path_from_media_url(url: str) -> Optional[str]:
    u = (url or "").strip()
    if u.startswith(_MEDIA_PREFIX):
        return u[len(_MEDIA_PREFIX):].lstrip("/")
    return None


def collect_property_blob_paths(prop: dict) -> List[str]:
    """Gather Object Storage paths for a property about to be hard-deleted."""
    paths: List[str] = []
    seen = set()

    def _add(path: Optional[str]) -> None:
        if not path:
            return
        p = path.lstrip("/")
        if p and p not in seen:
            seen.add(p)
            paths.append(p)

    for key in ("photos", "videos", "floor_plans"):
        for item in prop.get(key) or []:
            if not isinstance(item, dict):
                continue
            _add(item.get("storage_path"))
            _add(_path_from_media_url(str(item.get("url") or "")))

    for doc in prop.get("documents") or []:
        if isinstance(doc, dict):
            _add(doc.get("storage_path"))

    return paths


def purge_property_blobs(prop: dict) -> int:
    """Best-effort delete_object for property media. Returns attempted count."""
    n = 0
    for path in collect_property_blob_paths(prop):
        try:
            delete_object(path)
            n += 1
        except Exception:
            logger.warning(
                "trash blob purge failed prop=%s path=%s",
                prop.get("id"),
                path,
                exc_info=True,
            )
    return n


@router.get("")
async def list_trash(
    kind: Optional[str] = Query(None, description="property | client | omit for both"),
    user: dict = Depends(require_roles(*_ADMIN)),
) -> Dict[str, Any]:
    agency_id = await _require_agency(user)
    db = Database.get()
    flt = {"agency_id": agency_id, **in_trash()}
    items: List[dict] = []

    if kind in (None, "", "property", "all"):
        props = await db.properties.find(
            flt,
            {
                "_id": 0,
                "id": 1,
                "title": 1,
                "city": 1,
                "reference_code": 1,
                "status": 1,
                "deleted_at": 1,
            },
        ).sort("deleted_at", -1).to_list(500)
        items.extend(_prop_item(p) for p in props)

    if kind in (None, "", "client", "all"):
        clients = await db.clients.find(
            flt,
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "surname": 1,
                "email": 1,
                "phone": 1,
                "client_type": 1,
                "deleted_at": 1,
            },
        ).sort("deleted_at", -1).to_list(500)
        items.extend(_client_item(c) for c in clients)

    items.sort(key=lambda x: x.get("deleted_at") or "", reverse=True)
    return {
        "items": items,
        "total": len(items),
        "retention_days": TRASH_RETENTION_DAYS,
    }


@router.post("/{kind}/{item_id}/restore")
async def restore_item(
    kind: str,
    item_id: str,
    user: dict = Depends(require_roles(*_ADMIN)),
) -> Dict[str, Any]:
    agency_id = await _require_agency(user)
    db = Database.get()
    coll = _collection(db, kind)
    result = await coll.update_one(
        {"id": item_id, "agency_id": agency_id, **in_trash()},
        restore_update(),
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="trash_item_not_found")
    return {"status": "ok", "restored": True, "kind": kind, "id": item_id}


@router.delete("/{kind}/{item_id}")
async def purge_item_now(
    kind: str,
    item_id: str,
    user: dict = Depends(require_roles(*_ADMIN)),
) -> Dict[str, Any]:
    """Eliminazione definitiva immediata dal Cestino (irreversibile)."""
    agency_id = await _require_agency(user)
    db = Database.get()
    coll = _collection(db, kind)
    flt = {"id": item_id, "agency_id": agency_id, **in_trash()}
    doc = await coll.find_one(flt, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="trash_item_not_found")

    blobs = 0
    if kind == "property":
        blobs = purge_property_blobs(doc)

    result = await coll.delete_one(flt)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="trash_item_not_found")
    return {
        "status": "ok",
        "purged": True,
        "kind": kind,
        "id": item_id,
        "blobs_purged": blobs,
    }


@router.post("/purge-expired")
async def purge_expired(
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Cancella dal Cestino ciò che ha superato i 30 giorni. super_admin o cron."""
    if user.get("role") not in {"super_admin"}:
        raise HTTPException(status_code=403, detail="cron_forbidden")
    return await run_trash_purge()


async def run_trash_purge() -> Dict[str, Any]:
    db = Database.get()
    cutoff = purge_cutoff_iso()
    flt = {"deleted_at": {"$exists": True, "$nin": [None, ""], "$lte": cutoff}}

    # Find properties first so we can purge blobs before Mongo delete_many.
    props = await db.properties.find(
        flt,
        {"_id": 0, "id": 1, "photos": 1, "videos": 1, "floor_plans": 1, "documents": 1},
    ).to_list(length=5000)
    blobs = 0
    for p in props:
        blobs += purge_property_blobs(p)

    props_res = await db.properties.delete_many(flt)
    clients = await db.clients.delete_many(flt)
    return {
        "ok": True,
        "cutoff": cutoff,
        "retention_days": TRASH_RETENTION_DAYS,
        "purged_properties": props_res.deleted_count,
        "purged_clients": clients.deleted_count,
        "blobs_purged": blobs,
    }


def _collection(db, kind: str):
    if kind == "property":
        return db.properties
    if kind == "client":
        return db.clients
    raise HTTPException(status_code=400, detail="invalid_trash_kind")
