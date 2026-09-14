"""OMNIA — Subscription plan catalog (M4.S3).

Listino ufficiale approvato Founder — 5 Agosto 2026.

- Fase Founders (12 mesi dall'ingresso agenzia): Starter €49 · Pro €99 · Agency €249
- Fase Standard (post 12 mesi Founders): €79 · €179 · €349
- Crediti inclusi/mese: Starter 120 · Pro 1200 · Agency 3600
- Valore credito: €0,05 (1 credito = 5 centesimi)
- Multiposting: incluso in tutti i piani, custom portal wizard su tutti

Enterprise resta nel catalogo (backward compat) con prezzi legacy —
posizionamento e API custom saranno rivisti in sessione dedicata.

Checkout usa stable Stripe `lookup_key` = f"{tier}_{cycle}" (es.
`pro_monthly`, `agency_yearly`). Vedi apps/billing/setup_stripe.py.
"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

PlanTier = Literal["starter", "pro", "agency", "enterprise"]


class PlanFeature(BaseModel):
    key: str
    label_it: str
    label_en: str
    label_es: str
    included: bool = True


class Plan(BaseModel):
    tier: PlanTier
    name: str
    price_monthly: float  # € canone mensile
    price_yearly: float   # € canone annuale (2 mesi in omaggio)
    max_agents: int       # -1 = illimitato
    max_properties: int   # -1 = illimitato
    credits_included_monthly: int = 0  # crediti gratuiti inclusi ogni mese
    features: List[PlanFeature] = Field(default_factory=list)
    trial_days: int = 14
    launch_discount_months: int = 0  # 0 = pricing pieno


# --- FASE FOUNDERS (primi 12 mesi dall'ingresso) -----------------------
# Listino ufficiale Founder — 5 Agosto 2026
LAUNCH_PLANS: Dict[PlanTier, Plan] = {
    "starter": Plan(
        tier="starter",
        name="Starter",
        price_monthly=49.0,
        price_yearly=490.0,
        max_agents=3,
        max_properties=30,
        credits_included_monthly=120,
    ),
    "pro": Plan(
        tier="pro",
        name="Pro",
        price_monthly=99.0,
        price_yearly=990.0,
        max_agents=10,
        max_properties=200,
        credits_included_monthly=1200,
    ),
    "agency": Plan(
        tier="agency",
        name="Agency",
        price_monthly=249.0,
        price_yearly=2490.0,
        max_agents=-1,
        max_properties=-1,
        credits_included_monthly=3600,
    ),
    # Enterprise: TBD in sessione dedicata (posizionamento + Custom API).
    # Mantenuto con prezzi legacy per non rompere il modello dati esistente.
    "enterprise": Plan(
        tier="enterprise",
        name="Enterprise",
        price_monthly=299.0,
        price_yearly=2990.0,
        max_agents=-1,
        max_properties=-1,
        credits_included_monthly=3600,
    ),
}

# --- FASE STANDARD (dopo 12 mesi Founders) -----------------------------
POST_TRACTION_PLANS: Dict[PlanTier, Plan] = {
    "starter": Plan(
        tier="starter", name="Starter",
        price_monthly=79.0, price_yearly=790.0,
        max_agents=3, max_properties=30,
        credits_included_monthly=120,
    ),
    "pro": Plan(
        tier="pro", name="Pro",
        price_monthly=179.0, price_yearly=1790.0,
        max_agents=10, max_properties=200,
        credits_included_monthly=1200,
    ),
    "agency": Plan(
        tier="agency", name="Agency",
        price_monthly=349.0, price_yearly=3490.0,
        max_agents=-1, max_properties=-1,
        credits_included_monthly=3600,
    ),
    "enterprise": Plan(
        tier="enterprise", name="Enterprise",
        price_monthly=499.0, price_yearly=4990.0,
        max_agents=-1, max_properties=-1,
        credits_included_monthly=3600,
    ),
}


def get_active_catalog() -> Dict[PlanTier, Plan]:
    """Return the currently active plan catalog based on PRICING_PHASE env."""
    import os
    phase = (os.environ.get("PRICING_PHASE") or "launch").lower()
    if phase == "post_traction":
        return POST_TRACTION_PLANS
    return LAUNCH_PLANS


def get_plan(tier: PlanTier) -> Optional[Plan]:
    return get_active_catalog().get(tier)


# --- Credit packages (pay-as-you-go top-up) ----------------------------
# Listino Founder — 5 Agosto 2026 · 1 credito = €0,05 · ratio 20 crediti/€

class CreditPackage(BaseModel):
    key: str
    credits: int
    price_eur: float


CREDIT_PACKAGES: List[CreditPackage] = [
    CreditPackage(key="pkg_400",   credits=400,   price_eur=20.0),
    CreditPackage(key="pkg_1000",  credits=1000,  price_eur=50.0),
    CreditPackage(key="pkg_2000",  credits=2000,  price_eur=100.0),
    CreditPackage(key="pkg_5000",  credits=5000,  price_eur=250.0),
    CreditPackage(key="pkg_10000", credits=10000, price_eur=500.0),
    CreditPackage(key="pkg_20000", credits=20000, price_eur=1000.0),
]

# --- Credit consumption catalog ---------------------------------------
# Listino Founder — 5 Agosto 2026 · Rimossi: planimetria catastale,
# ispezione ipotecaria (margini troppo bassi in v1).
CREDIT_COSTS: Dict[str, int] = {
    "valuator_base": 6,            # Quotazione base (€0,30)
    "valuator_uni_pdf": 12,        # Quotazione UNI 10750 con PDF (€0,60)
    "visura_catastale": 24,        # Visura catastale
    "ape_search": 60,              # Ricerca APE regionale (partner)
    "sms_notification": 4,         # SMS al cliente
    "hal_legal_query": 12,         # Query HAL Legal (con citazioni)
    "hal_agents_query": 4,         # Query HAL Agents (assistente CRM)
    "virtual_staging_render": 18,  # Render staging AI (pipeline 3-stage)
    "micro_tour_render": 60,       # Video micro-tour 10s (Kling Pro)
    "top_promotion": 400,          # Promozione TOP 7 giorni
    "premium_promotion": 1000,     # Promozione Premium 15 giorni
    "featured_promotion": 2000,    # In Evidenza 30 giorni
}
