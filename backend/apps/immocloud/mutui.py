"""OMNIA — M5.S5 Comparatore Mutui (motore in-house, D-037).

Simulazione ORIENTATIVA: ammortamento francese, TAN = benchmark + spread,
TAEG via IRR (spese incluse), controllo soglia usura TEGM, vincoli LTV e
sostenibilità rata/reddito. NON è offerta né mediazione creditizia
(art. 128-sexies TUB) — disclaimer obbligatorio lato UI.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from shared.db.connection import Database

from .data.mortgage_data import (
    BANK_OFFERS,
    DATA_UPDATED_AT,
    DURATIONS,
    EURIBOR_3M,
    EURIRS,
    MAX_LTV_STANDARD,
    MAX_LTV_UNDER36,
    MAX_RATA_REDDITO,
    TEGM,
)

logger = logging.getLogger("omnia.mutui")
router = APIRouter(prefix="/mutui", tags=["cloud-mutui"])

IMPOSTA_SOSTITUTIVA_PRIMA = 0.0025  # 0,25% prima casa
IMPOSTA_SOSTITUTIVA_SECONDA = 0.02  # 2% seconda casa


# ─── Schemas ─────────────────────────────────────────────────────
class CompareBody(BaseModel):
    property_price: float = Field(..., gt=10000, le=10_000_000)
    down_payment: float = Field(..., ge=0)
    duration_years: int = Field(..., description="10|15|20|25|30")
    rate_type: str = Field(default="entrambi", description="fisso | variabile | entrambi")
    income_monthly: Optional[float] = Field(default=None, ge=0)
    first_home: bool = True
    age_under_36: bool = False


class LeadBody(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    property_price: float
    loan_amount: float
    duration_years: int
    rate_type: str
    best_rata: Optional[float] = None
    gdpr_consent: bool = False


class PlanBody(BaseModel):
    loan_amount: float = Field(..., gt=1000, le=10_000_000)
    tan_pct: float = Field(..., gt=0, le=15)
    duration_years: int = Field(..., ge=1, le=40)


# ─── Math ────────────────────────────────────────────────────────
def french_installment(principal: float, annual_rate_pct: float, years: int) -> float:
    i = annual_rate_pct / 100 / 12
    n = years * 12
    if i <= 0:
        return principal / n
    return principal * i / (1 - (1 + i) ** -n)


def compute_taeg(principal: float, upfront_costs: float, monthly_payment: float,
                 monthly_fee: float, years: int) -> float:
    """TAEG: IRR mensile del flusso (erogato - spese iniziali) vs rate+oneri, annualizzato composto."""
    n = years * 12
    net = principal - upfront_costs
    cash_out = monthly_payment + monthly_fee

    def npv(r: float) -> float:
        if r <= -0.999:
            return float("inf")
        return net - cash_out * (1 - (1 + r) ** -n) / r if r > 1e-12 else net - cash_out * n

    lo, hi = 1e-6, 0.05
    for _ in range(80):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            hi = mid
        else:
            lo = mid
    monthly_irr = (lo + hi) / 2
    return round(((1 + monthly_irr) ** 12 - 1) * 100, 3)


def _benchmark(rate_type: str, years: int) -> float:
    if rate_type == "fisso":
        tenor = min(EURIRS.keys(), key=lambda t: abs(t - years))
        return EURIRS[tenor]
    return max(EURIBOR_3M, 0.0)  # floor 0 (clausola standard)


def _upfront_costs(offer: dict, loan: float, first_home: bool) -> Dict[str, float]:
    if offer.get("istruttoria_pct") is not None:
        istr = max(loan * offer["istruttoria_pct"] / 100, offer.get("istruttoria_min", 0))
    else:
        istr = offer.get("istruttoria_flat", 0)
    imposta = loan * (IMPOSTA_SOSTITUTIVA_PRIMA if first_home else IMPOSTA_SOSTITUTIVA_SECONDA)
    return {
        "istruttoria": round(istr, 2),
        "perizia": float(offer.get("perizia", 0)),
        "imposta_sostitutiva": round(imposta, 2),
    }


# ─── Endpoints ───────────────────────────────────────────────────
@router.get("/config")
async def mutui_config() -> Dict[str, Any]:
    return {
        "durations": DURATIONS,
        "benchmarks": {"eurirs": EURIRS, "euribor_3m": EURIBOR_3M},
        "tegm": TEGM,
        "max_ltv_standard": MAX_LTV_STANDARD,
        "max_ltv_under36": MAX_LTV_UNDER36,
        "max_rata_reddito_pct": MAX_RATA_REDDITO * 100,
        "banks_count": len({o["bank"] for o in BANK_OFFERS}),
        "offers_count": len(BANK_OFFERS),
        "data_updated_at": DATA_UPDATED_AT,
    }


@router.post("/compare")
async def compare_mortgages(body: CompareBody) -> Dict[str, Any]:
    if body.duration_years not in DURATIONS:
        raise HTTPException(400, f"Durata non supportata: {body.duration_years} (ammesse: {DURATIONS})")
    if body.rate_type not in ("fisso", "variabile", "entrambi"):
        raise HTTPException(400, f"Tipo tasso non valido: {body.rate_type}")
    if body.down_payment >= body.property_price:
        raise HTTPException(400, "L'anticipo non può essere ≥ del prezzo")

    loan = body.property_price - body.down_payment
    ltv = round(loan / body.property_price * 100, 1)
    max_ltv_user = MAX_LTV_UNDER36 if (body.age_under_36 and body.first_home) else MAX_LTV_STANDARD

    if ltv > max_ltv_user:
        min_down = body.property_price * (1 - max_ltv_user / 100)
        return {
            "eligible": False,
            "reason": "ltv",
            "ltv": ltv,
            "max_ltv": max_ltv_user,
            "loan_amount": round(loan, 2),
            "min_down_payment": round(min_down, 2),
            "offers": [],
        }

    offers_out: List[Dict[str, Any]] = []
    for offer in BANK_OFFERS:
        if body.rate_type != "entrambi" and offer["type"] != body.rate_type:
            continue
        offer_max_ltv = MAX_LTV_UNDER36 if (body.age_under_36 and body.first_home and offer.get("consap")) else offer["max_ltv"]
        if ltv > offer_max_ltv:
            continue

        bench = _benchmark(offer["type"], body.duration_years)
        tan = round(bench + offer["spread"], 3)
        rata = french_installment(loan, tan, body.duration_years)
        costs = _upfront_costs(offer, loan, body.first_home)
        upfront = sum(costs.values())
        taeg = compute_taeg(loan, upfront, rata, offer["incasso_rata"], body.duration_years)
        n = body.duration_years * 12
        total_paid = rata * n + offer["incasso_rata"] * n + upfront

        soglia = TEGM[offer["type"]]["soglia"]
        offers_out.append({
            "bank": offer["bank"],
            "product": offer["product"],
            "type": offer["type"],
            "benchmark": bench,
            "spread": offer["spread"],
            "tan": tan,
            "taeg": taeg,
            "rata": round(rata, 2),
            "incasso_rata": offer["incasso_rata"],
            "costs": costs,
            "upfront_total": round(upfront, 2),
            "total_interest": round(rata * n - loan, 2),
            "total_cost": round(total_paid, 2),
            "usury_ok": taeg < soglia,
            "consap_eligible": bool(offer.get("consap")),
        })

    offers_out.sort(key=lambda o: o["taeg"])
    for i, o in enumerate(offers_out):
        o["rank"] = i + 1

    sustainability = None
    if body.income_monthly and offers_out:
        best_rata = offers_out[0]["rata"]
        ratio = best_rata / body.income_monthly
        sustainability = {
            "ratio_pct": round(ratio * 100, 1),
            "max_pct": MAX_RATA_REDDITO * 100,
            "ok": ratio <= MAX_RATA_REDDITO,
            "max_sustainable_rata": round(body.income_monthly * MAX_RATA_REDDITO, 2),
        }

    return {
        "eligible": True,
        "loan_amount": round(loan, 2),
        "ltv": ltv,
        "max_ltv": max_ltv_user,
        "duration_years": body.duration_years,
        "consap_applied": body.age_under_36 and body.first_home and ltv > MAX_LTV_STANDARD,
        "sustainability": sustainability,
        "offers": offers_out,
        "tegm": TEGM,
        "data_updated_at": DATA_UPDATED_AT,
        "disclaimer": (
            "Simulazione orientativa basata su dati pubblici e fogli informativi. Non costituisce "
            "offerta al pubblico né attività di mediazione creditizia ai sensi dell'art. 128-sexies TUB. "
            "Condizioni effettive soggette a valutazione della banca."
        ),
    }


@router.post("/plan")
async def amortization_plan(body: PlanBody) -> Dict[str, Any]:
    rata = french_installment(body.loan_amount, body.tan_pct, body.duration_years)
    i = body.tan_pct / 100 / 12
    balance = body.loan_amount
    months: List[Dict[str, float]] = []
    for m in range(1, body.duration_years * 12 + 1):
        interest = balance * i
        principal = rata - interest
        balance = max(balance - principal, 0.0)
        months.append({
            "month": m,
            "rata": round(rata, 2),
            "interest": round(interest, 2),
            "principal": round(principal, 2),
            "balance": round(balance, 2),
        })
    years = []
    for y in range(body.duration_years):
        chunk = months[y * 12:(y + 1) * 12]
        years.append({
            "year": y + 1,
            "interest": round(sum(c["interest"] for c in chunk), 2),
            "principal": round(sum(c["principal"] for c in chunk), 2),
            "balance": chunk[-1]["balance"],
        })
    return {"rata": round(rata, 2), "months_first_year": months[:12], "years": years}


@router.post("/lead")
async def mortgage_lead(body: LeadBody) -> Dict[str, Any]:
    db = Database.get()
    lead_id = str(uuid4())
    await db.mortgage_leads.insert_one({
        "id": lead_id,
        "name": body.name,
        "email": body.email.lower(),
        "phone": body.phone,
        "property_price": body.property_price,
        "loan_amount": body.loan_amount,
        "duration_years": body.duration_years,
        "rate_type": body.rate_type,
        "best_rata": body.best_rata,
        "gdpr_consent": body.gdpr_consent,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "ImmobilCloud-Mutui",
    })
    return {"ok": True, "lead_id": lead_id}
