"""OMNIA — Scout: Buyer Brief for ImmobilCloud listings.

Pre-visita intelligence (nord B2C):
- Completezza annuncio (0–100)
- Prezzo: segnale + fascia stimata (€) + perché + confidenza/limiti
- Domande concrete da fare al venditore
- Optional LLM polish (falls back to deterministic brief)

Endpoint: POST /api/cloud/property/{pid}/scout
Public + IP rate-limited. No payment.
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


def price_vs_zone(p: Dict[str, Any], *, completeness_score_val: Optional[int] = None) -> Dict[str, Any]:
    """Compare asking €/mq to curated CITY_PRICES — fascia + perché + confidenza.

    North star: prezzo come segnale + fascia stimata + perché + limiti,
    mai come verità assoluta di mercato.
    """
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
    city_known = bool(city)
    if city:
        band_key = "semicentro"
        lo, hi = city.get("semicentro") or city.get("centro") or (0, 0)
        source = city.get("source") or "CITY_PRICES"
        zone_tier = "semicentro"
    else:
        lo, hi = REGIONAL_DEFAULTS["center"]
        source = "regional_fallback"
        zone_tier = "media_regionale"
        band_key = "regional"

    mid = (lo + hi) / 2 if lo and hi else 0
    if not mid:
        return {"available": False, "reason": "no_benchmark"}

    delta_pct = round(100.0 * (e_mq - mid) / mid, 1)
    if e_mq < lo * 0.95:
        signal = "sotto_mercato"
        label = "Sotto la fascia stimata di zona"
    elif e_mq > hi * 1.05:
        signal = "sopra_mercato"
        label = "Sopra la fascia stimata di zona"
    else:
        signal = "in_linea"
        label = "In linea con la fascia stimata"

    band_min = int(round(lo * surface))
    band_max = int(round(hi * surface))
    band_mid = int(round(mid * surface))

    # Confidence — honest without pretending we have street-level comps
    conf_pts = 0
    limits: List[str] = []
    if city_known:
        conf_pts += 40
    else:
        conf_pts += 10
        limits.append("Città non nel benchmark locale: usiamo una media regionale, meno precisa.")
    if source != "regional_fallback":
        conf_pts += 15
    if 30 <= surface <= 250:
        conf_pts += 15
    else:
        limits.append("Superficie fuori dalla fascia tipica (30–250 m²): il confronto €/m² è più debole.")
    cscore = completeness_score_val
    if cscore is None:
        cscore = completeness_score(p)["score"]
    if cscore >= 60:
        conf_pts += 15
    elif cscore < 45:
        conf_pts += 0
        limits.append("Annuncio incompleto: con pochi dati il segnale prezzo è meno affidabile.")
    else:
        conf_pts += 8
    if p.get("lat") and p.get("lng"):
        conf_pts += 5
    if p.get("address") and len(str(p.get("address"))) > 4:
        conf_pts += 5
    conf_pts = max(0, min(100, conf_pts))
    # Cap: thin listings never claim "alta" — honesty over optimism
    if cscore < 45:
        conf_pts = min(conf_pts, 55)
    if conf_pts >= 70:
        conf_level = "alta"
        conf_label = "Confidenza alta per un primo sguardo"
    elif conf_pts >= 45:
        conf_level = "media"
        conf_label = "Confidenza media — verifica in visita"
    else:
        conf_level = "bassa"
        conf_label = "Confidenza bassa — trattala come indizio"

    limits.append(
        "Fascia da €/m² di zona (benchmark semicentro), non da comparabili puntuali di questo civico."
    )
    limits.append("Non è una perizia né un valore OMI ufficiale per questo immobile.")

    why: List[Dict[str, str]] = [
        {
            "key": "asking",
            "label_it": (
                f"Il prezzo chiesto è circa € {int(round(e_mq))}/m² "
                f"({int(round(trying)):,} € su {int(surface)} m²).".replace(",", ".")
            ),
        },
        {
            "key": "band",
            "label_it": (
                f"In {p.get('city') or 'zona'}, la fascia stimata {zone_tier.replace('_', ' ')} "
                f"è € {lo}–{hi}/m² → per questi mq circa "
                f"€ {band_min:,}–{band_max:,}.".replace(",", ".")
            ),
        },
    ]
    if signal == "sopra_mercato":
        why.append({
            "key": "signal",
            "label_it": (
                "Il chiesto sta sopra quella fascia: chiedi motivazione (vista, ristrutturazione, "
                "piano) o margine di trattativa — non è automaticamente ‘caro’."
            ),
        })
    elif signal == "sotto_mercato":
        why.append({
            "key": "signal",
            "label_it": (
                "Il chiesto sta sotto quella fascia: verifica urgenza, stato, vincoli o successione "
                "prima di entusiasmarti."
            ),
        })
    else:
        why.append({
            "key": "signal",
            "label_it": "Il chiesto cade dentro la fascia stimata: buon punto di partenza, non una garanzia.",
        })
    why.append({
        "key": "source",
        "label_it": f"Fonte benchmark: {source}.",
    })

    return {
        "available": True,
        "signal": signal,
        "label_it": label,
        "asking_eur_mq": round(e_mq),
        "asking_eur": int(round(trying)),
        "zone_eur_mq_min": lo,
        "zone_eur_mq_max": hi,
        "zone_eur_mq_mid": round(mid),
        "zone_tier": zone_tier,
        "delta_pct_vs_mid": delta_pct,
        "estimated_band_eur": {
            "min": band_min,
            "max": band_max,
            "mid": band_mid,
        },
        "why": why,
        "confidence": {
            "level": conf_level,
            "score": conf_pts,
            "label_it": conf_label,
            "limits_it": limits[:4],
            "comparables_n": None,  # filled by endpoint when nearby listings exist
            "band_key": band_key,
        },
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
        band = vs_zone.get("estimated_band_eur") or {}
        if band.get("max"):
            flags.append(
                f"Chiesto sopra la fascia stimata (fino a circa € {int(band['max']):,}). "
                "Chiedi giustificazione o margine di trattativa.".replace(",", ".")
            )
        else:
            flags.append("Chiesto sopra la fascia stimata di zona — chiedi giustificazione o margine.")
    if vs_zone.get("signal") == "sotto_mercato" and (vs_zone.get("delta_pct_vs_mid") or 0) < -20:
        flags.append(
            "Prezzo sotto la fascia stimata: verifica motivazione (urgenza, difetti, successione) prima di entusiasmarti."
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


def seller_gaps(completeness: Dict[str, Any]) -> List[Dict[str, str]]:
    """Actionable gaps for thin listings (grade C/D) — unique vs Idealista/Immobiliare."""
    tips: List[Dict[str, str]] = []
    for c in completeness.get("checks") or []:
        if c.get("points", 0) >= c.get("max", 0):
            continue
        key = c.get("key")
        if key == "foto":
            tips.append({
                "key": "foto",
                "label_it": "Aggiungi almeno 8–10 foto (ogni stanza + esterni + dettagli).",
            })
        elif key == "descrizione":
            tips.append({
                "key": "descrizione",
                "label_it": "Allunga la descrizione: stato, impianti, esposizione, spese, contesto.",
            })
        elif key == "ape":
            tips.append({"key": "ape", "label_it": "Carica la classe energetica APE — obbligatoria in vendita."})
        elif key == "planimetria":
            tips.append({"key": "planimetria", "label_it": "Allega la planimetria: riduce richieste inutili e aumenta fiducia."})
        elif key == "geolocalizzazione":
            tips.append({"key": "geo", "label_it": "Imposta la posizione sulla mappa per comparire nelle ricerche locali."})
        elif key == "indirizzo":
            tips.append({"key": "indirizzo", "label_it": "Indica indirizzo e piano (anche zona se preferisci riservatezza)."})
        elif key == "superficie":
            tips.append({"key": "superficie", "label_it": "Inserisci i mq commerciali/calpestabili."})
        elif key == "locali":
            tips.append({"key": "locali", "label_it": "Specifica locali e camere da letto."})
        elif key == "prezzo":
            tips.append({"key": "prezzo", "label_it": "Pubblica un prezzo chiaro: gli annunci senza cifra filtrano male."})
        elif key == "visibilità":
            tips.append({
                "key": "boost",
                "label_it": "Con Vetrina / Premium / TOP sali in cima alle ricerche (pagamento carta).",
            })
    return tips[:6]


def visit_checklist(p: Dict[str, Any]) -> List[Dict[str, str]]:
    """Thin in-visit checks — same Scout panel, not a new product."""
    items: List[Dict[str, str]] = [
        {
            "key": "photo_vs_reality",
            "label_it": "Confronta ogni stanza con le foto: finiture, luce, eventuali difetti nascosti.",
        },
        {
            "key": "moisture",
            "label_it": "Controlla umidità, muffa, odori di chiuso — angoli, sottotetto, cantina se c’è.",
        },
        {
            "key": "systems",
            "label_it": "Prova acqua calda, termosifoni/condizionamento, prese e citofono.",
        },
        {
            "key": "noise_light",
            "label_it": "Ascolta rumori (strada, vicini, ascensore) e valuta esposizione reale vs annuncio.",
        },
        {
            "key": "commons",
            "label_it": "Guarda le parti comuni: scale, androne, tetto/lastrico se accessibili.",
        },
    ]
    energy = None
    if isinstance(p.get("energy"), dict):
        energy = p["energy"].get("energy_class")
    else:
        energy = p.get("energy_class")
    if energy in ("E", "F", "G") or not energy:
        items.append({
            "key": "energy_reality",
            "label_it": "Chiedi spese di riscaldamento reali e eventuali lavori di efficientamento già deliberati.",
        })
    if p.get("floor") is not None or p.get("elevator") is False:
        items.append({
            "key": "access",
            "label_it": "Verifica piano, ascensore e accessibilità (anche per trasloco).",
        })
    if (p.get("operation") or "sale") == "rent":
        items.append({
            "key": "rent_condition",
            "label_it": "Annota stato di consegna e cosa è incluso (arredi, box, cantina).",
        })
    else:
        items.append({
            "key": "inclusions",
            "label_it": "Chiarisci cosa resta in vendita (cucina, armadi, box, cantina, posto auto).",
        })
        items.append({
            "key": "sqm_feel",
            "label_it": "I mq “si sentono”? Confronta planimetria (se ce l’hai) con gli spazi reali.",
        })
    # Dedupe by key, cap 10
    out: List[Dict[str, str]] = []
    seen = set()
    for it in items:
        if it["key"] in seen:
            continue
        seen.add(it["key"])
        out.append(it)
    return out[:10]


def documents_before_offer(p: Dict[str, Any]) -> List[Dict[str, str]]:
    """Thin doc list before offer — points to what to ask, not a vault."""
    sale = (p.get("operation") or "sale") != "rent"
    docs: List[Dict[str, str]] = [
        {
            "key": "ape",
            "label_it": "APE aggiornato (classe e data del certificato).",
            "why_it": "Obbligatorio in vendita; utile anche in affitto per costi reali.",
        },
        {
            "key": "planimetria",
            "label_it": "Planimetria catastale coerente con lo stato di fatto.",
            "why_it": "Scostamenti = rischi in atto o sanatorie.",
        },
    ]
    if sale:
        docs.extend([
            {
                "key": "visura",
                "label_it": "Visura catastale aggiornata.",
                "why_it": "Intestatari, categoria, consistenza — prima di impegnarti.",
            },
            {
                "key": "provenienza",
                "label_it": "Atto di provenienza / titolo di proprietà.",
                "why_it": "Capisci chi vende e se ci sono quote o comunioni.",
            },
            {
                "key": "ipoteche",
                "label_it": "Esistenza di ipoteche, pignoramenti o diritti di terzi.",
                "why_it": "Vanno estinti o gestiti prima del rogito.",
            },
            {
                "key": "spese",
                "label_it": "Spese condominiali e ultime delibere (lavori, fondi).",
                "why_it": "Costi futuri che non vedi nel prezzo chiesto.",
            },
        ])
    else:
        docs.extend([
            {
                "key": "contratto",
                "label_it": "Bozza di contratto e regolamento condominiale.",
                "why_it": "Cauzione, recesso, divieti (animali, subaffitto).",
            },
            {
                "key": "spese_rent",
                "label_it": "Spese accessorie mensili e cosa è incluso nel canone.",
                "why_it": "Il canone non è tutto il costo.",
            },
            {
                "key": "idoneita",
                "label_it": "Documenti richiesti al conduttore (reddito, garanzia).",
                "why_it": "Evita sorprese a verbale.",
            },
        ])
    return docs[:6]


def deterministic_insight(p: Dict[str, Any], vs_zone: Dict[str, Any], score: int) -> str:
    """Fallback one-liner when LLM is off — still useful on poor listings."""
    city = p.get("city") or "questa zona"
    if score < 40:
        return (
            f"Annuncio molto incompleto su {city}: poche prove documentali. "
            "Usa le domande Scout prima di fissare una visita."
        )
    if score < 60:
        return (
            f"Dati parziali su {city}. Completa le lacune (APE, foto, planimetria) "
            "prima di fidarti del prezzo richiesto."
        )
    if vs_zone.get("available") and vs_zone.get("signal") == "sopra_mercato":
        return f"Completezza ok, ma il chiesto è sopra la fascia stimata a {city}: chiedi margine o motivazione."
    if vs_zone.get("available") and vs_zone.get("signal") == "sotto_mercato":
        return f"Chiesto sotto la fascia stimata a {city}: verifica motivazione e documentazione prima di accelerare."
    return f"Annuncio solido su {city}: usa Scout per le domande mirate in visita."


async def _count_nearby_sale(db, p: Dict[str, Any]) -> Optional[int]:
    """Soft ‘comparabili’ count: other public sales in same city (not street-level comps)."""
    city = (p.get("city") or "").strip()
    if not city or (p.get("operation") or "sale") == "rent":
        return None
    try:
        n = await db.properties.count_documents({
            "status": "active",
            "visibility": "public",
            "is_listed_on_immobilcloud": {"$ne": False},
            "moderation_status": {"$nin": ["pending", "rejected"]},
            "operation": "sale",
            "city": {"$regex": f"^{re.escape(city)}$", "$options": "i"},
            "id": {"$ne": p.get("id")},
            "price": {"$gt": 0},
            "surface_sqm": {"$gt": 0},
        })
        return int(n)
    except Exception as e:
        logger.info("scout nearby count skip: %s", e)
        return None


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
                system="Sei Scout di ImmobilCloud. Solo fatti utili all'acquirente, senza promettere verità di mercato.",
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
    vs = price_vs_zone(p, completeness_score_val=comp["score"])
    gaps = seller_gaps(comp)  # always: buyers see lacune; sellers get actionable tips
    return {
        "product": "scout_hal",
        "listing_id": p.get("id"),
        "completeness": comp,
        "price_vs_zone": vs,
        "red_flags": red_flags(p, vs, comp),
        "questions_for_seller": seller_questions(p, comp),
        "seller_gaps": gaps,
        "visit_checklist": visit_checklist(p),
        "documents_before_offer": documents_before_offer(p),
        "next_steps": next_steps(p),
        "insight": insight or deterministic_insight(p, vs, comp["score"]),
        "disclaimer_it": (
            "Scout legge i dati dell'annuncio e i prezzi di zona ImmobilCloud. "
            "È un aiuto pre-visita, non una perizia né un parere legale."
        ),
    }


@router.post("/property/{pid}/scout")
async def scout_listing(pid: str, request: Request, payload: ScoutRequest = ScoutRequest()):
    """Generate Scout buyer brief for a public listing."""
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

    comp = completeness_score(p)
    vs = price_vs_zone(p, completeness_score_val=comp["score"])
    nearby = await _count_nearby_sale(db, p)
    if vs.get("available") and nearby is not None and vs.get("confidence"):
        vs["confidence"]["comparables_n"] = nearby
        if nearby >= 8:
            # mild bump when we have peer listings in-city (still not street comps)
            vs["confidence"]["limits_it"] = list(vs["confidence"].get("limits_it") or [])
            vs["confidence"]["limits_it"].insert(
                0,
                f"Ci sono {nearby} altri annunci in vendita a {p.get('city')} su ImmobilCloud — utili come contesto, non come perizia.",
            )
            vs["confidence"]["limits_it"] = vs["confidence"]["limits_it"][:4]

    insight = await _llm_one_liner(p, vs, comp["score"])
    brief = build_brief(p, insight=insight)
    # Prefer the enriched vs (with comparables_n) over the rebuild inside build_brief
    brief["price_vs_zone"] = vs
    brief["red_flags"] = red_flags(p, vs, comp)
    brief["lang"] = (payload.lang or "it")[:2]
    return brief
