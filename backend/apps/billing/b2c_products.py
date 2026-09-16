"""OMNIA — Catalogo prodotti B2C one-shot (ImmobilCloud privati).

Rail SEPARATO da plans.py:
- plans.py = abbonamenti B2B + crediti pay-as-you-go (agenzie)
- b2c_products.py = pagamenti one-shot con carta (privati sul portale /cloud)

Listino approvato Founder — 6 Agosto 2026 (strumenti + boost Premium/TOP).
Vetrina B2C aggiunta 16-Set-2026 (entry boost sotto Premium).
Vedi documentazione: memory/PRICING_B2C.md

Regola cardine:
- Nessun prodotto B2C sotto €0,99 (tranne lead magnet espliciti gratuiti).
- Tutti i pagamenti B2C via Stripe carta one-shot, MAI crediti.
"""
from typing import Dict, List, Optional, TypedDict


class B2CProduct(TypedDict, total=False):
    """Un singolo prodotto B2C one-shot."""
    key: str                       # id interno stabile
    label_it: str                  # nome mostrato all'utente
    price_eur: float               # prezzo lordo in €
    stripe_lookup_key: str         # stable Stripe lookup key
    unit: str                      # "per_report", "per_photo", "per_listing_boost", ...
    daily_limit_per_user: Optional[int]
    notes: str
    # Boost-only fields (Vetrina / Premium / TOP)
    boost_tier: str                # "vetrina" | "premium" | "top"
    duration_days: int
    requires_listing: bool


# Sort weight used by public search (higher = shown first while active)
BOOST_RANK: Dict[str, int] = {
    "top": 300,
    "premium": 200,
    "vetrina": 100,
}


# --- Prodotti attivi ----------------------------------------------------
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
    "b2c_visura_catastale": {
        "key": "b2c_visura_catastale",
        "label_it": "Visura catastale (PDF ufficiale)",
        "price_eur": 4.90,
        "stripe_lookup_key": "b2c_visura_catastale",
        "unit": "per_document",
        "daily_limit_per_user": 10,
        "notes": (
            "Pagamento carta Stripe one-shot (mai crediti). "
            "Fulfillment via OpenAPI.it Catasto → PDF. "
            "Costo vivo sandbox/listino partner ~€0,40 — retail Founder 15-Sep-2026."
        ),
    },
    # --- Boost visibilità annuncio privato (carta one-shot) -------------
    "b2c_vetrina_30": {
        "key": "b2c_vetrina_30",
        "label_it": "Vetrina — 30 giorni",
        "price_eur": 14.90,
        "stripe_lookup_key": "b2c_vetrina_30",
        "unit": "per_listing_boost",
        "daily_limit_per_user": 10,
        "boost_tier": "vetrina",
        "duration_days": 30,
        "requires_listing": True,
        "notes": (
            "Entry boost: badge Vetrina + ranking sopra gli annunci base. "
            "Sotto Premium (€19,90). vs Subito 'in vetrina' ~€9–13/mese."
        ),
    },
    "b2c_premium_30": {
        "key": "b2c_premium_30",
        "label_it": "Premium — 30 giorni",
        "price_eur": 19.90,
        "stripe_lookup_key": "b2c_premium_30",
        "unit": "per_listing_boost",
        "daily_limit_per_user": 10,
        "boost_tier": "premium",
        "duration_days": 30,
        "requires_listing": True,
        "notes": "PRICING_B2C.md · -33% vs Idealista Premium ~€29,90 · -41% vs Immobiliare.it ~€34.",
    },
    "b2c_premium_90": {
        "key": "b2c_premium_90",
        "label_it": "Premium — 90 giorni",
        "price_eur": 49.90,
        "stripe_lookup_key": "b2c_premium_90",
        "unit": "per_listing_boost",
        "daily_limit_per_user": 10,
        "boost_tier": "premium",
        "duration_days": 90,
        "requires_listing": True,
        "notes": "PRICING_B2C.md · vs Immobiliare.it Premium 90gg ~€24,95–€79 (medio storico).",
    },
    "b2c_premium_180": {
        "key": "b2c_premium_180",
        "label_it": "Premium — 180 giorni",
        "price_eur": 89.90,
        "stripe_lookup_key": "b2c_premium_180",
        "unit": "per_listing_boost",
        "daily_limit_per_user": 10,
        "boost_tier": "premium",
        "duration_days": 180,
        "requires_listing": True,
        "notes": "PRICING_B2C.md · vs Immobiliare.it Premium 180gg ~€44,95–€139.",
    },
    "b2c_top_30": {
        "key": "b2c_top_30",
        "label_it": "TOP — 30 giorni",
        "price_eur": 29.90,
        "stripe_lookup_key": "b2c_top_30",
        "unit": "per_listing_boost",
        "daily_limit_per_user": 10,
        "boost_tier": "top",
        "duration_days": 30,
        "requires_listing": True,
        "notes": "PRICING_B2C.md · -19% vs Idealista TOP ~€36,90 · -45% vs Immobiliare.it ~€54.",
    },
    "b2c_top_90": {
        "key": "b2c_top_90",
        "label_it": "TOP — 90 giorni",
        "price_eur": 79.90,
        "stripe_lookup_key": "b2c_top_90",
        "unit": "per_listing_boost",
        "daily_limit_per_user": 10,
        "boost_tier": "top",
        "duration_days": 90,
        "requires_listing": True,
        "notes": "PRICING_B2C.md · vs Immobiliare.it TOP 90gg ~€99,95–€109.",
    },
    "b2c_top_180": {
        "key": "b2c_top_180",
        "label_it": "TOP — 180 giorni",
        "price_eur": 149.90,
        "stripe_lookup_key": "b2c_top_180",
        "unit": "per_listing_boost",
        "daily_limit_per_user": 10,
        "boost_tier": "top",
        "duration_days": 180,
        "requires_listing": True,
        "notes": "PRICING_B2C.md · vs Immobiliare.it TOP 180gg ~€179,95–€189.",
    },
}


# --- Lead magnet gratuiti (no checkout, solo limiti anti-abuso) --------
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
B2C_COMING_SOON: Dict[str, dict] = {
    "b2c_planimetria_catastale": {
        "label_it": "Planimetria catastale",
        "planned_price_eur": None,
        "cost_ref_eur": 6.90,
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


def is_b2c_boost_product(key: str) -> bool:
    """True when the product is a listing visibility boost (requires listing_id)."""
    p = B2C_ONE_SHOT_PRODUCTS.get(key)
    return bool(p and p.get("requires_listing") and p.get("boost_tier"))


def list_b2c_catalog(*, include_boosts: bool = True) -> List[dict]:
    """Public-facing catalog rows for UI / API."""
    rows: List[dict] = []
    for key, p in B2C_ONE_SHOT_PRODUCTS.items():
        if not include_boosts and p.get("requires_listing"):
            continue
        rows.append({
            "key": p["key"],
            "label_it": p["label_it"],
            "price_eur": p["price_eur"],
            "unit": p["unit"],
            "boost_tier": p.get("boost_tier"),
            "duration_days": p.get("duration_days"),
            "requires_listing": bool(p.get("requires_listing")),
            "daily_limit_per_user": p.get("daily_limit_per_user"),
        })
    return rows


def list_boost_products() -> List[dict]:
    """Boost SKUs only, ordered Vetrina → Premium → TOP, then by duration."""
    tier_order = {"vetrina": 0, "premium": 1, "top": 2}
    rows = [r for r in list_b2c_catalog(include_boosts=True) if r.get("requires_listing")]
    rows.sort(key=lambda r: (tier_order.get(r.get("boost_tier") or "", 9), r.get("duration_days") or 0))
    return rows
