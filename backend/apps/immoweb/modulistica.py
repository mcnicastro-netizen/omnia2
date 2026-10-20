"""OMNIA — Modulistica CRM (M5.S7) + e-sign (M5.S8).

Endpoints under /api/app/modulistica:
  GET    /templates
  GET    /documents
  POST   /documents/generate
  GET    /documents/{id}
  GET    /documents/{id}/download
  POST   /documents/{id}/send-sign
  POST   /documents/{id}/sync-esign
  POST   /documents/{id}/mark-signed   (mock / manual helper)
  POST   /esign/webhook                (YouTrust — no auth, HMAC)
  GET    /esign/status

PDF branding: hybrid/turnkey show OMNIA footer note; plan_type=whitelabel omits it
(agency brand only — D-041). Same templates + e-sign for both.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, EmailStr, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import arequire_agency
from shared.db.connection import Database
from shared.modulistica.catalog import TEMPLATES, list_templates, get_template
from shared.modulistica.pdf import render_modulistica_pdf
from shared.modulistica.esign import (
    get_esign_provider,
    MockESignProvider,
    YousignProvider,
    verify_yousign_webhook_signature,
)
from shared.storage import put_object, get_object, ObjStoreError

logger = logging.getLogger("omnia.modulistica")
router = APIRouter(prefix="/modulistica", tags=["modulistica"])


class GenerateBody(BaseModel):
    slug: str = Field(min_length=2, max_length=60)
    property_id: Optional[str] = None
    client_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    title: Optional[str] = Field(default=None, max_length=200)


class SignerIn(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    role: Optional[str] = None  # buyer|seller|agency|client|…


class SendSignBody(BaseModel):
    signers: List[SignerIn] = Field(min_length=1, max_length=10)


def _strip(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "_id"}


async def _load_agency(db, agency_id: str) -> dict:
    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0})
    if not agency:
        raise HTTPException(404, "Agenzia non trovata")
    return agency


def _branding_of(agency: dict) -> Dict[str, Any]:
    b = agency.get("branding") or {}
    return {
        "logo_url": b.get("logo_url"),
        "primary_color": b.get("primary_color") or "#0B1E3F",
        "accent_color": b.get("accent_color") or "#1F6B5C",
        "tagline": b.get("tagline"),
        "display_name": agency.get("display_name") or agency.get("name"),
    }


async def _autofill_context(
    db, agency: dict, property_id: Optional[str], client_id: Optional[str], extra: Dict[str, Any]
) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {}
    fiscal = agency.get("fiscal") or {}
    contact = agency.get("contact") or {}
    address = agency.get("address") or {}
    addr_line = ", ".join(
        x for x in [
            address.get("street"),
            address.get("postal_code"),
            address.get("city"),
            address.get("province"),
        ] if x
    )
    ctx.update({
        "agency_name": fiscal.get("legal_name") or agency.get("display_name") or agency.get("name"),
        "agency_piva": fiscal.get("vat_number") or "",
        "agency_address": addr_line,
        "agency_rea": fiscal.get("rea") or "",
        "agency_pec": contact.get("email") or "",
        "agency_email": contact.get("email") or "",
        "agency_phone": contact.get("phone") or "",
    })

    if property_id:
        prop = await db.properties.find_one(
            {"id": property_id, "agency_id": agency["id"]}, {"_id": 0}
        )
        if prop:
            loc = prop.get("location") or {}
            ctx.update({
                "property_address": loc.get("address") or prop.get("address") or prop.get("title") or "",
                "property_city": loc.get("city") or prop.get("city") or "",
                "property_type": prop.get("property_type") or "",
                "property_cadastral": prop.get("cadastral_ref") or prop.get("catasto") or "",
                "asking_price": str(prop.get("price") or ""),
                "sale_price": str(prop.get("price") or ""),
                "offer_price": str(prop.get("price") or ""),
                "rent_monthly": str(prop.get("price") or "") if prop.get("operation") in ("affitto", "rent") else "",
            })
            # seller from property owner fields if present
            owner = prop.get("owner") or {}
            if owner.get("name"):
                ctx.setdefault("seller_name", owner.get("name"))
                ctx.setdefault("landlord_name", owner.get("name"))
                ctx.setdefault("seller_cf", owner.get("fiscal_code") or "")
                ctx.setdefault("seller_address", owner.get("address") or "")
                ctx.setdefault("seller_email", owner.get("email") or "")
                ctx.setdefault("landlord_email", owner.get("email") or "")
                ctx.setdefault("seller_phone", owner.get("phone") or "")

    if client_id:
        client = await db.clients.find_one(
            {"id": client_id, "agency_id": agency["id"]}, {"_id": 0}
        )
        if client:
            full = f"{client.get('name', '')} {client.get('surname', '')}".strip()
            ctype = (client.get("client_type") or "").lower()
            email = client.get("email") or ""
            ctx.update({
                "client_name": full,
                "client_cf": client.get("fiscal_code") or client.get("cf") or "",
                "client_address": client.get("address") or "",
                "client_email": email,
                "buyer_email": email,
            })
            if ctype in ("buyer", "acquirente", "tenant", "conduttore"):
                ctx["buyer_name"] = full
                ctx["buyer_cf"] = ctx["client_cf"]
                ctx["buyer_address"] = ctx["client_address"]
            elif ctype in ("seller", "venditore", "landlord", "locatore"):
                ctx["seller_name"] = full
                ctx["landlord_name"] = full
                ctx["seller_cf"] = ctx["client_cf"]
                ctx["seller_address"] = ctx["client_address"]
                ctx["landlord_cf"] = ctx["client_cf"]
                ctx["landlord_address"] = ctx["client_address"]
                ctx["seller_email"] = email
                ctx["landlord_email"] = email
            else:
                ctx.setdefault("buyer_name", full)
                ctx.setdefault("buyer_cf", ctx["client_cf"])
                ctx.setdefault("buyer_address", ctx["client_address"])

    # Defaults for common optional fields
    ctx.setdefault("exclusive", "a titolo non esclusivo")
    ctx.setdefault("duration_months", "6")
    ctx.setdefault("commission_pct", "3")
    ctx.setdefault("commission_months", "1")
    ctx.setdefault("validity_days", "15")
    ctx.setdefault("deposit_amount", "")
    ctx.setdefault("purpose", "vendita / locazione dell'unità")
    ctx.setdefault("dpo_email", ctx.get("agency_email") or "")
    ctx.setdefault("pep_declared", "No")
    ctx.setdefault("funds_origin", "")
    ctx.setdefault("operation_type", "mediazione immobiliare")
    ctx.setdefault("client_doc_type", "CI")
    ctx.setdefault("client_doc_number", "")
    ctx.setdefault("client_doc_issuer", "")
    ctx.setdefault("client_doc_expiry", "")

    ctx.update({k: v for k, v in (extra or {}).items() if v is not None and v != ""})
    # Normalize None → "" for stable PDF + API payloads
    for k, v in list(ctx.items()):
        if v is None:
            ctx[k] = ""
    return ctx


@router.get("/templates")
async def get_templates(user: dict = Depends(get_current_user)):
    await arequire_agency(user)
    return {"items": list_templates(), "total": len(TEMPLATES)}


@router.get("/esign/status")
async def esign_status(user: dict = Depends(get_current_user)):
    await arequire_agency(user)
    provider = get_esign_provider()
    import os
    whsec = bool((os.environ.get("YOUSIGN_WEBHOOK_SECRET") or "").strip())
    return {
        "provider": provider.name,
        "ready": True,
        "webhook_configured": whsec if provider.name == "yousign" else provider.name == "mock",
        "note": (
            "Mock: demo locale senza account paid."
            if provider.name == "mock"
            else (
                f"Provider reale attivo: {provider.name}"
                + (" · webhook OK" if whsec else " · webhook secret assente (usa sync-esign)")
            )
        ),
        "branding": "hybrid_and_whitelabel",
    }


async def _store_signed_pdf(doc: dict, pdf_bytes: bytes) -> Optional[str]:
    """Persist signed PDF next to draft; return storage path or None."""
    if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
        return None
    agency_id = doc.get("agency_id") or "unknown"
    doc_id = doc.get("id") or uuid4().hex
    path = f"omnia/modulistica/{agency_id}/{doc_id}.signed.pdf"
    try:
        put_object(path, pdf_bytes, "application/pdf")
        return path
    except ObjStoreError as e:
        logger.warning("signed pdf store failed: %s", e)
        return None


async def _mark_document_signed(
    db,
    doc: dict,
    *,
    message: str,
    event_id: Optional[str] = None,
    signed_pdf: Optional[bytes] = None,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    esign = dict(doc.get("esign") or {})
    esign["status"] = "signed"
    esign["message"] = message
    esign["updated_at"] = now
    if event_id:
        esign["last_event_id"] = event_id
    updates: Dict[str, Any] = {
        "esign": esign,
        "status": "signed",
        "updated_at": now,
        "signed_at": now,
    }
    if signed_pdf:
        path = await _store_signed_pdf(doc, signed_pdf)
        if path:
            updates["signed_storage_path"] = path
            esign["signed_storage_path"] = path
            updates["esign"] = esign
    await db.modulistica_documents.update_one(
        {"id": doc["id"]},
        {"$set": updates},
    )
    return {**doc, **updates}


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    property_id: Optional[str] = None,
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    agency_id = await arequire_agency(user)
    db = Database.get()
    q: Dict[str, Any] = {"agency_id": agency_id}
    if property_id:
        q["property_id"] = property_id
    if client_id:
        q["client_id"] = client_id
    if status:
        q["status"] = status
    total = await db.modulistica_documents.count_documents(q)
    docs = await (
        db.modulistica_documents.find(q, {"_id": 0, "context": 0})
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list(page_size)
    )
    return {"items": docs, "total": total, "page": page, "page_size": page_size}


@router.post("/documents/generate", status_code=201)
async def generate_document(
    body: GenerateBody,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin", "branch_admin", "group_admin")),
):
    if body.slug not in TEMPLATES:
        raise HTTPException(404, "template_not_found")
    agency_id = await arequire_agency(user)
    db = Database.get()
    agency = await _load_agency(db, agency_id)
    ctx = await _autofill_context(db, agency, body.property_id, body.client_id, body.context)
    branding = _branding_of(agency)
    plan_type = agency.get("plan_type") or "hybrid"

    try:
        pdf = render_modulistica_pdf(
            body.slug, ctx, branding=branding, plan_type=plan_type
        )
    except Exception as e:
        logger.exception("PDF render failed")
        raise HTTPException(500, f"pdf_render_failed: {e}") from e

    doc_id = str(uuid4())
    storage_path = f"omnia/modulistica/{agency_id}/{doc_id}.pdf"
    try:
        put_object(storage_path, pdf, "application/pdf")
    except ObjStoreError as e:
        raise HTTPException(503, f"storage_unavailable: {e}") from e

    tpl = get_template(body.slug)
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": doc_id,
        "agency_id": agency_id,
        "slug": body.slug,
        "title": body.title or (tpl["name"] if tpl else body.slug),
        "category": tpl["category"] if tpl else "altro",
        "property_id": body.property_id,
        "client_id": body.client_id,
        "status": "draft",  # draft | sent | signed | void
        "storage_path": storage_path,
        "context": ctx,
        "esign_policy": (tpl or {}).get("esign") or "optional",
        "expected_signers": list((tpl or {}).get("signers") or []),
        "branding_snapshot": {
            "primary_color": branding["primary_color"],
            "accent_color": branding["accent_color"],
            "display_name": branding["display_name"],
            "plan_type": plan_type,
        },
        "esign": None,
        "created_by": user.get("id"),
        "created_at": now,
        "updated_at": now,
    }
    await db.modulistica_documents.insert_one(record)
    return _strip({**record, "context": {k: ctx.get(k) for k in (tpl["fields"] if tpl else [])}})


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, user: dict = Depends(get_current_user)):
    agency_id = await arequire_agency(user)
    db = Database.get()
    doc = await db.modulistica_documents.find_one(
        {"id": doc_id, "agency_id": agency_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(404, "Documento non trovato")
    return doc


@router.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: str,
    signed: bool = Query(False, description="Preferisci PDF firmato se disponibile"),
    user: dict = Depends(get_current_user),
):
    agency_id = await arequire_agency(user)
    db = Database.get()
    doc = await db.modulistica_documents.find_one(
        {"id": doc_id, "agency_id": agency_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(404, "Documento non trovato")
    prefer_signed = signed or doc.get("status") == "signed"
    path = None
    if prefer_signed:
        path = doc.get("signed_storage_path") or (doc.get("esign") or {}).get("signed_storage_path")
    path = path or doc.get("storage_path")
    try:
        data, _mime = get_object(path)
    except ObjStoreError as e:
        raise HTTPException(404, f"file_missing: {e}") from e
    suffix = "firmato" if path and path.endswith(".signed.pdf") else "bozza"
    filename = f"{doc.get('slug', 'documento')}_{doc_id[:8]}_{suffix}.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/documents/{doc_id}/send-sign")
async def send_for_signature(
    doc_id: str,
    body: SendSignBody,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin", "branch_admin", "group_admin")),
):
    agency_id = await arequire_agency(user)
    db = Database.get()
    doc = await db.modulistica_documents.find_one(
        {"id": doc_id, "agency_id": agency_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(404, "Documento non trovato")
    tpl = get_template(doc.get("slug") or "")
    policy = doc.get("esign_policy") or (tpl or {}).get("esign") or "optional"
    if policy == "none":
        raise HTTPException(
            400,
            "Questo template è solo PDF/comunicazione: non si invia in firma elettronica.",
        )
    expected = doc.get("expected_signers") or list((tpl or {}).get("signers") or [])
    if expected and len(body.signers) < len(expected):
        raise HTTPException(
            400,
            f"Servono {len(expected)} firmatari ({', '.join(expected)}), "
            f"ne sono stati inviati {len(body.signers)}.",
        )
    try:
        pdf_bytes, _ = get_object(doc["storage_path"])
    except ObjStoreError as e:
        raise HTTPException(404, f"file_missing: {e}") from e

    provider = get_esign_provider()
    signers = [s.model_dump() for s in body.signers]
    # Fill role from template order when client omits it
    for i, s in enumerate(signers):
        if not s.get("role") and i < len(expected):
            s["role"] = expected[i]
    result = await provider.create_signature_request(
        pdf_bytes=pdf_bytes,
        filename=f"{doc.get('slug', 'doc')}.pdf",
        document_name=doc.get("title") or doc.get("slug") or "Documento OMNIA",
        signers=signers,
    )
    now = datetime.now(timezone.utc).isoformat()
    esign_meta = {
        "provider": result.provider,
        "external_id": result.external_id,
        "status": result.status,
        "sign_url": result.sign_url,
        "message": result.message,
        "signers": signers,
        "updated_at": now,
    }
    new_status = "sent" if result.ok else doc.get("status", "draft")
    await db.modulistica_documents.update_one(
        {"id": doc_id, "agency_id": agency_id},
        {"$set": {"esign": esign_meta, "status": new_status, "updated_at": now}},
    )
    if not result.ok:
        raise HTTPException(502, result.message or "esign_failed")
    return {"ok": True, "document_id": doc_id, "esign": esign_meta}


@router.post("/documents/{doc_id}/sync-esign")
async def sync_esign_status(
    doc_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin", "branch_admin", "group_admin")),
):
    """Poll YouTrust status; if done, download signed PDF into CRM storage."""
    agency_id = await arequire_agency(user)
    db = Database.get()
    doc = await db.modulistica_documents.find_one(
        {"id": doc_id, "agency_id": agency_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(404, "Documento non trovato")
    esign = doc.get("esign") or {}
    external_id = esign.get("external_id") or ""
    if not external_id:
        raise HTTPException(400, "Nessuna richiesta firma collegata a questo documento.")
    provider = get_esign_provider()
    if not isinstance(provider, (YousignProvider, MockESignProvider)):
        raise HTTPException(501, "sync_esign non supportato per questo provider")

    if isinstance(provider, MockESignProvider):
        updated = await _mark_document_signed(
            db, doc, message="Firmato (mock sync).",
        )
        return {"ok": True, "status": "signed", "esign": updated.get("esign"), "downloaded": False}

    # Already signed but missing PDF — retry download
    if doc.get("status") == "signed" and not doc.get("signed_storage_path"):
        if isinstance(provider, YousignProvider):
            pdf = await provider.download_completed_documents(external_id)
            if pdf:
                path = await _store_signed_pdf(doc, pdf)
                if path:
                    esign = {**(doc.get("esign") or {}), "signed_storage_path": path}
                    await db.modulistica_documents.update_one(
                        {"id": doc_id, "agency_id": agency_id},
                        {"$set": {"signed_storage_path": path, "esign": esign}},
                    )
                    return {
                        "ok": True,
                        "status": "signed",
                        "esign": esign,
                        "downloaded": True,
                        "signed_storage_path": path,
                    }
        return {
            "ok": True,
            "status": "signed",
            "esign": doc.get("esign"),
            "downloaded": False,
            "signed_storage_path": doc.get("signed_storage_path"),
        }

    status, raw = await provider.fetch_signature_status(external_id)
    now = datetime.now(timezone.utc).isoformat()
    if status == "signed":
        pdf = await provider.download_completed_documents(external_id)
        updated = await _mark_document_signed(
            db,
            doc,
            message="Firma YouTrust completata (sync).",
            signed_pdf=pdf,
        )
        return {
            "ok": True,
            "status": "signed",
            "esign": updated.get("esign"),
            "downloaded": bool(pdf),
            "signed_storage_path": updated.get("signed_storage_path"),
        }
    if status == "void":
        esign = {**esign, "status": "void", "message": "Richiesta firma annullata/scaduta/rifiutata.", "updated_at": now, "raw_status": (raw or {}).get("status")}
        await db.modulistica_documents.update_one(
            {"id": doc_id, "agency_id": agency_id},
            {"$set": {"esign": esign, "status": "void", "updated_at": now}},
        )
        return {"ok": True, "status": "void", "esign": esign, "downloaded": False}
    esign = {**esign, "status": "sent", "updated_at": now, "raw_status": (raw or {}).get("status")}
    await db.modulistica_documents.update_one(
        {"id": doc_id, "agency_id": agency_id},
        {"$set": {"esign": esign, "updated_at": now}},
    )
    return {"ok": True, "status": "sent", "esign": esign, "downloaded": False}


@router.post("/documents/{doc_id}/mark-signed")
async def mark_signed(
    doc_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "branch_admin", "group_admin")),
):
    """Complete mock signature / manual confirmation (fallback se webhook assente)."""
    agency_id = await arequire_agency(user)
    db = Database.get()
    doc = await db.modulistica_documents.find_one(
        {"id": doc_id, "agency_id": agency_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(404, "Documento non trovato")
    provider = get_esign_provider()
    esign = doc.get("esign") or {}
    signed_pdf = None
    message = "Contrassegnato come firmato."
    if isinstance(provider, MockESignProvider) and esign.get("external_id"):
        result = await provider.mark_signed(esign["external_id"])
        message = result.message
    elif isinstance(provider, YousignProvider) and esign.get("external_id"):
        st, _ = await provider.fetch_signature_status(esign["external_id"])
        if st == "signed":
            signed_pdf = await provider.download_completed_documents(esign["external_id"])
            message = "Firma YouTrust completata."
        else:
            message = "Contrassegnato come firmato (manuale — YouTrust non ancora done)."
    updated = await _mark_document_signed(db, doc, message=message, signed_pdf=signed_pdf)
    return {
        "ok": True,
        "status": "signed",
        "esign": updated.get("esign"),
        "downloaded": bool(signed_pdf),
    }


@router.post("/esign/webhook")
async def yousign_esign_webhook(request: Request):
    """YouTrust webhook: signature_request.done → status signed + PDF firmato.

    Auth: HMAC `x-yousign-signature-256` with YOUSIGN_WEBHOOK_SECRET (required in prod).
    Idempotent on event_id.
    """
    raw = await request.body()
    sig = (
        request.headers.get("x-yousign-signature-256")
        or request.headers.get("X-Yousign-Signature-256")
        or ""
    )
    import os
    secret = (os.environ.get("YOUSIGN_WEBHOOK_SECRET") or "").strip()
    if not secret:
        logger.error("YOUSIGN_WEBHOOK_SECRET missing — rejecting webhook")
        raise HTTPException(503, "webhook_secret_missing")
    if not verify_yousign_webhook_signature(raw, sig, secret):
        logger.warning("YouTrust webhook invalid signature")
        raise HTTPException(400, "invalid_signature")

    try:
        import json
        payload = json.loads(raw.decode("utf-8") or "{}")
    except Exception as e:
        raise HTTPException(400, f"invalid_json: {e}") from e

    event_name = (payload.get("event_name") or "").strip()
    event_id = (payload.get("event_id") or "").strip()
    data = payload.get("data") or {}
    sr = data.get("signature_request") or {}
    external_id = (sr.get("id") or "").strip()

    db = Database.get()
    # Dedup
    if event_id:
        seen = await db.modulistica_esign_events.find_one({"event_id": event_id}, {"_id": 0, "event_id": 1})
        if seen:
            return {"ok": True, "duplicate": True}

    if not external_id:
        return {"ok": True, "ignored": True, "reason": "no_signature_request_id"}

    doc = await db.modulistica_documents.find_one(
        {"esign.external_id": external_id}, {"_id": 0}
    )
    if not doc:
        logger.info("YouTrust webhook: unknown external_id=%s event=%s", external_id[:12], event_name)
        if event_id:
            await db.modulistica_esign_events.insert_one({
                "event_id": event_id,
                "event_name": event_name,
                "external_id": external_id,
                "handled": False,
                "reason": "document_not_found",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        return {"ok": True, "ignored": True, "reason": "document_not_found"}

    now = datetime.now(timezone.utc).isoformat()
    handled = False
    if event_name == "signature_request.done":
        provider = get_esign_provider()
        pdf = None
        if isinstance(provider, YousignProvider):
            pdf = await provider.download_completed_documents(external_id)
        await _mark_document_signed(
            db,
            doc,
            message="Firma YouTrust completata (webhook).",
            event_id=event_id or None,
            signed_pdf=pdf,
        )
        handled = True
    elif event_name in (
        "signature_request.declined",
        "signature_request.canceled",
        "signature_request.expired",
        "signature_request.rejected",
    ):
        esign = dict(doc.get("esign") or {})
        esign.update({
            "status": "void",
            "message": f"YouTrust: {event_name}",
            "updated_at": now,
            "last_event_id": event_id,
        })
        await db.modulistica_documents.update_one(
            {"id": doc["id"]},
            {"$set": {"esign": esign, "status": "void", "updated_at": now}},
        )
        handled = True

    if event_id:
        await db.modulistica_esign_events.insert_one({
            "event_id": event_id,
            "event_name": event_name,
            "external_id": external_id,
            "document_id": doc.get("id"),
            "handled": handled,
            "created_at": now,
        })
    return {"ok": True, "handled": handled, "event_name": event_name, "document_id": doc.get("id")}
