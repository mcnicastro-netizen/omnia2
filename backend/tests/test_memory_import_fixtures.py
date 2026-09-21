"""Offline: fixture canoniche in memory/fixtures/import/ (5 XML + CSV B/D)."""
from pathlib import Path
from xml.etree import ElementTree as ET

FIX = Path("/workspace/memory/fixtures/import")
if not FIX.exists():
    FIX = Path(__file__).resolve().parents[2] / "memory" / "fixtures" / "import"


def test_sample_xml_has_five_italian_listings():
    root = ET.fromstring((FIX / "sample-gestionale-italiano.xml").read_text(encoding="utf-8"))
    items = root.findall(".//immobile")
    assert len(items) == 5
    for el in items:
        tags = {c.tag.lower() for c in el}
        assert len(tags & {"prezzo", "canone", "mq", "citta", "titolo", "riferimento"}) >= 3
        assert el.findtext("titolo")
        assert el.findtext("citta")


def test_sample_immobili_csv_template_headers():
    header = (FIX / "sample-immobili.csv").read_text(encoding="utf-8").splitlines()[0]
    for col in ("title", "city", "property_type", "operation", "price"):
        assert col in header.split(";")
    assert header.startswith("title;")


def test_sample_clienti_csv_template_headers():
    header = (FIX / "sample-clienti.csv").read_text(encoding="utf-8").splitlines()[0]
    assert header.startswith("name;surname;email")
    assert "gdpr_consent" in header.split(";")
