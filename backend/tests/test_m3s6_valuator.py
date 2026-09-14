"""OMNIA — M3.S6 GIS Valuator congruence tests.

These tests verify the valuator returns realistic, market-consistent estimates
across a broad spectrum of Italian cities and conditions. Each test asserts a
plausible range based on 2024-2025 published benchmarks (Borsino Immobiliare,
OMI, Idealista, Tecnocasa).

Pricing tiers we expect (€/m², centro semicentro periferia):
  - Ultra-premium (Portofino/Capri/PortoCervo): 6000-25000
  - Tier 1 capitals (Milano/Roma/Firenze centro): 5500-13000
  - Tier 2 capitals (Bologna/Torino/Napoli centro): 3000-6500
  - Tier 3 capitals (Bari/Palermo/Catania centro): 1700-4000
  - Small Sud cities (Crotone/Enna periferia): 450-1500
"""
from fastapi.testclient import TestClient
import pytest

from server import app


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================
# CITY × ZONE — realistic €/m² congruence
# ============================================================

@pytest.mark.parametrize("payload,expect_psm_min,expect_psm_max,label", [
    # ---------- ULTRA-PREMIUM ----------
    ({"city": "Portofino", "zone": "centro", "surface_sqm": 100}, 14000, 26000, "Portofino centro"),
    ({"city": "Capri",     "zone": "centro", "surface_sqm": 100}, 11500, 20500, "Capri centro"),
    ({"city": "Porto Cervo", "zone": "centro", "surface_sqm": 100}, 14500, 25500, "Porto Cervo centro"),

    # ---------- TIER 1 CAPITALS ----------
    ({"city": "Milano",  "zone": "centro",     "surface_sqm": 80}, 8500, 13500, "Milano centro"),
    ({"city": "Milano",  "zone": "semicentro", "surface_sqm": 80}, 5000, 8000,  "Milano semicentro"),
    ({"city": "Milano",  "zone": "periferia",  "surface_sqm": 80}, 3000, 5000,  "Milano periferia"),
    ({"city": "Roma",    "zone": "centro",     "surface_sqm": 80}, 6000, 10000, "Roma centro"),
    ({"city": "Roma",    "zone": "semicentro", "surface_sqm": 80}, 3500, 6000,  "Roma semicentro"),
    ({"city": "Roma",    "zone": "periferia",  "surface_sqm": 80}, 2000, 3500,  "Roma periferia"),
    ({"city": "Firenze", "zone": "centro",     "surface_sqm": 80}, 5000, 9000,  "Firenze centro"),

    # ---------- TIER 2 CAPITALS ----------
    ({"city": "Bologna", "zone": "centro",     "surface_sqm": 80}, 4000, 7000, "Bologna centro"),
    ({"city": "Torino",  "zone": "centro",     "surface_sqm": 80}, 2800, 5000, "Torino centro"),
    ({"city": "Napoli",  "zone": "centro",     "surface_sqm": 80}, 3000, 6000, "Napoli centro"),
    ({"city": "Verona",  "zone": "centro",     "surface_sqm": 80}, 3000, 5500, "Verona centro"),
    ({"city": "Padova",  "zone": "centro",     "surface_sqm": 80}, 2500, 4500, "Padova centro"),
    ({"city": "Genova",  "zone": "centro",     "surface_sqm": 80}, 2200, 4000, "Genova centro"),
    ({"city": "Trento",  "zone": "centro",     "surface_sqm": 80}, 3000, 5000, "Trento centro"),
    ({"city": "Bolzano", "zone": "centro",     "surface_sqm": 80}, 4000, 7000, "Bolzano centro"),

    # ---------- TIER 3 CAPITALS ----------
    ({"city": "Bari",    "zone": "centro",     "surface_sqm": 80}, 2500, 4500, "Bari centro"),
    ({"city": "Palermo", "zone": "centro",     "surface_sqm": 80}, 1500, 3200, "Palermo centro"),
    ({"city": "Catania", "zone": "centro",     "surface_sqm": 80}, 1500, 3000, "Catania centro"),
    ({"city": "Cagliari","zone": "centro",     "surface_sqm": 80}, 2200, 4000, "Cagliari centro"),

    # ---------- SMALL SOUTH ----------
    ({"city": "Crotone", "zone": "periferia",  "surface_sqm": 80}, 400, 800,   "Crotone periferia"),
    ({"city": "Enna",    "zone": "periferia",  "surface_sqm": 80}, 400, 800,   "Enna periferia"),
    ({"city": "Foggia",  "zone": "periferia",  "surface_sqm": 80}, 450, 900,   "Foggia periferia"),
])
def test_city_zone_psm_congruence(client, payload, expect_psm_min, expect_psm_max, label):
    """Each city/zone returns an avg €/m² inside published market range."""
    p = {"property_type": "appartamento", "condition": "buono", **payload}
    r = client.post("/api/cloud/valuator", json=p)
    assert r.status_code == 200, f"{label} → HTTP {r.status_code}"
    d = r.json()
    psm = d["price_per_sqm"]["avg"]
    assert expect_psm_min <= psm <= expect_psm_max, (
        f"{label} avg €/m² {psm} OUT OF RANGE [{expect_psm_min},{expect_psm_max}]"
    )
    assert d["confidence"] in ("high", "medium")


# ============================================================
# MONOTONICITY — centro > semicentro > periferia in same city
# ============================================================

@pytest.mark.parametrize("city", [
    "Milano", "Roma", "Napoli", "Torino", "Firenze", "Bologna",
    "Genova", "Palermo", "Bari", "Verona", "Cagliari", "Catania",
])
def test_zone_monotonicity(client, city):
    """centro €/m² > semicentro > periferia for every covered city."""
    def psm(zone):
        r = client.post("/api/cloud/valuator", json={
            "city": city, "zone": zone, "property_type": "appartamento",
            "surface_sqm": 80, "condition": "buono",
        })
        assert r.status_code == 200
        return r.json()["price_per_sqm"]["avg"]
    c, s, p = psm("centro"), psm("semicentro"), psm("periferia")
    assert c > s > p, f"{city}: centro {c} > semicentro {s} > periferia {p} VIOLATED"


# ============================================================
# CITY RANKING — known order: Milano > Roma > Bologna > Napoli > Palermo
# ============================================================

def test_intercity_ranking(client):
    """Verify well-known order of average €/m² across major Italian cities (centro)."""
    def psm(city):
        r = client.post("/api/cloud/valuator", json={
            "city": city, "zone": "centro",
            "property_type": "appartamento", "surface_sqm": 80, "condition": "buono",
        })
        return r.json()["price_per_sqm"]["avg"]
    psms = {
        c: psm(c) for c in ["Milano", "Roma", "Firenze", "Bologna", "Napoli", "Torino", "Palermo", "Crotone"]
    }
    # Milano deve essere il più caro tra capoluoghi standard
    assert psms["Milano"] > psms["Roma"] > psms["Bologna"]
    assert psms["Bologna"] > psms["Palermo"] > psms["Crotone"]
    assert psms["Milano"] > psms["Napoli"]


# ============================================================
# MULTIPLIERS — property_type/condition/energy applied correctly
# ============================================================

def test_villa_costs_more_than_apartment(client):
    base = {"city": "Roma", "zone": "centro", "surface_sqm": 100, "condition": "buono"}
    app_r = client.post("/api/cloud/valuator", json={**base, "property_type": "appartamento"}).json()
    villa_r = client.post("/api/cloud/valuator", json={**base, "property_type": "villa"}).json()
    assert villa_r["price_per_sqm"]["avg"] > app_r["price_per_sqm"]["avg"]
    # ratio should be ~1.25
    ratio = villa_r["price_per_sqm"]["avg"] / app_r["price_per_sqm"]["avg"]
    assert 1.20 <= ratio <= 1.30, f"villa/apartment ratio {ratio} not ~1.25"


def test_garage_costs_less(client):
    base = {"city": "Milano", "zone": "semicentro", "surface_sqm": 30, "condition": "buono"}
    app_r = client.post("/api/cloud/valuator", json={**base, "property_type": "appartamento"}).json()
    gar_r = client.post("/api/cloud/valuator", json={**base, "property_type": "garage_box"}).json()
    assert gar_r["price_per_sqm"]["avg"] < app_r["price_per_sqm"]["avg"] * 0.6


def test_to_renovate_penalty(client):
    base = {"city": "Milano", "zone": "semicentro", "property_type": "appartamento", "surface_sqm": 80}
    good = client.post("/api/cloud/valuator", json={**base, "condition": "buono"}).json()
    ren  = client.post("/api/cloud/valuator", json={**base, "condition": "da_ristrutturare"}).json()
    assert ren["price_per_sqm"]["avg"] < good["price_per_sqm"]["avg"] * 0.80


def test_energy_class_a_premium(client):
    base = {"city": "Milano", "zone": "semicentro", "property_type": "appartamento",
            "surface_sqm": 80, "condition": "buono"}
    a = client.post("/api/cloud/valuator", json={**base, "energy_class": "A"}).json()
    g = client.post("/api/cloud/valuator", json={**base, "energy_class": "G"}).json()
    assert a["price_per_sqm"]["avg"] > g["price_per_sqm"]["avg"]


def test_top_floor_bonus(client):
    base = {"city": "Roma", "zone": "centro", "property_type": "appartamento",
            "surface_sqm": 80, "condition": "buono"}
    top = client.post("/api/cloud/valuator", json={**base, "floor": 6}).json()
    ground = client.post("/api/cloud/valuator", json={**base, "floor": 0}).json()
    assert top["price_per_sqm"]["avg"] > ground["price_per_sqm"]["avg"]


# ============================================================
# RESILIENCE — unknown cities, synonyms, casing
# ============================================================

def test_english_city_synonym_resolves(client):
    """English names should resolve."""
    for city in ["Milan", "Rome", "Florence", "Naples", "Turin"]:
        r = client.post("/api/cloud/valuator", json={
            "city": city, "zone": "centro", "property_type": "appartamento",
            "surface_sqm": 80, "condition": "buono",
        })
        d = r.json()
        assert d["city_in_dataset"] is True, f"{city} did not resolve"
        assert d["confidence"] == "high"


def test_unknown_city_falls_back_low_confidence(client):
    r = client.post("/api/cloud/valuator", json={
        "city": "PaeseInesistenteXYZ", "property_type": "appartamento",
        "surface_sqm": 80, "condition": "buono",
    })
    d = r.json()
    assert d["city_in_dataset"] is False
    assert d["confidence"] in ("low", "medium")
    # Still must return something usable
    assert d["price_per_sqm"]["avg"] > 0
    assert d["estimated_value"]["avg"] > 0


def test_zone_inferred_from_address(client):
    """If user types 'Via del Trastevere' but no zone, expect 'centro' inferred."""
    r = client.post("/api/cloud/valuator", json={
        "city": "Roma", "address": "Via del Trastevere 12",
        "property_type": "appartamento", "surface_sqm": 80, "condition": "buono",
    })
    d = r.json()
    assert d["zone_tier"] == "centro"
    assert d["zone_explicit"] is False


# ============================================================
# VALIDATION
# ============================================================

def test_invalid_surface_rejected(client):
    r = client.post("/api/cloud/valuator", json={
        "city": "Milano", "surface_sqm": 5, "property_type": "appartamento",
    })
    assert r.status_code == 422

    r = client.post("/api/cloud/valuator", json={
        "city": "Milano", "surface_sqm": 100000, "property_type": "appartamento",
    })
    assert r.status_code == 422


def test_invalid_energy_class_rejected(client):
    r = client.post("/api/cloud/valuator", json={
        "city": "Milano", "surface_sqm": 80, "energy_class": "Z",
    })
    assert r.status_code == 422


def test_coverage_endpoint(client):
    r = client.get("/api/cloud/valuator/coverage")
    assert r.status_code == 200
    d = r.json()
    assert d["cities_covered"] >= 100
    assert d["regions_covered"] >= 18
    assert "centro" in d["zone_tiers"]


# ============================================================
# RESPONSE COMPLETENESS
# ============================================================

def test_response_includes_all_fields(client):
    r = client.post("/api/cloud/valuator", json={
        "city": "Bologna", "zone": "centro", "property_type": "appartamento",
        "surface_sqm": 90, "condition": "ottimo", "energy_class": "B", "floor": 3,
    })
    d = r.json()
    expected_keys = {
        "ok", "city_resolved", "city_in_dataset", "region", "zone_tier",
        "zone_explicit", "price_per_sqm", "estimated_value", "currency",
        "surface_sqm", "multipliers_applied", "confidence", "confidence_score",
        "methodology", "data_source", "comparable_count", "comparables",
        "valuation_lead_id", "disclaimer",
    }
    assert expected_keys.issubset(d.keys())
    assert d["price_per_sqm"]["min"] < d["price_per_sqm"]["avg"] < d["price_per_sqm"]["max"]
    assert d["estimated_value"]["min"] < d["estimated_value"]["avg"] < d["estimated_value"]["max"]
