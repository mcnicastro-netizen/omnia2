"""Founders 50 lead capture & email notification.

POST /api/founders/register  -> store lead + email founder + thank-you email to lead
GET  /api/founders/spots     -> public spots-remaining counter (cached 60s)
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from motor.motor_asyncio import AsyncIOMotorClient

from shared.email.client import send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/founders", tags=["founders"])

# MongoDB connection (reuse the global pattern)
_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
_db = _client[os.environ["DB_NAME"]]
_leads = _db["founders_50_leads"]

# Configuration
FOUNDERS_TOTAL_SPOTS = 50
ADMIN_NOTIFICATION_EMAIL = "mcnicastro@gmail.com"


class FounderRegistration(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    agency: str = Field(min_length=2, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    agents_count: int = Field(ge=1, le=500, description="Number of agents in the agency")
    tier_interest: Optional[str] = Field(default=None, description="Optional: starter|pro|agency")
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("name", "agency", "city")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


@router.get("/spots")
async def spots_remaining():
    """Public counter: how many Founders 50 spots are left."""
    try:
        registered = await _leads.count_documents({})
    except Exception as e:
        logger.warning(f"Could not count founders leads: {e}")
        registered = 0
    remaining = max(0, FOUNDERS_TOTAL_SPOTS - registered)
    return {
        "total": FOUNDERS_TOTAL_SPOTS,
        "registered": registered,
        "remaining": remaining,
        "is_open": remaining > 0,
    }


@router.post("/register")
async def register_founder(payload: FounderRegistration, request: Request):
    """Register a new Founders 50 interest lead."""
    # Check if spots are still open
    registered = await _leads.count_documents({})
    if registered >= FOUNDERS_TOTAL_SPOTS:
        raise HTTPException(status_code=409, detail="Founders 50 program is full. Join the waitlist.")

    # Check duplicate by email
    existing = await _leads.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already registered. We will get back to you soon.",
        )

    # Build lead document
    now = datetime.now(timezone.utc)
    lead_doc = {
        "email": payload.email.lower(),
        "name": payload.name,
        "agency": payload.agency,
        "city": payload.city,
        "agents_count": payload.agents_count,
        "tier_interest": payload.tier_interest,
        "notes": payload.notes,
        "created_at": now.isoformat(),
        "source": "landing_agenzie",
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", "")[:300],
        "status": "new",
        "position": registered + 1,
    }

    result = await _leads.insert_one(lead_doc)
    position = lead_doc["position"]
    remaining = FOUNDERS_TOTAL_SPOTS - position

    # Send thank-you email to lead (fire & forget — don't fail registration if email fails)
    try:
        await send_email(
            to=payload.email,
            subject=f"✨ Benvenuto in OMNIA Founders 50 — Posto #{position} confermato",
            template="founders_welcome",
            variables={
                "name": payload.name,
                "agency": payload.agency,
                "position": position,
                "remaining": remaining,
            },
            lang="it",
        )
    except Exception as e:
        logger.warning(f"Founders welcome email failed for {payload.email}: {e}")

    # Notify admin of new registration
    try:
        await send_email(
            to=ADMIN_NOTIFICATION_EMAIL,
            subject=f"🎯 OMNIA Founders 50 — Nuovo lead #{position}/50: {payload.agency}",
            template="founders_admin_notification",
            variables={
                "name": payload.name,
                "email": payload.email,
                "agency": payload.agency,
                "city": payload.city,
                "agents_count": payload.agents_count,
                "tier_interest": payload.tier_interest or "—",
                "notes": payload.notes or "—",
                "position": position,
                "remaining": remaining,
            },
            lang="it",
        )
    except Exception as e:
        logger.warning(f"Founders admin notification failed: {e}")

    return {
        "ok": True,
        "id": str(result.inserted_id),
        "position": position,
        "remaining": remaining,
        "message": f"Sei il #{position}/50. Ti abbiamo inviato una mail di conferma a {payload.email}.",
    }
