"""Fase C — Fascicolo Immobile AI + descrizione coordinata staging.

Live API tests. LLM calls (analyze, rewrite-description) cost pennies on Gemini Flash.
"""
import base64
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]

FAKE_PDF = base64.b64encode(b"%PDF-1.4 fake test doc").decode()


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def test_property(admin_session):
    payload = {
        "title": f"TEST Fascicolo {uuid.uuid4().hex[:6]}",
        "operation": "sale",
        "property_type": "appartamento",
        "city": "Catania",
        "zone": "centro",
        "price": 220000,
        "surface_sqm": 90,
        "rooms": 4,
        "energy": {"energy_class": "C"},
    }
    r = admin_session.post(f"{API}/app/properties", json=payload, timeout=20)
    assert r.status_code in (200, 201), r.text
    prop_id = r.json()["id"]
    yield prop_id
    admin_session.delete(f"{API}/app/properties/{prop_id}", timeout=15)


def test_fascicolo_requires_auth():
    r = requests.get(f"{API}/app/fascicolo/{uuid.uuid4()}", timeout=15)
    assert r.status_code in (401, 403)


def test_fascicolo_unknown_property(admin_session):
    r = admin_session.get(f"{API}/app/fascicolo/{uuid.uuid4()}", timeout=15)
    assert r.status_code == 404


def test_fascicolo_structure_and_valuation(admin_session, test_property):
    r = admin_session.get(f"{API}/app/fascicolo/{test_property}", timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["property"]["id"] == test_property
    keys = {c["key"] for c in d["checklist"]}
    # condo items present (appartamento)
    assert {"ape", "planimetria_catastale", "visura_catastale", "regolamento_condominio"} <= keys
    assert d["progress"]["required_total"] == 5
    assert d["progress"]["required_done"] == 0
    # APE note: energy class declared but no APE uploaded
    ape = next(c for c in d["checklist"] if c["key"] == "ape")
    assert "note" in ape
    # valuation computed (Catania is in dataset)
    assert d["valuation"] and d["valuation"]["estimated_value"]["avg"] > 0


def test_upload_invalid_doc_type(admin_session, test_property):
    r = admin_session.post(f"{API}/app/fascicolo/{test_property}/documents", json={
        "doc_type": "rogito_klingon", "name": "x.pdf", "mime": "application/pdf", "file_data": FAKE_PDF,
    }, timeout=15)
    assert r.status_code == 400


def test_upload_invalid_base64(admin_session, test_property):
    r = admin_session.post(f"{API}/app/fascicolo/{test_property}/documents", json={
        "doc_type": "ape", "name": "x.pdf", "mime": "application/pdf", "file_data": "not-base64!!!",
    }, timeout=15)
    assert r.status_code == 400


def test_document_lifecycle(admin_session, test_property):
    # upload APE
    up = admin_session.post(f"{API}/app/fascicolo/{test_property}/documents", json={
        "doc_type": "ape", "name": "ape_test.pdf", "mime": "application/pdf", "file_data": FAKE_PDF,
    }, timeout=15)
    assert up.status_code == 200, up.text
    doc_id = up.json()["document"]["id"]
    assert "file_data" not in up.json()["document"]

    # fascicolo reflects it
    f = admin_session.get(f"{API}/app/fascicolo/{test_property}", timeout=30).json()
    ape = next(c for c in f["checklist"] if c["key"] == "ape")
    assert ape["present"] is True and "note" not in ape
    assert f["progress"]["required_done"] == 1
    assert all("file_data" not in d for d in f["documents"])

    # download
    dl = admin_session.get(f"{API}/app/fascicolo/{test_property}/documents/{doc_id}/download", timeout=15)
    assert dl.status_code == 200
    assert dl.content.startswith(b"%PDF")

    # delete
    de = admin_session.delete(f"{API}/app/fascicolo/{test_property}/documents/{doc_id}", timeout=15)
    assert de.status_code == 200
    f2 = admin_session.get(f"{API}/app/fascicolo/{test_property}", timeout=30).json()
    assert f2["progress"]["required_done"] == 0


def test_analyze_with_al(admin_session, test_property):
    r = admin_session.post(f"{API}/app/fascicolo/{test_property}/analyze", timeout=60)
    assert r.status_code == 200, r.text
    a = r.json()["analysis"]
    assert a["source"] in ("al", "rule_based")
    assert len(a["text"]) > 30
    # persisted
    f = admin_session.get(f"{API}/app/fascicolo/{test_property}", timeout=30).json()
    assert f["last_analysis"]["text"] == a["text"]
