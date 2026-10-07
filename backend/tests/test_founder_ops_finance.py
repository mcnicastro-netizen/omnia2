"""Unit tests — Founder Ops finance helpers (D-117)."""
from apps.immoweb.founder_ops_finance import (
    build_revenue_lines,
    month_label,
    purchase_amount_eur,
    stripe_fees_eur,
)


def test_purchase_amount_prefers_ledger_then_catalog():
    assert purchase_amount_eur({"amount_eur": 4.9}) == 4.9
    assert purchase_amount_eur({"price_eur": 2.99}) == 2.99
    assert purchase_amount_eur({}, {"price_eur": 1.0}) == 1.0
    assert purchase_amount_eur({}) == 0.0


def test_stripe_fees():
    assert stripe_fees_eur(4.90, 1) == round(4.90 * 0.015 + 0.25, 2)
    assert stripe_fees_eur(0, 0) == 0.0


def test_build_revenue_lines_visura_and_catalog_zeros():
    catalog = {
        "b2c_visura_catastale": {
            "label_it": "Visura catastale (PDF ufficiale)",
            "price_eur": 4.90,
        },
        "b2c_hal_legal_query": {
            "label_it": "HAL Legal — 1 domanda con citazioni",
            "price_eur": 1.00,
        },
    }
    lines, rev, cogs, fees, margin = build_revenue_lines(
        b2c_rows=[
            {"product_key": "b2c_visura_catastale", "amount_eur": 4.90, "status": "paid"},
        ],
        b2b_rows=[],
        catalog=catalog,
    )
    by_key = {l["key"]: l for l in lines}
    assert by_key["b2c_visura_catastale"]["count"] == 1
    assert by_key["b2c_visura_catastale"]["revenue_eur"] == 4.9
    assert by_key["b2c_hal_legal_query"]["count"] == 0  # still listed
    assert rev == 4.9
    assert fees > 0
    assert cogs >= 0.40  # product COGS
    assert margin == round(rev - cogs, 2)


def test_month_label_it():
    assert month_label("2026-10") == "Ottobre 2026"
