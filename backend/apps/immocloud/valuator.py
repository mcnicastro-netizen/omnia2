"""OMNIA — GIS Property Valuator (M3.S6).

Public, no-auth endpoint that estimates the market value of a residential
property in Italy based on:
  - City + zone tier (centro / semicentro / periferia)
  - Property type (appartamento, villa, attico, ...)
  - Surface in m²
  - Condition (nuovo, buono, da_ristrutturare, ...)
  - Energy class (optional)
  - Other adjustments (floor, elevator, lift impact — future)

Output: a range (min/avg/max) total value + €/m² + a confidence score +
methodology + data source + comparables count when available.

Algorithm overview (deterministic, auditable):

  1. Normalize city name → lookup table key (lowercase, ASCII, snake_case)
  2. Resolve zone tier: explicit user input OR heuristic from address keywords
     (centro storico, centro, semicentro, periferia, ...) OR default "semicentro"
  3. Read base €/m² (min, max) from CITY_PRICES; if missing, use regional default
     (REGION_TO_AREA → REGIONAL_DEFAULTS)
  4. Apply multipliers in order: property_type × condition × energy_class
  5. Multiply by surface to get total value range
  6. Compute confidence:
       - high  if city found AND zone explicit AND property_type known AND condition known
       - medium if city found but zone inferred or condition missing
       - low   if city not found (regional fallback) OR property_type unusual
  7. Optionally, query db.properties for comparables in same city + property_type
     to refine the estimate (price_per_sqm of recent active listings)

Endpoint:
  POST /api/cloud/valuator
"""
import logging
import re
import unicodedata
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_optional_user
from shared.db.connection import Database
from apps.billing.b2c_entitlements import (
    check_base_valuation_allowed,
    check_uni_entitlement,
    hash_valuation_payload,
    is_uni_payload,
    record_base_valuation,
)
from apps.immocloud.data.italy_real_estate_prices_2025 import (
    CITY_PRICES,
    REGION_TO_AREA,
    REGIONAL_DEFAULTS,
    PROPERTY_TYPE_MULTIPLIER,
    CONDITION_MULTIPLIER,
    ENERGY_CLASS_MULTIPLIER,
)
from apps.immocloud.data.province_prices import PROVINCE_PRICES, PROVINCE_NAMES
from apps.immocloud.data.coefficients import (
    compute_commercial_surface,
    compute_merit_adjustment,
    compute_regional_adjustment,
    foi_revaluation,
)
import httpx

logger = logging.getLogger("omnia.valuator")
router = APIRouter(prefix="/valuator", tags=["cloud-valuator"])

ZoneTier = Literal["centro", "semicentro", "periferia"]


# ----------- Normalization helpers ------------

def _normalize_city(name: str) -> str:
    """Lowercase, strip accents, replace spaces/special with underscores."""
    if not name:
        return ""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    n = n.lower().strip()
    n = re.sub(r"[\s\-'`]+", "_", n)
    n = re.sub(r"[^a-z0-9_]", "", n)
    return n


# Common synonyms / mis-spellings → canonical key
CITY_SYNONYMS = {
    "milan": "milano",
    "rome": "roma",
    "florence": "firenze",
    "naples": "napoli",
    "venice": "venezia",
    "turin": "torino",
    "genoa": "genova",
    "padua": "padova",
    "forli_cesena": "forli",
    "forlì": "forli",
    "lecco_città": "lecco",
    "monza_brianza": "monza",
    "monza_e_brianza": "monza",
    "carrara": "massa",
    "barletta_andria_trani": "barletta",
    "reggio_di_calabria": "reggio_calabria",
    "reggio_nell_emilia": "reggio_emilia",
    "la_spezia_città": "la_spezia",
    "l_aquila_città": "l_aquila",
    "laquila": "l_aquila",
    "aquila": "l_aquila",
}


def _resolve_city_key(city_raw: str) -> Optional[str]:
    key = _normalize_city(city_raw)
    if not key:
        return None
    if key in CITY_PRICES:
        return key
    if key in CITY_SYNONYMS:
        return CITY_SYNONYMS[key]
    # Try partial match (e.g., "milano_2" → "milano")
    for canonical in CITY_PRICES:
        if key.startswith(canonical + "_") or canonical.startswith(key + "_"):
            return canonical
    return None


# Heuristic zone tier inference from free-text address/zone
ZONE_TIER_KEYWORDS = {
    "centro": [
        "centro storico", "centro", "centrale", "duomo", "navigli",
        "trastevere", "spagna", "campo de fiori", "chiaia", "vomero",
        "santo stefano", "centro città",
    ],
    "semicentro": [
        "semicentro", "semicentrale", "porta", "stazione",
        "fiera", "università", "city life", "isola", "porta romana",
        "porta venezia", "san paolo", "san donato",
    ],
    "periferia": [
        "periferia", "periferico", "ext", "fuori", "hinterland",
        "tor bella monaca", "scampia", "secondigliano", "quarto",
        "metropolitano", "borgata",
    ],
}


def _infer_zone_tier(zone_text: Optional[str], address: Optional[str]) -> Tuple[ZoneTier, bool]:
    """Return (tier, explicit_user_input). If we can't infer, default 'semicentro'."""
    if zone_text:
        z = zone_text.lower().strip()
        if z in ("centro", "semicentro", "periferia"):
            return z, True
    haystack = " ".join(filter(None, [zone_text, address])).lower()
    for tier, keywords in ZONE_TIER_KEYWORDS.items():
        for kw in keywords:
            if kw in haystack:
                return tier, False  # inferred — not explicit
    return "semicentro", False


# ----------- Core valuation function ------------

# Nominatim helper for province lookup of unknown comuni
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_TIMEOUT = 5.0
_NOMINATIM_HEADERS = {"User-Agent": "OMNIA-Valuator/1.0 (mcnicastro@gmail.com)"}


async def _lookup_province_via_nominatim(city: str) -> Optional[str]:
    """Return a 2-letter province sigla (es. 'MI') for the given city.

    Tries ANNCSU first (ISTAT-authoritative), Nominatim OSM as fallback.
    Returns None on any failure — caller falls back to the regional default.
    """
    # 1. ANNCSU (ISTAT) primary
    try:
        from apps.immocloud.anncsu import _try_anncsu
        anncsu_result = await _try_anncsu(city)
        if anncsu_result and anncsu_result.get("provincia_sigla") in PROVINCE_PRICES:
            return anncsu_result["provincia_sigla"]
    except Exception:
        pass

    # 2. Nominatim OSM fallback
    try:
        async with httpx.AsyncClient(timeout=_NOMINATIM_TIMEOUT) as client:
            r = await client.get(
                _NOMINATIM_URL,
                params={
                    "q": f"{city}, Italia",
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                    "countrycodes": "it",
                },
                headers=_NOMINATIM_HEADERS,
            )
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        addr = data[0].get("address", {}) or {}
        # ISO3166-2 returns IT-MI, IT-RM, ecc.
        iso = addr.get("ISO3166-2-lvl6") or addr.get("ISO3166-2-lvl4") or ""
        if isinstance(iso, str) and iso.startswith("IT-") and len(iso) >= 5:
            sigla = iso.split("-")[-1].upper()
            if sigla in PROVINCE_PRICES:
                return sigla
        # Fallback: county field sometimes contains "Provincia di Milano" / "Milano"
        county = (addr.get("county") or "").lower()
        for sigla, name in PROVINCE_NAMES.items():
            if name.lower() in county:
                return sigla
    except Exception:
        return None
    return None


class CommercialSurfaces(BaseModel):
    """Componenti di superficie ponderata UNI 10750 (opzionali, default 0)."""
    principale_mq: Optional[float] = Field(default=None, ge=0, le=10000)
    veranda_mq: Optional[float] = Field(default=0, ge=0, le=500)
    terrazzo_mq: Optional[float] = Field(default=0, ge=0, le=2000)
    balcone_mq: Optional[float] = Field(default=0, ge=0, le=500)
    cantina_mq: Optional[float] = Field(default=0, ge=0, le=200)
    soffitta_mq: Optional[float] = Field(default=0, ge=0, le=200)
    box_auto_mq: Optional[float] = Field(default=0, ge=0, le=200)
    posto_auto_scoperto_mq: Optional[float] = Field(default=0, ge=0, le=100)
    giardino_villa_mq: Optional[float] = Field(default=0, ge=0, le=20000)
    giardino_condom_mq: Optional[float] = Field(default=0, ge=0, le=2000)
    taverna_mq: Optional[float] = Field(default=0, ge=0, le=300)
    mansarda_abitabile_mq: Optional[float] = Field(default=0, ge=0, le=300)


class MeritFactors(BaseModel):
    """Coefficienti di merito UNI 10750 (tutti opzionali)."""
    floor_class: Optional[str] = None     # seminterrato | piano_terra | piano_1 | piano_intermedio | ultimo_no_asc | ultimo_con_asc | attico_panoramico
    exposure: Optional[str] = None        # sud | sud_est | sud_ovest | est | ovest | nord_est | nord_ovest | nord | cieca | doppia_esp
    view: Optional[str] = None            # interno | cortile | strada | verde | panoramico | mare | lago_montagna
    heating: Optional[str] = None         # autonomo | centralizzato | pompa_calore | assente
    elevator: Optional[str] = None        # presente | presente_piano_alto | assente_piano_basso | assente_piano_alto
    year_built: Optional[int] = Field(default=None, ge=1700, le=2030)
    vincolo_storico: Optional[bool] = False
    vincolo_paesag: Optional[bool] = False
    locazione_libera_breve: Optional[bool] = False
    locazione_lunga: Optional[bool] = False
    nuda_proprieta: Optional[bool] = False


class ValuationPayload(BaseModel):
    city: str = Field(min_length=2, max_length=100)
    zone: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=300)
    property_type: str = Field(default="appartamento", max_length=50)
    surface_sqm: int = Field(ge=10, le=10000)   # superficie calpestabile principale
    condition: Optional[str] = Field(default="buono", max_length=50)
    energy_class: Optional[str] = Field(default=None, pattern="^(A4|A3|A2|A1|A|B|C|D|E|F|G)?$")
    floor: Optional[int] = Field(default=None, ge=-2, le=80)

    # NEW M3.S6-pro: superficie commerciale UNI 10750 (se passata, sovrascrive surface_sqm)
    commercial_surfaces: Optional[CommercialSurfaces] = None
    # NEW M3.S6-pro: coefficienti di merito
    merit: Optional[MeritFactors] = None

    # Lead capture
    email: Optional[str] = Field(default=None, max_length=200)
    name: Optional[str] = Field(default=None, max_length=200)


@router.post("")
async def estimate_value(
    payload: ValuationPayload,
    request: Request = None,
    user: Optional[dict] = Depends(get_optional_user),
    bypass_gate: bool = False,
) -> Dict[str, Any]:
    """Estimate the market value range for a residential property.

    Pipeline (M3.S6-pro):
      1. Resolve città → prezzo base (CITY_PRICES → PROVINCE_PRICES via Nominatim → regional fallback)
      2. Risolvi zone tier (centro/semicentro/periferia)
      3. Superficie commerciale UNI 10750 (se commercial_surfaces è passato)
      4. Moltiplicatori: property_type · condition · energy_class · floor
      5. Coefficienti di merito (esposizione, vista, riscaldamento, ascensore, età, vincoli)
      6. Coefficienti regionali (liquidità + trend)
      7. FOI ISTAT (rivalutazione FOI cumulato a oggi)
      8. Comparables + lead capture

    B2C gate (Cap. 21 · task B2C-VAL-01):
    - Anonimo + base → 401
    - B2C senza email verificata → 403
    - B2C base, quota esaurita → 429
    - Payload UNI (commercial_surfaces o merit) senza pagamento → 402
    - Agente B2B → passa senza Stripe (crediti agenzia scalati altrove — TODO)
    - Fascicolo agenzia → bypass tramite `bypass_gate=True` (chiamata Python interna)
    - Header `X-Omnia-Caller: agency_fascicolo` bypass gate se agente
    """
    # Detect internal caller (fascicolo) via header o kwarg
    header_caller = ""
    if request is not None:
        header_caller = (request.headers.get("x-omnia-caller") or "").lower().strip()
    is_agency_fascicolo = bypass_gate or header_caller == "agency_fascicolo"

    uni_requested = is_uni_payload(payload)
    is_agent = bool(user and (user.get("agency_id") or user.get("agency_ids")))
    is_b2c = bool(user and not is_agent)

    if not is_agency_fascicolo:
        # --- Gate BASE (no commercial_surfaces / merit) ---
        if not uni_requested:
            if not user:
                raise HTTPException(status_code=401, detail={
                    "code": "login_required",
                    "message": "Accedi per la stima gratuita",
                })
            if is_b2c and not user.get("email_verified"):
                raise HTTPException(status_code=403, detail={
                    "code": "email_verification_required",
                    "message": "Verifica l'email per usare la stima gratuita",
                })
            if is_b2c:
                allowed, reset_at = await check_base_valuation_allowed(user["id"])
                if not allowed:
                    raise HTTPException(status_code=429, detail={
                        "code": "base_limit_reached",
                        "message": "Hai gia' usato la stima gratuita di quest'anno",
                        "reset_at": reset_at,
                        "upsell_product_key": "b2c_valuator_uni_pdf",
                        "upsell_price_eur": 2.99,
                    })
            # agents: base senza gate (crediti B2B scalati dal caller applicativo, non qui)
        # --- Gate UNI (commercial_surfaces or merit present) ---
        else:
            if not user:
                raise HTTPException(status_code=401, detail={
                    "code": "login_required",
                    "message": "Accedi per la valutazione UNI 10750",
                })
            if is_b2c:
                payload_hash = hash_valuation_payload(payload.model_dump(exclude_none=True))
                has_ent = await check_uni_entitlement(user["id"], payload_hash)
                if not has_ent:
                    raise HTTPException(status_code=402, detail={
                        "code": "payment_required",
                        "message": "Valutazione UNI 10750 + PDF a €2,99",
                        "product_key": "b2c_valuator_uni_pdf",
                        "price_eur": 2.99,
                        "payload_hash": payload_hash,
                    })
            # agents: crediti B2B scalati dal caller applicativo (out-of-scope questo endpoint)

    result = await _estimate_value_core(payload)

    # Track base usage only for B2C base tier (no fascicolo, no agent, no UNI)
    if is_b2c and not uni_requested and not is_agency_fascicolo:
        try:
            await record_base_valuation(user["id"], result.get("valuation_id") or "-")
        except Exception as e:
            logger.warning("record_base_valuation failed: %s", e)

    return result


async def _estimate_value_core(payload: ValuationPayload) -> Dict[str, Any]:
    """Estimate the market value range for a residential property.

    Pipeline (M3.S6-pro):
      1. Resolve città → prezzo base (CITY_PRICES → PROVINCE_PRICES via Nominatim → regional fallback)
      2. Risolvi zone tier (centro/semicentro/periferia)
      3. Superficie commerciale UNI 10750 (se commercial_surfaces è passato)
      4. Moltiplicatori: property_type · condition · energy_class · floor
      5. Coefficienti di merito (esposizione, vista, riscaldamento, ascensore, età, vincoli)
      6. Coefficienti regionali (liquidità + trend)
      7. FOI ISTAT (rivalutazione FOI cumulato a oggi)
      8. Comparables + lead capture
    """
    city_key = _resolve_city_key(payload.city)
    city_data = CITY_PRICES.get(city_key) if city_key else None

    zone_tier, zone_explicit = _infer_zone_tier(payload.zone, payload.address)

    # 1. Base price resolution — 3 layer cascade
    fallback_source = None
    province_sigla = None
    if city_data:
        base_min, base_max = city_data[zone_tier]
        region = city_data.get("region")
        data_source = city_data.get("source", "Borsino/OMI 2025 curated city")
    else:
        # Layer 2: Nominatim geocoding → province lookup
        province_sigla = await _lookup_province_via_nominatim(payload.city)
        if province_sigla and province_sigla in PROVINCE_PRICES:
            prov = PROVINCE_PRICES[province_sigla]
            base_min, base_max = prov[zone_tier]
            region = prov.get("region")
            data_source = f"Province fallback ({PROVINCE_NAMES.get(province_sigla, province_sigla)}) via Nominatim geocoding"
            fallback_source = "province"
            # comune piccolo → discount 8-15% vs capoluogo
            small_town_discount = 0.88
            base_min = round(base_min * small_town_discount)
            base_max = round(base_max * small_town_discount)
        else:
            # Layer 3: regional default (worst case)
            region = None
            base_min, base_max = REGIONAL_DEFAULTS["center"]
            data_source = "Regional fallback (no city/province match)"
            fallback_source = "regional"

    # 2. Calcolo superficie commerciale ponderata UNI 10750
    if payload.commercial_surfaces:
        surf_dict = payload.commercial_surfaces.model_dump(exclude_none=True)
        # Se utente non passa principale_mq esplicito, usa surface_sqm come principale
        if not surf_dict.get("principale_mq"):
            surf_dict["principale_mq"] = float(payload.surface_sqm)
        commercial_mq, surface_breakdown = compute_commercial_surface(surf_dict)
    else:
        commercial_mq = float(payload.surface_sqm)
        surface_breakdown = {"principale_mq": float(payload.surface_sqm)}

    # 3. Base multipliers
    ptype_mult = PROPERTY_TYPE_MULTIPLIER.get(payload.property_type, 0.90)
    cond_mult = CONDITION_MULTIPLIER.get(payload.condition or "buono", 1.00)
    energy_mult = ENERGY_CLASS_MULTIPLIER.get(payload.energy_class, 1.00) if payload.energy_class else 1.00
    floor_mult = 1.00
    if payload.floor is not None:
        if payload.floor >= 5:
            floor_mult = 1.04
        elif payload.floor <= 0:
            floor_mult = 0.95
        elif payload.floor == 1:
            floor_mult = 0.98

    # 4. Coefficienti di merito UNI 10750
    if payload.merit:
        merit_dict = payload.merit.model_dump(exclude_none=True)
        merit_pct, merit_breakdown = compute_merit_adjustment(merit_dict)
    else:
        merit_pct, merit_breakdown = 0.0, {}

    # 5. Coefficienti regionali (liquidità + trend)
    regional_pct, regional_breakdown = compute_regional_adjustment(region, months_since_omi=6)

    # 6. Total combined multiplier
    base_mult = ptype_mult * cond_mult * energy_mult * floor_mult
    coefficient_mult = (1 + merit_pct) * (1 + regional_pct)
    total_mult = base_mult * coefficient_mult

    psm_min = round(base_min * total_mult)
    psm_max = round(base_max * total_mult)
    psm_avg = round((psm_min + psm_max) / 2)

    # 7. Final values use COMMERCIAL surface (not raw calpestabile)
    value_min = round(psm_min * commercial_mq)
    value_max = round(psm_max * commercial_mq)
    value_avg = round(psm_avg * commercial_mq)

    # Confidence scoring
    confidence_score = 0
    if city_data:
        confidence_score += 50
    elif province_sigla:
        confidence_score += 30
    if zone_explicit:
        confidence_score += 20
    if payload.property_type in PROPERTY_TYPE_MULTIPLIER:
        confidence_score += 10
    if payload.condition and payload.condition in CONDITION_MULTIPLIER:
        confidence_score += 10
    if payload.energy_class:
        confidence_score += 5
    if payload.address:
        confidence_score += 5
    if payload.commercial_surfaces:
        confidence_score += 5
    if payload.merit:
        confidence_score += 5

    if confidence_score >= 80:
        confidence = "high"
    elif confidence_score >= 55:
        confidence = "medium"
    else:
        confidence = "low"

    # Comparables (active listings in same city + property type)
    comparables = []
    comparable_count = 0
    if city_key:
        db = Database.get()
        try:
            cursor = db.properties.find({
                "status": "active",
                "visibility": "public",
                "moderation_status": {"$nin": ["pending", "rejected"]},
                "property_type": payload.property_type,
                "city": {"$regex": f"^{payload.city}", "$options": "i"},
                "price": {"$gt": 0},
                "surface_sqm": {"$gt": 0},
            }, {
                "_id": 0, "id": 1, "title": 1, "price": 1, "surface_sqm": 1,
                "rooms": 1, "city": 1, "zone": 1,
            }).limit(20)
            comps = await cursor.to_list(length=20)
            for c in comps:
                if c["surface_sqm"] > 0:
                    c["price_per_sqm"] = round(c["price"] / c["surface_sqm"])
                    comparables.append(c)
            comparable_count = len(comparables)
        except Exception as e:
            logger.warning("comparables query failed: %s", e)

    # Best-effort capture of a "valuation lead" when user provides email
    lead_id = None
    if payload.email and payload.name and city_key:
        try:
            from datetime import datetime, timezone
            from uuid import uuid4
            db = Database.get()
            now = datetime.now(timezone.utc).isoformat()
            lead_id = str(uuid4())
            await db.valuation_leads.insert_one({
                "id": lead_id,
                "name": payload.name,
                "email": payload.email.lower(),
                "city": payload.city,
                "zone": payload.zone,
                "address": payload.address,
                "property_type": payload.property_type,
                "surface_sqm": payload.surface_sqm,
                "condition": payload.condition,
                "energy_class": payload.energy_class,
                "estimated_value_min": value_min,
                "estimated_value_max": value_max,
                "estimated_value_avg": value_avg,
                "created_at": now,
                "source": "ImmobilCloud-Valuator",
            })
        except Exception as e:
            logger.warning("valuation lead capture failed: %s", e)
            lead_id = None

    return {
        "ok": True,
        "city_resolved": city_key,
        "city_in_dataset": city_data is not None,
        "province_sigla": province_sigla,
        "province_name": PROVINCE_NAMES.get(province_sigla) if province_sigla else None,
        "fallback_used": fallback_source,
        "region": region,
        "zone_tier": zone_tier,
        "zone_explicit": zone_explicit,
        "surface": {
            "calpestabile_mq": payload.surface_sqm,
            "commercial_mq": commercial_mq,
            "breakdown": surface_breakdown,
            "method": "UNI 10750 / DPR 138/1998" if payload.commercial_surfaces else "calpestabile_only",
        },
        "price_per_sqm": {
            "min": psm_min, "avg": psm_avg, "max": psm_max,
        },
        "estimated_value": {
            "min": value_min, "avg": value_avg, "max": value_max,
        },
        "currency": "EUR",
        "surface_sqm": payload.surface_sqm,  # kept for backwards-compat
        "multipliers_applied": {
            "property_type": ptype_mult,
            "condition": cond_mult,
            "energy_class": energy_mult,
            "floor": floor_mult,
            "merit_pct": round(merit_pct, 4),
            "regional_pct": round(regional_pct, 4),
            "total": round(total_mult, 4),
        },
        "merit_breakdown": merit_breakdown,
        "regional_breakdown": regional_breakdown,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "methodology": (
            "Pipeline professionale OMNIA: 1) prezzo base OMI/Borsino città o provincia (Nominatim), "
            "2) superficie commerciale UNI 10750 / DPR 138/1998 con ponderazione di balconi/terrazzi/cantine/box, "
            "3) moltiplicatori tipologia·condizione·classe energetica·piano, "
            "4) coefficienti di merito (esposizione, vista, riscaldamento, ascensore, età, vincoli), "
            "5) coefficienti regionali (liquidità + trend semestrale)."
        ),
        "data_source": data_source,
        "comparable_count": comparable_count,
        "comparables": comparables[:10],
        "valuation_lead_id": lead_id,
        "disclaimer": (
            "Stima orientativa basata su dati statistici di mercato e norme UNI 10750. "
            "Per una valutazione vincolante richiedi una perizia ufficiale a un agente OMNIA "
            "certificato o un perito iscritto all'Albo."
        ),
    }


@router.get("/coverage")
async def coverage_info():
    """Public info endpoint: how many cities + provinces are in the dataset."""
    return {
        "cities_covered": len(CITY_PRICES),
        "provinces_covered": len(PROVINCE_PRICES),
        "regions_covered": len(set(c.get("region") for c in CITY_PRICES.values() if c.get("region"))),
        "national_coverage": True,
        "fallback_chain": ["city_curated", "province_via_nominatim", "regional_default"],
        "zone_tiers": ["centro", "semicentro", "periferia"],
        "property_types": list(PROPERTY_TYPE_MULTIPLIER.keys()),
        "conditions": list(CONDITION_MULTIPLIER.keys()),
        "norms_applied": ["UNI 10750:1998", "DPR 138/1998"],
        "data_year": 2025,
    }
