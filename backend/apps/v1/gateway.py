"""OMNIA — Public v1 API Gateway (M2.5.2 Track B, D-041).

Endpoints under `/api/v1/*` — authenticated via Bearer API key (no cookie/JWT).
Every call debits credits from the key's wallet and is logged to `api_usage_log`.

Endpoints (v1):
    POST /api/v1/valuator            — property valuation UNI 10750 (5 credits)
    POST /api/v1/mortgages/compare   — mortgage comparison (1 credit)
    POST /api/v1/legal/ask           — HAL Legal one-shot Q&A (3 credits)
    GET  /api/v1/feed/properties     — export the agency inventory (free)
    GET  /api/v1/me                  — inspect the API key + balance (free)
    GET  /api/v1/health              — no-auth ping

For the async Virtual Staging pipeline (~15 credits), see /api/v1/staging/*
in M2.5.3 (widget-friendly) — placeholder 501 in this MVP.
"""
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from shared.db.connection import Database
from shared.auth.api_key import make_key_dep, charge_and_log, CREDIT_COSTS

# Reuse the existing business models & handlers where possible
from apps.immocloud.valuator import (
    estimate_value as _valuator_run,
    ValuationPayload,
)
from apps.immocloud.mutui import (
    compare_mortgages as _mutui_compare_run,
    CompareBody,
)

# HAL Legal — we call the LLM helper directly, no session persistence for v1
from apps.immoweb.al_legal.router import _call_llm as _legal_call_llm

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["v1"])


# ---------------- HEALTH ----------------

@router.get("/health")
async def v1_health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "api_version": "v1",
        "credit_costs": CREDIT_COSTS,
        "docs_hint": "Authenticate with header 'Authorization: Bearer omk_live_...'",
    }


# ---------------- ME (inspect key) ----------------

@router.get("/me")
async def v1_me(request: Request, key=Depends(make_key_dep("feed_properties"))) -> Dict[str, Any]:
    """Return the calling API key metadata + credit balance."""
    try:
        return {
            "id": key["id"],
            "name": key["name"],
            "key_prefix": key["key_prefix"],
            "agency_id": key["agency_id"],
            "group_id": key.get("group_id"),
            "partner_id": key.get("partner_id"),
            "credits_balance": key.get("credits_balance", 0),
            "credits_spent": key.get("credits_spent", 0),
            "is_active": key.get("is_active", True),
        }
    finally:
        await charge_and_log(request, status_code=200)


# ---------------- VALUATOR ----------------

@router.post("/valuator")
async def v1_valuator(
    payload: ValuationPayload,
    request: Request,
    key=Depends(make_key_dep("valuator")),
) -> Dict[str, Any]:
    """UNI 10750 valuation (5 credits). Wraps `/api/cloud/valuator`."""
    try:
        result = await _valuator_run(payload)
        # Track B: strip lead capture side-effects (no `valuation_leads` row here)
        # The wrapped handler already inserts into DB if payload has email/name;
        # partner integrations typically don't want that. Leave that behavior
        # opt-in for now — the caller controls it by omitting email/name.
        await charge_and_log(request, status_code=200)
        return {"data": result, "credits_charged": request.state.api_cost}
    except HTTPException as e:
        await charge_and_log(request, status_code=e.status_code, error_code=str(e.detail)[:60])
        raise
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_valuator failed")
        raise HTTPException(status_code=500, detail="internal_error")


# ---------------- MORTGAGES ----------------

@router.post("/mortgages/compare")
async def v1_mortgages_compare(
    body: CompareBody,
    request: Request,
    key=Depends(make_key_dep("mortgages_compare")),
) -> Dict[str, Any]:
    """Compare mortgage offers (1 credit). Wraps `/api/cloud/mutui/compare`."""
    try:
        result = await _mutui_compare_run(body)
        await charge_and_log(request, status_code=200)
        return {"data": result, "credits_charged": request.state.api_cost}
    except HTTPException as e:
        await charge_and_log(request, status_code=e.status_code, error_code=str(e.detail)[:60])
        raise
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_mortgages_compare failed")
        raise HTTPException(status_code=500, detail="internal_error")


# ---------------- HAL LEGAL (one-shot Q&A) ----------------

class LegalAskBody(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    lang: str = Field(default="it", pattern="^(it|en|es)$")


@router.post("/legal/ask")
async def v1_legal_ask(
    body: LegalAskBody,
    request: Request,
    key=Depends(make_key_dep("legal_ask")),
) -> Dict[str, Any]:
    """One-shot legal Q&A (3 credits). Reuses HAL Legal LLM stack (no session)."""
    try:
        system_prompt = (
            "Sei HAL Legal, assistente informativo giuridico-notarile italiano. "
            "Rispondi in modo sintetico (max 400 parole), cita norme e fonti quando possibile, "
            "e ricorda che le tue risposte sono orientative e non sostituiscono un parere di notaio/avvocato. "
            f"Rispondi in lingua: {body.lang}."
        )
        answer = await _legal_call_llm(
            system_prompt=system_prompt,
            user_msg=body.question,
            session_id=f"apikey_{key['id'][:8]}",
        )
        await charge_and_log(request, status_code=200)
        return {
            "data": {
                "question": body.question,
                "answer": answer,
                "disclaimer": "Informazioni orientative. Non sostituisce parere legale (L.247/2012).",
            },
            "credits_charged": request.state.api_cost,
        }
    except HTTPException as e:
        await charge_and_log(request, status_code=e.status_code, error_code=str(e.detail)[:60])
        raise
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_legal_ask failed")
        raise HTTPException(status_code=500, detail="internal_error")


# ---------------- FEED / PROPERTIES ----------------

@router.get("/feed/properties")
async def v1_feed_properties(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    status: str = "active",
    key=Depends(make_key_dep("feed_properties")),
) -> Dict[str, Any]:
    """
    Export the agency's inventory as JSON (free). For XML/OSF feed use
    the existing public `/api/feed/{slug}.xml` (no API key required, SEO-friendly).
    """
    try:
        db = Database.get()
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        flt = {"agency_id": key["agency_id"]}
        if status and status != "all":
            flt["status"] = status
        cursor = (
            db.properties.find(flt, {"_id": 0, "photos": 0})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        total = await db.properties.count_documents(flt)
        await charge_and_log(request, status_code=200)
        return {
            "data": {"items": items, "total": total, "limit": limit, "offset": offset},
            "credits_charged": 0,
        }
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_feed_properties failed")
        raise HTTPException(status_code=500, detail="internal_error")


# ---------------- FEED INBOUND (ingest properties from external CRM, D-041) ----------------


class FeedPropertyItem(BaseModel):
    """Minimal payload accepted from external CRMs.

    Only the OMNIA-canonical fields are surfaced here; unknown fields are
    silently dropped to keep the ingest tolerant to schema drift.
    """
    external_id: str = Field(min_length=1, max_length=120)
    title: Optional[str] = Field(default=None, max_length=300)
    description: Optional[str] = Field(default=None, max_length=5000)
    property_type: Optional[str] = Field(default=None, max_length=40)
    operation: Optional[str] = Field(default=None, pattern="^(sale|rent)$")
    price: Optional[float] = None
    rent_monthly: Optional[float] = None
    surface_sqm: Optional[float] = None
    rooms: Optional[int] = None
    bathrooms: Optional[int] = None
    city: Optional[str] = Field(default=None, max_length=120)
    province: Optional[str] = Field(default=None, max_length=10)
    address: Optional[str] = Field(default=None, max_length=300)
    energy_class: Optional[str] = Field(default=None, max_length=5)
    photo_urls: Optional[list[str]] = Field(default=None, max_length=30)
    status: Optional[str] = Field(default="active", pattern="^(active|reserved|sold|rented|withdrawn|draft)$")


class FeedIngestBody(BaseModel):
    items: list[FeedPropertyItem] = Field(min_length=1, max_length=500)
    mode: str = Field(default="upsert", pattern="^(upsert|append)$")


@router.post("/feed/properties", status_code=201)
async def v1_feed_properties_ingest(
    body: FeedIngestBody,
    request: Request,
    key=Depends(make_key_dep("feed_properties_ingest")),
) -> Dict[str, Any]:
    """
    **Feed bidirezionale (D-041, Track B modalità 3)** — INGEST endpoint.

    Track B agencies (structured, keeping their own CRM) push their inventory
    into OMNIA via this endpoint. Idempotent per `external_id` when `mode=upsert`.
    Photos are stored as external URLs — no base64 payload accepted here to
    keep the ingest lightweight (D-041 wedge: zero-friction migration).
    """
    try:
        from uuid import uuid4
        db = Database.get()
        now = _now_iso()
        inserted, updated, skipped = 0, 0, 0

        for item in body.items:
            data = item.model_dump(exclude_none=True)
            external_id = data.pop("external_id")
            photos_urls = data.pop("photo_urls", None)
            if photos_urls:
                data["photos"] = [
                    {"id": str(uuid4()), "url": url, "order": i, "is_cover": i == 0}
                    for i, url in enumerate(photos_urls) if isinstance(url, str) and url.startswith("http")
                ]

            base_doc = {
                **data,
                "agency_id": key["agency_id"],
                "external_id": external_id,
                "ingested_via": "api_feed",
                "ingested_api_key_id": key["id"],
                "updated_at": now,
            }

            if body.mode == "upsert":
                existing = await db.properties.find_one(
                    {"agency_id": key["agency_id"], "external_id": external_id}
                )
                if existing:
                    await db.properties.update_one(
                        {"id": existing["id"]}, {"$set": base_doc}
                    )
                    updated += 1
                    continue
            base_doc["id"] = str(uuid4())
            base_doc["created_at"] = now
            base_doc.setdefault("status", "active")
            await db.properties.insert_one(base_doc)
            inserted += 1

        await charge_and_log(request, status_code=201)
        return {
            "data": {
                "inserted": inserted,
                "updated": updated,
                "skipped": skipped,
                "total_received": len(body.items),
            },
            "credits_charged": 0,
        }
    except HTTPException as e:
        await charge_and_log(request, status_code=e.status_code, error_code=str(e.detail)[:60])
        raise
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_feed_properties_ingest failed")
        raise HTTPException(status_code=500, detail="internal_error")


# ---------------- LEADS EXPORT (Track B closes the loop, D-041) ----------------


@router.get("/leads/export")
async def v1_leads_export(
    request: Request,
    since: Optional[str] = None,
    limit: int = 100,
    key=Depends(make_key_dep("leads_export")),
) -> Dict[str, Any]:
    """
    **Feed bidirezionale (D-041, Track B modalità 3)** — LEAD EXPORT endpoint.

    Track B agencies pull leads generated by their embedded OMNIA widgets
    (Valuator, Mortgages, Legal) back into their own CRM.
    Filters leads by `key.agency_id` (multi-tenant safe).
    `since` accepts ISO datetime; only leads with `created_at >= since` are returned.
    """
    try:
        db = Database.get()
        limit = max(1, min(limit, 500))
        flt: Dict[str, Any] = {"agency_id": key["agency_id"]}
        if since:
            flt["created_at"] = {"$gte": since}
        cursor = (
            db.leads.find(flt, {"_id": 0})
            .sort("created_at", -1)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        total = await db.leads.count_documents(flt)
        await charge_and_log(request, status_code=200)
        return {
            "data": {
                "items": items,
                "total": total,
                "limit": limit,
                "since": since,
            },
            "credits_charged": 0,
        }
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_leads_export failed")
        raise HTTPException(status_code=500, detail="internal_error")


# ---------------- WIDGET LEAD CAPTURE (M2.5.3) ----------------

class WidgetLeadBody(BaseModel):
    widget: str = Field(pattern="^(valuator|mortgages|legal|staging)$")
    name: Optional[str] = Field(default=None, max_length=120)
    email: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=40)
    message: Optional[str] = Field(default=None, max_length=1000)
    context: Optional[Dict[str, Any]] = None  # e.g. valuation result, mortgage details
    consent: bool = False
    source_url: Optional[str] = Field(default=None, max_length=500)


@router.post("/widgets/lead")
async def v1_widget_lead(
    body: WidgetLeadBody,
    request: Request,
    key=Depends(make_key_dep("widget_lead")),
) -> Dict[str, Any]:
    """
    Capture a lead from a Track B widget into the owning agency's CRM.
    Cost: 0 credits (free — monetization via feature access, not lead ingestion).
    """
    try:
        if not (body.email or body.phone):
            raise HTTPException(status_code=400, detail="email_or_phone_required")
        if not body.consent:
            raise HTTPException(status_code=400, detail="consent_required")

        db = Database.get()
        now_iso = _now_iso()
        lead_id = os.urandom(12).hex()
        lead_doc = {
            "id": lead_id,
            "agency_id": key["agency_id"],
            "group_id": key.get("group_id"),
            "source": f"widget_{body.widget}",
            "source_url": body.source_url,
            "partner_id": key.get("partner_id"),
            "api_key_id": key["id"],
            "name": body.name,
            "email": body.email,
            "phone": body.phone,
            "message": body.message,
            "context": body.context or {},
            "status": "new",
            "score": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        await db.leads.insert_one(lead_doc)
        await charge_and_log(request, status_code=201)
        return {"data": {"id": lead_id, "status": "new"}, "credits_charged": 0}
    except HTTPException as e:
        await charge_and_log(request, status_code=e.status_code, error_code=str(e.detail)[:60])
        raise
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_widget_lead failed")
        raise HTTPException(status_code=500, detail="internal_error")


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ---------------- STAGING (placeholder) ----------------

@router.post("/staging/render")
async def v1_staging_render(request: Request,
                            key=Depends(make_key_dep("staging_render"))) -> Dict[str, Any]:
    """Reserved for M2.5.3 (widget-friendly async pipeline). Returns 501 for now."""
    await charge_and_log(request, status_code=501, error_code="not_implemented")
    raise HTTPException(
        status_code=501,
        detail="staging_via_api_available_in_m2_5_3",
    )


# ---------------- DOMAIN CHECK (M2.5.4b, D-054) ----------------

class DomainCheckV1Body(BaseModel):
    domain: str = Field(min_length=3, max_length=253)
    agency_name: Optional[str] = Field(default=None, max_length=200)


@router.post("/domain/check")
async def v1_domain_check(
    body: DomainCheckV1Body,
    request: Request,
    key=Depends(make_key_dep("domain_check")),
) -> Dict[str, Any]:
    """RDAP domain ownership check (1 credit). Same output as `/api/domain/check`
    but authenticated + billed. Useful for partner web agencies embedding the
    checker in their own sales flow with white-label branding."""
    try:
        from apps.marketing.domain_check import run_check
        result = await run_check(
            domain_raw=body.domain,
            agency_name=body.agency_name,
            source=f"apikey_{key.get('partner_id') or 'direct'}",
            client_ip=None,  # keep IP out of billed logs
        )
        await charge_and_log(request, status_code=200)
        return {"data": result, "credits_charged": request.state.api_cost}
    except HTTPException as e:
        await charge_and_log(request, status_code=e.status_code, error_code=str(e.detail)[:60])
        raise
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_domain_check failed")
        raise HTTPException(status_code=500, detail="internal_error")


# ---------------- LEGAL KIT (M2.5.4c, D-055) ----------------

class LegalRenderBody(BaseModel):
    slug: str = Field(min_length=3, max_length=50)
    context: Optional[Dict[str, Any]] = None


@router.post("/legal/render")
async def v1_legal_render(
    body: LegalRenderBody,
    request: Request,
    key=Depends(make_key_dep("legal_render")),
):
    """Generate a filled Legal Kit PDF (2 credits). Returns raw application/pdf."""
    try:
        from shared.legal_kit.templates import TEMPLATES
        from shared.legal_kit.pdf_generator import render_pdf
        if body.slug not in TEMPLATES:
            raise HTTPException(status_code=404, detail="template_not_found")
        pdf_bytes = render_pdf(body.slug, body.context or {})
        await charge_and_log(request, status_code=200)
        from fastapi.responses import Response as _Response
        return _Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="omnia_legal_{body.slug}.pdf"',
                "X-Credits-Charged": str(request.state.api_cost),
            },
        )
    except HTTPException as e:
        await charge_and_log(request, status_code=e.status_code, error_code=str(e.detail)[:60])
        raise
    except Exception as e:
        await charge_and_log(request, status_code=500, error_code=type(e).__name__)
        logger.exception("v1_legal_render failed")
        raise HTTPException(status_code=500, detail="internal_error")
