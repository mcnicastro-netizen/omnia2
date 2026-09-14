"""OMNIA — API Key models (M2.5.2 Track B API Gateway, D-041/D-046).

An API key belongs to an agency (and optionally to a group). It carries:
  - hashed secret (never store plaintext after issuance)
  - credit wallet (integer balance)
  - optional partner_id for Web Agency Partner rev-share (D-046)
  - audit trail via ApiUsageLog
"""
from typing import Optional
from uuid import uuid4

from pydantic import Field

from shared.models.base import TimestampedModel, OmniaBaseModel


class ApiKeyInDB(TimestampedModel):
    """Stored form of an API key. Only the hash is persisted."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    agency_id: str                                    # owning agency (branch)
    group_id: Optional[str] = None                    # optional group parent
    name: str = Field(max_length=120)                 # human label ("Widget Sito Cliente A")
    key_prefix: str                                   # first 12 chars of the plaintext (searchable)
    key_hash: str                                     # SHA-256 hex digest of the plaintext
    credits_balance: int = 0                          # remaining credits
    credits_spent: int = 0                            # cumulative spend (audit)
    partner_id: Optional[str] = None                  # Web Agency partner (D-046)
    # M2.5.3 — Widget security: origins whitelist (empty = allow all, deployment gate at UI level)
    allowed_origins: list = Field(default_factory=list)  # e.g. ["https://agenziarossi.it", "https://*.agenziarossi.it"]
    is_active: bool = True
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None


class ApiKeyPublic(OmniaBaseModel):
    """Safe shape returned to management UI (never exposes plaintext or hash)."""
    id: str
    agency_id: str
    group_id: Optional[str] = None
    name: str
    key_prefix: str
    credits_balance: int
    credits_spent: int
    partner_id: Optional[str] = None
    allowed_origins: list = []
    is_active: bool
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None
    created_at: str
    updated_at: str


class ApiKeyCreate(OmniaBaseModel):
    name: str = Field(min_length=1, max_length=120)
    initial_credits: int = Field(default=0, ge=0, le=1_000_000)
    partner_id: Optional[str] = Field(default=None, max_length=60)
    allowed_origins: list = []                        # empty = permissive; recommended: set for widget keys


class ApiKeyIssueResponse(OmniaBaseModel):
    """Returned ONCE at issue time — plaintext included. Never persisted or returned again."""
    key: str                                          # plaintext, show-once
    api_key: ApiKeyPublic


class CreditAdjustment(OmniaBaseModel):
    """Manual credit adjustment (super_admin/agency_admin only until M4 Stripe)."""
    delta: int = Field(ge=-1_000_000, le=1_000_000)   # positive = top-up, negative = deduct
    reason: str = Field(min_length=1, max_length=200)


class ApiUsageLogInDB(TimestampedModel):
    """One row per API call — used for billing audit and analytics."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    api_key_id: str
    agency_id: str
    partner_id: Optional[str] = None
    endpoint: str = Field(max_length=120)             # e.g. "POST /api/v1/valuator"
    credits_charged: int = 0
    status_code: int = 200
    ok: bool = True
    error_code: Optional[str] = Field(default=None, max_length=60)
    latency_ms: Optional[int] = None
