"""OMNIA ImmobilCloud — B2C contact / inquiry (MOVE-ONLY)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from shared.db.connection import Database
from apps.immocloud.portal_common import _base_filter

logger = logging.getLogger("omnia.immobilcloud")
router = APIRouter(tags=["immobilcloud"])

class PropertyContactPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    surname: Optional[str] = Field(default=None, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    message: str = Field(min_length=10, max_length=2000)
    gdpr_consent: bool = False
    visit_requested: bool = False  # optional checkbox "richiedi visita"


@router.post("/property/{pid}/contact")
async def public_property_contact(pid: str, payload: PropertyContactPayload, request: Request):
    """B2C contact form.

    Agency listings → CRM client + lead + agent/agency notify.
    Private listings → listing_inquiries + notify owner (no agency CRM).
    """
    from shared.security.rate_limit import enforce_ip_rate_limit
    await enforce_ip_rate_limit(request, bucket="cloud_contact", max_requests=20, window_seconds=3600)
    if not payload.gdpr_consent:
        raise HTTPException(status_code=400, detail="gdpr_consent_required")

    try:
        from shared.privacy.consent_log import log_consent
        fwd = request.headers.get("x-forwarded-for") or ""
        ip = (fwd.split(",")[0].strip() if fwd else None) or (
            request.client.host if request.client else None
        )
        await log_consent(
            action="property_contact_consent",
            email=str(payload.email),
            source="cloud.property.contact",
            ip=ip,
            meta={"property_id": pid, "visit_requested": bool(payload.visit_requested)},
        )
    except Exception:
        pass

    db = Database.get()
    prop = await db.properties.find_one(
        {"id": pid, **_base_filter()},
        {
            "_id": 0, "id": 1, "agency_id": 1, "title": 1,
            "is_private_listing": 1, "owner_user_id": 1, "owner": 1,
        },
    )
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")

    is_private = bool(prop.get("is_private_listing")) or prop.get("agency_id") == "_private_listings"
    if is_private:
        return await _private_listing_contact(db, prop, payload)

    agency_id = prop.get("agency_id")
    if not agency_id:
        raise HTTPException(status_code=409, detail="property_has_no_agency")

    now = datetime.now(timezone.utc).isoformat()

    # 1) Find or create client
    existing = await db.clients.find_one(
        {"agency_id": agency_id, "email": payload.email.lower()},
        {"_id": 0, "id": 1},
    )
    if existing:
        client_id = existing["id"]
        # Refresh updated_at + last source if reused
        await db.clients.update_one(
            {"id": client_id},
            {"$set": {"updated_at": now}, "$setOnInsert": {}},
        )
    else:
        client_id = str(uuid4())
        await db.clients.insert_one({
            "id": client_id,
            "agency_id": agency_id,
            "name": payload.name,
            "surname": payload.surname,
            "email": payload.email.lower(),
            "phone": payload.phone,
            "whatsapp": None,
            "fiscal_code": None,
            "client_type": "buyer",
            "status": "new",
            "source": "ImmobilCloud",
            "assigned_agent_id": None,
            "preferences": {},
            "notes": None,
            "gdpr_consent": True,
            "created_at": now,
            "updated_at": now,
        })

    # 2) Fetch listing agent OR fallback to agency email
    prop_full = await db.properties.find_one(
        {"id": pid},
        {"_id": 0, "listing_agent_id": 1},
    )
    notify_email = None
    notify_lang = "it"
    if prop_full and prop_full.get("listing_agent_id"):
        agent = await db.users.find_one(
            {"id": prop_full["listing_agent_id"]},
            {"_id": 0, "email": 1, "lang": 1,
             "notification_channels": 1, "notification_email_types": 1},
        )
        if agent and agent.get("email"):
            from shared.notifications.prefs import user_allows_email
            if user_allows_email(agent, "lead_notification"):
                notify_email = agent["email"]
                notify_lang = agent.get("lang") or "it"
    if not notify_email:
        agency_doc = await db.agencies.find_one(
            {"id": agency_id},
            {"_id": 0, "email": 1, "lang": 1},
        )
        if agency_doc and agency_doc.get("email"):
            notify_email = agency_doc["email"]
            notify_lang = agency_doc.get("lang") or "it"

    # 3) Create lead
    lead_id = str(uuid4())
    note_lines = [payload.message.strip()]
    if payload.visit_requested:
        note_lines.append("[richiesta visita immobile]")
    await db.leads.insert_one({
        "id": lead_id,
        "agency_id": agency_id,
        "client_id": client_id,
        "property_id": pid,
        "status": "new",
        "score": None,
        "notes": "\n".join(note_lines),
        "assigned_agent_id": None,
        "source": "ImmobilCloud",
        "created_at": now,
        "updated_at": now,
    })

    # D-089 — auto-crea Richiesta tipo A (interesse immobile)
    try:
        from apps.immoweb.client_requests_service import ensure_from_immobilcloud
        await ensure_from_immobilcloud(
            db,
            agency_id=agency_id,
            client_id=client_id,
            property_id=pid,
            lead_id=lead_id,
            notes="\n".join(note_lines),
            assigned_agent_id=(prop_full or {}).get("listing_agent_id"),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("client_request from ImmobilCloud failed: %s", e)

    # 4) Bump property lead counter + daily bucket (best-effort) — D-093 / A-029
    try:
        await db.properties.update_one({"id": pid}, {"$inc": {"lead_count": 1}})
        from apps.immocloud.listing_stats import bump_daily_stat
        await bump_daily_stat(db, pid, "lead")
    except Exception:
        pass

    # 5) Fire-and-forget email notification to agent (M3.S4.1)
    if notify_email:
        _schedule_lead_email(
            to=notify_email,
            lang=notify_lang,
            property_title=prop.get("title") or "Immobile",
            lead_name=f"{payload.name} {payload.surname or ''}".strip(),
            lead_email=payload.email,
            lead_phone=payload.phone,
            lead_message="\n".join(note_lines),
            agency_id=agency_id,
            property_id=pid,
        )

    # 6) A-017 — in-app inbox for listing agent + agency admins
    try:
        from shared.notifications.center import (
            TYPE_LEAD_NEW,
            notify_users,
            resolve_lead_recipients,
        )
        lead_name = f"{payload.name} {payload.surname or ''}".strip()
        prop_title = prop.get("title") or "Immobile"
        recipients = await resolve_lead_recipients(
            agency_id,
            (prop_full or {}).get("listing_agent_id"),
        )
        await notify_users(
            recipients,
            type=TYPE_LEAD_NEW,
            title=f"Nuovo lead · {prop_title}",
            body=f"{lead_name} ha contattato l'agenzia da ImmobilCloud.",
            link="/app/requests",
            agency_id=agency_id,
            meta={"lead_id": lead_id, "property_id": pid, "client_id": client_id},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("in-app lead notification failed: %s", e)

    logger.info("B2C contact: lead=%s client=%s property=%s agency=%s notify=%s",
                lead_id, client_id, pid, agency_id, notify_email or "—")
    return {"ok": True, "lead_id": lead_id, "client_id": client_id}


async def _private_listing_contact(db, prop: Dict[str, Any], payload: PropertyContactPayload) -> Dict[str, Any]:
    """Inquiry to a private seller — no agency CRM client/lead."""
    owner_user_id = prop.get("owner_user_id")
    if not owner_user_id:
        raise HTTPException(status_code=409, detail="private_listing_has_no_owner")

    owner_email = (prop.get("owner") or {}).get("email")
    owner_user = await db.users.find_one(
        {"id": owner_user_id},
        {"_id": 0, "email": 1, "lang": 1, "name": 1},
    )
    if not owner_email:
        owner_email = (owner_user or {}).get("email")
    if not owner_email:
        raise HTTPException(status_code=409, detail="private_seller_unreachable")

    now = datetime.now(timezone.utc).isoformat()
    inquiry_id = str(uuid4())
    note_lines = [payload.message.strip()]
    if payload.visit_requested:
        note_lines.append("[richiesta visita immobile]")
    visit_requested = bool(payload.visit_requested)
    doc = {
        "id": inquiry_id,
        "property_id": prop["id"],
        "owner_user_id": owner_user_id,
        "name": payload.name,
        "surname": payload.surname,
        "email": payload.email.lower(),
        "phone": payload.phone,
        "message": "\n".join(note_lines),
        "visit_requested": visit_requested,
        # D-138 Idealista+ inbox fields
        "visit_status": "requested" if visit_requested else "none",
        "archived": False,
        "read_at": None,
        "seller_note": "",
        "property_title": prop.get("title") or "Immobile",
        "property_city": prop.get("city"),
        "listing_code": prop.get("listing_code"),
        "gdpr_consent": True,
        "source": "ImmobilCloud",
        "created_at": now,
        "updated_at": now,
    }
    await db.listing_inquiries.insert_one(doc)

    try:
        await db.properties.update_one({"id": prop["id"]}, {"$inc": {"lead_count": 1}})
        from apps.immocloud.listing_stats import bump_daily_stat
        await bump_daily_stat(db, prop["id"], "lead")
    except Exception:
        pass

    notify_lang = (owner_user or {}).get("lang") or "it"
    from shared.public_base import get_public_base_url
    _lang = notify_lang if notify_lang in ("it", "en", "es") else "it"
    inbox_url = (
        f"{get_public_base_url()}/{_lang}/cloud/account/messages?id={inquiry_id}"
    )
    _schedule_lead_email(
        to=owner_email,
        lang=notify_lang,
        property_title=prop.get("title") or "Immobile",
        lead_name=f"{payload.name} {payload.surname or ''}".strip(),
        lead_email=payload.email,
        lead_phone=payload.phone,
        lead_message="\n".join(note_lines),
        agency_id="_private_listings",
        property_id=prop["id"],
        action_url=inbox_url,
    )

    try:
        from shared.notifications.center import TYPE_LISTING_INQUIRY, notify_users
        lead_name = f"{payload.name} {payload.surname or ''}".strip()
        prop_title = prop.get("title") or "Immobile"
        await notify_users(
            [owner_user_id],
            type=TYPE_LISTING_INQUIRY,
            title=f"Nuovo messaggio · {prop_title}",
            body=f"{lead_name} ti ha contattato da ImmobilCloud.",
            link=f"/cloud/account/messages?id={inquiry_id}",
            agency_id=None,
            meta={"inquiry_id": inquiry_id, "property_id": prop["id"]},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("in-app private inquiry notification failed: %s", e)

    logger.info(
        "B2C private inquiry: id=%s property=%s owner=%s notify=%s",
        inquiry_id, prop["id"], owner_user_id, owner_email,
    )
    return {"ok": True, "inquiry_id": inquiry_id, "kind": "private"}


def _schedule_lead_email(*, to: str, lang: str, property_title: str,
                        lead_name: str, lead_email: str,
                        lead_phone: Optional[str], lead_message: str,
                        agency_id: str, property_id: str,
                        action_url: Optional[str] = None) -> None:
    """Fire-and-forget Resend notification to listing agent / agency / private seller."""
    import asyncio
    from shared.email.client import send_email

    from shared.public_base import get_public_base_url
    base = get_public_base_url()
    crm_url = action_url or (
        f"{base}/{lang if lang in ('it', 'en', 'es') else 'it'}/app/properties/{property_id}"
    )
    phone_block = (
        f'<p style="margin:4px 0 0 0; font-size:14px; color:#0E1419;">📞 '
        f'<a href="tel:{lead_phone}" style="color:#0B1E3F;">{lead_phone}</a></p>'
        if lead_phone else ""
    )

    async def _task():
        # Retry with exponential back-off (1s, 3s, 10s). Log final failure.
        delays = [0, 1, 3, 10]
        last_exc: Optional[Exception] = None
        for attempt, delay in enumerate(delays, start=1):
            if delay:
                await asyncio.sleep(delay)
            try:
                await send_email(
                    to=to,
                    template="lead_notification",
                    lang=lang,
                    variables={
                        "property_title": property_title,
                        "lead_name": lead_name,
                        "lead_email": lead_email,
                        "lead_phone_block": phone_block,
                        "lead_message": lead_message,
                        "crm_url": crm_url,
                    },
                )
                if attempt > 1:
                    logger.info("lead email delivered on attempt %d to=%s", attempt, to)
                return
            except Exception as e:  # noqa: BLE001
                last_exc = e
                logger.warning("lead email attempt %d/%d failed: %s", attempt, len(delays), e)
        # All retries exhausted → durable log for manual replay
        logger.error("lead email PERMANENTLY FAILED to=%s agency=%s property=%s: %s",
                     to, agency_id, property_id, last_exc)

    try:
        asyncio.create_task(_task())
    except RuntimeError:
        pass
