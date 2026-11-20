"""OMNIA — Billing data models (subscriptions, invoices, credits ledger)."""
from datetime import datetime, timezone
from typing import Literal, Optional, List
from pydantic import Field

from shared.models.base import TenantModel, TimestampedModel, OmniaBaseModel

SubStatus = Literal["trialing", "active", "past_due", "canceled", "unpaid", "incomplete"]


class SubscriptionInDB(TenantModel):
    """Subscription row — still agency-scoped for legacy UI; B04-I adds CC link + snapshot.

    `status` remains the Stripe-mirrored status for backward compatibility.
    `stripe_status` is the explicit Stripe mirror (DES-02). OMNIA commercial/operational
    states live on CommercialCustomer, not here.
    """
    tier: str  # PlanTier from plans.py
    commercial_customer_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    status: SubStatus = "trialing"
    stripe_status: Optional[SubStatus] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    trial_end: Optional[str] = None
    # B04-DES-03 — frozen commercial terms at acceptance
    commercial_terms: Optional[dict] = None
    catalog_version_id: Optional[str] = None


class InvoiceInDB(TenantModel):
    stripe_invoice_id: str
    amount_paid: float  # €
    amount_due: float
    currency: str = "eur"
    status: str  # paid / open / uncollectible / void
    hosted_invoice_url: Optional[str] = None
    pdf_url: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class CreditWalletInDB(TenantModel):
    """Legacy per-agency credit wallet mirror (M4.S4 / B04-II dual-write)."""
    balance: int = 0
    last_topup_at: Optional[str] = None


class CreditLedgerEntry(TimestampedModel):
    """Legacy agency ledger mirror — never updated, only appended."""
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    agency_id: str
    delta: int  # positive = topup / refund, negative = consumption
    reason: str  # e.g. "valuator_pdf" or "topup_pkg_200"
    balance_after: int
    ref_id: Optional[str] = None  # e.g. property_id, invoice_id, stripe_session_id
    ref_type: Optional[str] = None


# --- B04-II / DES-04 — CommercialCustomer-scoped wallet (SoT) -------------

class CommercialCreditWalletInDB(TimestampedModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    commercial_customer_id: str
    balance_unallocated: int = 0
    balance_total: int = 0


class CreditLotInDB(TimestampedModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    commercial_customer_id: str
    wallet_id: str
    origin: str
    original_qty: int
    remaining_qty: int
    idempotency_key: Optional[str] = None


class CreditAllocationInDB(TimestampedModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    commercial_customer_id: str
    lot_id: str
    organization_id: str
    original_qty: int
    remaining_qty: int
    revoked_at: Optional[str] = None


class CommercialCreditLedgerEntry(TimestampedModel):
    """Append-only CC ledger — corrections via compensating entries only."""
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    commercial_customer_id: str
    organization_id: Optional[str] = None
    lot_id: Optional[str] = None
    allocation_id: Optional[str] = None
    entry_type: str  # grant|allocate|revoke|consume|compensate|return_to_central
    delta: int
    reason: str
    ref_id: Optional[str] = None
    ref_type: Optional[str] = None
    idempotency_key: Optional[str] = None
    meta: dict = Field(default_factory=dict)


class CheckoutSessionRequest(OmniaBaseModel):
    plan_tier: str  # PlanTier
    billing_cycle: Literal["monthly", "yearly"] = "monthly"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CreditPurchaseRequest(OmniaBaseModel):
    """D-175 C5 — purchase bound to CommercialCustomer (C5-D01)."""

    package_key: str  # e.g. "pkg_200"
    commercial_customer_id: str
    agency_id: Optional[str] = None  # optional contextual audit only
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class StoragePurchaseRequest(OmniaBaseModel):
    """D-175 C5 — storage addon bound to CommercialCustomer (C5-D01/D03)."""

    commercial_customer_id: str
    package_key: str = "storage_100gb"
    agency_id: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
