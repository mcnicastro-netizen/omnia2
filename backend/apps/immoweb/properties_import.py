"""OMNIA — ImmoWeb Properties: import CSV/XML (L9 — estratto da properties.py).

Le route si registrano sullo stesso `router` di properties.py; il modulo viene
importato per side-effect da apps/immoweb/routes.py.
"""
import csv
import io
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import BackgroundTasks, Depends, File, HTTPException, Response, UploadFile
from xml.etree import ElementTree as ET

from shared.db.connection import Database
from shared.auth.dependencies import get_current_user, require_roles
from shared.models.property import (
    PropertyInDB,
    ImportJob,
    CSVImportPayload,
    XMLImportPayload,
)
from shared.importers.vendor_map_legacy_a import detect_and_parse as detect_vendor_a
from shared.utils.net_guard import assert_public_url
from uuid import uuid4

from apps.immoweb.properties import router, _require_agency

logger = logging.getLogger(__name__)


# -------------------- CSV TEMPLATE --------------------

CSV_HEADERS = [
    "title", "description", "reference_code",
    "property_type", "operation", "status", "condition",
    "address", "city", "province", "postal_code", "zone",
    "price", "rent_monthly", "condo_fees",
    "surface_sqm", "rooms", "bedrooms", "bathrooms", "floor", "total_floors",
    "year_built", "energy_class", "energy_value", "heating", "furnished",
    "owner_name", "owner_phone", "owner_email",
    "balcone", "terrazza", "giardino", "ascensore", "aria_condizionata",
    "cantina", "posto_auto", "box_auto", "porta_blindata", "arredato",
]

CSV_EXAMPLE_ROW = [
    "Bilocale luminoso centro città", "Ampio bilocale ristrutturato con vista", "RM-001",
    "appartamento", "sale", "active", "ristrutturato",
    "Via Roma 10", "Roma", "RM", "00100", "Centro Storico",
    "250000", "", "120",
    "65", "2", "1", "1", "3", "5",
    "1965", "C", "120", "autonomo", "non_arredato",
    "Mario Bianchi", "+39 333 1234567", "owner@example.it",
    "true", "false", "false", "true", "true",
    "true", "true", "false", "true", "false",
]


@router.get("/_template/csv")
async def download_csv_template(user: dict = Depends(get_current_user)):
    """Return a CSV template with headers and 1 example row (Excel-friendly UTF-8 BOM)."""
    buf = io.StringIO()
    buf.write("\ufeff")  # UTF-8 BOM for Excel
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(CSV_HEADERS)
    writer.writerow(CSV_EXAMPLE_ROW)
    csv_content = buf.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=omnia-immobili-template.csv"},
    )


# -------------------- CSV IMPORT --------------------

BOOL_FEATURES = {
    "balcone", "terrazza", "giardino", "piscina", "ascensore",
    "aria_condizionata", "riscaldamento_autonomo", "cantina", "soffitta",
    "posto_auto", "box_auto", "portineria", "videocitofono", "allarme",
    "porta_blindata", "cucina_abitabile", "camino", "parquet",
    "vista_panoramica", "luminoso", "arredato", "pannelli_solari",
    "cancello_elettrico", "impianto_domotico", "accesso_disabili",
}


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("true", "1", "yes", "si", "sì", "x", "vero")


def _to_float(v):
    if v in (None, "", "null"):
        return None
    try:
        return float(str(v).replace(",", ".").replace("€", "").strip())
    except (ValueError, TypeError):
        return None


def _to_int(v):
    f = _to_float(v)
    return int(f) if f is not None else None


def _row_to_property(row: dict, agency_id: str, listing_agent_id: str) -> tuple[Optional[PropertyInDB], Optional[str]]:
    """Parse a CSV row into a Property model. Returns (model, error_message)."""
    try:
        title = (row.get("title") or "").strip()
        city = (row.get("city") or "").strip()
        if not title or len(title) < 3:
            return None, "title mancante o troppo corto"
        if not city:
            return None, "city mancante"

        features = {k: _to_bool(row.get(k)) for k in BOOL_FEATURES if k in row}
        energy = {
            "energy_class": (row.get("energy_class") or None) or None,
            "energy_value": _to_float(row.get("energy_value")),
            "heating": (row.get("heating") or None) or None,
        }
        owner = {
            "name": (row.get("owner_name") or "").strip() or None,
            "phone": (row.get("owner_phone") or "").strip() or None,
            "email": (row.get("owner_email") or "").strip() or None,
        }

        prop = PropertyInDB(
            agency_id=agency_id,
            listing_agent_id=listing_agent_id,
            title=title,
            description=(row.get("description") or "").strip() or None,
            reference_code=(row.get("reference_code") or "").strip() or None,
            property_type=(row.get("property_type") or "appartamento").strip().lower() or "appartamento",
            operation=(row.get("operation") or "sale").strip().lower() or "sale",
            status=(row.get("status") or "draft").strip().lower() or "draft",
            condition=(row.get("condition") or None) or None,
            address=(row.get("address") or "").strip() or None,
            city=city,
            province=(row.get("province") or "").strip() or None,
            postal_code=(row.get("postal_code") or "").strip() or None,
            zone=(row.get("zone") or "").strip() or None,
            price=_to_float(row.get("price")),
            rent_monthly=_to_float(row.get("rent_monthly")),
            condo_fees=_to_float(row.get("condo_fees")),
            surface_sqm=_to_float(row.get("surface_sqm")),
            rooms=_to_int(row.get("rooms")),
            bedrooms=_to_int(row.get("bedrooms")),
            bathrooms=_to_int(row.get("bathrooms")),
            floor=_to_int(row.get("floor")),
            total_floors=_to_int(row.get("total_floors")),
            year_built=_to_int(row.get("year_built")),
            features=PropertyFeatures(**features),
            furnished=(row.get("furnished") or None) or None,
            energy=PropertyEnergy(**{k: v for k, v in energy.items() if v is not None}),
            owner=PropertyOwner(**{k: v for k, v in owner.items() if v}),
        )
        return prop, None
    except Exception as e:
        return None, f"errore parsing: {e}"


@router.post("/import/csv")
async def import_csv(
    payload: CSVImportPayload,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Bulk import properties from a list of CSV rows (already parsed by frontend)."""
    agency_id = await _require_agency(user)
    db = Database.get()

    job = ImportJob(
        agency_id=agency_id,
        source="csv",
        source_label=payload.filename or "upload.csv",
        status="processing",
        total_rows=len(payload.rows),
        initiated_by=user["id"],
    )
    job_doc = job.model_dump()
    await db.import_jobs.insert_one(job_doc)

    imported = 0
    errors = []
    docs_to_insert = []
    for i, row in enumerate(payload.rows, start=1):
        prop, err = _row_to_property(row, agency_id, user["id"])
        if err:
            errors.append({"row": i, "message": err})
            continue
        docs_to_insert.append(prop.model_dump())

    if docs_to_insert:
        await db.properties.insert_many(docs_to_insert)
        imported = len(docs_to_insert)

    final_status = (
        "completed_with_errors" if errors and imported else
        "failed" if errors and not imported else
        "completed"
    )
    await db.import_jobs.update_one(
        {"id": job.id},
        {"$set": {
            "imported_count": imported,
            "error_count": len(errors),
            "errors": errors[:200],
            "status": final_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return {
        "job_id": job.id,
        "imported": imported,
        "total_rows": len(payload.rows),
        "errors": errors,
        "status": final_status,
    }


# -------------------- XML FEED IMPORT --------------------

def _xml_get(elem, *paths):
    """Return text of first matching path."""
    for p in paths:
        node = elem.find(p)
        if node is not None and node.text:
            return node.text.strip()
    return None


async def _process_xml_text(
    db, xml_text: str, agency_id: str, user_id: str, source_label: str, job_id: Optional[str] = None
) -> dict:
    """Parse + insert del feed XML; crea/aggiorna l'ImportJob.

    Usata sia in modalità sincrona (XML incollato) sia in background (M23, feed URL).
    Auto-rileva lo schema legacy "vendor A", altrimenti parsing XML generico.
    """

    # Try vendor "A" dedicated parser first (heuristic detection)
    is_vendor_a, vendor_a_props, vendor_a_errors = detect_vendor_a(xml_text, agency_id, user_id)

    if is_vendor_a:
        # Use vendor A-parsed properties
        job = ImportJob(
            agency_id=agency_id,
            source="xml_feed",
            source_label=f"[legacy-vendor-a] {source_label}",
            status="processing",
            total_rows=len(vendor_a_props) + len(vendor_a_errors),
            initiated_by=user_id,
        )
        if job_id:
            job.id = job_id
            await db.import_jobs.replace_one({"id": job_id}, job.model_dump(), upsert=True)
        else:
            await db.import_jobs.insert_one(job.model_dump())
        docs = [p.model_dump() for p in vendor_a_props]
        if docs:
            await db.properties.insert_many(docs)
        final_status = (
            "completed_with_errors" if vendor_a_errors and docs else
            "failed" if vendor_a_errors and not docs else
            "completed"
        )
        await db.import_jobs.update_one(
            {"id": job.id},
            {"$set": {
                "imported_count": len(docs),
                "error_count": len(vendor_a_errors),
                "errors": vendor_a_errors[:200],
                "status": final_status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        return {
            "job_id": job.id,
            "imported": len(docs),
            "total_rows": len(vendor_a_props) + len(vendor_a_errors),
            "errors": vendor_a_errors,
            "status": final_status,
            "format_detected": "legacy_vendor_a",
        }

    # Generic XML fallback
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"invalid_xml: {e}")

    # Try common patterns: <annunci><annuncio> or <properties><property> or root children
    candidates = (
        root.findall(".//annuncio")
        or root.findall(".//property")
        or root.findall(".//inmueble")
        or root.findall(".//listing")
        or list(root)
    )

    job = ImportJob(
        agency_id=agency_id,
        source="xml_feed",
        source_label=source_label,
        status="processing",
        total_rows=len(candidates),
        initiated_by=user_id,
    )
    if job_id:
        job.id = job_id
        await db.import_jobs.replace_one({"id": job_id}, job.model_dump(), upsert=True)
    else:
        await db.import_jobs.insert_one(job.model_dump())

    imported = 0
    errors = []
    docs_to_insert = []

    for i, elem in enumerate(candidates, start=1):
        try:
            title = _xml_get(elem, "title", "titolo", "headline") or _xml_get(elem, "ref", "codice_riferimento") or "Annuncio importato"
            city = _xml_get(elem, "city", "citta", "town", "comune") or "Sconosciuta"
            ptype = (_xml_get(elem, "type", "tipologia") or "appartamento").lower()
            op = (_xml_get(elem, "operation", "operazione") or "sale").lower()
            price = _to_float(_xml_get(elem, "price", "prezzo"))
            rent = _to_float(_xml_get(elem, "rent", "canone", "rent_monthly"))
            sqm = _to_float(_xml_get(elem, "surface", "superficie", "size", "mq"))
            rooms = _to_int(_xml_get(elem, "rooms", "vani", "locali"))
            bedrooms = _to_int(_xml_get(elem, "bedrooms", "camere"))
            bathrooms = _to_int(_xml_get(elem, "bathrooms", "bagni"))
            description = _xml_get(elem, "description", "descrizione", "body")
            address = _xml_get(elem, "address", "indirizzo")
            province = _xml_get(elem, "province", "provincia")
            zone = _xml_get(elem, "zone", "zona", "quartiere")
            ref_code = _xml_get(elem, "reference", "ref", "codice", "id")

            photos = []
            for pi, pelem in enumerate(elem.findall(".//image") + elem.findall(".//foto") + elem.findall(".//photo")):
                url = pelem.text and pelem.text.strip()
                if not url:
                    url = pelem.get("url") or pelem.get("href")
                if url:
                    photos.append({"id": str(uuid4()), "url": url, "order": pi, "is_cover": pi == 0})

            prop = PropertyInDB(
                agency_id=agency_id,
                listing_agent_id=user_id,
                title=title[:200],
                description=description[:10000] if description else None,
                reference_code=ref_code[:50] if ref_code else None,
                property_type=ptype if ptype in {
                    "appartamento", "villa", "villetta_a_schiera", "loft", "attico",
                    "monolocale", "rustico_casale", "ufficio", "negozio", "magazzino",
                    "capannone", "garage_box", "terreno_agricolo", "terreno_edificabile",
                    "palazzo_stabile", "altro",
                } else "appartamento",
                operation=op if op in {"sale", "rent", "rent_to_buy", "auction"} else "sale",
                status="draft",
                city=city,
                address=address,
                province=province,
                zone=zone,
                price=price,
                rent_monthly=rent,
                surface_sqm=sqm,
                rooms=rooms,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                photos=photos,
            )
            docs_to_insert.append(prop.model_dump())
        except Exception as e:
            errors.append({"row": i, "message": str(e)})

    if docs_to_insert:
        await db.properties.insert_many(docs_to_insert)
        imported = len(docs_to_insert)

    final_status = (
        "completed_with_errors" if errors and imported else
        "failed" if errors and not imported else
        "completed"
    )
    await db.import_jobs.update_one(
        {"id": job.id},
        {"$set": {
            "imported_count": imported,
            "error_count": len(errors),
            "errors": errors[:200],
            "status": final_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return {
        "job_id": job.id,
        "imported": imported,
        "total_rows": len(candidates),
        "errors": errors,
        "status": final_status,
    }


async def _run_url_import(feed_url: str, agency_id: str, user_id: str, job_id: str) -> None:
    """M23 — download + import in background; il job traccia lo stato."""
    db = Database.get()
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            r = await client.get(feed_url)
            r.raise_for_status()
            xml_text = r.text
        await _process_xml_text(db, xml_text, agency_id, user_id, feed_url, job_id=job_id)
    except Exception as e:
        logger.exception("xml url import failed job=%s: %s", job_id, e)
        await db.import_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "failed",
                "error_count": 1,
                "errors": [{"row": 0, "message": str(e)[:500]}],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )


@router.post("/import/xml")
async def import_xml_feed(
    payload: XMLImportPayload,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Import da feed XML: contenuto incollato → sincrono; URL → job in background (M23)."""
    agency_id = await _require_agency(user)
    db = Database.get()

    if not payload.feed_url and not payload.xml_content:
        raise HTTPException(status_code=400, detail="feed_url_or_xml_required")

    if payload.xml_content:
        return await _process_xml_text(db, payload.xml_content, agency_id, user["id"], "pasted-xml")

    assert_public_url(payload.feed_url)  # C7 — SSRF guard (sincrona: 400 immediato)
    job = ImportJob(
        agency_id=agency_id,
        source="xml_feed",
        source_label=payload.feed_url,
        status="pending",
        total_rows=0,
        initiated_by=user["id"],
    )
    await db.import_jobs.insert_one(job.model_dump())
    background_tasks.add_task(_run_url_import, payload.feed_url, agency_id, user["id"], job.id)
    return {"job_id": job.id, "status": "processing", "async": True}


@router.get("/import/jobs/{import_job_id}")
async def get_import_job(import_job_id: str, user: dict = Depends(get_current_user)):
    agency_id = await _require_agency(user)
    db = Database.get()
    doc = await db.import_jobs.find_one({"id": import_job_id, "agency_id": agency_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="job_not_found")
    return doc
