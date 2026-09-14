"""M5.S5 — Comparatore Mutui: test motore + API (nessun costo esterno)."""
import os

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api/cloud/mutui"


# ─── Unit: motore ────────────────────────────────────────────────
def _mod():
    from apps.immocloud import mutui
    return mutui


def test_french_installment_known_value():
    m = _mod()
    # 200k, 3.6% annuo, 25 anni → ~1012 €/mese
    rata = m.french_installment(200000, 3.6, 25)
    assert 1010 < rata < 1014


def test_french_installment_zero_rate():
    m = _mod()
    assert abs(m.french_installment(120000, 0, 10) - 1000) < 0.01


def test_taeg_above_tan_with_costs():
    m = _mod()
    rata = m.french_installment(200000, 3.6, 25)
    taeg = m.compute_taeg(200000, 1500, rata, 3.0, 25)
    assert 3.6 < taeg < 4.2


def test_taeg_equals_tan_without_costs():
    m = _mod()
    rata = m.french_installment(200000, 3.6, 25)
    taeg = m.compute_taeg(200000, 0, rata, 0, 25)
    # TAEG composto ≈ (1+i)^12-1 leggermente > TAN nominale
    assert 3.6 <= taeg < 3.72


# ─── API ─────────────────────────────────────────────────────────
def test_config():
    r = requests.get(f"{API}/config", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["durations"] == [10, 15, 20, 25, 30]
    assert d["banks_count"] >= 7
    assert "eurirs" in d["benchmarks"]


def test_compare_basic():
    r = requests.post(f"{API}/compare", json={
        "property_price": 250000, "down_payment": 50000, "duration_years": 25,
        "rate_type": "entrambi", "income_monthly": 3500, "first_home": True,
    }, timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["eligible"] and d["loan_amount"] == 200000 and d["ltv"] == 80.0
    assert len(d["offers"]) >= 10
    # ordinati per TAEG crescente
    taegs = [o["taeg"] for o in d["offers"]]
    assert taegs == sorted(taegs)
    assert all(o["usury_ok"] for o in d["offers"])
    assert all(o["taeg"] >= o["tan"] - 0.01 for o in d["offers"])
    assert d["sustainability"]["ok"] is True
    assert "128-sexies" in d["disclaimer"]


def test_compare_only_fisso():
    r = requests.post(f"{API}/compare", json={
        "property_price": 200000, "down_payment": 60000, "duration_years": 20, "rate_type": "fisso",
    }, timeout=15)
    d = r.json()
    assert all(o["type"] == "fisso" for o in d["offers"])


def test_compare_ltv_exceeded():
    r = requests.post(f"{API}/compare", json={
        "property_price": 200000, "down_payment": 10000, "duration_years": 25, "rate_type": "fisso",
    }, timeout=15)
    d = r.json()
    assert d["eligible"] is False and d["reason"] == "ltv"
    assert d["min_down_payment"] == pytest.approx(40000, abs=1)


def test_compare_under36_consap():
    r = requests.post(f"{API}/compare", json={
        "property_price": 200000, "down_payment": 10000, "duration_years": 25,
        "rate_type": "fisso", "first_home": True, "age_under_36": True,
    }, timeout=15)
    d = r.json()
    assert d["eligible"] is True and d["ltv"] == 95.0 and d["consap_applied"] is True
    # solo banche consap
    assert all(o["consap_eligible"] for o in d["offers"])


def test_compare_validation():
    assert requests.post(f"{API}/compare", json={
        "property_price": 200000, "down_payment": 0, "duration_years": 17, "rate_type": "fisso",
    }, timeout=15).status_code == 400
    assert requests.post(f"{API}/compare", json={
        "property_price": 200000, "down_payment": 250000, "duration_years": 20, "rate_type": "fisso",
    }, timeout=15).status_code == 400
    assert requests.post(f"{API}/compare", json={
        "property_price": 200000, "down_payment": 0, "duration_years": 20, "rate_type": "misto",
    }, timeout=15).status_code == 400


def test_plan():
    r = requests.post(f"{API}/plan", json={"loan_amount": 200000, "tan_pct": 3.6, "duration_years": 25}, timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert len(d["years"]) == 25 and len(d["months_first_year"]) == 12
    assert d["years"][-1]["balance"] == pytest.approx(0, abs=1)
    total_principal = sum(y["principal"] for y in d["years"])
    assert total_principal == pytest.approx(200000, abs=5)


def test_lead_capture():
    r = requests.post(f"{API}/lead", json={
        "name": "Test Mutui", "email": "test.mutui@example.com", "phone": "3331234567",
        "property_price": 250000, "loan_amount": 200000, "duration_years": 25,
        "rate_type": "fisso", "best_rata": 1006.62, "gdpr_consent": True,
    }, timeout=15)
    assert r.status_code == 200 and r.json()["ok"] is True
