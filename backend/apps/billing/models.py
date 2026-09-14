"""OMNIA — Billing data models (subscriptions, invoices, credits ledger)."""
from datetime import datetime, timezone
from typing import Literal, Optional, List
from pydantic import Field

from shared.models.base import TenantModel, TimestampedModel, OmniaBaseModel

SubStatus = Literal["trialing", "active", "past_due", "canceled", "unpaid", "incomplete"]


class SubscriptionInDB(TenantModel):
    """One row per active/past subscription per agency."""
    tier: str  # PlanTier from plans.py
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    status: SubStatus = "trialing"
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    trial_end: Optional[str] = None


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
    """Per-agency credit wallet (M4.S4)."""
    balance: int = 0
    last_topup_at: Optional[str] = None


class CreditLedgerEntry(TimestampedModel):
    """Immutable ledger — never updated, only appended."""
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    agency_id: str
    delta: int  # positive = topup / refund, negative = consumption
    reason: str  # e.g. "valuator_pdf" or "topup_pkg_200"
    balance_after: int
    ref_id: Optional[str] = None  # e.g. property_id, invoice_id, stripe_session_id
    ref_type: Optional[str] = None


class CheckoutSessionRequest(OmniaBaseModel):
    plan_tier: str  # PlanTier
    billing_cycle: Literal["monthly", "yearly"] = "monthly"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CreditPurchaseRequest(OmniaBaseModel):
    package_key: str  # e.g. "pkg_200"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
