"""A-028d property coach + list smart filters helpers."""
from __future__ import annotations

from apps.immoweb.property_coach import build_coach_report


def test_coach_ready_listing():
    prop = {
        "id": "p1",
        "title": "Bilocale luminoso zona Navigli",
        "description": "Ampio bilocale ristrutturato con cucina abitabile e balcone. Vicino metro.",
        "operation": "sale",
        "price": 320000,
        "surface_sqm": 65,
        "city": "Milano",
        "province": "MI",
        "rooms": 2,
        "energy": {"energy_class": "C", "ipe": 120},
        "photos": [
            {"url": "/a.jpg"},
            {"url": "/b.jpg"},
            {"url": "/c.jpg"},
        ],
    }
    r = build_coach_report(prop)
    assert r["publishable"] is True
    assert r["hard_count"] == 0


def test_coach_missing_hard():
    prop = {
        "id": "p2",
        "title": "Casa",
        "description": "Corta",
        "operation": "sale",
        "city": "Roma",
        "photos": [],
    }
    r = build_coach_report(prop)
    assert r["publishable"] is False
    codes = {g["code"] for g in r["gaps"]}
    assert "less_than_3_photos" in codes or "no_valid_photo_url" in codes
    assert "missing_price" in codes
    soft = [g for g in r["gaps"] if g["hal_action"] == "description"]
    assert soft
