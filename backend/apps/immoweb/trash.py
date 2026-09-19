"""OMNIA — Cestino (trash): lista, ripristino, eliminazione definitiva, purge."""
from __future__ import annotations

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

router = APIRouter(prefix="/trash", tags=["trash"])

_ADMIN = ("agency_admin", "super_admin")


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
    result = await coll.delete_one(
        {"id": item_id, "agency_id": agency_id, **in_trash()}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="trash_item_not_found")
    return {"status": "ok", "purged": True, "kind": kind, "id": item_id}


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
    props = await db.properties.delete_many(flt)
    clients = await db.clients.delete_many(flt)
    return {
        "ok": True,
        "cutoff": cutoff,
        "retention_days": TRASH_RETENTION_DAYS,
        "purged_properties": props.deleted_count,
        "purged_clients": clients.deleted_count,
    }


def _collection(db, kind: str):
    if kind == "property":
        return db.properties
    if kind == "client":
        return db.clients
    raise HTTPException(status_code=400, detail="invalid_trash_kind")
