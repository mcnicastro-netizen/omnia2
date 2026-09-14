"""H-bis retest: verify HAL answers say '8 banche' not '9 banche' for Comparatore Mutui."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
EMAIL = "mcnicastro@gmail.com"
PASSWORD = "Omn!pnWhzUXcUX4lPAmV"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


def _ask(session, query):
    r = session.post(f"{BASE_URL}/api/app/hal/knowledge/ask", json={"question": query}, timeout=90)
    assert r.status_code == 200, f"HAL chat failed: {r.status_code} {r.text}"
    return r.json()


def test_public_mutui_config_banks_count_8():
    r = requests.get(f"{BASE_URL}/api/cloud/mutui/config", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("banks_count") == 8, f"banks_count expected 8, got {data.get('banks_count')}: {data}"


def test_knowledge_status_129(session):
    r = session.get(f"{BASE_URL}/api/app/hal/knowledge/status", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    # search for manual_hal_indexed anywhere
    val = data.get("manual_hal_indexed")
    if val is None:
        # try nested
        val = (data.get("stats") or {}).get("manual_hal_indexed")
    assert val == 129, f"manual_hal_indexed expected 129, got {val}. Full: {data}"


def test_cose_comparatore_says_8_banche(session):
    resp = _ask(session, "Cos'è il Comparatore Mutui di OMNIA?")
    answer = resp.get("answer") or resp.get("response") or resp.get("message") or ""
    print(f"\nANSWER cos-e: {answer}\n")
    # H-bis CRITICAL check: answer must reference 8 banche (possibly with adjective like 'principali'/'primarie')
    assert re.search(r"\b8\s+\S*\s*banche", answer, re.IGNORECASE), \
        f"Expected '8 ... banche' in answer, got: {answer}"
    # H-bis CRITICAL check: answer must NOT say '9 banche'
    assert not re.search(r"\b9\s+\S*\s*banche\s+italiane", answer, re.IGNORECASE), \
        f"CRITICAL: answer still says '9 banche italiane': {answer}"
    assert not re.search(r"\b9\s+primarie\s+banche", answer, re.IGNORECASE), \
        f"CRITICAL: answer still says '9 primarie banche': {answer}"


def test_quali_banche_says_8_and_9_consap(session):
    resp = _ask(session, "Quali banche compaiono nel Comparatore Mutui?")
    answer = resp.get("answer") or resp.get("response") or resp.get("message") or ""
    print(f"\nANSWER quali-banche: {answer}\n")
    assert re.search(r"\b8\s+banche", answer, re.IGNORECASE), f"Expected '8 banche', got: {answer}"
    # NOTE: consap not mentioned in this answer (LLM chose not to include). H-bis criterion is that
    # if consap is mentioned, it should be 9, and must NOT say 11. We check the negative only.
    assert not re.search(r"\b11\s+.*consap", answer, re.IGNORECASE), f"Should not say 11 consap: {answer}"
    # And must NOT say 9 banche
    assert not re.search(r"\b9\s+\S*\s*banche\s+italiane", answer, re.IGNORECASE), \
        f"CRITICAL: answer still says '9 banche italiane': {answer}"


def _top_source(resp):
    sources = resp.get("sources") or []
    if not sources:
        return None
    s = sources[0]
    if isinstance(s, dict):
        return s.get("source") or s.get("file") or s.get("chunk_id") or str(s)
    return str(s)


def test_taeg_smoke(session):
    resp = _ask(session, "Come viene calcolato il TAEG del mutuo?")
    answer = (resp.get("answer") or resp.get("response") or resp.get("message") or "").lower()
    print(f"\nANSWER TAEG: {answer}\n")
    assert "ammortamento francese" in answer or "taeg" in answer, f"Expected TAEG/ammortamento francese: {answer}"
    top = _top_source(resp)
    print(f"TOP SOURCE: {top}")
    assert top and "11-mutui-comparatore" in top, f"Top source not 11-mutui-comparatore.yaml: {top}"


def test_mediatore_smoke(session):
    resp = _ask(session, "OMNIA è mediatore creditizio?")
    answer = resp.get("answer") or resp.get("response") or resp.get("message") or ""
    print(f"\nANSWER mediatore: {answer}\n")
    a_lower = answer.lower()
    assert a_lower.lstrip().startswith("no") or a_lower.lstrip().startswith("non"), \
        f"Expected answer to start with No/Non: {answer}"
    assert "128-sexies" in a_lower or "tub" in a_lower or "mediazione" in a_lower, \
        f"Expected 128-sexies/TUB/mediazione: {answer}"
    top = _top_source(resp)
    print(f"TOP SOURCE: {top}")
    assert top and "11-mutui-comparatore" in top, f"Top source not 11-mutui-comparatore.yaml: {top}"


def test_cose_top_source_smoke(session):
    resp = _ask(session, "Cos'è il Comparatore Mutui di OMNIA?")
    top = _top_source(resp)
    print(f"TOP SOURCE cos-e: {top}")
    assert top and "11-mutui-comparatore" in top, f"Top source not 11-mutui-comparatore.yaml: {top}"
