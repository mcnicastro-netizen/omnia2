"""OMNIA — Universal XML Importer HTTP API (M2.5.4a, D-050).

Two-phase import flow protected by JWT (agency_admin+).

POST /api/app/import/xml/preview   (multipart: file)
    → parses the uploaded XML, returns ParseReport (no DB writes)
    → stores parsed dicts in an in-memory session keyed by a random id
      that survives ~10 minutes for the commit step.

POST /api/app/import/xml/commit
    Body: { "session_id": "...", "skip_duplicates_by_ref": true, ... }
    → replays a previously-previewed import into the caller's agency
    → returns the created ids + skipped/updated counts
    → persists an ImportJob row (non dry-run)

GET  /api/app/import/jobs
    → agency import history (CSV + XML feed + universal XML)

The UI ("il tuo attuale gestionale") intentionally avoids any competitor
name. Internally the parser is `universal_xml`, and any vendor-specific
mapping logic lives inside its heuristic tables — not exposed to the client.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from pydantic import BaseModel, Field

from shared.db.connection import Database
from shared.auth.dependencies import require_roles
from shared.importers.universal_xml import parse_xml_feed
from shared.models.property import ImportJob

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/import", tags=["import"])


# Simple in-memory session store (LOCAL to the backend process — good enough
# for a two-phase preview → commit flow that lives within a single UI session).
_PREVIEW_SESSIONS: Dict[str, Dict[str, Any]] = {}
_PREVIEW_TTL_SECONDS = 10 * 60


def _cleanup_sessions() -> None:
    now = time.time()
    stale = [k for k, v in _PREVIEW_SESSIONS.items() if now - v.get("_ts", 0) > _PREVIEW_TTL_SECONDS]
    for k in stale:
        _PREVIEW_SESSIONS.pop(k, None)


def _agency_id_of(user: dict) -> str:
    agencies = user.get("agency_ids") or []
    if not agencies:
        raise HTTPException(status_code=404, detail="no_agency")
    return agencies[0]


class CommitBody(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    skip_duplicates_by_ref: bool = True
    dry_run: bool = False
    # Post-import publishing (default ON — populate ImmobilCloud + MLS inventory)
    list_on_immobilcloud: bool = True
    share_on_mls: bool = True
    # Optional: assign all imported listings to this agency member (default: committer)
    listing_agent_id: Optional[str] = Field(default=None, max_length=64)


async def _resolve_listing_agent(db, agency_id: str, requested_id: Optional[str], fallback_user_id: str) -> str:
    """Validate listing_agent_id belongs to the agency; else fall back to committer."""
    agent_id = (requested_id or "").strip() or fallback_user_id
    if agent_id == fallback_user_id:
        return agent_id
    member = await db.users.find_one(
        {"id": agent_id, "agency_ids": agency_id},
        {"_id": 0, "id": 1},
    )
    if not member:
        raise HTTPException(status_code=400, detail="listing_agent_not_in_agency")
    return agent_id


@router.post("/xml/preview")
async def preview_xml(
    file: UploadFile = File(...),
    lang: str = "it",
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """
    Upload an XML feed export from the caller's current CRM ("il tuo attuale
    gestionale") and receive a dry-run parse report.

    Nothing is written to the database at this stage.
    """
    _cleanup_sessions()

    if not file.filename or not file.filename.lower().endswith((".xml", ".txt")):
        raise HTTPException(status_code=400, detail="file_must_be_xml")

    raw = await file.read()
    if not raw or len(raw) < 40:
        raise HTTPException(status_code=400, detail="file_empty_or_too_small")
    if len(raw) > 50 * 1024 * 1024:  # 50MB hard cap
        raise HTTPException(status_code=413, detail="file_too_large")

    agency_id = _agency_id_of(user)
    properties, report = parse_xml_feed(raw, agency_id=agency_id, preferred_lang=lang if lang in {"it", "en", "es", "de", "fr"} else "it")

    if report.total_found == 0:
        raise HTTPException(status_code=422, detail="no_property_records_detected")

    # Session store
    session_id = f"prv_{int(time.time() * 1000)}_{user['id'][:8]}"
    _PREVIEW_SESSIONS[session_id] = {
        "_ts": time.time(),
        "agency_id": agency_id,
        "user_id": user["id"],
        "properties": properties,
        "report": report.to_dict(),
        "filename": file.filename,
        "size_bytes": len(raw),
    }
    logger.info(
        "xml_import_preview: session=%s agency=%s parsed=%d found=%d",
        session_id, agency_id, report.parsed_ok, report.total_found,
    )
    return {"session_id": session_id, "report": report.to_dict()}


@router.post("/xml/commit")
async def commit_xml(
    body: CommitBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Commit a previously-previewed XML import to `db.properties`."""
    _cleanup_sessions()

    sess = _PREVIEW_SESSIONS.get(body.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="preview_session_not_found_or_expired")
    if sess["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="session_owner_mismatch")

    agency_id = _agency_id_of(user)
    if sess["agency_id"] != agency_id:
        raise HTTPException(status_code=403, detail="session_agency_mismatch")

    db = Database.get()
    properties: List[Dict[str, Any]] = sess["properties"]
    listing_agent_id = await _resolve_listing_agent(
        db, agency_id, body.listing_agent_id, user["id"],
    )

    # Optionally dedupe by reference_code within the same agency
    existing_refs: set = set()
    if body.skip_duplicates_by_ref:
        refs = [p.get("reference_code") for p in properties if p.get("reference_code")]
        if refs:
            async for doc in db.properties.find(
                {"agency_id": agency_id, "reference_code": {"$in": refs}},
                {"reference_code": 1, "_id": 0},
            ):
                existing_refs.add(doc.get("reference_code"))

    to_insert: List[Dict[str, Any]] = []
    skipped_ref: List[str] = []
    for p in properties:
        ref = p.get("reference_code")
        if body.skip_duplicates_by_ref and ref and ref in existing_refs:
            skipped_ref.append(ref)
            continue
        # Apply publish flags chosen in preview UI
        doc = dict(p)
        list_cloud = bool(body.list_on_immobilcloud)
        share_mls = bool(body.share_on_mls)
        doc["listing_agent_id"] = listing_agent_id
        doc["is_listed_on_immobilcloud"] = list_cloud
        doc["mls_shared"] = share_mls
        doc["moderation_status"] = doc.get("moderation_status") or "approved"
        doc["status"] = "active"
        if list_cloud and share_mls:
            doc["visibility"] = "public"
        elif list_cloud and not share_mls:
            doc["visibility"] = "public"
        elif not list_cloud and share_mls:
            doc["visibility"] = "mls_only"
            doc["is_listed_on_immobilcloud"] = False
        else:
            doc["visibility"] = "private"
            doc["is_listed_on_immobilcloud"] = False
            doc["mls_shared"] = False
        to_insert.append(doc)

    inserted_ids: List[str] = []
    if to_insert and not body.dry_run:
        # Insert in chunks of 100 to keep it responsive
        chunk = 100
        for i in range(0, len(to_insert), chunk):
            batch = to_insert[i:i + chunk]
            await db.properties.insert_many(batch, ordered=False)
            inserted_ids.extend([p["id"] for p in batch])

    # dry_run must keep the session so the user can confirm after simulation
    if not body.dry_run:
        _PREVIEW_SESSIONS.pop(body.session_id, None)

    # dry_run: report how many WOULD be inserted (UI Cap.14 simulation copy)
    inserted_count = len(to_insert) if body.dry_run else len(inserted_ids)

    job_id: Optional[str] = None
    if not body.dry_run:
        status = "completed" if inserted_count > 0 or len(skipped_ref) > 0 else "completed"
        if inserted_count == 0 and len(skipped_ref) == 0:
            status = "failed"
        job = ImportJob(
            agency_id=agency_id,
            source="universal_xml",
            source_label=sess.get("filename") or "upload.xml",
            status=status,
            total_rows=len(properties),
            imported_count=inserted_count,
            error_count=len(skipped_ref),
            errors=[{"row": ref, "message": "skipped_duplicate_reference"} for ref in skipped_ref[:50]],
            initiated_by=user["id"],
        )
        job_doc = job.model_dump()
        job_doc["listing_agent_id"] = listing_agent_id
        job_doc["list_on_immobilcloud"] = body.list_on_immobilcloud
        job_doc["share_on_mls"] = body.share_on_mls
        await db.import_jobs.insert_one(job_doc)
        job_id = job.id

    now_iso = datetime.now(timezone.utc).isoformat()
    logger.info(
        "xml_import_commit: agency=%s inserted=%d skipped=%d dry_run=%s cloud=%s mls=%s agent=%s job=%s",
        agency_id, inserted_count, len(skipped_ref), body.dry_run,
        body.list_on_immobilcloud, body.share_on_mls, listing_agent_id, job_id,
    )
    return {
        "inserted": inserted_count,
        "skipped_by_reference": len(skipped_ref),
        "skipped_references": skipped_ref[:50],
        "committed_at": now_iso,
        "dry_run": body.dry_run,
        "list_on_immobilcloud": body.list_on_immobilcloud,
        "share_on_mls": body.share_on_mls,
        "listing_agent_id": listing_agent_id,
        "job_id": job_id,
    }


@router.get("/xml/session/{session_id}")
async def get_preview_session(
    session_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Return the report for an active preview session (useful on page reload)."""
    _cleanup_sessions()
    sess = _PREVIEW_SESSIONS.get(session_id)
    if not sess or sess["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="preview_session_not_found_or_expired")
    return {
        "session_id": session_id,
        "report": sess["report"],
        "filename": sess["filename"],
        "size_bytes": sess["size_bytes"],
        "expires_in_seconds": max(0, int(_PREVIEW_TTL_SECONDS - (time.time() - sess["_ts"]))),
    }


@router.get("/jobs")
async def list_import_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Agency import history (CSV, XML feed, universal XML). Newest first."""
    agency_id = _agency_id_of(user)
    db = Database.get()
    cursor = db.import_jobs.find(
        {"agency_id": agency_id},
        {"_id": 0},
    ).sort("created_at", -1).limit(limit)
    jobs = await cursor.to_list(length=limit)
    return {"jobs": jobs, "count": len(jobs)}
