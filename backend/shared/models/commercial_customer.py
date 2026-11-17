"""OMNIA — CommercialCustomer (B01 / D-173): cliente commerciale identificato dalla P.IVA."""
from typing import Literal, Optional
from uuid import uuid4

from pydantic import Field

from shared.models.base import OmniaBaseModel, TimestampedModel

CustomerStatus = Literal["active", "suspended", "closed"]


def normalize_vat_number(vat: str | None) -> str:
    """Normalize VAT for uniqueness (IT: strip spaces/dots, uppercase, drop IT prefix)."""
    raw = (vat or "").strip().upper()
    raw = raw.replace(" ", "").replace(".", "").replace("-", "")
    if raw.startswith("IT") and len(raw) > 2:
        raw = raw[2:]
    return raw


class CommercialCustomerInDB(TimestampedModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    country_code: str = Field(default="IT", min_length=2, max_length=2)
    vat_number_normalized: str = Field(min_length=5, max_length=32)
    legal_name: str = Field(min_length=1, max_length=200)
    fiscal_data: dict = Field(default_factory=dict)
    customer_status: CustomerStatus = "active"


class CommercialCustomerPublic(OmniaBaseModel):
    id: str
    country_code: str
    vat_number_normalized: str
    legal_name: str
    customer_status: CustomerStatus
