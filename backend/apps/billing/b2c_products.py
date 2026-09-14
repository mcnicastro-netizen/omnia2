"""OMNIA — Catalogo prodotti B2C one-shot (ImmobilCloud privati).

Rail SEPARATO da plans.py:
- plans.py = abbonamenti B2B + crediti pay-as-you-go (agenzie)
- b2c_products.py = pagamenti one-shot con carta (privati sul portale /cloud)

Listino approvato Founder — 6 Agosto 2026.
Vedi documentazione: memory/PRICING_B2C.md

STATO: STUB. In questo sprint sono definiti solo i prodotti e i prezzi.
Il checkout Stripe one-shot (POST /api/billing/b2c/checkout) sarà
implementato nello sprint successivo.

Regola cardine:
- Nessun prodotto B2C sotto €0,99 (tranne lead magnet espliciti gratuiti).
- Tutti i pagamenti B2C via Stripe carta one-shot, MAI crediti.
"""
from typing import Dict, TypedDict, Optional


class B2CProduct(TypedDict):
    """Un singolo prodotto B2C one-shot."""
    key: str                       # id interno stabile
    label_it: str                  # nome mostrato all'utente
    price_eur: float               # prezzo lordo in €
    stripe_lookup_key: str         # stable Stripe lookup key
    unit: str                      # "per_report", "per_photo", "per_query", ...
    daily_limit_per_user: Optional[int]
    notes: str


# --- Prodotti attivi (implementabili nello sprint checkout) ------------
B2C_ONE_SHOT_PRODUCTS: Dict[str, B2CProduct] = {
    "b2c_valuator_uni_pdf": {
        "key": "b2c_valuator_uni_pdf",
        "label_it": "Valutazione UNI 10750 + PDF brandizzato",
        "price_eur": 2.99,
        "stripe_lookup_key": "b2c_valuator_uni_pdf",
        "unit": "per_report",
        "daily_limit_per_user": 5,
        "notes": (
            "Checkout Stripe prima del download del PDF. "
            "Retail 5x vs prezzo B2B (€0,60 = 12 crediti agenzia)."
        ),
    },
    "b2c_staging_render": {
        "key": "b2c_staging_render",
        "label_it": "Virtual Staging (per foto)",
        "price_eur": 0.90,
        "stripe_lookup_key": "b2c_staging_render",
        "unit": "per_photo",
        "daily_limit_per_user": 3,
        "notes": (
            "Max 3 foto per annuncio UGC del cliente. "
            "Stesso € del prezzo B2B agenzia. Margine ~65% netto Stripe."
        ),
    },
    "b2c_hal_legal_query": {
        "key": "b2c_hal_legal_query",
        "label_it": "HAL Legal — 1 domanda con citazioni",
        "price_eur": 1.00,
        "stripe_lookup_key": "b2c_hal_legal_query",
        "unit": "per_query",
        "daily_limit_per_user": 20,
        "notes": (
            "Rate limit 20 query/ora per IP a livello di piattaforma. "
            "Disclaimer obbligatorio prima della risposta."
        ),
    },
}


# --- Lead magnet gratuiti (no checkout, solo limiti anti-abuso) --------
# Documentati qui per completezza. NON creano Stripe products.
B2C_FREE_LEAD_MAGNETS: Dict[str, dict] = {
    "b2c_valuator_base": {
        "label_it": "Valutatore base (stima rapida)",
        "unit": "per_valuation",
        "annual_limit_per_user": 1,
        "requires_email_verified": True,
        "notes": (
            "1 valutazione ogni 12 mesi per email verificato. "
            "Lead magnet + upsell verso Valutazione UNI a pagamento."
        ),
    },
    "b2c_mortgage_compare": {
        "label_it": "Comparatore mutui",
        "unit": "per_simulation",
        "annual_limit_per_user": None,
        "requires_email_verified": False,
        "notes": "Illimitato. Lead → agenzia partner / mediatore.",
    },
}


# --- Prodotti "in arrivo" (fase 2 — NON esporre come acquistabili) -----
# Documentati qui per traccia; il checkout NON deve mostrarli finché
# margini e partner esterni non sono validati.
B2C_COMING_SOON: Dict[str, dict] = {
    "b2c_visura_catastale": {
        "label_it": "Visura catastale",
        "planned_price_eur": None,   # da definire in fase 2
        "cost_ref_eur": 0.40,        # costo vivo indicativo
        "notes": "Attendere validazione partner catasto + policy antiabuso.",
    },
    "b2c_planimetria_catastale": {
        "label_it": "Planimetria catastale",
        "planned_price_eur": None,   # da definire in fase 2
        "cost_ref_eur": 6.90,        # costo vivo indicativo elevato
        "notes": (
            "Margine da validare. Serve accordo commerciale con partner "
            "per ridurre il costo vivo o accettare margine minimo."
        ),
    },
}


def get_b2c_product(key: str) -> Optional[B2CProduct]:
    """Return the active B2C product for the given key, or None if missing."""
    return B2C_ONE_SHOT_PRODUCTS.get(key)


def is_b2c_free(key: str) -> bool:
    """True if the key corresponds to a documented free lead magnet."""
    return key in B2C_FREE_LEAD_MAGNETS


def is_b2c_coming_soon(key: str) -> bool:
    """True if the key is a documented "coming soon" product (do NOT sell)."""
    return key in B2C_COMING_SOON
