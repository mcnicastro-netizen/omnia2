"""Notify Founder + customer after every paid B2C Stripe Checkout."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omnia.b2c_payment_alerts")


def founder_alert_emails() -> List[str]:
    out: List[str] = []
    for key in (
        "FOUNDER_ALERT_EMAIL",
        "OMNIA_ADMIN_EMAIL",
        "ADMIN_EMAIL",
        "SUPER_ADMIN_EMAIL",
    ):
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        for part in raw.split(","):
            email = part.strip().lower()
            if "@" in email and email not in out:
                out.append(email)
    return out


async def notify_b2c_payment(
    *,
    session: Dict[str, Any],
    purchase: Optional[Dict[str, Any]] = None,
) -> None:
    """Best-effort: Stripe already emailed receipt_email; Resend confirms to client + Founder."""
    md = session.get("metadata") or {}
    product_key = md.get("b2c_product_key") or (purchase or {}).get("product_key") or "b2c"
    session_id = session.get("id") or (purchase or {}).get("stripe_session_id") or ""
    user_id = md.get("user_id") or (purchase or {}).get("user_id")
    listing_id = md.get("listing_id") or (purchase or {}).get("listing_id") or ""

    amount_total = session.get("amount_total")
    try:
        amount_eur = round(float(amount_total) / 100.0, 2) if amount_total is not None else (
            (purchase or {}).get("amount_eur")
        )
    except (TypeError, ValueError):
        amount_eur = (purchase or {}).get("amount_eur")

    currency = (session.get("currency") or "eur").upper()
    customer_email = ""
    details = session.get("customer_details") or {}
    if isinstance(details, dict):
        customer_email = (details.get("email") or "").strip()
    if not customer_email:
        customer_email = (session.get("customer_email") or "").strip()

    client_code = ""
    listing_code = ""
    client_name = ""
    try:
        from shared.db.connection import Database
        from shared.ids import ensure_client_code, ensure_listing_code

        db = Database.get()
        if user_id:
            client_code = (await ensure_client_code(db, user_id)) or ""
            u = await db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "name": 1})
            if u:
                client_name = (u.get("name") or "").strip()
                if not customer_email:
                    customer_email = (u.get("email") or "").strip()
        if listing_id:
            listing_code = (await ensure_listing_code(db, listing_id)) or ""
    except Exception:
        logger.exception("b2c payment alert: code resolve failed session=%s", session_id)

    product_label = product_key
    try:
        from apps.billing.b2c_products import B2C_ONE_SHOT_PRODUCTS
        product_label = (B2C_ONE_SHOT_PRODUCTS.get(product_key) or {}).get("label_it") or product_key
    except Exception:
        pass

    amount_txt = f"{amount_eur:.2f} {currency}" if amount_eur is not None else "—"
    vars_common = {
        "product_label": product_label,
        "product_key": product_key,
        "amount": amount_txt,
        "session_id": session_id,
        "client_email": customer_email or "—",
        "client_name": client_name or "—",
        "client_code": client_code or "—",
        "listing_code": listing_code or "—",
        "listing_id": listing_id or "—",
    }

    try:
        from shared.email.client import send_email

        if customer_email:
            await send_email(
                to=customer_email,
                template="b2c_payment_receipt",
                lang="it",
                variables=vars_common,
            )
        for founder_to in founder_alert_emails():
            await send_email(
                to=founder_to,
                template="b2c_payment_founder",
                lang="it",
                variables=vars_common,
            )
    except Exception:
        logger.exception("b2c payment alert email failed session=%s", session_id)

    try:
        from shared.db.connection import Database
        from shared.notifications.center import TYPE_BILLING_PAYMENT, notify_users

        db = Database.get()
        admins = await db.users.find(
            {"role": "super_admin", "is_active": {"$ne": False}},
            {"_id": 0, "id": 1},
        ).to_list(length=20)
        ids = [a["id"] for a in admins if a.get("id")]
        if ids:
            await notify_users(
                ids,
                type=TYPE_BILLING_PAYMENT,
                title=f"Incasso B2C · {amount_txt}",
                body=(
                    f"{product_label} · cliente {client_code or customer_email or user_id}"
                    f"{f' · annuncio {listing_code}' if listing_code else ''}"
                ),
                link="/app/ops",
                meta={
                    "session_id": session_id,
                    "product_key": product_key,
                    "amount_eur": amount_eur,
                    "client_code": client_code,
                    "listing_code": listing_code,
                },
            )
    except Exception:
        logger.exception("b2c payment alert inbox failed session=%s", session_id)
