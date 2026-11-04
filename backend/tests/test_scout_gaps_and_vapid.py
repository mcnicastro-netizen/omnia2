"""Unit tests: Scout gaps + price fascia/why/confidence + VAPID bootstrap."""
from __future__ import annotations

import os

from apps.immocloud.buyer_brief import (
    build_brief,
    completeness_score,
    documents_before_offer,
    price_vs_zone,
    seller_gaps,
    visit_checklist,
)
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
    assert vs["benchmark_source"] == "none"
    assert vs["signal"] == "benchmark_assente"
    assert vs["estimated_band_eur"] is None
    assert vs["confidence"]["level"] == "bassa"
    assert vs.get("valuator_suggested") is True
    joined = " ".join(w["label_it"] for w in vs["why"]).lower()
    assert "regional_fallback" not in joined
    assert "fonte zona" not in joined
    assert "valutatore" in joined


def test_price_mascalucia_uses_catania_parent_not_center_italy():
    """Dogfood: Mascalucia must not get fake «media regionale» centro Italia."""
    p = {
        "city": "Mascalucia",
        "operation": "sale",
        "price": 200000,
        "surface_sqm": 160,
        "photos": [{"url": "/x.jpg"}] * 5,
        "description": "Villetta con giardino e garage doppio, ambienti luminosi e zona servita.",
        "address": "via del bosco 1",
        "lat": 37.57,
        "lng": 15.05,
        "rooms": 5,
    }
    vs = price_vs_zone(p)
    assert vs["available"] is True
    assert vs["benchmark_source"] == "city_parent"
    assert vs["zone_eur_mq_min"] and vs["zone_eur_mq_max"]
    # Catania semicentro ~1200–1700 × 0.88 → ~1056–1496 (not 1900–2800 centro IT)
    assert vs["zone_eur_mq_max"] < 1900
    joined = " ".join(w["label_it"] for w in vs["why"]).lower()
    assert "regional_fallback" not in joined
    assert "fonte zona" not in joined
    assert "entusiasmarti" not in joined
    assert "chiesto" not in joined
    comp = completeness_score(p)
    assert comp["grade_label_it"] in ("Ottima", "Buona", "Sufficiente", "Da completare")


def test_visit_checklist_and_documents_sale():
    p = {
        "city": "Milano",
        "operation": "sale",
        "price": 400000,
        "surface_sqm": 80,
        "energy": {"energy_class": "G"},
        "floor": 3,
    }
    visit = visit_checklist(p)
    docs = documents_before_offer(p)
    assert 4 <= len(visit) <= 10
    assert any(i["key"] == "moisture" for i in visit)
    assert any(i["key"] == "energy_reality" for i in visit)
    assert not any(i["key"] in ("systems", "noise_light", "inclusions", "access") for i in visit)
    assert 4 <= len(docs) <= 9
    keys = {d["key"] for d in docs}
    assert "ape" in keys and "visura" in keys
    assert "concessione" in keys and "abitabilita" in keys and "impianti" in keys
    brief = build_brief(p)
    assert brief["visit_checklist"]
    assert brief["documents_before_offer"]
    assert all("why_it" in d for d in brief["documents_before_offer"])
    assert any("mutuabile" in q.lower() for q in brief["questions_for_seller"])


def test_documents_rent_differs_from_sale():
    rent_docs = {d["key"] for d in documents_before_offer({"operation": "rent"})}
    sale_docs = {d["key"] for d in documents_before_offer({"operation": "sale"})}
    assert "contratto" in rent_docs
    assert "visura" in sale_docs
    assert "contratto" not in sale_docs


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
