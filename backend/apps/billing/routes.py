"""OMNIA — Billing API endpoints (Stripe checkout, portal, webhook, credits).

M4.S3/S4 — Stripe integrato in test mode (claimable sandbox Emergent).
Il Founder claimerà l'account tramite `onboarding_url` (vedi /app/memory/STRIPE_ONBOARDING.md)
per passare a live mode. Nessuna modifica di codice richiesta.

No brand mentions (D-051) — pricing rispetta LAUNCH_PLANS di plans.py.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request

from shared.auth.dependencies import get_current_user, require_roles
from shared.db.connection import Database

from apps.billing.plans import (
    get_active_catalog, get_plan, CREDIT_PACKAGES, CREDIT_COSTS,
)
from apps.billing.models import (
    CheckoutSessionRequest, CreditPurchaseRequest,
)

logger = logging.getLogger("omnia.billing")
router = APIRouter(prefix="/billing", tags=["billing"])

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def _is_enabled() -> bool:
    return (os.environ.get("STRIPE_ENABLED") or "").lower() == "true" and bool(
        stripe.api_key
    )


def _guard_enabled() -> None:
    if not _is_enabled():
        raise HTTPException(
            status_code=503,
            detail={"error": "stripe_not_configured",
                    "message": "Billing è in preparazione."},
        )


def _build_success_url(origin: str) -> str:
    origin = origin.rstrip("/")
    return f"{origin}/it/app/settings/billing?session_id={{CHECKOUT_SESSION_ID}}&ok=1"


def _build_cancel_url(origin: str) -> str:
    origin = origin.rstrip("/")
    return f"{origin}/it/app/settings/billing?cancel=1"


# --------------- Public: plan catalog (no auth) --------------------

@router.get("/plans")
async def list_plans():
    """Public plan listing — usato da landing e Settings > Billing."""
    catalog = get_active_catalog()
    return {
        "plans": [p.model_dump() for p in catalog.values()],
        "credit_packages": [pkg.model_dump() for pkg in CREDIT_PACKAGES],
        "credit_costs": CREDIT_COSTS,
        "trial_days": 14,
        "currency": "eur",
        "enabled": _is_enabled(),
        "mode": os.environ.get("STRIPE_MODE", "test"),
        "publishable_key": os.environ.get("STRIPE_PUBLISHABLE_KEY", ""),
    }


# --------------- Authenticated: subscription lifecycle -----------

@router.get("/subscription")
async def get_subscription(user: dict = Depends(get_current_user)):
    """Current agency subscription state (if any)."""
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        return {"subscription": None, "wallet": {"balance": 0}}
    aid = agency_ids[0]
    sub = await db.subscriptions.find_one({"agency_id": aid}, {"_id": 0})
    wallet = await db.credit_wallets.find_one({"agency_id": aid}, {"_id": 0})
    return {
        "subscription": sub,
        "wallet": wallet or {"agency_id": aid, "balance": 0},
    }


@router.post("/checkout")
async def create_checkout(
    payload: CheckoutSessionRequest,
    request: Request,
    user: dict = Depends(require_roles("super_admin", "agency_admin", "group_admin")),
):
    """Create a Stripe Checkout session for a subscription tier."""
    _guard_enabled()
    plan = get_plan(payload.plan_tier)  # type: ignore[arg-type]
    if not plan:
        raise HTTPException(status_code=400, detail="unknown_plan_tier")

    lookup_key = f"{plan.tier}_{payload.billing_cycle}"
    prices = stripe.Price.list(lookup_keys=[lookup_key], active=True, limit=1).data
    if not prices:
        raise HTTPException(
            status_code=503,
            detail=f"price_not_found:{lookup_key} — run setup_stripe.py",
        )
    price = prices[0]

    origin = payload.success_url or str(request.base_url)
    agency_id = user["agency_ids"][0] if user.get("agency_ids") else None

    try:
        session = stripe.checkout.Session.create(
            line_items=[{"price": price.id, "quantity": 1}],
            mode="subscription",
            success_url=_build_success_url(origin),
            cancel_url=payload.cancel_url or _build_cancel_url(origin),
            customer_email=user["email"],
            subscription_data={"trial_period_days": plan.trial_days},
            metadata={
                "agency_id": agency_id or "",
                "user_id": user["id"],
                "tier": plan.tier,
                "billing_cycle": payload.billing_cycle,
                "kind": "subscription",
            },
        )
    except stripe.error.StripeError as e:
        logger.exception("stripe checkout error: %s", e)
        raise HTTPException(status_code=502, detail={"stripe_error": str(e)})

    # persist payment_transactions BEFORE returning
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    await db.payment_transactions.insert_one({
        "session_id": session.id,
        "agency_id": agency_id,
        "user_id": user["id"],
        "lookup_key": lookup_key,
        "amount": (price.unit_amount or 0) / 100.0,
        "currency": price.currency,
        "kind": "subscription",
        "tier": plan.tier,
        "billing_cycle": payload.billing_cycle,
        "status": "initiated",
        "payment_status": "pending",
        "created_at": now,
        "updated_at": now,
    })
    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/credits/purchase")
async def buy_credits(
    payload: CreditPurchaseRequest,
    request: Request,
    user: dict = Depends(require_roles("super_admin", "agency_admin", "group_admin")),
):
    """Buy a credit package (one-off payment)."""
    _guard_enabled()
    pkg = next((p for p in CREDIT_PACKAGES if p.key == payload.package_key), None)
    if not pkg:
        raise HTTPException(status_code=400, detail="unknown_package")

    prices = stripe.Price.list(lookup_keys=[pkg.key], active=True, limit=1).data
    if not prices:
        raise HTTPException(status_code=503, detail=f"price_not_found:{pkg.key}")
    price = prices[0]

    origin = payload.success_url or str(request.base_url)
    agency_id = user["agency_ids"][0] if user.get("agency_ids") else None
    try:
        session = stripe.checkout.Session.create(
            line_items=[{"price": price.id, "quantity": 1}],
            mode="payment",
            success_url=_build_success_url(origin),
            cancel_url=payload.cancel_url or _build_cancel_url(origin),
            customer_email=user["email"],
            metadata={
                "agency_id": agency_id or "",
                "user_id": user["id"],
                "package_key": pkg.key,
                "credits": str(pkg.credits),
                "kind": "credits_topup",
            },
        )
    except stripe.error.StripeError as e:
        logger.exception("stripe checkout credits error: %s", e)
        raise HTTPException(status_code=502, detail={"stripe_error": str(e)})

    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    await db.payment_transactions.insert_one({
        "session_id": session.id,
        "agency_id": agency_id,
        "user_id": user["id"],
        "lookup_key": pkg.key,
        "amount": pkg.price_eur,
        "currency": price.currency,
        "kind": "credits_topup",
        "credits": pkg.credits,
        "status": "initiated",
        "payment_status": "pending",
        "created_at": now,
        "updated_at": now,
    })
    return {"checkout_url": session.url, "session_id": session.id}


@router.get("/status/{session_id}")
async def get_session_status(session_id: str, user: dict = Depends(get_current_user)):
    """Frontend polling on success page. Auth-bound (H15): only the initiating
    user/agency (or super_admin) can read the transaction status."""
    db = Database.get()
    record = await db.payment_transactions.find_one(
        {"session_id": session_id},
        {"_id": 0, "session_id": 1, "status": 1, "payment_status": 1, "kind": 1,
         "tier": 1, "credits": 1, "user_id": 1, "agency_id": 1},
    )
    if not record:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    if user.get("role") != "super_admin":
        if record.get("user_id") != user["id"] and record.get("agency_id") not in (user.get("agency_ids") or []):
            raise HTTPException(status_code=403, detail="forbidden")
    record.pop("user_id", None)
    record.pop("agency_id", None)

    # Webhook fallback: if still pending, ask Stripe directly.
    if record.get("payment_status") != "paid":
        try:
            s = stripe.checkout.Session.retrieve(session_id)
            if s.payment_status == "paid" or s.status == "complete":
                now = datetime.now(timezone.utc).isoformat()
                await db.payment_transactions.update_one(
                    {"session_id": session_id, "payment_status": {"$ne": "paid"}},
                    {"$set": {"status": "completed", "payment_status": "paid",
                              "stripe_subscription_id": s.subscription,
                              "stripe_payment_intent_id": s.payment_intent,
                              "updated_at": now}},
                )
                # Apply side-effect (grant credits or activate sub)
                await _apply_session_side_effects(session_id)
                record = await db.payment_transactions.find_one(
                    {"session_id": session_id},
                    {"_id": 0, "session_id": 1, "status": 1, "payment_status": 1,
                     "kind": 1, "tier": 1, "credits": 1},
                )
        except stripe.error.StripeError:
            pass
    return record


@router.post("/portal")
async def customer_portal(request: Request, user: dict = Depends(get_current_user)):
    """Return a Stripe Customer Portal link for the current agency."""
    _guard_enabled()
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        raise HTTPException(status_code=400, detail="no_agency")
    sub = await db.subscriptions.find_one({"agency_id": agency_ids[0]}, {"stripe_customer_id": 1})
    if not sub or not sub.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="no_stripe_customer")
    origin = str(request.base_url).rstrip("/")
    try:
        portal = stripe.billing_portal.Session.create(
            customer=sub["stripe_customer_id"],
            return_url=f"{origin}/it/app/settings/billing",
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail={"stripe_error": str(e)})
    return {"portal_url": portal.url}


# --------------- Webhook (signature-verified) --------------------

async def _apply_session_side_effects(session_id: str) -> None:
    """Grant credits (kind=credits_topup) or activate subscription (kind=subscription).

    Idempotent: guarded by payment_status=paid + `applied_at` field.
    """
    db = Database.get()
    tx = await db.payment_transactions.find_one({"session_id": session_id})
    if not tx or tx.get("payment_status") != "paid" or tx.get("applied_at"):
        return
    now = datetime.now(timezone.utc).isoformat()

    if tx["kind"] == "credits_topup":
        credits = int(tx.get("credits") or 0)
        agency_id = tx.get("agency_id")
        if credits > 0 and agency_id:
            wallet = await db.credit_wallets.find_one_and_update(
                {"agency_id": agency_id},
                {"$inc": {"balance": credits}, "$set": {"last_topup_at": now, "updated_at": now}},
                upsert=True, return_document=True,
            )
            new_balance = (wallet or {}).get("balance", credits)
            await db.credit_ledger.insert_one({
                "id": __import__("uuid").uuid4().hex,
                "agency_id": agency_id,
                "delta": credits,
                "reason": f"topup_{tx.get('lookup_key')}",
                "balance_after": new_balance,
                "ref_id": session_id, "ref_type": "checkout_session",
                "created_at": now,
            })
            logger.info("Credits granted: agency=%s +%d (session=%s)", agency_id, credits, session_id)

    elif tx["kind"] == "subscription":
        # Load Stripe subscription for period info
        agency_id = tx.get("agency_id")
        if not agency_id:
            return
        stripe_sub_id = tx.get("stripe_subscription_id")
        stripe_customer_id = None
        current_period_start = None
        current_period_end = None
        status = "active"
        if stripe_sub_id:
            try:
                s = stripe.Subscription.retrieve(stripe_sub_id)
                stripe_customer_id = s.customer
                status = s.status
                current_period_start = datetime.fromtimestamp(s.current_period_start, tz=timezone.utc).isoformat() if s.current_period_start else None
                current_period_end = datetime.fromtimestamp(s.current_period_end, tz=timezone.utc).isoformat() if s.current_period_end else None
            except stripe.error.StripeError:
                pass
        await db.subscriptions.update_one(
            {"agency_id": agency_id},
            {"$set": {
                "agency_id": agency_id,
                "tier": tx.get("tier"),
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_sub_id,
                "status": status,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "cancel_at_period_end": False,
                "updated_at": now,
            }, "$setOnInsert": {"id": __import__("uuid").uuid4().hex, "created_at": now}},
            upsert=True,
        )
        logger.info("Subscription applied: agency=%s tier=%s", agency_id, tx.get("tier"))

    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"applied_at": now}},
    )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Stripe webhook handler with signature verification."""
    if not _is_enabled():
        raise HTTPException(status_code=503, detail="stripe_not_configured")
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="webhook_secret_missing")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.warning("webhook invalid sig: %s", e)
        raise HTTPException(status_code=400, detail="invalid_signature")

    db = Database.get()
    obj = event["data"]["object"]
    etype = event["type"]
    now = datetime.now(timezone.utc).isoformat()

    if etype == "checkout.session.completed":
        session_id = obj["id"]
        await db.payment_transactions.update_one(
            {"session_id": session_id, "payment_status": {"$ne": "paid"}},
            {"$set": {"status": "completed",
                      "payment_status": obj.get("payment_status", "paid"),
                      "stripe_subscription_id": obj.get("subscription"),
                      "stripe_payment_intent_id": obj.get("payment_intent"),
                      "updated_at": now}},
        )
        await _apply_session_side_effects(session_id)
        # Cap. 21 · B2C one-shot (valuator UNI PDF, staging, legal — future)
        md = obj.get("metadata") or {}
        if md.get("b2c_product_key"):
            from apps.billing.b2c_checkout import apply_b2c_purchase_side_effects
            await apply_b2c_purchase_side_effects(obj)

    elif etype == "customer.subscription.updated":
        agency_id = (obj.get("metadata") or {}).get("agency_id")
        current_period_start = datetime.fromtimestamp(obj["current_period_start"], tz=timezone.utc).isoformat() if obj.get("current_period_start") else None
        current_period_end = datetime.fromtimestamp(obj["current_period_end"], tz=timezone.utc).isoformat() if obj.get("current_period_end") else None
        upd = {
            "status": obj.get("status"),
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "cancel_at_period_end": obj.get("cancel_at_period_end", False),
            "updated_at": now,
        }
        q = {"stripe_subscription_id": obj["id"]} if not agency_id else {"agency_id": agency_id}
        await db.subscriptions.update_one(q, {"$set": upd})

    elif etype == "invoice.paid":
        await db.invoices.insert_one({
            "id": __import__("uuid").uuid4().hex,
            "agency_id": (obj.get("metadata") or {}).get("agency_id"),
            "stripe_invoice_id": obj["id"],
            "amount_paid": (obj.get("amount_paid") or 0) / 100.0,
            "amount_due": (obj.get("amount_due") or 0) / 100.0,
            "currency": obj.get("currency", "eur"),
            "status": "paid",
            "hosted_invoice_url": obj.get("hosted_invoice_url"),
            "pdf_url": obj.get("invoice_pdf"),
            "created_at": now, "updated_at": now,
        })

    elif etype == "invoice.payment_failed":
        stripe_sub_id = obj.get("subscription")
        if stripe_sub_id:
            await db.subscriptions.update_one(
                {"stripe_subscription_id": stripe_sub_id},
                {"$set": {"status": "past_due", "updated_at": now}},
            )

    elif etype in ("checkout.session.expired", "checkout.session.async_payment_failed"):
        session_id = obj["id"]
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": "failed", "payment_status": "failed", "updated_at": now}},
        )

    return {"received": True}


# --------------- Credit consumption (internal API) -----------------

async def debit_credits(agency_id: str, amount: int, reason: str,
                        ref_id: str = None, ref_type: str = None) -> int:
    """Atomic debit of credits from an agency wallet.

    Returns new balance. Raises HTTPException(402) if insufficient.
    Called by internal services (valuator, HAL, virtual staging, ...).
    """
    if amount <= 0:
        raise ValueError("amount_must_be_positive")
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    wallet = await db.credit_wallets.find_one_and_update(
        {"agency_id": agency_id, "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount}, "$set": {"updated_at": now}},
        return_document=True,
    )
    if not wallet:
        raise HTTPException(status_code=402, detail={
            "error": "insufficient_credits",
            "required": amount,
            "reason": reason,
        })
    new_balance = wallet["balance"]
    await db.credit_ledger.insert_one({
        "id": __import__("uuid").uuid4().hex,
        "agency_id": agency_id,
        "delta": -amount,
        "reason": reason,
        "balance_after": new_balance,
        "ref_id": ref_id,
        "ref_type": ref_type,
        "created_at": now,
    })
    return new_balance
