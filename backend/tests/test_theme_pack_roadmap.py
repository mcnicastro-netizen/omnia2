"""D-150/D-151 — catalogo 8 live; roadmap vuota; MLS matrix; fasce prezzo."""
from apps.billing.plans import (
    SITE_THEME_PREMIUM_IDS,
    SITE_THEME_PRICES_EUR,
    SITE_THEME_SIMPLE_IDS,
)
from apps.immoweb.theme_catalog import THEME_CATALOG, THEME_IDS, THEME_ROADMAP

LIVE_IDS = {
    "minimal", "classic", "bold", "luxury",
    "atelier", "cinematic", "editorial", "mediterranean",
}


def test_live_themes_declare_mls_variants():
    assert {t["id"] for t in THEME_CATALOG} == LIVE_IDS
    assert THEME_IDS == LIVE_IDS
    for t in THEME_CATALOG:
        assert t["status"] == "live"
        assert set(t["mls_variants"]) == {"on", "off"}
        assert t["id"] in THEME_IDS


def test_roadmap_empty_when_gallery_complete():
    assert THEME_ROADMAP == []


def test_d151_price_tiers_align_with_plans():
    assert SITE_THEME_PRICES_EUR["starter_neo_simple"] == 99.0
    assert SITE_THEME_PRICES_EUR["starter_neo_premium"] == 199.0
    assert SITE_THEME_PRICES_EUR["restyling"] == 199.0
    assert set(SITE_THEME_SIMPLE_IDS) == {"minimal", "classic"}
    assert set(SITE_THEME_PREMIUM_IDS) == {
        "bold", "luxury", "atelier", "cinematic", "editorial", "mediterranean",
    }
    for t in THEME_CATALOG:
        if t["id"] in SITE_THEME_SIMPLE_IDS:
            assert t["price_tier"] == "simple"
        else:
            assert t["price_tier"] == "premium"
