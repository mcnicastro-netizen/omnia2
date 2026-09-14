"""OMNIA — Clients (CRM) routes."""
import csv
import io
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from shared.db.connection import Database
from shared.auth.dependencies import get_current_user, require_roles
from shared.models.client import (
    ClientInDB, ClientCreate, ClientUpdate, ClientListResponse,
    ClientCSVPayload, SearchPreferences,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["clients"])


def _strip(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "_id"}


from shared.auth.tenant import arequire_agency as _agency


@router.get("", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    client_type: Optional[str] = None,
    q: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    agency_id = await _agency(user)
    db = Database.get()
    query = {"agency_id": agency_id}
    if status:
        query["status"] = status
    if client_type:
        query["client_type"] = client_type
    if q:
        q_safe = re.escape(q[:100])
        query["$or"] = [
            {"name": {"$regex": q_safe, "$options": "i"}},
            {"surname": {"$regex": q_safe, "$options": "i"}},
            {"email": {"$regex": q_safe, "$options": "i"}},
            {"phone": {"$regex": q_safe, "$options": "i"}},
        ]
    total = await db.clients.count_documents(query)
    docs = await db.clients.find(query, {"_id": 0}).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size).to_list(page_size)
    return {
        "items": docs, "total": total, "page": page, "page_size": page_size,
    }


@router.post("", status_code=201)
async def create_client(
    payload: ClientCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _agency(user)
    db = Database.get()
    data = payload.model_dump(exclude_unset=False)
    if data.get("preferences") is None:
        data["preferences"] = SearchPreferences().model_dump()
    client = ClientInDB(agency_id=agency_id, assigned_agent_id=user["id"], **data)
    doc = client.model_dump()
    await db.clients.insert_one(doc)
    return _strip(doc)


@router.get("/sellers")
async def list_sellers_for_autocomplete(
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """Lightweight client list for the Property form 'Owner / Seller' dropdown.
    Returns only clients of type seller or landlord, minimal fields.
    M2.S3.5 (D-026).
    """
    agency_id = await _agency(user)
    db = Database.get()
    query = {
        "agency_id": agency_id,
        "client_type": {"$in": ["seller", "landlord"]},
    }
    if q:
        q_safe = re.escape(q[:100])
        query["$or"] = [
            {"name": {"$regex": q_safe, "$options": "i"}},
            {"surname": {"$regex": q_safe, "$options": "i"}},
            {"email": {"$regex": q_safe, "$options": "i"}},
            {"phone": {"$regex": q_safe, "$options": "i"}},
        ]
    docs = await db.clients.find(
        query, {"_id": 0, "id": 1, "name": 1, "surname": 1, "email": 1, "phone": 1, "client_type": 1},
    ).sort("name", 1).limit(limit).to_list(limit)
    return {"items": docs, "total": len(docs)}


@router.get("/{cid}")
async def get_client(cid: str, user: dict = Depends(get_current_user)):
    agency_id = await _agency(user)
    db = Database.get()
    doc = await db.clients.find_one({"id": cid, "agency_id": agency_id})
    if not doc:
        raise HTTPException(status_code=404, detail="client_not_found")
    return _strip(doc)


@router.patch("/{cid}")
async def update_client(
    cid: str,
    payload: ClientUpdate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _agency(user)
    db = Database.get()
    if not await db.clients.find_one({"id": cid, "agency_id": agency_id}):
        raise HTTPException(status_code=404, detail="client_not_found")
    data = payload.model_dump(exclude_unset=True)
    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for k, v in data.items():
        if v is None:
            continue
        update_doc[k] = v.model_dump() if hasattr(v, "model_dump") else v
    await db.clients.update_one({"id": cid, "agency_id": agency_id}, {"$set": update_doc})
    return _strip(await db.clients.find_one({"id": cid}))


@router.delete("/{cid}")
async def delete_client(cid: str, user: dict = Depends(require_roles("agency_admin", "super_admin"))):
    agency_id = await _agency(user)
    db = Database.get()
    # Refuse deletion if the client has properties in carico (avoid orphan seller_client_id)
    linked_count = await db.properties.count_documents(
        {"agency_id": agency_id, "seller_client_id": cid}
    )
    if linked_count > 0:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "client_has_linked_properties",
                "linked_properties": linked_count,
                "message": (
                    "Impossibile eliminare: questo cliente ha "
                    f"{linked_count} immobile/i in carico. Riassegna o elimina prima quegli immobili."
                ),
            },
        )
    result = await db.clients.delete_one({"id": cid, "agency_id": agency_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="client_not_found")
    return {"status": "ok"}


@router.get("/{cid}/properties")
async def list_properties_for_client(cid: str, user: dict = Depends(get_current_user)):
    """List properties where this client is the seller/landlord. M2.S3.5 (D-026)."""
    agency_id = await _agency(user)
    db = Database.get()
    # ensure client exists in tenant
    if not await db.clients.find_one({"id": cid, "agency_id": agency_id}, {"_id": 0, "id": 1}):
        raise HTTPException(status_code=404, detail="client_not_found")
    cursor = db.properties.find(
        {"agency_id": agency_id, "seller_client_id": cid},
        {"_id": 0, "id": 1, "title": 1, "property_type": 1, "operation": 1,
         "status": 1, "city": 1, "price": 1, "rent_monthly": 1,
         "surface_sqm": 1, "rooms": 1, "reference_code": 1,
         "created_at": 1, "photos": 1},
    ).sort("created_at", -1)
    docs = await cursor.to_list(length=200)
    # collapse photo array to first/cover URL only
    for d in docs:
        photos = d.pop("photos", []) or []
        cover = next((p for p in photos if p.get("is_cover")), photos[0] if photos else None)
        d["cover_photo_url"] = (cover or {}).get("url")
    return {"items": docs, "total": len(docs)}


# CSV TEMPLATE + IMPORT
CSV_HEADERS = [
    "name", "surname", "email", "phone", "whatsapp", "fiscal_code",
    "client_type", "status", "source",
    "pref_operation", "pref_cities", "pref_property_types",
    "pref_price_min", "pref_price_max", "pref_surface_min", "pref_rooms_min", "pref_bedrooms_min",
    "notes", "gdpr_consent",
]
CSV_EXAMPLE = [
    "Mario", "Rossi", "mario@example.it", "+39 333 1234567", "+39 333 1234567", "RSSMRA80A01H501Z",
    "buyer", "new", "Idealista",
    "sale", "Roma;Milano", "appartamento;loft",
    "150000", "300000", "60", "2", "1",
    "Cliente interessato a zone centrali", "true",
]


@router.get("/_template/csv")
async def csv_template(user: dict = Depends(get_current_user)):
    buf = io.StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf, delimiter=";")
    w.writerow(CSV_HEADERS)
    w.writerow(CSV_EXAMPLE)
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=omnia-clienti-template.csv"},
    )


def _to_float(v):
    if v in (None, "", "null"):
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def _to_int(v):
    f = _to_float(v)
    return int(f) if f is not None else None


def _to_list(v):
    if not v:
        return []
    return [s.strip() for s in str(v).split(";") if s.strip()]


@router.post("/import/csv")
async def import_csv(
    payload: ClientCSVPayload,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _agency(user)
    db = Database.get()
    imported = 0
    errors = []
    docs = []
    for i, row in enumerate(payload.rows, start=1):
        try:
            name = (row.get("name") or "").strip()
            if not name:
                errors.append({"row": i, "message": "nome mancante"})
                continue
            prefs = SearchPreferences(
                operation=(row.get("pref_operation") or None) or None,
                property_types=_to_list(row.get("pref_property_types")),
                cities=_to_list(row.get("pref_cities")),
                price_min=_to_float(row.get("pref_price_min")),
                price_max=_to_float(row.get("pref_price_max")),
                surface_min=_to_float(row.get("pref_surface_min")),
                rooms_min=_to_int(row.get("pref_rooms_min")),
                bedrooms_min=_to_int(row.get("pref_bedrooms_min")),
            )
            client = ClientInDB(
                agency_id=agency_id,
                assigned_agent_id=user["id"],
                name=name,
                surname=(row.get("surname") or "").strip() or None,
                email=(row.get("email") or "").strip() or None,
                phone=(row.get("phone") or "").strip() or None,
                whatsapp=(row.get("whatsapp") or "").strip() or None,
                fiscal_code=(row.get("fiscal_code") or "").strip() or None,
                client_type=(row.get("client_type") or "buyer").strip().lower() or "buyer",
                status=(row.get("status") or "new").strip().lower() or "new",
                source=(row.get("source") or "").strip() or None,
                preferences=prefs,
                notes=(row.get("notes") or "").strip() or None,
                gdpr_consent=str(row.get("gdpr_consent") or "").strip().lower() in ("true", "1", "yes", "si", "sì"),
            )
            docs.append(client.model_dump())
        except Exception as e:
            errors.append({"row": i, "message": str(e)})
    if docs:
        await db.clients.insert_many(docs)
        imported = len(docs)
    return {"imported": imported, "total_rows": len(payload.rows), "errors": errors, "status": "completed" if not errors else ("completed_with_errors" if imported else "failed")}
