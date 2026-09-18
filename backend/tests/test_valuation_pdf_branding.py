"""Unit tests for valuation PDF branding (OMNIA vs white-label)."""
from __future__ import annotations

from apps.immocloud.valuation_pdf import OMNIA_BRAND, build_valuation_pdf
from apps.immocloud.valuator import ValuationPayload


def _sample_result(**over):
    base = {
        "city_resolved": "milano",
        "zone_tier": "semicentro",
        "surface": {
            "calpestabile_mq": 80,
            "commercial_mq": 92.5,
            "breakdown": {
                "principale_mq": {"mq": 80, "coeff": 1.0, "weighted": 80},
                "balcone_mq": {"mq": 10, "coeff": 0.3, "weighted": 3},
                "cantina_mq": {"mq": 12, "coeff": 0.3, "weighted": 3.6},
                "box_mq": {"mq": 12, "coeff": 0.5, "weighted": 6},
            },
        },
        "price_per_sqm": {"min": 5500, "avg": 6500, "max": 7500},
        "estimated_value": {"min": 508750, "avg": 601250, "max": 693750},
        "confidence": "high",
        "confidence_score": 92,
        "merit_breakdown": {
            "exposure": {"pct": 0.03},
            "elevator": {"pct": 0.02},
            "view": {"pct": -0.01},
        },
        "comparables": [
            {"title": "Appartamento semicentro", "zone": "Porta Romana", "surface_sqm": 78, "price": 520000, "price_per_sqm": 6667},
            {"title": "Trilocale ristrutturato", "zone": "Navigli", "surface_sqm": 85, "price": 610000, "price_per_sqm": 7176},
        ],
        "methodology": (
            "Pipeline professionale OMNIA: 1) prezzo base OMI/Borsino città, "
            "2) superficie commerciale UNI 10750."
        ),
        "data_source": "CITY_PRICES · Milano semicentro",
        "disclaimer": (
            "Stima orientativa basata su dati statistici di mercato e norme UNI 10750. "
            "Per una valutazione vincolante richiedi una perizia ufficiale a un agente OMNIA "
            "certificato o un perito iscritto all'Albo."
        ),
    }
    base.update(over)
    return base


def _payload():
    return ValuationPayload(
        city="Milano",
        zone="semicentro",
        property_type="appartamento",
        surface_sqm=80,
        condition="buono",
        energy_class="C",
        commercial_surfaces={
            "principale_mq": 80,
            "balcone_mq": 10,
            "cantina_mq": 12,
            "box_auto_mq": 12,
        },
        merit={
            "exposure": "sud",
            "elevator": "presente",
            "view": "interno",
        },
    )


def _pdf_text(pdf_bytes: bytes) -> str:
    # Prefer pypdf if available; else crude Latin-1 extract of content streams
    try:
        from pypdf import PdfReader
        reader = PdfReader(__import__("io").BytesIO(pdf_bytes))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return pdf_bytes.decode("latin-1", errors="ignore")


def test_pdf_magic_and_min_size():
    pdf = build_valuation_pdf(_sample_result(), _payload(), branding=dict(OMNIA_BRAND))
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2500


def test_omnia_brand_mentions_immobilcloud():
    pdf = build_valuation_pdf(_sample_result(), _payload(), branding=dict(OMNIA_BRAND))
    text = _pdf_text(pdf)
    assert "ImmobilCloud" in text
    assert "Rapporto di valutazione" in text.lower() or "VALORE DI MERCATO" in text or "Valore" in text


def test_whitelabel_omits_omnia_and_sanitizes_disclaimer():
    branding = {
        "name": "Nicastro Immobiliare",
        "tagline": "Casa con cura",
        "primary_color": "#1A3A2A",
        "accent_color": "#C4A35A",
        "email": "info@nicastro.example",
        "phone": "+39 02 000000",
        "plan_type": "whitelabel",
    }
    pdf = build_valuation_pdf(_sample_result(), _payload(), branding=branding)
    text = _pdf_text(pdf)
    assert "Nicastro Immobiliare" in text
    assert "OMNIA" not in text
    assert "ImmobilCloud" not in text
    assert "agente OMNIA" not in text


def test_hybrid_agency_keeps_soft_omnia_credit():
    branding = {
        "name": "Studio Lago",
        "tagline": "Lago di Como",
        "primary_color": "#0B1E3F",
        "accent_color": "#1F6B5C",
        "plan_type": "hybrid",
    }
    pdf = build_valuation_pdf(_sample_result(), _payload(), branding=branding)
    text = _pdf_text(pdf)
    assert "Studio Lago" in text
    assert "OMNIA" in text or "ImmobilCloud" in text
