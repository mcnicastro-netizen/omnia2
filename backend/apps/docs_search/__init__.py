"""OMNIA — Fascicolo Digitale: APE scaffold + OpenAPI.it visure (D-082).

OpenAPI.it Catasto replaces SISTER scraping for production visure.
Endpoints return 503 until OPENAPI_ENABLED=true and
(OPENAPI_TOKEN or OPENAPI_EMAIL+OPENAPI_API_KEY) are set.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import arequire_agency
from shared.db.connection import Database
from shared.openapi_catasto import (
    openapi_enabled,
    request_visura_catastale,
    get_visura_status,
    download_visura_document,
    ping as openapi_ping,
)
from shared.storage import put_object, ObjStoreError

logger = logging.getLogger("omnia.docs_search")
router = APIRouter(prefix="/docs", tags=["docs_search"])


class APESearchRequest(BaseModel):
    property_id: str = Field(min_length=1)
    region: str = Field(default="sicilia")
    codice_ape: Optional[str] = None
    codice_fiscale_proprietario: Optional[str] = None
    indirizzo: Optional[str] = None
    comune: Optional[str] = None


class VisuraRequest(BaseModel):
    property_id: str = Field(min_length=1)
    provincia: str = Field(min_length=2, max_length=2)
    comune: str = Field(min_length=1, max_length=120)
    foglio: str = Field(min_length=1, max_length=20)
    particella: str = Field(min_length=1, max_length=20)
    subalterno: Optional[str] = Field(default=None, max_length=20)
    tipo_catasto: str = Field(default="F", pattern=r"^[FTft]$")
    tipo_visura: str = Field(default="ordinaria", pattern=r"^(ordinaria|storica)$")
    sezione: Optional[str] = None


def _siape_enabled() -> bool:
    return (os.environ.get("SIAPE_ENABLED") or "").lower() == "true" and bool(
        os.environ.get("SIAPE_API_KEY")
    )


@router.get("/status")
async def docs_search_status(user: dict = Depends(get_current_user)):
    """Feature-flag status per il frontend."""
    return {
        "ape_search_enabled": _siape_enabled(),
        "openapi_visure_enabled": openapi_enabled(),
        "openai_docs_enabled": False,  # deprecated path — use OpenAPI.it
        "esign_provider": (os.environ.get("ESIGN_PROVIDER") or "mock").lower(),
        "supported_regions": [
            "sicilia", "lombardia", "lazio", "campania", "piemonte",
            "veneto", "emilia-romagna", "toscana", "puglia",
        ],
    }


@router.post("/openapi/ping")
async def openapi_health(
    user: dict = Depends(require_roles("super_admin", "agency_admin")),
):
    """Founder/admin: verify OpenAPI token works."""
    if not openapi_enabled():
        raise HTTPException(503, detail="openapi_not_configured")
    try:
        result = await openapi_ping()
        return result
    except Exception as e:
        raise HTTPException(502, detail=str(e)[:300]) from e


@router.post("/visura/request", status_code=201)
async def request_visura(
    payload: VisuraRequest,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin", "branch_admin")),
):
    """Request a cadastral visura via OpenAPI.it and track it on the property."""
    if not openapi_enabled():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "openapi_not_configured",
                "message": "Imposta OPENAPI_ENABLED=true e OPENAPI_EMAIL+OPENAPI_API_KEY (o OPENAPI_TOKEN) in backend/.env",
            },
        )
    agency_id = await arequire_agency(user)
    db = Database.get()
    prop = await db.properties.find_one(
        {"id": payload.property_id, "agency_id": agency_id}, {"_id": 0, "id": 1, "title": 1}
    )
    if not prop:
        raise HTTPException(404, "Immobile non trovato")

    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0, "fiscal": 1, "display_name": 1})
    richiedente = None
    if agency:
        fiscal = agency.get("fiscal") or {}
        richiedente = fiscal.get("legal_name") or agency.get("display_name")

    try:
        raw = await request_visura_catastale(
            provincia=payload.provincia,
            comune=payload.comune,
            foglio=payload.foglio,
            particella=payload.particella,
            subalterno=payload.subalterno,
            tipo_catasto=payload.tipo_catasto.upper(),
            tipo_visura=payload.tipo_visura,
            sezione=payload.sezione,
            richiedente=richiedente,
            formato="pdf",
        )
    except Exception as e:
        logger.exception("OpenAPI visura request failed")
        raise HTTPException(502, detail=str(e)[:400]) from e

    ext_id = str(raw.get("id") or raw.get("_id") or "")
    remote_stato = str(raw.get("stato") or "").lower()
    initial_status = "pending"
    if "evas" in remote_stato:
        initial_status = "ready"
    elif "error" in remote_stato or "fail" in remote_stato:
        initial_status = "failed"
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "id": str(uuid4()),
        "agency_id": agency_id,
        "property_id": payload.property_id,
        "provider": "openapi",
        "external_id": ext_id,
        "status": initial_status,
        "request": payload.model_dump(),
        "raw_create": raw,
        "created_by": user.get("id"),
        "created_at": now,
        "updated_at": now,
    }
    await db.visura_jobs.insert_one(job)
    return {k: v for k, v in job.items() if k != "_id"}


@router.get("/visura")
async def list_visura_jobs(
    property_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    agency_id = await arequire_agency(user)
    db = Database.get()
    q: Dict[str, Any] = {"agency_id": agency_id}
    if property_id:
        q["property_id"] = property_id
    jobs = await (
        db.visura_jobs.find(q, {"_id": 0, "raw_create": 0, "raw_status": 0})
        .sort("created_at", -1)
        .limit(50)
        .to_list(50)
    )
    return {"items": jobs, "total": len(jobs), "openapi_enabled": openapi_enabled()}


@router.get("/visura/{job_id}")
async def visura_job_status(
    job_id: str,
    user: dict = Depends(get_current_user),
):
    agency_id = await arequire_agency(user)
    db = Database.get()
    job = await db.visura_jobs.find_one({"id": job_id, "agency_id": agency_id}, {"_id": 0})
    if not job:
        raise HTTPException(404, "Richiesta non trovata")
    if not job.get("external_id") or not openapi_enabled():
        return job
    try:
        remote = await get_visura_status(job["external_id"])
        stato = str(remote.get("stato") or remote.get("status") or remote.get("state") or "").lower()
        mapped = job.get("status") or "pending"
        if "evas" in stato or stato in {"done", "completed", "ready"}:
            mapped = "ready"
        elif "erog" in stato or "lavor" in stato or stato in {"pending", "processing"}:
            mapped = "processing"
        elif "error" in stato or "annul" in stato or "fail" in stato:
            mapped = "failed"
        now = datetime.now(timezone.utc).isoformat()
        await db.visura_jobs.update_one(
            {"id": job_id},
            {"$set": {"status": mapped, "raw_status": remote, "updated_at": now}},
        )
        job["status"] = mapped
        job["raw_status"] = remote
        job["updated_at"] = now
    except Exception as e:
        job["poll_error"] = str(e)[:200]
    return job


@router.post("/visura/{job_id}/attach")
async def attach_visura_to_fascicolo(
    job_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin", "branch_admin")),
):
    """Download PDF from OpenAPI and attach to property Fascicolo as visura_catastale."""
    if not openapi_enabled():
        raise HTTPException(503, detail="openapi_not_configured")
    agency_id = await arequire_agency(user)
    db = Database.get()
    job = await db.visura_jobs.find_one({"id": job_id, "agency_id": agency_id}, {"_id": 0})
    if not job:
        raise HTTPException(404, "Richiesta non trovata")
    if not job.get("external_id"):
        raise HTTPException(409, "missing_external_id")

    try:
        pdf = await download_visura_document(job["external_id"])
    except Exception as e:
        raise HTTPException(502, detail=str(e)[:300]) from e

    doc_id = str(uuid4())
    path = f"omnia/fascicolo/{job['property_id']}/{doc_id}.pdf"
    try:
        put_object(path, pdf, "application/pdf")
    except ObjStoreError as e:
        raise HTTPException(503, f"storage_unavailable: {e}") from e

    now = datetime.now(timezone.utc).isoformat()
    doc_meta = {
        "id": doc_id,
        "doc_type": "visura_catastale",
        "name": f"Visura catastale OpenAPI {job['external_id'][:8]}.pdf",
        "mime": "application/pdf",
        "storage_path": path,
        "uploaded_at": now,
        "source": "openapi",
        "visura_job_id": job_id,
    }
    await db.properties.update_one(
        {"id": job["property_id"], "agency_id": agency_id},
        {"$push": {"documents": doc_meta}},
    )
    await db.visura_jobs.update_one(
        {"id": job_id},
        {"$set": {"status": "attached", "document_id": doc_id, "updated_at": now}},
    )
    return {"ok": True, "document": doc_meta, "property_id": job["property_id"]}


@router.post("/ape/search")
async def ape_search(
    payload: APESearchRequest,
    user: dict = Depends(get_current_user),
):
    if not _siape_enabled():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ape_search_not_configured",
                "message": "La ricerca APE via portali regionali è in preparazione.",
            },
        )
    raise HTTPException(status_code=503, detail="siape_client_not_yet_wired")


@router.post("/ape/upload-ocr")
async def ape_upload_ocr(
    property_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    raise HTTPException(status_code=503, detail="ape_ocr_pipeline_not_yet_wired")


# Legacy alias kept so old clients don't 404
@router.post("/openai/search")
async def openai_docs_search_legacy(user: dict = Depends(get_current_user)):
    raise HTTPException(
        status_code=410,
        detail="deprecated — use POST /api/docs/visura/request (OpenAPI.it)",
    )
