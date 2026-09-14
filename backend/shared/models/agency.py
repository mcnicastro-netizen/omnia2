"""OMNIA — Agency model (multi-tenant root entity for ImmoWeb)."""
from typing import List, Optional, Literal
from pydantic import EmailStr, Field, HttpUrl, field_validator
from uuid import uuid4
import re

from shared.models.base import TimestampedModel, OmniaBaseModel, utcnow_iso

AgencyPlan = Literal["free", "starter", "pro", "enterprise"]
InviteStatus = Literal["pending", "accepted", "revoked", "expired"]

# M2.5.1 — Doppio Binario (D-041)
# Each agency declares how it consumes OMNIA:
#   turnkey    -> UI OMNIA end-to-end (Track A)
#   whitelabel -> API + widgets, own CRM/site kept (Track B pure)
#   hybrid     -> both UI OMNIA + API/widgets (default for existing agencies)
PlanType = Literal["turnkey", "whitelabel", "hybrid"]

# Where the credit budget lives:
#   group  -> holding pays for all branches
#   branch -> each branch pays its own (default — autonomous multi-sede)
CreditsMode = Literal["group", "branch"]


def _slugify(text: str) -> str:
    """Convert agency name to URL-safe slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = s.strip("-")
    return s[:60] or "agency"


# -------------------- AGENCY --------------------

class AgencyFiscal(OmniaBaseModel):
    """Italian fiscal / legal identity fields."""
    legal_name: str = Field(min_length=2, max_length=200)
    vat_number: Optional[str] = Field(default=None, max_length=20)       # Partita IVA
    fiscal_code: Optional[str] = Field(default=None, max_length=20)      # Codice Fiscale
    rea: Optional[str] = Field(default=None, max_length=30)              # REA (Repertorio Economico Amministrativo)
    fiaip_code: Optional[str] = Field(default=None, max_length=30)       # codice agente FIAIP


class AgencyAddress(OmniaBaseModel):
    street: Optional[str] = Field(default=None, max_length=200)
    city: Optional[str] = Field(default=None, max_length=100)
    province: Optional[str] = Field(default=None, max_length=10)         # es. "RM", "MI"
    postal_code: Optional[str] = Field(default=None, max_length=10)
    country: str = Field(default="IT", max_length=2)


class AgencyContact(OmniaBaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    website: Optional[str] = Field(default=None, max_length=200)


class AgencyBranding(OmniaBaseModel):
    """Visual branding (logo/colors arrive properly in M2.S6 white-label)."""
    logo_url: Optional[str] = Field(default=None, max_length=500)
    primary_color: str = Field(default="#0B1E3F", pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str = Field(default="#1F6B5C", pattern=r"^#[0-9a-fA-F]{6}$")
    tagline: Optional[str] = Field(default=None, max_length=200)


# Website strategy: agencies either already have a site (we feed it via XML)
# or they want one built by OMNIA (template gallery, custom domain — M2.S6).
WebsiteMode = Literal["external", "omnia_template"]


class AgencyWebsite(OmniaBaseModel):
    """How the agency wants its public website handled."""
    mode: Optional[WebsiteMode] = None
    external_url: Optional[str] = Field(default=None, max_length=300)
    template_id: Optional[str] = Field(default=None, max_length=60)
    custom_domain: Optional[str] = Field(default=None, max_length=120)
    # M2.S6 — custom domain verification workflow
    custom_domain_status: Optional[Literal["pending", "verified", "error"]] = None
    custom_domain_token: Optional[str] = Field(default=None, max_length=64)
    custom_domain_requested_at: Optional[str] = None
    custom_domain_verified_at: Optional[str] = None
    custom_domain_last_error: Optional[str] = Field(default=None, max_length=300)
    # M2.S5 Layer D Phase 1 — raw extracted brand profile (output of /website/extract-from-url)
    extracted_profile: Optional[dict] = None
    # M2.S5 Layer D Phase 2 — active theme configuration applied to the public site
    theme_config: Optional[dict] = None


class AgencyInDB(TimestampedModel):
    """Agency stored in MongoDB."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    slug: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(min_length=2, max_length=120)
    fiscal: AgencyFiscal
    address: AgencyAddress = Field(default_factory=AgencyAddress)
    contact: AgencyContact = Field(default_factory=AgencyContact)
    branding: AgencyBranding = Field(default_factory=AgencyBranding)
    website: AgencyWebsite = Field(default_factory=AgencyWebsite)
    plan: AgencyPlan = "free"
    owner_id: str  # user_id of the agency_admin who created it
    is_active: bool = True
    onboarding_completed: bool = False
    # M2.5.1 — Franchising / Multi-branch layer (D-041)
    group_id: Optional[str] = None                # attached to an AgencyGroup (None = standalone)
    branch_code: Optional[str] = Field(default=None, max_length=30)  # internal code (e.g. "MI-01")
    plan_type: PlanType = "hybrid"                # default: both UI + API access
    # M2.5.5 — Domain Vault / Domain Sovereignty (D-051/D-054)
    # Contractual promise: OMNIA never registers domains in its own name.
    domain_sovereignty_confirmed: bool = False
    domain_sovereignty_confirmed_at: Optional[str] = None
    existing_domain: Optional[str] = Field(default=None, max_length=253)


class AgencyPublic(OmniaBaseModel):
    """Agency shape returned to the client."""
    id: str
    slug: str
    display_name: str
    fiscal: AgencyFiscal
    address: AgencyAddress
    contact: AgencyContact
    branding: AgencyBranding
    website: AgencyWebsite = Field(default_factory=AgencyWebsite)
    plan: AgencyPlan
    owner_id: str
    is_active: bool
    onboarding_completed: bool
    created_at: str
    updated_at: str
    # M2.5.1 — Franchising fields
    group_id: Optional[str] = None
    branch_code: Optional[str] = None
    plan_type: PlanType = "hybrid"
    # M2.5.5 — Domain Vault
    domain_sovereignty_confirmed: bool = False
    domain_sovereignty_confirmed_at: Optional[str] = None
    existing_domain: Optional[str] = None


class AgencyCreate(OmniaBaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    fiscal: AgencyFiscal
    address: Optional[AgencyAddress] = None
    contact: Optional[AgencyContact] = None
    branding: Optional[AgencyBranding] = None


class AgencyUpdate(OmniaBaseModel):
    display_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    fiscal: Optional[AgencyFiscal] = None
    address: Optional[AgencyAddress] = None
    contact: Optional[AgencyContact] = None
    branding: Optional[AgencyBranding] = None
    website: Optional[AgencyWebsite] = None
    onboarding_completed: Optional[bool] = None


def make_slug(display_name: str) -> str:
    return _slugify(display_name)


# -------------------- INVITE --------------------

class AgencyInviteInDB(TimestampedModel):
    """Magic-link invitation to join an agency."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    agency_id: str
    email: EmailStr
    role: Literal["agent", "agency_admin"] = "agent"
    token: str                             # secure random token (32+ chars)
    expires_at: str                        # ISO timestamp
    status: InviteStatus = "pending"
    invited_by: str                        # user_id of inviter
    name_hint: Optional[str] = Field(default=None, max_length=120)


class AgencyInvitePublic(OmniaBaseModel):
    """Public-safe invite payload (no token)."""
    id: str
    agency_id: str
    email: EmailStr
    role: str
    status: InviteStatus
    expires_at: str
    invited_by: str
    name_hint: Optional[str] = None
    created_at: str


class InviteCreateRequest(OmniaBaseModel):
    email: EmailStr
    role: Literal["agent", "agency_admin"] = "agent"
    name_hint: Optional[str] = Field(default=None, max_length=120)


class InviteVerifyResponse(OmniaBaseModel):
    """Returned when the invitee visits the accept page (no token leak)."""
    invite_id: str
    agency_name: str
    role: str
    email: EmailStr
    expires_at: str


class InviteAcceptRequest(OmniaBaseModel):
    token: str
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


# -------------------- DASHBOARD KPI --------------------

class DashboardKPI(OmniaBaseModel):
    key: str
    label: str
    value: int
    delta_label: Optional[str] = None
    delta_direction: Optional[Literal["up", "down", "flat"]] = None
    icon: Optional[str] = None
    locked: bool = False  # True means "coming in future milestone"


# -------------------- AGENCY GROUP (M2.5.1 — Franchising Layer, D-041) --------------------

class AgencyGroupInDB(TimestampedModel):
    """
    Holding / franchising layer that sits on top of one or more agencies.
    A standalone agency has `group_id = None`. When multi-branch is enabled,
    an AgencyGroup owns N agencies (branches) and consolidates KPIs + credits.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    slug: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=2, max_length=120)
    franchise_name: Optional[str] = Field(default=None, max_length=120)
    # e.g. "Tecnocasa", "RE/MAX", "Gabetti" — free text; branded groups can leverage it in UI
    owner_id: str                                    # user_id of the group_admin who created it
    credits_mode: CreditsMode = "branch"             # who pays credits — default: each branch autonomous
    is_active: bool = True
    notes: Optional[str] = Field(default=None, max_length=500)


class AgencyGroupPublic(OmniaBaseModel):
    id: str
    slug: str
    name: str
    franchise_name: Optional[str] = None
    owner_id: str
    credits_mode: CreditsMode
    is_active: bool
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    # Enrichments computed at read time (not persisted)
    branches_count: Optional[int] = None


class AgencyGroupCreate(OmniaBaseModel):
    name: str = Field(min_length=2, max_length=120)
    franchise_name: Optional[str] = Field(default=None, max_length=120)
    credits_mode: CreditsMode = "branch"
    notes: Optional[str] = Field(default=None, max_length=500)


class AgencyGroupUpdate(OmniaBaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    franchise_name: Optional[str] = Field(default=None, max_length=120)
    credits_mode: Optional[CreditsMode] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class BranchAttachRequest(OmniaBaseModel):
    """Attach an existing agency as a branch of this group."""
    agency_id: str
    branch_code: Optional[str] = Field(default=None, max_length=30)


class BranchSummary(OmniaBaseModel):
    """Compact branch view used in group dashboards."""
    id: str
    slug: str
    display_name: str
    branch_code: Optional[str] = None
    plan_type: PlanType
    plan: AgencyPlan
    is_active: bool
    city: Optional[str] = None
    # Rollup counters
    properties_active: int = 0
    clients_total: int = 0
    leads_open: int = 0


class GroupConsolidatedKPIs(OmniaBaseModel):
    """Consolidated KPIs across all branches of a group."""
    group_id: str
    branches_count: int
    branches_active: int
    properties_active: int = 0
    properties_total: int = 0
    clients_total: int = 0
    leads_open: int = 0
    leads_total: int = 0
