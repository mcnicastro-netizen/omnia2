"""OMNIA — ImmoWeb Properties routes (CRUD + CSV/XML import)."""
import csv
import io
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from xml.etree import ElementTree as ET

from shared.db.connection import Database
from shared.auth.dependencies import get_current_user, require_roles
from shared.storage import put_object, ObjStoreError
from shared.models.property import (
    PropertyInDB,
    PropertyCreate,
    PropertyUpdate,
    PropertyListItem,
    PropertyListResponse,
    PropertyFeatures,
    PropertyEnergy,
    PropertyOwner,
    ImportJob,
    CSVImportPayload,
    XMLImportPayload,
)
from shared.importers.vendor_map_legacy_a import detect_and_parse as detect_vendor_a
from shared.utils.net_guard import assert_public_url
from apps.immocloud.geocoding import schedule_geocode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/properties", tags=["properties"])


def _strip(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "_id"}


from shared.auth.tenant import arequire_agency as _require_agency


_VALID_PROPERTY_TYPES = {
    "appartamento", "villa", "villetta_a_schiera", "loft", "attico",
    "monolocale", "rustico_casale", "ufficio", "negozio", "magazzino",
    "capannone", "garage_box", "terreno_agricolo", "terreno_edificabile",
    "palazzo_stabile", "altro",
}
_PROPERTY_TYPE_LEGACY_MAP = {
    "apartment": "appartamento",
    "house": "villa",
    "office": "ufficio",
    "shop": "negozio",
    "garage": "garage_box",
    "land": "terreno_edificabile",
    None: "altro",
    "": "altro",
}


def _normalize_property_type(v):
    if v in _VALID_PROPERTY_TYPES:
        return v
    return _PROPERTY_TYPE_LEGACY_MAP.get(v, "altro")


def _to_list_item(doc: dict) -> dict:
    cover = next((p["url"] for p in (doc.get("photos") or []) if p.get("is_cover")), None)
    if not cover and doc.get("photos"):
        cover = doc["photos"][0].get("url")
    return {
        "id": doc["id"],
        "title": doc["title"],
        "property_type": _normalize_property_type(doc.get("property_type")),
        "operation": doc.get("operation", "sale"),
        "status": doc.get("status", "draft"),
        "city": doc.get("city", ""),
        "address": doc.get("address"),
        "price": doc.get("price"),
        "rent_monthly": doc.get("rent_monthly"),
        "surface_sqm": doc.get("surface_sqm"),
        "rooms": doc.get("rooms"),
        "bedrooms": doc.get("bedrooms"),
        "cover_photo_url": cover,
        "reference_code": doc.get("reference_code"),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


# -------------------- LIST --------------------

@router.get("", response_model=PropertyListResponse)
async def list_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    operation: Optional[str] = None,
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    q: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    agency_id = await _require_agency(user)
    db = Database.get()

    query = {"agency_id": agency_id}
    if status:
        query["status"] = status
    if operation:
        query["operation"] = operation
    if property_type:
        query["property_type"] = property_type
    if city:
        query["city"] = {"$regex": re.escape(city[:100]), "$options": "i"}
    if q:
        q_safe = re.escape(q[:100])
        query["$or"] = [
            {"title": {"$regex": q_safe, "$options": "i"}},
            {"description": {"$regex": q_safe, "$options": "i"}},
            {"reference_code": {"$regex": q_safe, "$options": "i"}},
        ]

    total = await db.properties.count_documents(query)
    # Sprint 4 · Task #11 — projection esplicita: evita di trasportare `photos`
    # (base64) e altri campi pesanti (features/energy/owner sub-docs) che poi
    # `_to_list_item` scarta. Rende GET /properties p95 <200ms vs ~3s prima.
    LIST_PROJECTION = {
        "_id": 0,
        "id": 1,
        "title": 1,
        "property_type": 1,
        "operation": 1,
        "status": 1,
        "city": 1,
        "address": 1,
        "price": 1,
        "rent_monthly": 1,
        "surface_sqm": 1,
        "rooms": 1,
        "bedrooms": 1,
        "reference_code": 1,
        "created_at": 1,
        "updated_at": 1,
        # Only the first photo is needed for `cover_photo_url`
        "photos": {"$slice": 1},
    }
    cursor = (
        db.properties.find(query, LIST_PROJECTION)
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    docs = await cursor.to_list(length=page_size)
    return {
        "items": [_to_list_item(d) for d in docs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# -------------------- CREATE --------------------

@router.post("", status_code=201)
async def create_property(
    payload: PropertyCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _require_agency(user)
    db = Database.get()
    data = payload.model_dump(exclude_unset=False)
    # Sub-models default factories
    if data.get("features") is None:
        data["features"] = PropertyFeatures().model_dump()
    if data.get("energy") is None:
        data["energy"] = PropertyEnergy().model_dump()
    if data.get("owner") is None:
        data["owner"] = PropertyOwner().model_dump()
    if data.get("photos") is None:
        data["photos"] = []

    prop = PropertyInDB(
        agency_id=agency_id,
        listing_agent_id=user["id"],
        **data,
    )
    doc = prop.model_dump()
    await db.properties.insert_one(doc)
    # M3.S3 — fire-and-forget geocoding (Nominatim/OSM)
    if not doc.get("lat") and not doc.get("lng"):
        schedule_geocode(db, doc["id"], {
            "address": doc.get("address"), "city": doc.get("city"),
            "province": doc.get("province"), "postal_code": doc.get("postal_code"),
        })
    return _strip(doc)


# -------------------- READ --------------------

@router.get("/{prop_id}")
async def get_property(prop_id: str, user: dict = Depends(get_current_user)):
    agency_id = await _require_agency(user)
    db = Database.get()
    doc = await db.properties.find_one({"id": prop_id, "agency_id": agency_id})
    if not doc:
        raise HTTPException(status_code=404, detail="property_not_found")
    return _strip(doc)


# -------------------- UPDATE --------------------

@router.patch("/{prop_id}")
async def update_property(
    prop_id: str,
    payload: PropertyUpdate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _require_agency(user)
    db = Database.get()
    existing = await db.properties.find_one({"id": prop_id, "agency_id": agency_id})
    if not existing:
        raise HTTPException(status_code=404, detail="property_not_found")

    data = payload.model_dump(exclude_unset=True)
    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat()}
    # Fields that the client can EXPLICITLY clear by sending null (vs omitted).
    NULLABLE_FIELDS = {"seller_client_id"}
    for k, v in data.items():
        if v is None:
            if k in NULLABLE_FIELDS:
                update_doc[k] = None  # explicit clear
            continue
        if hasattr(v, "model_dump"):
            update_doc[k] = v.model_dump()
        else:
            update_doc[k] = v

    await db.properties.update_one({"id": prop_id, "agency_id": agency_id}, {"$set": update_doc})
    updated = await db.properties.find_one({"id": prop_id})
    # M3.S3 — re-geocode if any address field changed (best-effort)
    address_changed = any(k in update_doc for k in ("address", "city", "province", "postal_code"))
    if address_changed:
        schedule_geocode(db, prop_id, {
            "address": updated.get("address"), "city": updated.get("city"),
            "province": updated.get("province"), "postal_code": updated.get("postal_code"),
        })
    return _strip(updated)


# -------------------- DELETE --------------------

@router.delete("/{prop_id}")
async def delete_property(
    prop_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    agency_id = await _require_agency(user)
    db = Database.get()
    result = await db.properties.delete_one({"id": prop_id, "agency_id": agency_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="property_not_found")
    return {"status": "ok"}


# -------------------- PHOTOS: UPLOAD FILE (Sprint 4 · GAP #1) --------------------

_ALLOWED_PHOTO_MIME = {"image/jpeg", "image/png", "image/webp"}
_MAX_PHOTO_BYTES = 8 * 1024 * 1024  # 8MB


@router.post("/{prop_id}/photos/upload")
async def upload_property_photo(
    prop_id: str,
    file: UploadFile = File(...),
    is_cover: bool = Query(False),
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Upload a photo binary to Object Storage.

    Sprint 4 · GAP #1 — Replaces Base64-in-Mongo with a persistent object store.
    Returns the new `photos` array for the property.
    """
    agency_id = await _require_agency(user)
    db = Database.get()
    prop = await db.properties.find_one({"id": prop_id, "agency_id": agency_id})
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")

    ct = (file.content_type or "").lower()
    if ct not in _ALLOWED_PHOTO_MIME:
        raise HTTPException(status_code=415, detail="unsupported_media_type")
    data = await file.read()
    if len(data) > _MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="file_too_large")
    if not data:
        raise HTTPException(status_code=400, detail="empty_file")

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[ct]
    photo_id = str(uuid4())
    storage_path = f"omnia/properties/{prop_id}/{photo_id}.{ext}"
    try:
        put_object(storage_path, data, ct)
    except ObjStoreError as e:
        logger.exception("photo upload failed prop=%s: %s", prop_id, e)
        raise HTTPException(status_code=502, detail="storage_upload_failed") from e

    photos = list(prop.get("photos") or [])
    if is_cover:
        for p in photos:
            p["is_cover"] = False
    new_photo = {
        "id": photo_id,
        "url": f"/api/media/{storage_path}",
        "caption": None,
        "order": len(photos),
        "is_cover": bool(is_cover) or not photos,
    }
    photos.append(new_photo)
    await db.properties.update_one(
        {"id": prop_id, "agency_id": agency_id},
        {"$set": {"photos": photos, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"photo": new_photo, "photos": photos}


@router.post("/photos/upload-tmp")
async def upload_photo_tmp(
    file: UploadFile = File(...),
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Upload a photo binary before the property exists (create mode) — H10.

    Stores in Object Storage under the agency namespace and returns the media URL
    to embed in the `photos` array on save.
    """
    agency_id = await _require_agency(user)
    ct = (file.content_type or "").lower()
    if ct not in _ALLOWED_PHOTO_MIME:
        raise HTTPException(status_code=415, detail="unsupported_media_type")
    data = await file.read()
    if len(data) > _MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="file_too_large")
    if not data:
        raise HTTPException(status_code=400, detail="empty_file")

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[ct]
    photo_id = str(uuid4())
    storage_path = f"omnia/agencies/{agency_id}/photos/{photo_id}.{ext}"
    try:
        put_object(storage_path, data, ct)
    except ObjStoreError as e:
        logger.exception("tmp photo upload failed agency=%s: %s", agency_id, e)
        raise HTTPException(status_code=502, detail="storage_upload_failed") from e
    return {"id": photo_id, "url": f"/api/media/{storage_path}"}
