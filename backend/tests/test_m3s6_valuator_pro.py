"""M3.S6-pro — Valutatore Pro: UNI 10750 + merit + regional + province fallback.

Backwards-compat tests for the original 161 cities are in test_m3s6_valuator.py.
This file focuses on the NEW pipeline capabilities introduced 25-Giu-2026.
"""
from __future__ import annotations

import pytest

from apps.immocloud.data.coefficients import (
    compute_commercial_surface,
    compute_merit_adjustment,
    compute_regional_adjustment,
    age_adjustment,
    foi_revaluation,
    SURFACE_WEIGHTS,
)
from apps.immocloud.data.province_prices import (
    PROVINCE_PRICES,
    PROVINCE_NAMES,
)

from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)


# ──────────────────────────────────────────────────────────────
# 1) UNI 10750 — Superficie commerciale ponderata
# ──────────────────────────────────────────────────────────────
class TestUNI10750:
    def test_only_principale(self):
        total, breakdown = compute_commercial_surface({"principale_mq": 90.0})
        assert total == 90.0
        assert breakdown == {"principale_mq": 90.0}

    def test_balcone_under_threshold(self):
        # 10mq balcone × 30% = 3mq
        total, breakdown = compute_commercial_surface({"principale_mq": 80, "balcone_mq": 10})
        assert breakdown["balcone_mq"] == 3.0
        assert total == 83.0

    def test_terrazzo_progressive(self):
        # 50mq terrazzo: primi 25 @ 30% = 7.5, restanti 25 @ 10% = 2.5 → 10mq totali
        total, breakdown = compute_commercial_surface({"principale_mq": 100, "terrazzo_mq": 50})
        assert breakdown["terrazzo_mq"] == 10.0
        assert total == 110.0

    def test_box_at_50pct(self):
        total, _ = compute_commercial_surface({"principale_mq": 80, "box_auto_mq": 18})
        assert total == 80 + 9.0  # 18 × 0.50

    def test_cantina_at_25pct(self):
        total, _ = compute_commercial_surface({"principale_mq": 80, "cantina_mq": 12})
        assert total == 80 + 3.0  # 12 × 0.25

    def test_giardino_condominiale_zero(self):
        # Condominiale = 0%
        total, _ = compute_commercial_surface({"principale_mq": 80, "giardino_condom_mq": 200})
        assert total == 80.0

    def test_giardino_villa_progressive(self):
        # 100mq giardino villa: 25@10% = 2.5 + 75@5% = 3.75 → 6.25
        total, _ = compute_commercial_surface({"principale_mq": 200, "giardino_villa_mq": 100})
        assert total == pytest.approx(206.25, abs=0.01)

    def test_multiple_components(self):
        total, _ = compute_commercial_surface({
            "principale_mq": 90, "balcone_mq": 10, "cantina_mq": 8, "box_auto_mq": 15
        })
        # 90 + 3 + 2 + 7.5 = 102.5
        assert total == 102.5

    def test_unknown_key_ignored(self):
        total, _ = compute_commercial_surface({"principale_mq": 80, "unknown_xyz_mq": 99})
        assert total == 80.0


# ──────────────────────────────────────────────────────────────
# 2) Coefficienti di merito
# ──────────────────────────────────────────────────────────────
class TestMeritAdjustment:
    def test_no_input_zero(self):
        pct, breakdown = compute_merit_adjustment({})
        assert pct == 0.0
        assert breakdown == {}

    def test_full_bonus(self):
        # Sud + verde + autonomo + presente_piano_alto → cumulative
        pct, breakdown = compute_merit_adjustment({
            "exposure": "sud", "view": "panoramico", "heating": "autonomo",
            "elevator": "presente_piano_alto",
        })
        # 0.05 + 0.08 + 0.03 + 0.03 = 0.19
        assert pct == pytest.approx(0.19, abs=0.001)
        assert "exposure" in breakdown

    def test_negative_cumulative(self):
        # nord + cieca already double-counted? exposure key gives only ONE
        pct, _ = compute_merit_adjustment({
            "exposure": "nord", "view": "interno", "heating": "assente",
            "elevator": "assente_piano_alto", "vincolo_storico": True,
        })
        # -0.04 + -0.04 + -0.08 + -0.10 + -0.10 = -0.36
        assert pct == pytest.approx(-0.36, abs=0.001)

    def test_cap_min_40pct(self):
        # Even with extreme inputs, capped at -0.40
        pct, _ = compute_merit_adjustment({
            "exposure": "cieca", "view": "interno", "heating": "assente",
            "elevator": "assente_piano_alto",
            "vincolo_storico": True, "locazione_lunga": True, "nuda_proprieta": True,
        })
        assert pct == -0.40

    def test_age_decay(self):
        # Year 1950 vs 2026 = 76y, excess 46y × -0.005 = -0.23, capped at -0.20
        assert age_adjustment(1950, 2026) == -0.20
        # Year 1990 vs 2026 = 36y, excess 6y × -0.005 = -0.03
        assert age_adjustment(1990, 2026) == pytest.approx(-0.03, abs=0.001)
        # No age penalty for new buildings
        assert age_adjustment(2020, 2026) == 0.0
        # None input
        assert age_adjustment(None) == 0.0


# ──────────────────────────────────────────────────────────────
# 3) Coefficienti regionali
# ──────────────────────────────────────────────────────────────
class TestRegionalAdjustment:
    def test_lombardia_neutral(self):
        pct, breakdown = compute_regional_adjustment("lombardia", months_since_omi=6)
        assert breakdown["liquidity"] == 0.00
        assert breakdown["trend_inflation"] == pytest.approx(0.025 / 2, abs=0.001)

    def test_calabria_heavy_discount(self):
        pct, breakdown = compute_regional_adjustment("calabria", months_since_omi=6)
        assert breakdown["liquidity"] == -0.08
        assert pct < -0.08  # liquidity + negative trend

    def test_unknown_region(self):
        pct, breakdown = compute_regional_adjustment("antarctica")
        assert pct == 0.0
        assert breakdown == {}

    def test_none_region(self):
        pct, breakdown = compute_regional_adjustment(None)
        assert pct == 0.0


# ──────────────────────────────────────────────────────────────
# 4) FOI rivalutazione
# ──────────────────────────────────────────────────────────────
class TestFOI:
    def test_revaluation_same_year(self):
        assert foi_revaluation(2026, 2026) == 1.0

    def test_revaluation_2020_to_2026(self):
        # 1.205 / 1.000 = 1.205
        assert foi_revaluation(2020, 2026) == pytest.approx(1.205, abs=0.001)

    def test_unknown_year_safe(self):
        assert foi_revaluation(1900, 2026) == 1.0


# ──────────────────────────────────────────────────────────────
# 5) Province coverage
# ──────────────────────────────────────────────────────────────
class TestProvinceCoverage:
    def test_107_provinces(self):
        assert len(PROVINCE_PRICES) >= 107

    def test_all_have_three_tiers(self):
        for sigla, data in PROVINCE_PRICES.items():
            assert "centro" in data
            assert "semicentro" in data
            assert "periferia" in data
            assert "region" in data

    def test_centro_prices_ordered(self):
        for sigla, data in PROVINCE_PRICES.items():
            c_min, c_max = data["centro"]
            s_min, s_max = data["semicentro"]
            p_min, p_max = data["periferia"]
            assert c_min <= c_max
            assert s_min <= s_max
            assert p_min <= p_max
            # Centro should be ≥ semicentro ≥ periferia (most cases)
            assert c_max >= s_max, f"{sigla}: centro {c_max} < semicentro {s_max}"
            assert s_max >= p_max, f"{sigla}: semicentro {s_max} < periferia {p_max}"

    def test_milan_premium(self):
        mi = PROVINCE_PRICES["MI"]
        assert mi["centro"][0] >= 7000   # Milan must be expensive
        assert mi["region"] == "lombardia"

    def test_naming_complete(self):
        for sigla in PROVINCE_PRICES.keys():
            assert sigla in PROVINCE_NAMES, f"Missing name for {sigla}"


# ──────────────────────────────────────────────────────────────
# 6) End-to-end via FastAPI client (province fallback + UNI 10750)
# ──────────────────────────────────────────────────────────────
class TestValuatorEndpoint:
    def test_curated_city_no_pro_fields(self, client):
        r = client.post("/api/cloud/valuator", json={
            "city": "Milano", "zone": "centro", "property_type": "appartamento",
            "surface_sqm": 80, "condition": "buono",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["city_in_dataset"] is True
        assert d["fallback_used"] is None
        assert d["confidence"] in ("high", "medium")

    def test_pro_payload_uni10750(self, client):
        r = client.post("/api/cloud/valuator", json={
            "city": "Milano", "zone": "semicentro", "property_type": "appartamento",
            "surface_sqm": 90, "condition": "ristrutturato", "energy_class": "B", "floor": 3,
            "commercial_surfaces": {
                "principale_mq": 90, "balcone_mq": 12, "cantina_mq": 8, "box_auto_mq": 15,
            },
            "merit": {
                "floor_class": "piano_intermedio", "exposure": "sud", "view": "verde",
                "heating": "autonomo", "elevator": "presente_piano_alto", "year_built": 2005,
            },
        })
        assert r.status_code == 200
        d = r.json()
        assert d["surface"]["commercial_mq"] > d["surface_sqm"]
        # 90 + 3.6 + 2 + 7.5 = 103.1
        assert d["surface"]["commercial_mq"] == pytest.approx(103.1, abs=0.1)
        assert d["multipliers_applied"]["merit_pct"] > 0
        assert d["confidence"] == "high"
        assert "method" in d["surface"]

    def test_unknown_city_province_fallback_does_not_crash(self, client):
        r = client.post("/api/cloud/valuator", json={
            "city": "Saronno", "property_type": "appartamento", "surface_sqm": 85,
            "condition": "buono",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["fallback_used"] in ("province", "regional", None)
        assert d["estimated_value"]["avg"] > 0

    def test_locazione_lunga_penalty(self, client):
        r = client.post("/api/cloud/valuator", json={
            "city": "Bologna", "zone": "semicentro", "surface_sqm": 70,
            "merit": {"locazione_lunga": True},
        })
        assert r.status_code == 200
        d = r.json()
        assert d["multipliers_applied"]["merit_pct"] == pytest.approx(-0.15, abs=0.001)

    def test_coverage_endpoint(self, client):
        r = client.get("/api/cloud/valuator/coverage")
        assert r.status_code == 200
        d = r.json()
        assert d["cities_covered"] >= 100
        assert d["provinces_covered"] >= 107
        assert d["national_coverage"] is True
        assert "UNI 10750:1998" in d["norms_applied"]


# ──────────────────────────────────────────────────────────────
# 7) ANNCSU health
# ──────────────────────────────────────────────────────────────
class TestAnncsu:
    def test_health(self, client):
        r = client.get("/api/cloud/anncsu/health")
        assert r.status_code == 200
        d = r.json()
        assert d["service"] == "anncsu"
        assert d["comune_index_size"] > 0
