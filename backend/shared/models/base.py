"""OMNIA — Shared base models (Pydantic v2)."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


# --- Time helper ---------------------------------------------------------

def utcnow_iso() -> str:
    """Return current UTC time as ISO 8601 string (for MongoDB storage)."""
    return datetime.now(timezone.utc).isoformat()


# --- Base models ---------------------------------------------------------

class OmniaBaseModel(BaseModel):
    """Base for all OMNIA Pydantic models. Strict, JSON-serializable."""
    model_config = ConfigDict(
        extra="ignore",        # ignore unknown fields (e.g. MongoDB _id)
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampedModel(OmniaBaseModel):
    """Adds created_at / updated_at."""
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)


class TenantModel(TimestampedModel):
    """Base for any model that belongs to a single agency (multi-tenant)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    agency_id: str  # REQUIRED — never optional for tenant data


# --- Translatable field --------------------------------------------------

TranslatableField = Dict[str, str]
# Convention:
#   {"it": "Bilocale Roma", "en": "1-bedroom Rome", "es": "Piso Roma"}
#   "it" is always the master/default; other languages are optional.


def get_translation(field: Optional[TranslatableField], lang: str = "it", fallback_lang: str = "it") -> str:
    """Safely read a translation with fallback."""
    if not field:
        return ""
    if lang in field and field[lang]:
        return field[lang]
    if fallback_lang in field and field[fallback_lang]:
        return field[fallback_lang]
    # last resort: return first available
    for v in field.values():
        if v:
            return v
    return ""


# --- Health response -----------------------------------------------------

class HealthResponse(OmniaBaseModel):
    status: str = "ok"
    app: str
    version: str = "0.1.0"
    timestamp: str = Field(default_factory=utcnow_iso)
    lang: str = "it"
    message: Dict[str, Any] = Field(default_factory=dict)
