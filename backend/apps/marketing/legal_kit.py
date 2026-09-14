"""OMNIA Legal Kit — Public router (M2.5.4c, D-055).

Public, no-auth endpoints exposing the Domain Sovereignty legal kit.
Rate-limited by IP to prevent abuse (same collection as domain_check).

Endpoints (all under /api/legal):
    GET  /templates                 List catalog (4 templates)
    POST /download/{slug}           Return one filled PDF (application/pdf)
    POST /kit                       Return the ZIP with all 4 PDFs + lead capture

The v1 API-key equivalent (paid, 2 credits) lives in `apps/v1/gateway.py`.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field

from shared.db.connection import Database
from shared.legal_kit.templates import list_templates, TEMPLATES
from shared.legal_kit.pdf_generator import render_pdf, render_kit_zip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/legal", tags=["legal-kit"])


# ------------------ Rate limit config ------------------
_RATE_LIMIT_MAX_PER_HOUR = 20
_RATE_LIMIT_WINDOW_SEC = 3600


async def _check_rate_limit(ip: str, action: str) -> None:
    if not ip:
        return
    db = Database.get()
    since = datetime.now(timezone.utc).timestamp() - _RATE_LIMIT_WINDOW_SEC
    count = await db.legal_kit_events.count_documents({
        "client_ip": ip, "action": action, "created_ts": {"$gte": since},
    })
    if count >= _RATE_LIMIT_MAX_PER_HOUR:
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")


async def _log_event(action: str, slug: Optional[str], client_ip: str,
                     ctx: Optional[dict] = None) -> str:
    db = Database.get()
    now = datetime.now(timezone.utc)
    event_id = str(uuid4())
    await db.legal_kit_events.insert_one({
        "id": event_id, "action": action, "template_slug": slug,
        "client_ip": client_ip,
        # persist only NON-PII flags, not the raw context (safer for GDPR)
        "has_agency_name": bool(ctx and ctx.get("agency_name")),
        "has_domain": bool(ctx and ctx.get("domain")),
        "created_at": now.isoformat(), "created_ts": now.timestamp(),
    })
    return event_id


# ------------------ Models ------------------

class KitContext(BaseModel):
    """Data the agency provides to pre-fill the templates.

    All fields are optional — missing ones render as `[DA COMPILARE]` in the PDF,
    which is still useful (agency can print, fill, sign later)."""
    signer_name: Optional[str] = Field(default=None, max_length=200)
    agency_name: Optional[str] = Field(default=None, max_length=200)
    agency_piva: Optional[str] = Field(default=None, max_length=40)
    agency_address: Optional[str] = Field(default=None, max_length=400)
    agency_pec: Optional[str] = Field(default=None, max_length=200)
    vendor_name: Optional[str] = Field(default=None, max_length=200)
    contract_ref: Optional[str] = Field(default=None, max_length=100)
    domain: Optional[str] = Field(default=None, max_length=253)


class KitEmailRequest(BaseModel):
    """Request to receive the full 4-PDF kit by email (lead capture)."""
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    agency: Optional[str] = Field(default=None, max_length=200)
    consent: bool = Field(default=False)
    source: str = Field(default="landing", max_length=40)
    # Optional pre-fill data — the same shape as KitContext
    context: Optional[KitContext] = None


# ------------------ Endpoints ------------------

@router.get("/templates")
async def list_available_templates() -> dict:
    """List the 4 available templates with their metadata."""
    return {"items": list_templates(), "count": len(TEMPLATES)}


@router.post("/download/{slug}")
async def download_single(slug: str, ctx: KitContext, request: Request) -> Response:
    """Generate and return one filled PDF."""
    if slug not in TEMPLATES:
        raise HTTPException(status_code=404, detail="template_not_found")
    ip = _extract_ip(request)
    await _check_rate_limit(ip, "download_single")
    pdf_bytes = render_pdf(slug, ctx.model_dump())
    await _log_event("download_single", slug, ip, ctx.model_dump())
    filename = f"omnia_legal_{slug}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/kit")
async def download_full_kit(payload: KitEmailRequest, request: Request) -> Response:
    """Generate the full 4-PDF ZIP + persist lead. Consent required (GDPR)."""
    if not payload.consent:
        raise HTTPException(status_code=400, detail="consent_required")
    ip = _extract_ip(request)
    await _check_rate_limit(ip, "download_kit")

    ctx = (payload.context or KitContext()).model_dump()
    zip_bytes = render_kit_zip(ctx)

    # Persist lead with same shape as domain_leads (for unified analytics)
    db = Database.get()
    now = datetime.now(timezone.utc)
    lead = {
        "id": str(uuid4()), "email": payload.email.lower(),
        "name": payload.name.strip(),
        "agency": (payload.agency or "").strip() or None,
        "source": payload.source,
        "consent_at": now.isoformat(),
        "created_at": now.isoformat(),
        "status": "new", "kit_type": "domain_sovereignty",
        "context_has_domain": bool(ctx.get("domain")),
    }
    await db.legal_kit_leads.insert_one(lead)
    await _log_event("download_kit", None, ip, ctx)

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="omnia_legal_kit.zip"',
            "Cache-Control": "no-store",
        },
    )


# ------------------ Helpers ------------------

def _extract_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for") or ""
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""
