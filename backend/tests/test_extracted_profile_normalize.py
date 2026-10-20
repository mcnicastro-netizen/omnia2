"""Normalize seed/legacy extracted_profile vs extractor nested brand_profile."""
from apps.immoweb.themes import normalize_extracted_profile, auto_pick_theme


def test_normalize_nested_extractor_shape():
    raw = {
        "brand_profile": {
            "palette": {"primary": "#BC4F08"},
            "voice": {"tone": "professionale"},
            "confidence": 80,
        },
        "logo_hint": {"url": "https://example.com/logo.jpg"},
        "extracted_from": "https://www.nicastroimmobiliare.it/",
    }
    out = normalize_extracted_profile(raw)
    assert out["brand_profile"]["palette"]["primary"] == "#BC4F08"
    assert out["logo_hint"]["url"].endswith("logo.jpg")


def test_normalize_flat_seed_shape():
    raw = {
        "source_url": "https://www.nicastroimmobiliare.it/",
        "palette": {
            "primary": "#BC4F08",
            "accent": "#3DB04B",
            "neutral_dark": "#2B2B2B",
            "neutral_light": "#F4F4F4",
        },
        "voice": {"tone": "professionale", "tagline_guess": "La tua casa in Sicilia"},
        "structure": {"header_style": "classic"},
        "logo_hint": {"url": "https://media.agestaweb.it/siti/02427/public/foto/logo.jpg"},
        "confidence": 70,
        "assisted": True,
    }
    out = normalize_extracted_profile(raw)
    bp = out["brand_profile"]
    assert bp["palette"]["primary"] == "#BC4F08"
    assert bp["voice"]["tone"] == "professionale"
    assert bp["confidence"] == 70
    assert out["logo_hint"]["url"].endswith("logo.jpg")
    assert auto_pick_theme(bp) == "classic"


def test_normalize_empty():
    assert normalize_extracted_profile(None) == {}
    assert normalize_extracted_profile({}) == {}
