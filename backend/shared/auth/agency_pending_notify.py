"""D-162 — Email «richiesta ricevuta» solo dopo KYC docs + pagamento."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("omnia.agency_pending_notify")


def _kyc_docs_ready(agency: dict) -> bool:
    kyc = agency.get("kyc") or {}
    cl = kyc.get("checklist") or {}
    if cl.get("visura_camerale") and cl.get("id_titolare"):
        return True
    docs = kyc.get("documents") or []
    types = {(d or {}).get("doc_type") for d in docs}
    return "visura_camerale" in types and "documento_identita" in types


async def maybe_send_agency_pending_ready(
    db,
    agency_id: str,
    *,
    force: bool = False,
) -> Dict[str, Any]:
    """Invia ``agency_pending`` una sola volta quando dossier + pagamento sono pronti.

    Idempotente via ``pending_notify_sent_at`` sull'agenzia.
    """
    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0})
    if not agency:
        return {"ok": False, "skipped": "agency_not_found"}

    st = (agency.get("activation_status") or "active").lower()
    if st != "pending":
        return {"ok": False, "skipped": "not_pending", "activation_status": st}

    if agency.get("pending_notify_sent_at") and not force:
        return {"ok": True, "skipped": "already_sent"}

    if not _kyc_docs_ready(agency):
        return {"ok": False, "skipped": "kyc_incomplete"}

    from shared.auth.agency_credentials import agency_payment_ok

    if not await agency_payment_ok(db, agency_id):
        return {"ok": False, "skipped": "payment_incomplete"}

    owner = await db.users.find_one(
        {"id": agency.get("owner_id")},
        {"_id": 0, "email": 1, "name": 1, "lang": 1},
    )
    to = (owner or {}).get("email") or ((agency.get("contact") or {}).get("email"))
    if not to:
        return {"ok": False, "skipped": "no_recipient"}

    from shared.email.client import send_email
    from shared.public_base import get_public_base_url

    lang = ((owner or {}).get("lang") or "it")[:2]
    frontend = get_public_base_url()
    preferred = (agency.get("preferred_plan_tier") or "pro").upper()
    try:
        result = await send_email(
            to=to,
            template="agency_pending",
            lang=lang if lang in ("it", "en", "es") else "it",
            variables={
                "name": (owner or {}).get("name") or "Colleague",
                "agency_name": agency.get("display_name") or agency.get("slug") or "",
                "plan_tier": preferred,
                "login_url": f"{frontend}/{lang}/login",
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("agency_pending ready email failed agency=%s: %s", agency_id, exc)
        return {"ok": False, "error": str(exc)[:200]}

    now = datetime.now(timezone.utc).isoformat()
    status = (result or {}).get("status")
    if status in ("sent", "mock"):
        await db.agencies.update_one(
            {"id": agency_id},
            {
                "$set": {
                    "pending_notify_sent_at": now,
                    "pending_notify_status": status,
                    "updated_at": now,
                }
            },
        )
        logger.info(
            "agency_pending sent agency=%s to=%s status=%s",
            agency_id,
            to,
            status,
        )
        return {"ok": True, "status": status, "to": to, "email": result}

    logger.warning(
        "agency_pending not marked sent agency=%s status=%s result=%s",
        agency_id,
        status,
        result,
    )
    return {"ok": False, "status": status, "email": result, "to": to}
