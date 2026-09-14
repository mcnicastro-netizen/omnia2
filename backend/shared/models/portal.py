"""OMNIA — Portal Subscription model (M2.S5 Layer A, D-029).

Each PortalSubscription = agency's integration credentials for one publisher portal.
Passwords stored encrypted via Fernet (key from env OMNIA_PORTAL_ENC_KEY).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

PortalFrequency = Literal["hourly", "every_4h", "daily", "weekly", "manual"]
PortalStatus = Literal["active", "disabled", "error", "pending"]


# Built-in portal catalog. Keep alphabetic codes — adapters live in adapters/.
PORTAL_CATALOG = [
    {"code": "idealista", "name": "Idealista", "site": "https://www.idealista.it",
     "mode": "pull_xml", "needs_credentials": False, "supports_omnia_extended": False},
    {"code": "immobiliare", "name": "Immobiliare.it", "site": "https://www.immobiliare.it",
     "mode": "pull_xml", "needs_credentials": True, "supports_omnia_extended": False},
    {"code": "casa", "name": "Casa.it", "site": "https://www.casa.it",
     "mode": "pull_xml", "needs_credentials": True, "supports_omnia_extended": False},
    {"code": "wikicasa", "name": "Wikicasa", "site": "https://www.wikicasa.it",
     "mode": "pull_xml", "needs_credentials": True, "supports_omnia_extended": False},
    {"code": "subito", "name": "Subito.it", "site": "https://www.subito.it",
     "mode": "push_api", "needs_credentials": True, "supports_omnia_extended": False},
    {"code": "facebook_catalog", "name": "Facebook Catalog", "site": "https://www.facebook.com/business/marketplace",
     "mode": "push_api", "needs_credentials": True, "supports_omnia_extended": True},
    {"code": "linkedin", "name": "LinkedIn", "site": "https://www.linkedin.com",
     "mode": "push_api", "needs_credentials": True, "supports_omnia_extended": True},
]


class PortalCredentials(BaseModel):
    """User-facing credentials (we never return password in cleartext on read)."""
    username: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=200)
    api_key: Optional[str] = Field(default=None, max_length=500)
    extra: Optional[dict] = None  # adapter-specific (e.g. fb_business_id, linkedin_page_urn)


class PortalSubscriptionCreate(BaseModel):
    portal_code: str = Field(..., min_length=2, max_length=60)
    credentials: PortalCredentials = Field(default_factory=PortalCredentials)
    password: Optional[str] = Field(default=None, max_length=500)  # plaintext on input only
    frequency: PortalFrequency = "daily"
    enabled: bool = False
    notes: Optional[str] = Field(default=None, max_length=2000)


class PortalSubscriptionUpdate(BaseModel):
    credentials: Optional[PortalCredentials] = None
    password: Optional[str] = Field(default=None, max_length=500)
    frequency: Optional[PortalFrequency] = None
    enabled: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=2000)


class PortalSubscriptionPublic(BaseModel):
    """Safe public read shape (never includes password)."""
    id: str
    agency_id: str
    portal_code: str
    portal_name: str
    site: str
    mode: str
    credentials: PortalCredentials
    has_password: bool
    frequency: PortalFrequency
    enabled: bool
    status: PortalStatus
    last_transfer_at: Optional[str] = None
    next_transfer_at: Optional[str] = None
    last_error: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# M2.6 Publishing Center models (D-052) — coexist with legacy PortalSubscription
# ============================================================================
from uuid import uuid4  # noqa: E402
from typing import List, Dict, Any  # noqa: E402
from shared.models.base import TimestampedModel, OmniaBaseModel  # noqa: E402


class PortalCatalog(TimestampedModel):
    """OMNIA-curated portal metadata (edited only by super_admin).

    M2.6d Universal Portal Wizard extension:
    - `owner_agency_id`: None for system portals, set for custom agency portals.
    - `is_custom`: True for portals created by an agency via the wizard.
    - `endpoint_url`: optional URL where the portal expects the feed (for
      documentation / copy-to-clipboard on push_url integrations later).
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9-]+$")
    name: str
    category: str = Field(default="gratuito")
    dialect: str = Field(default="osf_federata")
    integration_type: str = Field(default="feed_pull")
    geographic_scope: str = Field(default="national")
    credential_fields: List[Dict[str, Any]] = Field(default_factory=list)
    logo_url: Optional[str] = None
    traffic_score: int = Field(default=3, ge=1, le=5)
    is_active: bool = True
    notes: Optional[str] = None
    # M2.6d — Universal Portal Wizard fields
    owner_agency_id: Optional[str] = None
    is_custom: bool = False
    endpoint_url: Optional[str] = None
    site_url: Optional[str] = None


class AgencyPortalConnection(TimestampedModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    agency_id: str
    portal_slug: str
    status: str = Field(default="pending")
    credentials_encrypted: Optional[str] = None
    last_sync_at: Optional[str] = None
    next_sync_at: Optional[str] = None
    last_error: Optional[str] = None
    items_published: int = 0
    items_failed: int = 0
    is_all_properties: bool = True
    notes: Optional[str] = None


class PortalSyncLog(TimestampedModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    agency_id: str
    portal_slug: str
    started_at: str
    ended_at: Optional[str] = None
    status: str = "running"
    items_ok: int = 0
    items_failed: int = 0
    error_message: Optional[str] = None


class PortalConnectionCreate(OmniaBaseModel):
    portal_slug: str
    credentials: Dict[str, str] = Field(default_factory=dict)
    is_all_properties: bool = True


class PortalConnectionUpdate(OmniaBaseModel):
    credentials: Optional[Dict[str, str]] = None
    is_all_properties: Optional[bool] = None
    status: Optional[str] = None

