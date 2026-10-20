"""Founder Ops — finance helpers (incassi per voce, fatture, P&L mensile).

D-117: il Founder deve vedere tutti gli incassi distinti per voce,
le fatture Stripe e un riepilogo mensile (incasso vs costo stimato).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger("omnia.founder_ops_finance")

# COGS unitari B2C (stime operative — non fatture provider).
B2C_UNIT_COGS_EUR: Dict[str, float] = {
    "b2c_visura_catastale": 0.40,   # OpenAPI.it / partner catasto
    "b2c_hal_legal_query": 0.025,   # Gemini + Tavily (ordine di grandezza)
    "b2c_staging_render": 0.056,    # allineato a staging job
    "b2c_valuator_uni_pdf": 0.01,   # LLM report
    # Boost = quasi solo piattaforma / Stripe
    "b2c_vetrina_30": 0.0,
    "b2c_premium_30": 0.0,
    "b2c_premium_90": 0.0,
    "b2c_premium_180": 0.0,
    "b2c_top_30": 0.0,
    "b2c_top_90": 0.0,
    "b2c_top_180": 0.0,
}

# Stima commissioni Stripe EU carta: 1,5% + €0,25
STRIPE_PCT = 0.015
STRIPE_FIXED_EUR = 0.25

_KIND_LABELS = {
    "subscription": "Abbonamenti agenzia",
    "credits_topup": "Ricariche crediti",
    "storage": "Archivio storage",
}


def purchase_amount_eur(doc: dict, catalog: Optional[dict] = None) -> float:
    """Resolve paid amount: ledger → catalog fallback."""
    for key in ("amount_eur", "price_eur"):
        raw = doc.get(key)
        if raw is not None:
            try:
                return round(float(raw), 2)
            except (TypeError, ValueError):
                pass
    if catalog:
        try:
            return round(float(catalog.get("price_eur") or 0), 2)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def stripe_fees_eur(revenue: float, count: int) -> float:
    if count <= 0 or revenue <= 0:
        return 0.0
    return round(revenue * STRIPE_PCT + count * STRIPE_FIXED_EUR, 2)


def build_revenue_lines(
    *,
    b2c_rows: List[dict],
    b2b_rows: List[dict],
    catalog: Dict[str, dict],
) -> Tuple[List[dict], float, float, float, float]:
    """Aggregate paid purchases into distinct revenue lines.

    Returns (lines, revenue_total, product_cogs_total, stripe_fees_total, margin).
    """
    buckets: Dict[str, dict] = {}

    for doc in b2c_rows:
        pk = doc.get("product_key") or "b2c_other"
        cat = catalog.get(pk) or {}
        amount = purchase_amount_eur(doc, cat)
        label = cat.get("label_it") or pk
        unit_cogs = float(B2C_UNIT_COGS_EUR.get(pk, 0.0))
        b = buckets.setdefault(pk, {
            "key": pk,
            "label": label,
            "channel": "b2c",
            "count": 0,
            "revenue_eur": 0.0,
            "unit_cogs_eur": unit_cogs,
            "cogs_eur": 0.0,
        })
        b["count"] += 1
        b["revenue_eur"] = round(b["revenue_eur"] + amount, 2)
        b["cogs_eur"] = round(b["cogs_eur"] + unit_cogs, 2)

    for doc in b2b_rows:
        kind = doc.get("kind") or "subscription"
        key = f"b2b_{kind}"
        try:
            amount = float(doc.get("amount") or doc.get("amount_eur") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        label = _KIND_LABELS.get(kind, kind)
        b = buckets.setdefault(key, {
            "key": key,
            "label": label,
            "channel": "b2b",
            "count": 0,
            "revenue_eur": 0.0,
            "unit_cogs_eur": 0.0,
            "cogs_eur": 0.0,
        })
        b["count"] += 1
        b["revenue_eur"] = round(b["revenue_eur"] + amount, 2)

    # Ensure catalog B2C products appear even with 0 sales (pronetezza voci).
    for pk, cat in catalog.items():
        if pk not in buckets:
            buckets[pk] = {
                "key": pk,
                "label": cat.get("label_it") or pk,
                "channel": "b2c",
                "count": 0,
                "revenue_eur": 0.0,
                "unit_cogs_eur": float(B2C_UNIT_COGS_EUR.get(pk, 0.0)),
                "cogs_eur": 0.0,
            }

    lines: List[dict] = []
    rev_total = 0.0
    cogs_total = 0.0
    tx_count = 0
    for key in sorted(buckets.keys(), key=lambda k: (-buckets[k]["revenue_eur"], buckets[k]["label"])):
        b = buckets[key]
        fees = stripe_fees_eur(b["revenue_eur"], b["count"]) if b["channel"] == "b2c" else stripe_fees_eur(b["revenue_eur"], b["count"])
        # Stripe fee on all card rails (B2B checkout too)
        line_cogs = round(b["cogs_eur"] + fees, 2)
        margin = round(b["revenue_eur"] - line_cogs, 2)
        lines.append({
            **b,
            "stripe_fees_eur": fees,
            "cogs_total_eur": line_cogs,
            "margin_eur": margin,
        })
        rev_total += b["revenue_eur"]
        cogs_total += line_cogs
        tx_count += int(b["count"])

    rev_total = round(rev_total, 2)
    cogs_total = round(cogs_total, 2)
    fees_total = round(sum(float(x.get("stripe_fees_eur") or 0) for x in lines), 2)
    margin_total = round(rev_total - cogs_total, 2)
    return lines, rev_total, cogs_total, fees_total, margin_total


def month_label(month_key: str) -> str:
    """'2026-10' → 'Ottobre 2026'."""
    months = (
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
    )
    try:
        y, m = month_key.split("-")
        return f"{months[int(m) - 1]} {y}"
    except Exception:
        return month_key


async def sync_stripe_invoices(db, *, limit: int = 40) -> int:
    """Import recent Stripe invoices into Mongo (idempotent upsert). Returns upserted count."""
    key = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        return 0
    try:
        import stripe
        stripe.api_key = key
        invoices = stripe.Invoice.list(limit=limit)
    except Exception:
        logger.warning("stripe Invoice.list failed", exc_info=True)
        return 0

    n = 0
    now = datetime.now(timezone.utc).isoformat()
    rows = list(getattr(invoices, "data", None) or invoices or [])
    for inv in rows[:limit]:
        sid = getattr(inv, "id", None) or (inv.get("id") if isinstance(inv, dict) else None)
        if not sid:
            continue
        amount_paid = getattr(inv, "amount_paid", None)
        if amount_paid is None and isinstance(inv, dict):
            amount_paid = inv.get("amount_paid")
        amount_due = getattr(inv, "amount_due", None)
        if amount_due is None and isinstance(inv, dict):
            amount_due = inv.get("amount_due")

        def _g(name, default=None):
            if isinstance(inv, dict):
                return inv.get(name, default)
            return getattr(inv, name, default)

        period_start = _g("period_start")
        period_end = _g("period_end")
        created = _g("created")
        lines = _g("lines") or {}
        line_data = []
        if hasattr(lines, "data"):
            line_data = list(lines.data or [])
        elif isinstance(lines, dict):
            line_data = list(lines.get("data") or [])
        desc = _g("description")
        if not desc and line_data:
            first = line_data[0]
            desc = first.get("description") if isinstance(first, dict) else getattr(first, "description", None)

        doc = {
            "stripe_invoice_id": sid,
            "number": _g("number"),
            "customer_email": _g("customer_email"),
            "customer_name": _g("customer_name"),
            "description": desc,
            "amount_paid": (amount_paid or 0) / 100.0,
            "amount_due": (amount_due or 0) / 100.0,
            "currency": _g("currency") or "eur",
            "status": _g("status") or "unknown",
            "hosted_invoice_url": _g("hosted_invoice_url"),
            "pdf_url": _g("invoice_pdf"),
            "period_start": datetime.fromtimestamp(period_start, tz=timezone.utc).isoformat() if period_start else None,
            "period_end": datetime.fromtimestamp(period_end, tz=timezone.utc).isoformat() if period_end else None,
            "agency_id": ((_g("metadata") or {}) or {}).get("agency_id") if isinstance(_g("metadata") or {}, dict) else None,
            "updated_at": now,
        }
        if created:
            try:
                doc.setdefault(
                    "stripe_created_at",
                    datetime.fromtimestamp(created, tz=timezone.utc).isoformat(),
                )
            except Exception:
                pass

        existing = await db.invoices.find_one({"stripe_invoice_id": sid})
        if existing:
            await db.invoices.update_one({"stripe_invoice_id": sid}, {"$set": doc})
        else:
            doc["id"] = uuid4().hex
            doc["created_at"] = now
            await db.invoices.insert_one(doc)
        n += 1
    return n


async def backfill_b2c_amounts(db, catalog: Dict[str, dict]) -> int:
    """Fill amount_eur on paid purchases missing it (legacy dogfood rows)."""
    cur = db.b2c_purchases.find({
        "status": {"$in": ["paid", "complete", "completed", "succeeded"]},
        "$or": [
            {"amount_eur": {"$exists": False}},
            {"amount_eur": None},
        ],
    })
    n = 0
    async for doc in cur:
        pk = doc.get("product_key") or ""
        amount = purchase_amount_eur(doc, catalog.get(pk))
        await db.b2c_purchases.update_one(
            {"_id": doc["_id"]},
            {"$set": {"amount_eur": amount, "price_eur": amount}},
        )
        n += 1
    return n
