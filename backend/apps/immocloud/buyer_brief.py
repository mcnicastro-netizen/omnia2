"""OMNIA — Scout HAL: Buyer Brief for ImmobilCloud listings.

Unique vs Idealista / Immobiliare.it:
- Transparent *completezza annuncio* score (0–100) from hard fields
- Price vs zone €/mq benchmark (CITY_PRICES) → sotto / in linea / sopra
- Domande concrete da fare al venditore (APE, spese, vincoli, stato)
- Optional LLM polish (falls back to deterministic brief if LLM down)

Endpoint: POST /api/cloud/property/{pid}/scout
Public + IP rate-limited. No payment. Lead-magnet toward valuator/visura.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from shared.db.connection import Database
from shared.security.rate_limit import enforce_ip_rate_limit

logger = logging.getLogger("omnia.scout_hal")
router = APIRouter(tags=["cloud-scout"])


class ScoutRequest(BaseModel):
    lang: Optional[str] = Field(default="it", max_length=5)


def _norm_city(name: Optional[str]) -> str:
    if not name:
        return ""
    s = name.lower().strip()
    s = re.sub(r"[àáâä]", "a", s)
    s = re.sub(r"[èéêë]", "e", s)
    s = re.sub(r"[ìíîï]", "i", s)
    s = re.sub(r"[òóôö]", "o", s)
    s = re.sub(r"[ùúûü]", "u", s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def completeness_score(p: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic listing quality score buyers can trust."""
    checks = []

    photos = p.get("photos") or []
    n_photos = len(photos) if isinstance(photos, list) else 0
    checks.append(("foto", min(n_photos, 10) * 3, 30, f"{n_photos} foto"))  # max 30

    desc = (p.get("description") or "").strip()
    desc_pts = 0
    if len(desc) >= 400:
        desc_pts = 15
    elif len(desc) >= 150:
        desc_pts = 10
    elif len(desc) >= 40:
        desc_pts = 5
    checks.append(("descrizione", desc_pts, 15, f"{len(desc)} caratteri"))

    energy = (p.get("energy") or {}).get("energy_class") if isinstance(p.get("energy"), dict) else p.get("energy_class")
    checks.append(("ape", 10 if energy else 0, 10, energy or "mancante"))

    checks.append(("planimetria", 8 if p.get("floor_plan_url") else 0, 8,
                   "sì" if p.get("floor_plan_url") else "no"))

    geo = 8 if (p.get("lat") and p.get("lng")) else 0
    checks.append(("geolocalizzazione", geo, 8, "sì" if geo else "no"))

    addr = 7 if (p.get("address") and len(str(p.get("address"))) > 4) else 0
    checks.append(("indirizzo", addr, 7, "visibile" if addr else "parziale/assente"))

    surface = 6 if p.get("surface_sqm") else 0
    checks.append(("superficie", surface, 6, str(p.get("surface_sqm") or "—")))

    rooms = 6 if p.get("rooms") or p.get("bedrooms") else 0
    checks.append(("locali", rooms, 6, str(p.get("rooms") or p.get("bedrooms") or "—")))

    price_ok = 5 if (p.get("price") or p.get("rent_monthly")) else 0
    checks.append(("prezzo", price_ok, 5, "indicato" if price_ok else "mancante"))

    boost = p.get("boost_tier")
    boost_pts = {"top": 5, "premium": 3, "vetrina": 2}.get(boost or "", 0)
    checks.append(("visibilità", boost_pts, 5, boost or "base"))

    score = sum(c[1] for c in checks)
    score = max(0, min(100, int(score)))
    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
    return {
        "score": score,
        "grade": grade,
        "checks": [
            {"key": k, "points": pts, "max": mx, "detail": detail}
            for k, pts, mx, detail in checks
        ],
    }


def price_vs_zone(p: Dict[str, Any]) -> Dict[str, Any]:
    """Compare asking €/mq to curated CITY_PRICES semicentro band."""
    from apps.immocloud.data.italy_real_estate_prices_2025 import CITY_PRICES, REGIONAL_DEFAULTS

    surface = float(p.get("surface_sqm") or 0)
    operation = p.get("operation") or "sale"
    asking = p.get("rent_monthly") if operation == "rent" else p.get("price")
    trying = float(asking or 0)
    if surface <= 0 or trying <= 0 or operation == "rent":
        return {
            "available": False,
            "reason": "rent_or_missing_surface" if operation == "rent" else "missing_price_or_surface",
        }

    e_mq = trying / surface
    city_key = _norm_city(p.get("city"))
    city = CITY_PRICES.get(city_key)
    if city:
        lo, hi = city.get("semicentro") or city.get("centro") or (0, 0)
        source = city.get("source") or "CITY_PRICES"
    else:
        lo, hi = REGIONAL_DEFAULTS["center"]
        source = "regional_fallback"

    mid = (lo + hi) / 2 if lo and hi else 0
    if not mid:
        return {"available": False, "reason": "no_benchmark"}

    delta_pct = round(100.0 * (e_mq - mid) / mid, 1)
    if e_mq < lo * 0.95:
        signal = "sotto_mercato"
        label = "Sotto la fascia di zona"
    elif e_mq > hi * 1.05:
        signal = "sopra_mercato"
        label = "Sopra la fascia di zona"
    else:
        signal = "in_linea"
        label = "In linea con la zona"

    return {
        "available": True,
        "signal": signal,
        "label_it": label,
        "asking_eur_mq": round(e_mq),
        "zone_eur_mq_min": lo,
        "zone_eur_mq_max": hi,
        "zone_eur_mq_mid": round(mid),
        "delta_pct_vs_mid": delta_pct,
        "benchmark_source": source,
        "city_key": city_key or None,
    }


def seller_questions(p: Dict[str, Any], completeness: Dict[str, Any]) -> List[str]:
    qs: List[str] = []
    energy = None
    if isinstance(p.get("energy"), dict):
        energy = p["energy"].get("energy_class")
    if not energy:
        qs.append("L'APE è disponibile? Qual è la classe energetica reale e la data del certificato?")
    if not p.get("floor_plan_url"):
        qs.append("Puoi condividere la planimetria catastale aggiornata?")
    if not p.get("address") or len(str(p.get("address") or "")) < 5:
        qs.append("Qual è l'indirizzo esatto e il piano? Ci sono vincoli di facciata o condominiali?")
    qs.append("Quali sono le spese condominiali mensili e ci sono lavori deliberati o fondi speciali?")
    if (p.get("operation") or "sale") == "sale":
        qs.append("L'immobile è libero subito? Ci sono ipoteche, usufrutto o diritti di terzi?")
    else:
        qs.append("Deposito cauzionale, garanzia reddito e contratti precedenti: quali condizioni?")
    # Deduplicate while preserving order
    out: List[str] = []
    for q in qs:
        if q not in out:
            out.append(q)
    return out[:5]


def red_flags(p: Dict[str, Any], vs_zone: Dict[str, Any], completeness: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    if completeness["score"] < 45:
        flags.append("Annuncio incompleto: poche informazioni verificate — chiedi documenti prima di visitare.")
    photos = p.get("photos") or []
    if len(photos) < 3:
        flags.append("Poche foto: rischio che dettagli critici (umidità, stato impianti) non siano visibili.")
    if vs_zone.get("signal") == "sopra_mercato" and (vs_zone.get("delta_pct_vs_mid") or 0) > 15:
        flags.append(
            f"Prezzo richiesto circa {vs_zone['delta_pct_vs_mid']}% sopra il mid di zona — chiedi giustificazione o margine di trattativa."
        )
    if vs_zone.get("signal") == "sotto_mercato" and (vs_zone.get("delta_pct_vs_mid") or 0) < -20:
        flags.append(
            "Prezzo molto sotto zona: verifica motivazione (urgenza, difetti, successione) prima di entusiasmarti."
        )
    energy = (p.get("energy") or {}).get("energy_class") if isinstance(p.get("energy"), dict) else None
    if energy in ("F", "G"):
        flags.append(f"Classe energetica {energy}: valuta costi di riqualificazione nel budget.")
    drop = p.get("last_price_drop") or {}
    if drop.get("drop_pct") and drop["drop_pct"] >= 5:
        flags.append(
            f"Ribasso recente del {drop['drop_pct']}%: il venditore sta correggendo il prezzo — utile in trattativa."
        )
    return flags[:5]


def next_steps(p: Dict[str, Any]) -> List[Dict[str, str]]:
    steps = [
        {"key": "visit", "label_it": "Prenota una visita e porta le domande Scout"},
        {"key": "valuator", "label_it": "Confronta con la stima ImmobilCloud (base gratis / UNI €2,99)"},
        {"key": "visura", "label_it": "Controlla visura catastale prima dell'offerta"},
        {"key": "mutuo", "label_it": "Simula la rata mutuo sullo stesso immobile"},
    ]
    if (p.get("operation") or "sale") == "rent":
        steps = [
            {"key": "visit", "label_it": "Prenota visita e verifica contratto/spese"},
            {"key": "docs", "label_it": "Chiedi APE e regolamento condominiale"},
        ]
    return steps


async def _llm_one_liner(p: Dict[str, Any], vs_zone: Dict[str, Any], score: int) -> Optional[str]:
    try:
        import asyncio
        from shared.llm import generate_text, LlmNotConfigured, LlmBusy
    except Exception:
        return None
    title = p.get("title") or p.get("property_type") or "Immobile"
    city = p.get("city") or ""
    signal = vs_zone.get("label_it") or "n/d"
    prompt = (
        f"Scrivi UNA sola frase in italiano (max 28 parole) per un acquirente che valuta "
        f"«{title}» a {city}. Completezza annuncio {score}/100. Segnale prezzo: {signal}. "
        f"Tono diretto, zero marketing, niente emoji."
    )
    try:
        text = await asyncio.wait_for(
            generate_text(
                prompt=prompt,
                system="Sei Scout HAL di ImmobilCloud. Solo fatti utili all'acquirente.",
                temperature=0.3,
            ),
            timeout=6.0,
        )
        text = (text or "").strip().strip('"')
        if len(text) > 220:
            text = text[:217] + "…"
        return text or None
    except (LlmNotConfigured, LlmBusy, asyncio.TimeoutError) as e:
        logger.info("scout llm skip: %s", e)
        return None
    except Exception as e:
        logger.warning("scout llm failed: %s", e)
        return None


def build_brief(p: Dict[str, Any], *, insight: Optional[str] = None) -> Dict[str, Any]:
    comp = completeness_score(p)
    vs = price_vs_zone(p)
    return {
        "product": "scout_hal",
        "listing_id": p.get("id"),
        "completeness": comp,
        "price_vs_zone": vs,
        "red_flags": red_flags(p, vs, comp),
        "questions_for_seller": seller_questions(p, comp),
        "next_steps": next_steps(p),
        "insight": insight,
        "disclaimer_it": (
            "Scout HAL è uno strumento informativo basato sui dati dell'annuncio e sui "
            "benchmark di zona ImmobilCloud. Non è una perizia né consulenza legale."
        ),
    }


@router.post("/property/{pid}/scout")
async def scout_listing(pid: str, request: Request, payload: ScoutRequest = ScoutRequest()):
    """Generate Scout HAL buyer brief for a public listing."""
    await enforce_ip_rate_limit(request, bucket="cloud_scout", max_requests=40, window_seconds=3600)
    db = Database.get()
    p = await db.properties.find_one(
        {
            "id": pid,
            "status": "active",
            "visibility": "public",
            "is_listed_on_immobilcloud": {"$ne": False},
            "moderation_status": {"$nin": ["pending", "rejected"]},
        },
        {"_id": 0, "owner": 0, "seller_client_id": 0, "commission_pct": 0},
    )
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")

    insight = await _llm_one_liner(p, price_vs_zone(p), completeness_score(p)["score"])
    brief = build_brief(p, insight=insight)
    brief["lang"] = (payload.lang or "it")[:2]
    return brief
