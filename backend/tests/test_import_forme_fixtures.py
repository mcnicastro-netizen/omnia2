"""Offline check: fixture forme A–E esistono e hanno i marker attesi (no API)."""
from pathlib import Path
from xml.etree import ElementTree as ET

FIX = Path(__file__).resolve().parent / "fixtures" / "import"


def test_forma_a_universal_xml_parses():
    root = ET.fromstring((FIX / "forma-a-universal.xml").read_text(encoding="utf-8"))
    items = root.findall(".//immobile")
    assert len(items) == 2
    assert items[0].findtext("riferimento") == "FIX-A-001"
    assert items[0].findtext("citta") == "Milano"
    assert items[1].findtext("canone") == "650"


def test_forma_b_csv_headers_match_template():
    text = (FIX / "forma-b-immobili.csv").read_text(encoding="utf-8")
    header = text.splitlines()[0]
    for col in ("title", "city", "property_type", "operation", "price"):
        assert col in header.split(";")
    assert "FIX-B-001" in text


def test_forma_c_vendor_a_heuristic_tags():
    root = ET.fromstring((FIX / "forma-c-vendor-a.xml").read_text(encoding="utf-8"))
    assert root.find(".//cod_tipologia") is not None
    assert root.find(".//id_agenzia") is not None
    assert root.find(".//rif").text == "FIX-C-001"


def test_forma_d_client_csv():
    text = (FIX / "forma-d-clienti.csv").read_text(encoding="utf-8")
    header = text.splitlines()[0]
    assert header.startswith("name;surname;email")
    assert "gdpr_consent" in header
    assert "lucia.verdi@example.it" in text


def test_forma_e_messy_text_has_contacts():
    text = (FIX / "forma-e-clienti-messy.txt").read_text(encoding="utf-8")
    assert "giuseppe.neri@example.it" in text
    assert "Anna Bianchi" in text
