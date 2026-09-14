"""OMNIA — Saved Searches & Alert Email Matching (M3.S7).

Lets B2C users save a property search and receive email digests when new
matching listings appear on ImmobilCloud.

Schema (`db.saved_searches`):
  {
    id: str,
    user_id: str,
    name: str,                # human-friendly label (e.g., "Bilo in Trastevere")
    filters: {
        operation: "sale"|"rent",
        city: str?,
        property_type: str?,
        price_min: int?, price_max: int?,
        surface_min: int?,
        rooms_min: int?, bedrooms_min: int?, bathrooms_min: int?,
        energy_class: str?,
    },
    frequency: "instant"|"daily"|"weekly",   # delivery cadence
    is_active: bool = True,
    last_run_at: str?         # ISO; matches "since" this timestamp
    last_match_count: int?
    created_at: str
    updated_at: str
  }

Endpoints (B2C auth required):
  POST    /api/cloud/me/saved-searches               — create
  GET     /api/cloud/me/saved-searches               — list
  PATCH   /api/cloud/me/saved-searches/{sid}         — toggle active/frequency/name
  DELETE  /api/cloud/me/saved-searches/{sid}         — delete
  POST    /api/cloud/me/saved-searches/{sid}/run     — manual run (preview matches)

Cron-style (admin only):
  POST    /api/app/cron/saved-searches/run-all       — run matching for all active
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database

logger = logging.getLogger("omnia.saved_searches")
router = APIRouter(prefix="/me/saved-searches", tags=["cloud-saved-searches"])

FREQ = Literal["instant", "daily", "weekly"]


# ----------------------------- Schemas -----------------------------

class SearchFilters(BaseModel):
    operation: Optional[Literal["sale", "rent"]] = None
    city: Optional[str] = Field(default=None, max_length=100)
    property_type: Optional[str] = Field(default=None, max_length=50)
    price_min: Optional[int] = Field(default=None, ge=0)
    price_max: Optional[int] = Field(default=None, ge=0)
    surface_min: Optional[int] = Field(default=None, ge=0)
    rooms_min: Optional[int] = Field(default=None, ge=0)
    bedrooms_min: Optional[int] = Field(default=None, ge=0)
    bathrooms_min: Optional[int] = Field(default=None, ge=0)
    energy_class: Optional[str] = Field(default=None, pattern="^(A4|A3|A2|A1|A|B|C|D|E|F|G)?$")


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    filters: SearchFilters
    frequency: FREQ = "daily"


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    frequency: Optional[FREQ] = None
    is_active: Optional[bool] = None


# ----------------------------- Helpers -----------------------------

async def _ensure_b2c(user: dict) -> None:
    if user.get("account_type") != "b2c":
        raise HTTPException(status_code=403, detail="b2c_account_required")


def _build_mongo_filter(filters: dict, since: Optional[str] = None) -> Dict[str, Any]:
    """Translate SearchFilters into Mongo query reusing the public _base_filter."""
    from apps.immocloud.public_portal import _base_filter
    flt: Dict[str, Any] = _base_filter()
    if filters.get("city"):
        flt["city"] = {"$regex": f"^{filters['city']}", "$options": "i"}
    if filters.get("property_type"):
        flt["property_type"] = filters["property_type"]
    if filters.get("operation"):
        flt["operation"] = filters["operation"]
    if filters.get("rooms_min"):
        flt["rooms"] = {"$gte": filters["rooms_min"]}
    if filters.get("bedrooms_min"):
        flt["bedrooms"] = {"$gte": filters["bedrooms_min"]}
    if filters.get("bathrooms_min"):
        flt["bathrooms"] = {"$gte": filters["bathrooms_min"]}
    if filters.get("energy_class"):
        flt["energy.energy_class"] = filters["energy_class"]
    if filters.get("surface_min"):
        flt["surface_sqm"] = {"$gte": filters["surface_min"]}
    if filters.get("price_min") or filters.get("price_max"):
        rng: Dict[str, Any] = {}
        if filters.get("price_min"):
            rng["$gte"] = filters["price_min"]
        if filters.get("price_max"):
            rng["$lte"] = filters["price_max"]
        key = "rent_monthly" if filters.get("operation") == "rent" else "price"
        flt[key] = rng
    if since:
        flt["created_at"] = {"$gt": since}
    return flt


def _strip(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


# ----------------------------- CRUD -----------------------------

@router.post("", status_code=201)
async def create_saved_search(
    payload: SavedSearchCreate,
    user: dict = Depends(get_current_user),
):
    await _ensure_b2c(user)
    db = Database.get()

    # Cap: max 10 saved searches per free user
    count = await db.saved_searches.count_documents({"user_id": user["id"]})
    if count >= 10:
        raise HTTPException(status_code=409, detail="saved_searches_limit_reached")

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid4()),
        "user_id": user["id"],
        "name": payload.name.strip(),
        "filters": payload.filters.model_dump(exclude_none=True),
        "frequency": payload.frequency,
        "is_active": True,
        "last_run_at": None,
        "last_match_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    await db.saved_searches.insert_one(doc)
    return _strip(doc)


@router.get("")
async def list_saved_searches(user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    db = Database.get()
    cursor = db.saved_searches.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1)
    items = await cursor.to_list(length=50)
    return {"items": items, "total": len(items)}


@router.patch("/{sid}")
async def update_saved_search(
    sid: str, payload: SavedSearchUpdate,
    user: dict = Depends(get_current_user),
):
    await _ensure_b2c(user)
    db = Database.get()
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="nothing_to_update")
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    r = await db.saved_searches.update_one(
        {"id": sid, "user_id": user["id"]},
        {"$set": updates},
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="saved_search_not_found")
    updated = await db.saved_searches.find_one({"id": sid}, {"_id": 0})
    return updated


@router.delete("/{sid}", status_code=204)
async def delete_saved_search(sid: str, user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    db = Database.get()
    r = await db.saved_searches.delete_one({"id": sid, "user_id": user["id"]})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="saved_search_not_found")
    return None


@router.post("/{sid}/run")
async def run_saved_search(sid: str, user: dict = Depends(get_current_user)):
    """Preview matches for THIS saved search right now (no email sent)."""
    await _ensure_b2c(user)
    db = Database.get()
    s = await db.saved_searches.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="saved_search_not_found")
    flt = _build_mongo_filter(s["filters"], since=s.get("last_run_at"))
    cursor = db.properties.find(flt, {
        "_id": 0, "id": 1, "title": 1, "city": 1, "zone": 1, "price": 1,
        "rent_monthly": 1, "surface_sqm": 1, "rooms": 1, "operation": 1,
        "property_type": 1, "photos": 1, "created_at": 1,
    }).sort("created_at", -1).limit(20)
    matches = await cursor.to_list(length=20)
    return {"saved_search_id": sid, "matches": matches, "count": len(matches)}


# ============================================================
# Matching engine — runs through all active saved searches and
# sends email digests via Resend.
# ============================================================

async def _send_alert_email(*, to_email: str, user_name: str, lang: str,
                            search_name: str, matches: list, frontend_base: str) -> None:
    """Fire-and-forget Resend email with the digest of new matches."""
    from shared.email.client import send_email

    rows_html = []
    for m in matches[:6]:
        price = m.get("rent_monthly") if m.get("operation") == "rent" else m.get("price")
        price_str = f"€ {int(price):,}".replace(",", ".") if price else "Su richiesta"
        if m.get("operation") == "rent" and price:
            price_str += "/mese"
        rows_html.append(
            f'<tr><td style="padding:12px 0;border-bottom:1px solid #E5E2DC;">'
            f'<a href="{frontend_base}/{lang}/cloud/property/{m["id"]}" '
            f'style="color:#0B1E3F;text-decoration:none;">'
            f'<strong style="font-size:15px;color:#0B1E3F;">{m.get("title") or m.get("property_type") or "Immobile"}</strong><br/>'
            f'<span style="font-size:12px;color:#5C6470;">{m.get("city","")}{" · " + m["zone"] if m.get("zone") else ""}{" · " + str(m["surface_sqm"]) + " m²" if m.get("surface_sqm") else ""}</span><br/>'
            f'<span style="font-size:14px;color:#C19A6B;font-weight:600;">{price_str}</span>'
            f'</a></td></tr>'
        )
    matches_html = "<table cellpadding='0' cellspacing='0' width='100%'>" + "".join(rows_html) + "</table>"

    try:
        await send_email(
            to=to_email,
            template="saved_search_alert",
            lang=lang,
            variables={
                "user_name": user_name or "",
                "search_name": search_name,
                "match_count": str(len(matches)),
                "matches_html": matches_html,
                "search_url": f"{frontend_base}/{lang}/cloud/account",
            },
        )
    except Exception as e:
        logger.warning("alert email failed for %s: %s", to_email, e)


async def run_all_active_saved_searches() -> Dict[str, Any]:
    """Iterate every active saved search and email matches found since last_run_at."""
    import os
    db = Database.get()
    frontend_base = os.environ.get("FRONTEND_BASE_URL", "https://omniarealestateecosystem.it")
    now = datetime.now(timezone.utc).isoformat()
    total_searches = 0
    total_emails = 0
    total_matches = 0

    cursor = db.saved_searches.find({"is_active": True})
    async for s in cursor:
        total_searches += 1
        user = await db.users.find_one({"id": s["user_id"]},
                                       {"_id": 0, "email": 1, "name": 1, "lang": 1,
                                        "notification_channels": 1, "account_type": 1})
        # Always update last_run_at (even on skip) to avoid stale digests
        # when user later enables email channel.
        should_email = (
            user
            and user.get("account_type") == "b2c"
            and "email" in (user.get("notification_channels") or [])
        )

        flt = _build_mongo_filter(s["filters"], since=s.get("last_run_at"))
        matches: List[dict] = []
        if should_email:
            matches_cursor = db.properties.find(flt, {
                "_id": 0, "id": 1, "title": 1, "city": 1, "zone": 1, "price": 1,
                "rent_monthly": 1, "surface_sqm": 1, "rooms": 1, "operation": 1,
                "property_type": 1, "created_at": 1,
            }).sort("created_at", -1).limit(20)
            matches = await matches_cursor.to_list(length=20)

            if matches:
                await _send_alert_email(
                    to_email=user["email"],
                    user_name=user.get("name") or "",
                    lang=user.get("lang") or "it",
                    search_name=s["name"],
                    matches=matches,
                    frontend_base=frontend_base,
                )
                total_emails += 1
                total_matches += len(matches)

        # Always advance last_run_at — guarantees no replay of old matches
        # when user toggles notification channels later.
        await db.saved_searches.update_one(
            {"id": s["id"]},
            {"$set": {"last_run_at": now, "last_match_count": len(matches),
                      "updated_at": now}},
        )

    logger.info("saved_searches cron: %d searches, %d emails sent, %d total matches",
                total_searches, total_emails, total_matches)
    return {
        "searches_checked": total_searches,
        "emails_sent": total_emails,
        "total_matches": total_matches,
        "run_at": now,
    }
