"""OMNIA — Visura catastale B2C (ImmobilCloud) pagata con Stripe carta.

Flusso:
  1. POST /cloud/visura/checkout  → Stripe Checkout (product b2c_visura_catastale)
  2. Webhook checkout.session.completed → mark paid + kick OpenAPI
  3. GET  /cloud/visura/orders/{session_id} → stato / polling
  4. GET  /cloud/visura/orders/{session_id}/documento → PDF

Mai crediti — solo carta (PRICING_B2C / Founder 15-Sep-2026).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

import stripe
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, HttpUrl

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from shared.openapi_catasto import (
    openapi_enabled,
    request_visura_catastale,
    get_visura_status,
    download_visura_document,
)
from shared.storage import put_object, get_object, ObjStoreError

from apps.billing.b2c_products import B2C_ONE_SHOT_PRODUCTS
from apps.billing.b2c_entitlements import record_uni_purchase

logger = logging.getLogger("omnia.visura_b2c")
router = APIRouter(prefix="/visura", tags=["immocloud-visura"])

PRODUCT_KEY = "b2c_visura_catastale"
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


def _stripe_enabled() -> bool:
    return (os.environ.get("STRIPE_ENABLED") or "").lower() == "true" and bool(stripe.api_key)


def hash_visura_payload(payload: Dict[str, Any]) -> str:
    keys = ("provincia", "comune", "foglio", "particella", "subalterno", "tipo_catasto", "tipo_visura")
    canonical = {k: (payload.get(k) or None) for k in keys}
    blob = json.dumps(canonical, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class VisuraCheckoutBody(BaseModel):
    provincia: str = Field(min_length=2, max_length=2)
    comune: str = Field(min_length=1, max_length=120)
    foglio: str = Field(min_length=1, max_length=20)
    particella: str = Field(min_length=1, max_length=20)
    subalterno: Optional[str] = Field(default=None, max_length=20)
    tipo_catasto: str = Field(default="F", pattern=r"^[FTft]$")
    tipo_visura: str = Field(default="ordinaria", pattern=r"^(ordinaria|storica)$")
    success_url: HttpUrl
    cancel_url: HttpUrl


def _get_or_create_price() -> str:
    catalog = B2C_ONE_SHOT_PRODUCTS[PRODUCT_KEY]
    lookup = catalog["stripe_lookup_key"]
    prices = stripe.Price.list(lookup_keys=[lookup], active=True, limit=1).data
    if prices:
        return prices[0].id
    product = stripe.Product.create(
        name=catalog["label_it"],
        metadata={"b2c_product_key": PRODUCT_KEY},
    )
    price = stripe.Price.create(
        product=product.id,
        unit_amount=int(round(float(catalog["price_eur"]) * 100)),
        currency="eur",
        lookup_key=lookup,
        transfer_lookup_key=True,
        metadata={"b2c_product_key": PRODUCT_KEY},
    )
    return price.id


@router.get("/catalog")
async def visura_catalog():
    """Public price card for the Visura page (no auth)."""
    catalog = B2C_ONE_SHOT_PRODUCTS.get(PRODUCT_KEY) or {}
    return {
        "product_key": PRODUCT_KEY,
        "label_it": catalog.get("label_it"),
        "price_eur": float(catalog.get("price_eur") or 4.90),
        "stripe_enabled": _stripe_enabled(),
        "openapi_enabled": openapi_enabled(),
        "payment": "card",  # never credits
    }


@router.post("/checkout")
async def visura_checkout(
    payload: VisuraCheckoutBody,
    user: dict = Depends(get_current_user),
):
    """Start Stripe card checkout, then fulfill via OpenAPI after payment."""
    if not _stripe_enabled():
        raise HTTPException(status_code=503, detail={
            "code": "stripe_not_configured",
            "message": "Pagamento carta in preparazione. Riprova a breve.",
        })
    if not openapi_enabled():
        raise HTTPException(status_code=503, detail={
            "code": "openapi_not_configured",
            "message": "Servizio visure temporaneamente non disponibile.",
        })

    catalog = B2C_ONE_SHOT_PRODUCTS[PRODUCT_KEY]
    daily_cap = int(catalog.get("daily_limit_per_user") or 10)
    db = Database.get()
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    used = await db.b2c_purchases.count_documents({
        "user_id": user["id"],
        "product_key": PRODUCT_KEY,
        "status": "paid",
        "created_at": {"$gte": start.isoformat()},
    })
    if used >= daily_cap:
        raise HTTPException(status_code=429, detail={
            "code": "daily_cap_reached",
            "message": f"Hai raggiunto il limite di {daily_cap} visure oggi.",
        })

    req = {
        "provincia": payload.provincia.strip().upper()[:2],
        "comune": payload.comune.strip(),
        "foglio": payload.foglio.strip(),
        "particella": payload.particella.strip(),
        "subalterno": (payload.subalterno or "").strip() or None,
        "tipo_catasto": payload.tipo_catasto.upper()[:1],
        "tipo_visura": payload.tipo_visura,
    }
    ph = hash_visura_payload(req)

    try:
        price_id = _get_or_create_price()
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{str(payload.success_url)}?session_id={{CHECKOUT_SESSION_ID}}&product=visura",
            cancel_url=str(payload.cancel_url),
            customer_email=user.get("email"),
            metadata={
                "b2c_product_key": PRODUCT_KEY,
                "user_id": user["id"],
                "payload_hash": ph,
            },
            payment_intent_data={
                "metadata": {
                    "b2c_product_key": PRODUCT_KEY,
                    "user_id": user["id"],
                    "payload_hash": ph,
                },
            },
        )
    except stripe.error.StripeError as e:
        logger.exception("visura b2c stripe error")
        raise HTTPException(status_code=502, detail={"code": "stripe_error", "message": str(e)}) from e

    await record_uni_purchase(
        user_id=user["id"],
        stripe_session_id=session["id"],
        payload_hash=ph,
        product_key=PRODUCT_KEY,
        status="pending",
    )

    now = datetime.now(timezone.utc).isoformat()
    order = {
        "id": str(uuid4()),
        "user_id": user["id"],
        "product_key": PRODUCT_KEY,
        "stripe_session_id": session["id"],
        "payload_hash": ph,
        "request": req,
        "status": "awaiting_payment",
        "external_id": None,
        "storage_path": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.b2c_visura_orders.insert_one(order)

    return {
        "checkout_url": session["url"],
        "session_id": session["id"],
        "price_eur": float(catalog["price_eur"]),
        "product_key": PRODUCT_KEY,
    }


async def fulfill_paid_visura_order(session_id: str) -> Optional[dict]:
    """Kick OpenAPI request after Stripe payment. Idempotent."""
    db = Database.get()
    order = await db.b2c_visura_orders.find_one({"stripe_session_id": session_id})
    if not order:
        logger.warning("visura fulfill: no order for session=%s", session_id)
        return None
    if order.get("external_id") and order.get("status") in {"ready", "processing", "attached"}:
        return order

    req = order.get("request") or {}
    try:
        raw = await request_visura_catastale(
            provincia=req["provincia"],
            comune=req["comune"],
            foglio=req["foglio"],
            particella=req["particella"],
            subalterno=req.get("subalterno"),
            tipo_catasto=req.get("tipo_catasto") or "F",
            tipo_visura=req.get("tipo_visura") or "ordinaria",
            formato="pdf",
        )
    except Exception as e:
        logger.exception("visura OpenAPI create failed session=%s", session_id)
        now = datetime.now(timezone.utc).isoformat()
        await db.b2c_visura_orders.update_one(
            {"stripe_session_id": session_id},
            {"$set": {"status": "failed", "error": str(e)[:300], "updated_at": now}},
        )
        return None

    ext_id = str(raw.get("id") or "")
    stato = str(raw.get("stato") or "").lower()
    status = "ready" if "evas" in stato else "processing"
    now = datetime.now(timezone.utc).isoformat()
    await db.b2c_visura_orders.update_one(
        {"stripe_session_id": session_id},
        {"$set": {
            "status": status,
            "external_id": ext_id,
            "raw_create": raw,
            "updated_at": now,
        }},
    )
    return await db.b2c_visura_orders.find_one({"stripe_session_id": session_id}, {"_id": 0})


@router.get("/orders/{session_id}")
async def visura_order_status(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    db = Database.get()
    order = await db.b2c_visura_orders.find_one(
        {"stripe_session_id": session_id, "user_id": user["id"]},
        {"_id": 0, "raw_create": 0, "raw_status": 0},
    )
    if not order:
        raise HTTPException(404, "order_not_found")

    purchase = await db.b2c_purchases.find_one(
        {"stripe_session_id": session_id, "user_id": user["id"]},
        {"_id": 0, "status": 1, "paid_at": 1, "expires_at": 1},
    )
    pay_status = (purchase or {}).get("status") or "pending"

    if pay_status == "paid" and order.get("status") in {"awaiting_payment", "failed"} and not order.get("external_id"):
        order = await fulfill_paid_visura_order(session_id) or order

    if order.get("external_id") and order.get("status") == "processing" and openapi_enabled():
        try:
            remote = await get_visura_status(order["external_id"])
            stato = str(remote.get("stato") or "").lower()
            mapped = "processing"
            if "evas" in stato:
                mapped = "ready"
            elif "error" in stato or "fail" in stato:
                mapped = "failed"
            now = datetime.now(timezone.utc).isoformat()
            await db.b2c_visura_orders.update_one(
                {"stripe_session_id": session_id},
                {"$set": {"status": mapped, "raw_status": remote, "updated_at": now}},
            )
            order["status"] = mapped
            order["updated_at"] = now
        except Exception as e:
            order["poll_error"] = str(e)[:200]

    catalog = B2C_ONE_SHOT_PRODUCTS.get(PRODUCT_KEY) or {}
    return {
        **order,
        "payment_status": pay_status,
        "price_eur": float(catalog.get("price_eur") or 4.90),
        "download_ready": order.get("status") == "ready",
    }


@router.get("/orders/{session_id}/documento")
async def visura_order_pdf(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    db = Database.get()
    order = await db.b2c_visura_orders.find_one(
        {"stripe_session_id": session_id, "user_id": user["id"]},
    )
    if not order:
        raise HTTPException(404, "order_not_found")
    purchase = await db.b2c_purchases.find_one(
        {"stripe_session_id": session_id, "user_id": user["id"], "status": "paid"},
    )
    if not purchase:
        raise HTTPException(402, detail={"code": "payment_required", "message": "Pagamento non confermato"})
    if not order.get("external_id"):
        await fulfill_paid_visura_order(session_id)
        order = await db.b2c_visura_orders.find_one({"stripe_session_id": session_id}) or order
    if not order.get("external_id"):
        raise HTTPException(409, detail="visura_not_ready")

    # Cache in object storage
    path = order.get("storage_path")
    pdf: Optional[bytes] = None
    if path:
        try:
            obj = get_object(path)
            pdf = obj[0] if isinstance(obj, tuple) else obj
        except Exception:
            pdf = None
    if not pdf:
        try:
            pdf = await download_visura_document(order["external_id"])
        except Exception as e:
            raise HTTPException(502, detail=str(e)[:300]) from e
        path = f"omnia/b2c-visura/{user['id']}/{order['id']}.pdf"
        try:
            put_object(path, pdf, "application/pdf")
            await db.b2c_visura_orders.update_one(
                {"stripe_session_id": session_id},
                {"$set": {"storage_path": path, "status": "ready",
                          "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
        except ObjStoreError:
            logger.warning("visura pdf storage unavailable — returning bytes without cache")

    filename = f"visura-catastale-{order.get('request', {}).get('comune', 'documento')}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
