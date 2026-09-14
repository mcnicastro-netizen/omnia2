"""OMNIA — M2.5.5 Domain Vault (D-051 / D-054).

Contractual promise: OMNIA never registers a domain on its own name.
Every agency owns its domain. This router:

  * Records the "domain sovereignty" confirmation on the agency doc.
  * Optionally attaches an existing_domain string that the agency already owns
    (help-to-connect flow, NOT a transfer).
  * Exposes GET to inspect the current state of the vault for the user's
    agency.

Kept intentionally small — the heavy lifting (DNS verification, custom_domain
onboarding, RDAP checks) is in `custom_domain.py` / `domain_check.py`.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.db.connection import Database
from shared.models.base import OmniaBaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agencies", tags=["domain-vault"])

# Loose FQDN check: labels + at least one dot, ≤253 chars.
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)([a-z0-9-]{1,63}(?<!-)\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)


class DomainSovereigntyRequest(OmniaBaseModel):
    confirmed: bool = Field(default=True)
    existing_domain: Optional[str] = Field(default=None, max_length=253)


class DomainSovereigntyResponse(OmniaBaseModel):
    agency_id: str
    confirmed: bool
    confirmed_at: Optional[str] = None
    existing_domain: Optional[str] = None
    # Policy reference (surfaced to the UI to link the public T&C page).
    policy_url: str = "/it/domain-sovereignty-policy"


def _normalize_domain(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    d = raw.strip().lower()
    if d.startswith(("http://", "https://")):
        d = d.split("://", 1)[1]
    d = d.split("/", 1)[0]
    if d.startswith("www."):
        d = d[4:]
    if not d:
        return None
    if not _DOMAIN_RE.match(d):
        raise HTTPException(status_code=400, detail="invalid_domain_format")
    return d


async def _resolve_agency_id(user: dict) -> str:
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if agency_ids:
        return agency_ids[0]
    # Fallback: some legacy users own an agency but are not attached yet.
    owned = await db.agencies.find_one({"owner_id": user["id"]})
    if owned:
        return owned["id"]
    raise HTTPException(status_code=404, detail="no_agency")


@router.get("/me/domain-sovereignty", response_model=DomainSovereigntyResponse)
async def get_domain_sovereignty(user: dict = Depends(get_current_user)):
    """Return current Domain Vault state for the caller's agency."""
    db = Database.get()
    agency_id = await _resolve_agency_id(user)
    doc = await db.agencies.find_one({"id": agency_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="agency_not_found")
    return DomainSovereigntyResponse(
        agency_id=agency_id,
        confirmed=bool(doc.get("domain_sovereignty_confirmed")),
        confirmed_at=doc.get("domain_sovereignty_confirmed_at"),
        existing_domain=doc.get("existing_domain"),
    )


@router.post("/me/domain-sovereignty", response_model=DomainSovereigntyResponse)
async def set_domain_sovereignty(
    payload: DomainSovereigntyRequest,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "branch_admin", "group_admin")),
):
    """Record the Domain Sovereignty confirmation on the caller's agency.

    Idempotent: sending `confirmed=True` twice keeps the FIRST timestamp; sending
    `confirmed=False` unsets the flag and preserves the audit log entry in
    `domain_vault_events` (append-only).
    """
    db = Database.get()
    agency_id = await _resolve_agency_id(user)
    existing = await db.agencies.find_one({"id": agency_id})
    if not existing:
        raise HTTPException(status_code=404, detail="agency_not_found")

    domain = _normalize_domain(payload.existing_domain)

    now_iso = datetime.now(timezone.utc).isoformat()
    updates: dict = {"updated_at": now_iso}

    if payload.confirmed:
        # Preserve first-confirmation timestamp (do not overwrite).
        if not existing.get("domain_sovereignty_confirmed"):
            updates["domain_sovereignty_confirmed"] = True
            updates["domain_sovereignty_confirmed_at"] = now_iso
        else:
            updates["domain_sovereignty_confirmed"] = True
    else:
        updates["domain_sovereignty_confirmed"] = False

    # existing_domain: only overwrite if explicitly provided (including "" to clear)
    if payload.existing_domain is not None:
        updates["existing_domain"] = domain  # can be None if payload was empty

    await db.agencies.update_one({"id": agency_id}, {"$set": updates})

    # Append-only audit trail
    await db.domain_vault_events.insert_one({
        "agency_id": agency_id,
        "user_id": user["id"],
        "user_email": user.get("email"),
        "confirmed": payload.confirmed,
        "existing_domain": domain,
        "at": now_iso,
    })

    refreshed = await db.agencies.find_one({"id": agency_id})
    logger.info(
        "Domain Vault updated: agency=%s confirmed=%s existing_domain=%s",
        agency_id, payload.confirmed, domain,
    )
    return DomainSovereigntyResponse(
        agency_id=agency_id,
        confirmed=bool(refreshed.get("domain_sovereignty_confirmed")),
        confirmed_at=refreshed.get("domain_sovereignty_confirmed_at"),
        existing_domain=refreshed.get("existing_domain"),
    )
