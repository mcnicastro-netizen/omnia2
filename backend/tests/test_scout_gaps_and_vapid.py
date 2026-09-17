"""Unit tests: Scout gaps + price fascia/why/confidence + VAPID bootstrap."""
from __future__ import annotations

import os

from apps.immocloud.buyer_brief import build_brief, completeness_score, price_vs_zone, seller_gaps
from shared.notifications.web_push import ensure_vapid_keys, is_push_configured, vapid_public_key


def test_seller_gaps_on_thin_listing():
    thin = {
        "id": "thin-1",
        "title": "Appartamento",
        "description": "Breve",
        "city": "Milano",
        "operation": "sale",
        "price": 300000,
        "photos": [],
    }
    comp = completeness_score(thin)
    assert comp["score"] < 70
    assert comp["grade"] in ("C", "D")
    gaps = seller_gaps(comp)
    keys = {g["key"] for g in gaps}
    assert "foto" in keys
    assert "ape" in keys or "descrizione" in keys
    brief = build_brief(thin)
    assert brief["insight"]
    assert brief["seller_gaps"]
    assert brief["product"] == "scout_hal"


def test_price_fascia_why_confidence_milano():
    p = {
        "id": "rich-1",
        "city": "Milano",
        "operation": "sale",
        "price": 520000,
        "surface_sqm": 95,
        "address": "Via Tortona 12",
        "lat": 45.45,
        "lng": 9.17,
        "photos": [{"url": "/x.jpg"}] * 6,
        "description": (
            "Ampio trilocale luminoso con cucina abitabile, due balconi e cantina. "
            "Ristrutturato nel 2019, riscaldamento autonomo, doppi vetri. "
            "Zona servita da metro e negozi. Spese condominiali contenute."
        ),
        "energy": {"energy_class": "D"},
        "rooms": 3,
    }
    vs = price_vs_zone(p)
    assert vs["available"] is True
    assert vs["signal"] in ("sotto_mercato", "in_linea", "sopra_mercato")
    assert "fascia stimata" in vs["label_it"].lower() or "linea" in vs["label_it"].lower()
    band = vs["estimated_band_eur"]
    assert band["min"] < band["max"]
    assert band["min"] == vs["zone_eur_mq_min"] * 95
    assert len(vs["why"]) >= 3
    assert vs["confidence"]["level"] in ("alta", "media", "bassa")
    assert vs["confidence"]["score"] >= 45
    assert len(vs["confidence"]["limits_it"]) >= 1
    assert "verità" not in vs["label_it"].lower()

    brief = build_brief(p)
    assert brief["price_vs_zone"]["estimated_band_eur"]
    assert brief["price_vs_zone"]["why"]
    assert brief["price_vs_zone"]["confidence"]["limits_it"]


def test_price_confidence_lower_on_unknown_city():
    p = {
        "city": "PaeseInesistenteXYZ",
        "operation": "sale",
        "price": 200000,
        "surface_sqm": 80,
        "photos": [],
        "description": "x",
    }
    vs = price_vs_zone(p)
    assert vs["available"] is True
    assert vs["benchmark_source"] == "regional_fallback"
    assert vs["confidence"]["level"] in ("bassa", "media")
    assert any("regionale" in lim.lower() for lim in vs["confidence"]["limits_it"])


def test_vapid_ensure_keys(tmp_path, monkeypatch):
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    cache = tmp_path / ".vapid_local.json"
    monkeypatch.setattr("shared.notifications.web_push._VAPID_CACHE_FILE", cache)
    out = ensure_vapid_keys()
    assert out.get("configured") is True
    assert is_push_configured()
    assert len(vapid_public_key()) > 20
    out2 = ensure_vapid_keys()
    assert out2.get("configured") is True
    assert cache.exists() or os.environ.get("VAPID_PUBLIC_KEY")
