"""CommercialCustomer helpers — B01 / D-173."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException

from shared.models.commercial_customer import (
    CommercialCustomerInDB,
    normalize_vat_number,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def get_or_create_commercial_customer(
    db,
    *,
    vat_number: str,
    legal_name: str,
    country_code: str = "IT",
    fiscal_extra: Optional[dict] = None,
) -> dict:
    """Return existing customer for normalized VAT or create one.

    Does not invent VAT: empty/missing raises.
    """
    normalized = normalize_vat_number(vat_number)
    if not normalized:
        raise HTTPException(
            status_code=400,
            detail={"error": "vat_required", "hint": "P.IVA obbligatoria per il cliente commerciale"},
        )
    country = (country_code or "IT").strip().upper()[:2]
    existing = await db.commercial_customers.find_one(
        {"country_code": country, "vat_number_normalized": normalized},
        {"_id": 0},
    )
    if existing:
        return existing

    customer = CommercialCustomerInDB(
        id=str(uuid4()),
        country_code=country,
        vat_number_normalized=normalized,
        legal_name=(legal_name or normalized).strip()[:200] or normalized,
        fiscal_data={
            "vat_number_raw": (vat_number or "").strip(),
            **(fiscal_extra or {}),
        },
        customer_status="active",
        commercial_status="pre_activation",
        operational_status="none",
    )
    doc = customer.model_dump()
    # Sparse unique indexes (e.g. stripe_customer_id) treat explicit null as a
    # value — omit unset optional uniques so concurrent creates do not collide
    # on null (W3 P.IVA race / 1 P.IVA = 1 CC still enforced by VAT unique).
    for sparse_key in ("stripe_customer_id", "main_admin_user_id"):
        if doc.get(sparse_key) in (None, ""):
            doc.pop(sparse_key, None)
    try:
        await db.commercial_customers.insert_one(doc)
    except Exception:
        # Race on unique index (VAT or sparse) — re-read by VAT SoT
        existing = await db.commercial_customers.find_one(
            {"country_code": country, "vat_number_normalized": normalized},
            {"_id": 0},
        )
        if existing:
            return existing
        raise
    return doc
