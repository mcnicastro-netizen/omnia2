"""D-168 — Percorso Avvio agenzia (checklist post-attivazione).

Ordine: sito → import immobili → MLS → documenti → pubblicazione → CRM → team.
Biforcazione sito: MLS sul sito pubblico ⇒ tema OMNIA (niente overlay clone).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import require_agency
from shared.db.connection import Database

logger = logging.getLogger("omnia.setup_journey")
router = APIRouter(prefix="/setup-journey", tags=["setup-journey"])

STEP_ORDER: List[str] = [
    "site",
    "import_properties",
    "mls",
    "documents",
    "publishing",
    "import_crm",
    "team",
]

SiteChoice = Literal["omnia_theme", "keep_brand", "external"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_setup_journey() -> Dict[str, Any]:
    steps = {
        "site": {"done": False, "choice": None, "mls_on_public_site": None},
        "import_properties": {"done": False},
        "mls": {
            "done": False,
            "joined": False,
            "share_listings": True,
            "share_requests": True,  # AgeStaNet-style default ON
        },
        "documents": {"done": False, "paperless_intent": False, "esign_ready": False},
        "publishing": {"done": False},
        "import_crm": {"done": False},
        "team": {"done": False, "optional": True},
    }
    return {
        "status": "in_progress",
        "current_step": "site",
        "steps": steps,
        "started_at": _now(),
        "completed_at": None,
    }


def ensure_journey(agency: dict) -> Dict[str, Any]:
    j = agency.get("setup_journey")
    if isinstance(j, dict) and j.get("steps"):
        # merge missing keys without wiping progress
        base = default_setup_journey()
        steps = dict(base["steps"])
        for k, v in (j.get("steps") or {}).items():
            if k in steps and isinstance(v, dict):
                steps[k] = {**steps[k], **v}
        out = {**base, **j, "steps": steps}
        return out
    return default_setup_journey()


def _progress(journey: dict) -> Dict[str, Any]:
    steps = journey.get("steps") or {}
    required = [s for s in STEP_ORDER if not (steps.get(s) or {}).get("optional")]
    done = sum(1 for s in required if (steps.get(s) or {}).get("done"))
    return {
        "done": done,
        "total": len(required),
        "optional_done": sum(
            1 for s in STEP_ORDER if (steps.get(s) or {}).get("optional") and (steps.get(s) or {}).get("done")
        ),
    }


def _next_step(journey: dict) -> str:
    steps = journey.get("steps") or {}
    for s in STEP_ORDER:
        st = steps.get(s) or {}
        if st.get("optional"):
            continue
        if not st.get("done"):
            return s
    # optional leftovers
    for s in STEP_ORDER:
        st = steps.get(s) or {}
        if st.get("optional") and not st.get("done"):
            return s
    return "done"


class SiteStepBody(BaseModel):
    choice: SiteChoice
    mls_on_public_site: bool = False


class MlsStepBody(BaseModel):
    join: bool = True
    share_listings: bool = True
    share_requests: bool = True
    accept_terms: bool = True


class DocumentsStepBody(BaseModel):
    paperless_intent: bool = True
    mark_done: bool = True


class GenericDoneBody(BaseModel):
    mark_done: bool = True


class CompleteBody(BaseModel):
    skip_optional: bool = True


@router.get("")
async def get_setup_journey(user: dict = Depends(get_current_user)):
    aid = require_agency(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid}, {"_id": 0})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    journey = ensure_journey(agency)
    # Persist seed if missing (legacy agencies)
    if not agency.get("setup_journey"):
        await db.agencies.update_one(
            {"id": aid},
            {"$set": {"setup_journey": journey, "updated_at": _now()}},
        )
    website = agency.get("website") or {}
    return {
        "agency_id": aid,
        "activation_status": agency.get("activation_status"),
        "journey": journey,
        "progress": _progress(journey),
        "next_step": _next_step(journey),
        "context": {
            "declared_url": (website.get("external_url") or agency.get("existing_domain")),
            "mls_enabled": bool(agency.get("mls_enabled")),
            "site_choice": (journey.get("steps") or {}).get("site", {}).get("choice"),
            "defaults": {
                "share_listings_mls": True,
                "share_requests_mls": True,
            },
        },
    }


async def _save_journey(db, agency_id: str, journey: dict) -> dict:
    journey["current_step"] = _next_step(journey)
    prog = _progress(journey)
    if prog["done"] >= prog["total"] and journey.get("status") != "completed":
        # still allow optional; status stays in_progress until complete endpoint
        pass
    await db.agencies.update_one(
        {"id": agency_id},
        {"$set": {"setup_journey": journey, "updated_at": _now()}},
    )
    return journey


@router.post("/site")
async def complete_site_step(
    body: SiteStepBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "group_admin")),
):
    """Biforcazione D-168: MLS sul sito pubblico ⇒ solo tema OMNIA."""
    aid = require_agency(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    journey = ensure_journey(agency)

    choice = body.choice
    if body.mls_on_public_site and choice != "omnia_theme":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "mls_public_requires_omnia_theme",
                "hint": "Per mostrare la rete MLS sul sito pubblico usa un tema OMNIA. "
                "Keep-brand / sito esterno: MLS resta solo in ImmoWeb tra agenzie.",
            },
        )

    journey["steps"]["site"] = {
        "done": True,
        "choice": choice,
        "mls_on_public_site": bool(body.mls_on_public_site),
        "completed_at": _now(),
    }
    # Mode website coerente con scelta (campi già usati)
    web_set: Dict[str, Any] = {"updated_at": _now()}
    if choice == "external":
        web_set["website.mode"] = "external"
    elif choice == "omnia_theme":
        web_set["website.mode"] = "omnia_template"
    # keep_brand: resta external/clone path in Brand Studio

    await db.agencies.update_one({"id": aid}, {"$set": web_set})
    journey = await _save_journey(db, aid, journey)
    return {"ok": True, "journey": journey, "progress": _progress(journey), "next_step": _next_step(journey)}


@router.post("/mls")
async def complete_mls_step(
    body: MlsStepBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "group_admin")),
):
    aid = require_agency(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    journey = ensure_journey(agency)
    site = (journey.get("steps") or {}).get("site") or {}
    if not site.get("done"):
        raise HTTPException(status_code=400, detail="complete_site_first")

    now = _now()
    if body.join:
        if not body.accept_terms:
            raise HTTPException(status_code=400, detail="accept_terms_required")
        await db.agencies.update_one(
            {"id": aid},
            {
                "$set": {
                    "mls_enabled": True,
                    "mls_joined_at": now,
                    "defaults.share_listings_mls": bool(body.share_listings),
                    "defaults.share_requests_mls": bool(body.share_requests),
                    "updated_at": now,
                },
                "$unset": {"mls_left_at": ""},
            },
        )
        joined = True
    else:
        await db.agencies.update_one(
            {"id": aid},
            {
                "$set": {
                    "mls_enabled": False,
                    "mls_left_at": now,
                    "defaults.share_listings_mls": bool(body.share_listings),
                    "defaults.share_requests_mls": bool(body.share_requests),
                    "updated_at": now,
                }
            },
        )
        joined = False

    journey["steps"]["mls"] = {
        "done": True,
        "joined": joined,
        "share_listings": bool(body.share_listings),
        "share_requests": bool(body.share_requests),
        "completed_at": now,
    }
    journey = await _save_journey(db, aid, journey)
    return {"ok": True, "journey": journey, "progress": _progress(journey), "next_step": _next_step(journey)}


@router.post("/documents")
async def complete_documents_step(
    body: DocumentsStepBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "group_admin")),
):
    aid = require_agency(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    journey = ensure_journey(agency)
    journey["steps"]["documents"] = {
        "done": bool(body.mark_done),
        "paperless_intent": bool(body.paperless_intent),
        # Provider firma: credenziali in produzione — predisposizione only
        "esign_ready": False,
        "esign_note": "provider_credentials_pending_production",
        "completed_at": _now(),
    }
    journey = await _save_journey(db, aid, journey)
    return {"ok": True, "journey": journey, "progress": _progress(journey), "next_step": _next_step(journey)}


@router.post("/complete")
async def complete_journey(
    body: CompleteBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "group_admin")),
):
    aid = require_agency(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    journey = ensure_journey(agency)
    prog = _progress(journey)
    if prog["done"] < prog["total"]:
        raise HTTPException(
            status_code=400,
            detail={"error": "steps_incomplete", "progress": prog, "next_step": _next_step(journey)},
        )
    if body.skip_optional:
        for s in STEP_ORDER:
            st = journey["steps"].get(s) or {}
            if st.get("optional") and not st.get("done"):
                journey["steps"][s] = {**st, "done": True, "skipped": True, "completed_at": _now()}
    journey["status"] = "completed"
    journey["completed_at"] = _now()
    journey["current_step"] = "done"
    await db.agencies.update_one(
        {"id": aid},
        {"$set": {"setup_journey": journey, "updated_at": _now()}},
    )
    return {"ok": True, "journey": journey, "progress": _progress(journey)}


@router.post("/step/{step_id}")
async def mark_step_done(
    step_id: str,
    body: GenericDoneBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "group_admin")),
):
    if step_id not in ("import_properties", "publishing", "import_crm", "team"):
        raise HTTPException(status_code=404, detail="unknown_step")
    aid = require_agency(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    journey = ensure_journey(agency)
    prev = dict((journey.get("steps") or {}).get(step_id) or {})
    prev.update({"done": bool(body.mark_done), "completed_at": _now()})
    journey["steps"][step_id] = prev
    journey = await _save_journey(db, aid, journey)
    return {"ok": True, "journey": journey, "progress": _progress(journey), "next_step": _next_step(journey)}
