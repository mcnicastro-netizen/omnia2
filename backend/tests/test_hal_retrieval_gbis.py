"""Test HAL Knowledge RAG retrieval fix G-bis"""
import os
import json
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://omnia-crm-docs.preview.emergentagent.com').rstrip('/')
EMAIL = "mcnicastro@gmail.com"
PASSWORD = "Omn!pnWhzUXcUX4lPAmV"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:300]}"
    return s


def _ask(session, question):
    r = session.post(f"{BASE_URL}/api/app/hal/knowledge/ask", json={"question": question}, timeout=90)
    assert r.status_code == 200, f"ask failed: {r.status_code} {r.text[:300]}"
    return r.json()


def _dump(label, data):
    sources = data.get("sources", [])
    print(f"\n===== {label} =====")
    print(f"status={data.get('status')} confidence={data.get('confidence')}")
    for i, s in enumerate(sources[:5]):
        print(f"  #{i+1} {s.get('file')}::{s.get('chunk_id')} sim={s.get('similarity')}")
    ans = data.get("answer", "") or ""
    print(f"answer[0:250]={ans[:250]}")


def test_status_117(session):
    """Legacy check dopo G-bis · confidence storica"""
    r = session.get(f"{BASE_URL}/api/app/hal/knowledge/status", timeout=30)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    count = data.get("manual_hal_indexed") or data.get("indexed") or data.get("total_voci")
    # Post-Cap. 11 aspettavamo 129; ora post-Cap. 13 aspettiamo 155.
    assert count in (117, 129, 142, 155), f"Expected 117/129/142/155 (pre→post Cap. 11/12/13), got {count}"


def test_status_129(session):
    """Post-Cap. 11 H-bis · 129 voci attese (o più con capitoli successivi)"""
    r = session.get(f"{BASE_URL}/api/app/hal/knowledge/status", timeout=30)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    print(f"\nSTATUS 129+: {json.dumps(data, ensure_ascii=False)[:600]}")
    count = data.get("manual_hal_indexed") or data.get("indexed") or data.get("total_voci")
    # Accettato: 129 (post-Cap.11 H-bis), 142 (post-Cap.12), 155 (post-Cap.13)
    assert count in (129, 142, 155), f"Expected 129/142/155 indexed voices, got {count}"


def test_cap11_disclaimer_tub(session):
    """Cap. 11 H-bis · smoke disclaimer legale mediazione creditizia"""
    data = _ask(session, "OMNIA è mediatore creditizio?")
    _dump("CAP11 disclaimer-tub", data)
    top = data["sources"][0]
    assert "11-mutui-comparatore.yaml" in (top.get("file") or ""), f"file: {top}"
    assert top.get("chunk_id") == "mutui.disclaimer-tub", f"chunk: {top}"
    assert (top.get("similarity") or 0) >= 0.15
    ans = (data.get("answer") or "").lower()
    # HAL deve rispondere onestamente "no" con riferimento art. 128-sexies TUB
    assert ("no" in ans[:100] or "non" in ans[:100]), f"Answer should start with denial: {ans[:200]}"
    assert ("128-sexies" in ans or "tub" in ans or "mediazione" in ans), f"Missing legal reference: {ans[:400]}"


def test_gbis_primary_query(session):
    data = _ask(session, "Quanto costa un render Virtual Staging?")
    _dump("G-BIS PRIMARY", data)
    sources = data.get("sources", [])
    assert sources, "No sources returned"
    top = sources[0]
    assert "09-virtual-staging.yaml" in (top.get("file") or ""), f"Top-1 file wrong: {top}"
    assert top.get("chunk_id") == "staging.crediti-costo", f"Top-1 chunk wrong: {top}"
    assert (top.get("similarity") or 0) >= 0.20, f"Top-1 similarity too low: {top.get('similarity')}"
    ans = (data.get("answer") or "").lower()
    assert ("18" in ans and "credit" in ans) or "0,90" in ans or "0.90" in ans, f"Answer missing cost mention: {ans[:400]}"


def test_gbis_alternative_query(session):
    data = _ask(session, "Quanto spendo in crediti per lo staging?")
    _dump("G-BIS ALT", data)
    sources = data.get("sources", [])
    assert sources, "No sources returned"
    top = sources[0]
    assert "09-virtual-staging.yaml" in (top.get("file") or ""), f"Top-1 file wrong: {top}"
    assert top.get("chunk_id") == "staging.crediti-costo", f"Top-1 chunk wrong: {top}"


def test_cap10_hal_cos_e(session):
    data = _ask(session, "Cos'è HAL Agent in OMNIA?")
    _dump("CAP10 cos-e", data)
    top = data["sources"][0]
    assert "10-hal-agent-crm.yaml" in (top.get("file") or ""), f"file: {top}"
    assert top.get("chunk_id") == "hal.cos-e", f"chunk: {top}"
    assert (top.get("similarity") or 0) >= 0.15


def test_cap10_hal_improve(session):
    data = _ask(session, "A cosa serve il pulsante Migliora con HAL nei form?")
    _dump("CAP10 improve", data)
    top = data["sources"][0]
    assert "10-hal-agent-crm.yaml" in (top.get("file") or "")
    assert top.get("chunk_id") == "hal.improve-titolo-descrizione", f"chunk: {top}"
    assert (top.get("similarity") or 0) >= 0.15


def test_public_config_banks_count_8():
    """Cap. 11 H-bis · endpoint pubblico coerenza fonte di verità"""
    r = requests.get(f"{BASE_URL}/api/cloud/mutui/config", timeout=30)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("banks_count") == 8, f"Expected banks_count=8, got {data.get('banks_count')}"
    assert data.get("offers_count") == 14, f"Expected offers_count=14, got {data.get('offers_count')}"


def test_cap11_offerte_14_banche_8(session):
    """Cap. 11 H-bis · voce rinominata da -banche-9 a -banche-8"""
    data = _ask(session, "Quali banche compaiono nel Comparatore Mutui?")
    _dump("CAP11 offerte-14-banche-8", data)
    top = data["sources"][0]
    assert "11-mutui-comparatore.yaml" in (top.get("file") or ""), f"file: {top}"
    assert top.get("chunk_id") == "mutui.offerte-14-banche-8", f"chunk (should be -banche-8, NOT -banche-9): {top}"
    assert (top.get("similarity") or 0) >= 0.15
    ans = (data.get("answer") or "").lower()
    # Deve menzionare 8 banche e 9 offerte Consap (non 9 banche o 11 Consap)
    assert "8" in ans, f"Answer must mention 8 banks: {ans[:400]}"
    assert "9" in ans, f"Answer must mention 9 Consap offers: {ans[:400]}"


def test_cap11_cos_e(session):
    data = _ask(session, "Cos'è il Comparatore Mutui di OMNIA?")
    _dump("CAP11 cos-e", data)
    top = data["sources"][0]
    assert "11-mutui-comparatore.yaml" in (top.get("file") or ""), f"file: {top}"
    assert top.get("chunk_id") == "mutui.cos-e", f"chunk: {top}"
    assert (top.get("similarity") or 0) >= 0.15


def test_cap11_motore_taeg(session):
    data = _ask(session, "Come viene calcolato il TAEG del mutuo?")
    _dump("CAP11 motore", data)
    top = data["sources"][0]
    assert "11-mutui-comparatore.yaml" in (top.get("file") or ""), f"file: {top}"
    assert top.get("chunk_id") == "mutui.motore", f"chunk: {top}"
    assert (top.get("similarity") or 0) >= 0.15


def test_cap10_hal_limiti(session):
    data = _ask(session, "Cosa NON può fare HAL Agent?")
    _dump("CAP10 limiti", data)
    top = data["sources"][0]
    assert "10-hal-agent-crm.yaml" in (top.get("file") or "")
    assert top.get("chunk_id") == "hal.limiti-cosa-non-fa", f"chunk: {top}"
    assert (top.get("similarity") or 0) >= 0.15
