"""OMNIA — CommercialCustomer (B01 / D-173 + B04-I): cliente commerciale P.IVA."""
from typing import Literal, Optional
from uuid import uuid4

from pydantic import Field

from shared.models.base import OmniaBaseModel, TimestampedModel

# B01 coarse status (legacy-compatible)
CustomerStatus = Literal["active", "suspended", "closed"]

# B04-DES-02 / DES-07 — OMNIA commercial state (not Stripe)
CommercialStatus = Literal[
    "pre_activation",
    "active",
    "cancel_pending",
    "grace",
    "suspended",
    "ceased",
]

# B04-DES-02 / DES-07 — OMNIA operational entitlement envelope
OperationalStatus = Literal[
    "none",
    "full",
    "billing_only",
    "closed_readonly",
]


def normalize_vat_number(vat: str | None) -> str:
    """Normalize VAT for uniqueness (IT: strip spaces/dots, uppercase, drop IT prefix)."""
    raw = (vat or "").strip().upper()
    raw = raw.replace(" ", "").replace(".", "").replace("-", "")
    if raw.startswith("IT") and len(raw) > 2:
        raw = raw[2:]
    return raw


def operational_status_for(commercial: CommercialStatus) -> OperationalStatus:
    """Derive default operational envelope from commercial status (DES-07)."""
    if commercial in ("active", "cancel_pending", "grace"):
        return "full"
    if commercial == "suspended":
        return "billing_only"
    if commercial == "ceased":
        return "closed_readonly"
    return "none"


class CommercialCustomerInDB(TimestampedModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    country_code: str = Field(default="IT", min_length=2, max_length=2)
    vat_number_normalized: str = Field(min_length=5, max_length=32)
    legal_name: str = Field(min_length=1, max_length=200)
    fiscal_data: dict = Field(default_factory=dict)
    customer_status: CustomerStatus = "active"
    # B04-I — Stripe + OMNIA state machine (DES-01 / DES-02)
    stripe_customer_id: Optional[str] = None
    commercial_status: CommercialStatus = "pre_activation"
    operational_status: OperationalStatus = "none"
    first_paid_activated_at: Optional[str] = None
    founder_period_ends_at: Optional[str] = None
    cancel_requested_at: Optional[str] = None
    ceased_at: Optional[str] = None


class CommercialCustomerPublic(OmniaBaseModel):
    id: str
    country_code: str
    vat_number_normalized: str
    legal_name: str
    customer_status: CustomerStatus
    commercial_status: CommercialStatus = "pre_activation"
    operational_status: OperationalStatus = "none"
    stripe_customer_id: Optional[str] = None
