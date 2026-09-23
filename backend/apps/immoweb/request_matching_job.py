"""OMNIA — Nightly request↔property matching digest (D-090).

AgestaNET-style: every night, for open requests with auto_match=True,
find new portfolio matches not yet notified and email the client (if GDPR)
and notify the listing agent / agency admins in-app.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shared.db.connection import Database
from apps.immoweb import client_requests_service as svc

logger = logging.getLogger("omnia.request_matching")

NOTIF_COLLECTION = "request_match_notifications"
MAX_PROPS_PER_EMAIL = 5
MAX_REQUESTS_PER_RUN = 500


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _already_notified(db, request_id: str, property_id: str) -> bool:
    hit = await db[NOTIF_COLLECTION].find_one(
        {"request_id": request_id, "property_id": property_id},
        {"_id": 1},
    )
    return bool(hit)


async def _mark_notified(
    db,
    *,
    agency_id: str,
    request_id: str,
    property_id: str,
    client_id: str,
    score: int,
    channel: str,
) -> None:
    await db[NOTIF_COLLECTION].update_one(
        {"request_id": request_id, "property_id": property_id},
        {"$set": {
            "id": str(uuid4()),
            "agency_id": agency_id,
            "request_id": request_id,
            "property_id": property_id,
            "client_id": client_id,
            "score": score,
            "channel": channel,
            "notified_at": _now(),
        }},
        upsert=True,
    )


def _format_price(v) -> str:
    if v is None:
        return "—"
    try:
        return f"€ {int(float(v)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(v)


def _matches_html(items: List[Dict[str, Any]]) -> str:
    rows = []
    for m in items[:MAX_PROPS_PER_EMAIL]:
        title = m.get("title") or m.get("reference_code") or m.get("property_id")
        city = m.get("city") or ""
        price = _format_price(m.get("price"))
        score = m.get("score")
        rows.append(
            f'<div style="padding:12px 0;border-bottom:1px solid #E5E2DC;">'
            f'<p style="margin:0;font-size:15px;font-weight:600;color:#0B1E3F;">{title}</p>'
            f'<p style="margin:4px 0 0;font-size:13px;color:#5C6470;">{city} · {price} · match {score}/100</p>'
            f"</div>"
        )
    return "".join(rows) or "<p>—</p>"


async def process_request(db, req: Dict[str, Any]) -> Dict[str, Any]:
    agency_id = req["agency_id"]
    result = await svc.match_request(db, agency_id, req)
    portfolio = result.get("portfolio_matches") or []
    # Nightly digest stays on portfolio (own inventory) — MLS fall-through is agent-driven
    fresh = []
    for m in portfolio:
        pid = m.get("property_id")
        if not pid:
            continue
        if await _already_notified(db, req["id"], pid):
            continue
        fresh.append(m)

    if not fresh:
        return {"request_id": req["id"], "new": 0, "emailed": False}

    client = await db.clients.find_one(
        {"id": req["client_id"]},
        {"_id": 0, "id": 1, "name": 1, "surname": 1, "email": 1, "gdpr_consent": 1, "lang": 1},
    )
    emailed = False
    to_email = (client or {}).get("email")
    if to_email and (client or {}).get("gdpr_consent"):
        try:
            from shared.email.client import send_email
            name = f"{(client or {}).get('name') or ''}".strip() or "Ciao"
            lang = ((client or {}).get("lang") or "it")[:2]
            await send_email(
                to=to_email,
                template="request_match_alert",
                lang=lang,
                vars={
                    "user_name": name,
                    "match_count": str(len(fresh)),
                    "request_title": req.get("title") or "la tua richiesta",
                    "matches_html": _matches_html(fresh),
                    "cta_url": "https://omniarealestateecosystem.it/it/cloud",
                },
            )
            emailed = True
        except Exception as e:  # noqa: BLE001
            logger.warning("request match email failed req=%s: %s", req.get("id"), e)

    # In-app notify agent / admins
    try:
        from shared.notifications.center import (
            TYPE_LEAD_NEW,
            notify_users,
            resolve_agency_owner_and_admins,
        )
        recipients = await resolve_agency_owner_and_admins(agency_id)
        if req.get("assigned_agent_id"):
            recipients = list({*recipients, req["assigned_agent_id"]})
        await notify_users(
            recipients,
            type=TYPE_LEAD_NEW,
            title=f"Match richieste · {len(fresh)} immobili",
            body=f"Nuovi match per «{req.get('title') or req.get('id')}».",
            link="/app/requests/" + req["id"],
            agency_id=agency_id,
            meta={"request_id": req["id"], "new_matches": len(fresh)},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("request match inbox failed: %s", e)

    channel = "email+inbox" if emailed else "inbox"
    for m in fresh:
        await _mark_notified(
            db,
            agency_id=agency_id,
            request_id=req["id"],
            property_id=m["property_id"],
            client_id=req["client_id"],
            score=int(m.get("score") or 0),
            channel=channel,
        )

    # Promote status if still open
    if req.get("status") == "open" and fresh:
        await db[svc.COLLECTION].update_one(
            {"id": req["id"]},
            {"$set": {"status": "matched", "updated_at": _now()}},
        )

    return {"request_id": req["id"], "new": len(fresh), "emailed": emailed}


async def run_all_request_matching(*, agency_id: Optional[str] = None) -> Dict[str, Any]:
    """Nightly job entrypoint. Optionally scope to one agency."""
    db = Database.get()
    await svc.ensure_indexes(db)
    await db[NOTIF_COLLECTION].create_index(
        [("request_id", 1), ("property_id", 1)], unique=True,
    )
    await db[NOTIF_COLLECTION].create_index([("agency_id", 1), ("notified_at", -1)])

    q: Dict[str, Any] = {
        "status": {"$in": ["open", "matched", "negotiating"]},
        "auto_match": {"$ne": False},
    }
    if agency_id:
        q["agency_id"] = agency_id

    reqs = await db[svc.COLLECTION].find(q, {"_id": 0}).sort("updated_at", -1).to_list(
        length=MAX_REQUESTS_PER_RUN,
    )

    processed = 0
    with_new = 0
    emailed = 0
    errors = 0
    for req in reqs:
        try:
            r = await process_request(db, req)
            processed += 1
            if r.get("new"):
                with_new += 1
            if r.get("emailed"):
                emailed += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning("request matching failed %s: %s", req.get("id"), e)

    return {
        "scanned": len(reqs),
        "processed": processed,
        "with_new_matches": with_new,
        "emailed": emailed,
        "errors": errors,
    }
