"""OMNIA — Universal XML Importer (M2.5.4a, D-050).

Generic XML feed parser that ingests real-estate listing feeds from a wide
range of legacy CRMs and normalizes them into the OMNIA `PropertyInDB` schema.

DESIGN:
    - Parser is schema-agnostic on the surface (accepts any <root><item>… structure)
    - Field-mapping table handles known dialects (numeric type/energy codes,
      multilingual text fields, photo repetition patterns) via best-effort
      heuristics — no vendor names in code paths.
    - Two-phase flow:
        1) POST /api/app/import/xml/preview  → uploads, parses, returns a
           dry-run report (no writes). Report contains: parsed count,
           divergences, mapping stats, sample of the first 5 properties as
           they will be stored.
        2) POST /api/app/import/xml/commit   → replays the preview and
           inserts into `properties` collection under the caller's agency.

Public API is intentionally generic ("il tuo attuale fornitore" — nessun
riferimento a competitor concreti nella UI o nei log).
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Field-mapping tables (heuristic dictionaries — extend as we ingest more feeds)
# =============================================================================

# Numeric property-type codes seen in legacy Italian feeds → OMNIA PropertyType
TYPE_CODE_MAP: Dict[str, str] = {
    "3": "appartamento",
    "10": "villa",
    "31": "attico",
    "32": "villetta_a_schiera",
    "33": "villa",  # bifamiliare → villa
    "34": "villetta_a_schiera",
    "4": "negozio",
    "20": "magazzino",
    "54": "negozio",  # bar → negozio commerciale
    "40": "ufficio",
    "60": "terreno_edificabile",
    "61": "terreno_agricolo",
    "70": "garage_box",
    "80": "capannone",
    "90": "palazzo_stabile",
    "11": "rustico_casale",
    "50": "loft",
    "51": "monolocale",
}

# Numeric energy-class codes → OMNIA EnergyClass literal
ENERGY_CODE_MAP: Dict[str, str] = {
    "1": "A", "2": "A", "3": "B", "4": "C", "5": "D",
    "6": "E", "7": "F", "8": "G",
    "10": "A4", "11": "A3", "12": "A2", "13": "A1",
    "14": "A", "15": "B", "16": "C", "17": "D",
    "18": "F", "19": "G",
    "99": "exempt",
}

# Category letters → informational only (residential/commercial/office)
CATEGORY_MAP: Dict[str, str] = {"R": "residenziale", "U": "ufficio", "C": "commerciale"}

# Contract letters → OMNIA PropertyOperation
OPERATION_CODE_MAP: Dict[str, str] = {
    "V": "sale",
    "A": "rent",
    "S": "rent",     # sfitto/stagionale → rent
    "R": "rent",
    "RB": "rent_to_buy",
    "ASTA": "auction",
}

# Condition heuristics
CONDITION_KEYWORDS: List[Tuple[str, str]] = [
    ("nuov", "nuovo"),
    ("ristruttura", "ristrutturato"),
    ("da_ristruttura", "da_ristrutturare"),
    ("ottim", "ottime"),
    ("buon", "buone"),
]

# Feature flag keyword → PropertyFeatures attribute
FEATURE_KEYWORDS: Dict[str, str] = {
    "balcon": "balcone",
    "terraz": "terrazza",
    "giardin": "giardino",
    "piscin": "piscina",
    "ascensor": "ascensore",
    "aria_cond": "aria_condizionata",
    "climatiz": "aria_condizionata",
    "cantin": "cantina",
    "soffit": "soffitta",
    "posto_auto": "posto_auto",
    "box": "box_auto",
    "portine": "portineria",
    "videocito": "videocitofono",
    "allarme": "allarme",
    "blindat": "porta_blindata",
    "cucin": "cucina_abitabile",
    "camin": "camino",
    "parquet": "parquet",
    "panoram": "vista_panoramica",
    "vista_mar": "vista_panoramica",
    "luminos": "luminoso",
    "arredat": "arredato",
    "solar": "pannelli_solari",
    "domotic": "impianto_domotico",
    "disabili": "accesso_disabili",
}


# =============================================================================
# Helpers
# =============================================================================

def _text(elem: Optional[ET.Element], tag: str) -> Optional[str]:
    """Case-insensitive tag text lookup with whitespace strip."""
    if elem is None:
        return None
    # exact
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip() or None
    # case-insensitive fallback
    lowered = tag.lower()
    for c in elem:
        if c.tag.lower() == lowered and c.text:
            return c.text.strip() or None
    return None


def _float(val: Optional[str]) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def _int(val: Optional[str]) -> Optional[int]:
    f = _float(val)
    if f is None:
        return None
    try:
        return int(f)
    except (ValueError, TypeError):
        return None


def _bool(val: Optional[str]) -> bool:
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in {"1", "true", "s", "si", "sì", "yes", "y", "on", "x"}


def _map_property_type(elem: ET.Element) -> str:
    """Try numeric code first, then text keyword, else default 'appartamento'."""
    code = _text(elem, "codice_tipologia") or _text(elem, "tipologia_codice") or _text(elem, "tipo_codice")
    if code and code.strip() in TYPE_CODE_MAP:
        return TYPE_CODE_MAP[code.strip()]
    label = (_text(elem, "tipologia") or _text(elem, "tipo") or "").lower()
    for keyword, ptype in [
        ("appartamento", "appartamento"), ("attico", "attico"),
        ("villa", "villa"), ("schiera", "villetta_a_schiera"),
        ("loft", "loft"), ("monolocale", "monolocale"),
        ("rustico", "rustico_casale"), ("casale", "rustico_casale"),
        ("ufficio", "ufficio"), ("negozio", "negozio"),
        ("magazzino", "magazzino"), ("capannone", "capannone"),
        ("box", "garage_box"), ("garage", "garage_box"),
        ("terreno agricol", "terreno_agricolo"),
        ("terreno", "terreno_edificabile"),
        ("palazzo", "palazzo_stabile"), ("stabile", "palazzo_stabile"),
    ]:
        if keyword in label:
            return ptype
    return "appartamento"


def _map_energy_class(elem: ET.Element) -> Optional[str]:
    code = _text(elem, "codice_classe_energetica") or _text(elem, "classe_energetica_codice")
    if code and code.strip() in ENERGY_CODE_MAP:
        return ENERGY_CODE_MAP[code.strip()]
    label = (_text(elem, "classe_energetica") or _text(elem, "classe") or "").upper().strip()
    if label in {"A4", "A3", "A2", "A1", "A", "B", "C", "D", "E", "F", "G"}:
        return label
    if label in {"ESENTE", "EXEMPT", "N/A"}:
        return "exempt"
    return None


def _map_operation(elem: ET.Element) -> str:
    code = (_text(elem, "codice_contratto") or _text(elem, "contratto") or "V").upper().strip()
    if code in OPERATION_CODE_MAP:
        return OPERATION_CODE_MAP[code]
    label = (_text(elem, "tipo_contratto") or "").lower()
    if "affitt" in label or "locazione" in label:
        return "rent"
    if "asta" in label:
        return "auction"
    if "rent" in label and "buy" in label:
        return "rent_to_buy"
    return "sale"


def _map_condition(elem: ET.Element) -> Optional[str]:
    label = (_text(elem, "stato") or _text(elem, "condizione") or _text(elem, "stato_immobile") or "").lower()
    for keyword, cond in CONDITION_KEYWORDS:
        if keyword in label:
            return cond
    return None


def _extract_features(elem: ET.Element) -> Dict[str, bool]:
    """Scan multiple hint fields for feature keywords."""
    features: Dict[str, bool] = {}
    haystack = " ".join(filter(None, [
        _text(elem, "descrizione"),
        _text(elem, "testo"),
        _text(elem, "caratteristiche"),
        _text(elem, "note"),
        _text(elem, "servizi"),
    ])).lower()

    # Explicit boolean sub-elements
    for tag in ["balcone", "terrazza", "giardino", "piscina", "ascensore",
                "cantina", "soffitta", "box", "posto_auto", "portineria",
                "videocitofono", "allarme", "camino", "parquet", "arredato",
                "pannelli_solari", "cancello_elettrico", "vista_mare",
                "prestigio"]:
        val = _text(elem, tag)
        if _bool(val):
            key = tag if tag != "box" else "box_auto"
            key = "vista_panoramica" if key == "vista_mare" else key
            features[key] = True

    # Keyword-based fallback on free text
    for keyword, key in FEATURE_KEYWORDS.items():
        if keyword in haystack:
            features[key] = True

    return features


def _extract_photos(elem: ET.Element) -> List[Dict[str, Any]]:
    """
    Photos in legacy feeds usually appear as repeated tags:
        <titolo1/>, <url1/>, <tipo1/>, <titolo2/>, <url2/>, <tipo2/>, …
    We iterate numerically until no more url<N> is found.
    """
    photos: List[Dict[str, Any]] = []
    i = 1
    consecutive_misses = 0
    while consecutive_misses < 3 and i < 100:
        url = _text(elem, f"url{i}") or _text(elem, f"foto{i}") or _text(elem, f"immagine{i}")
        if url:
            consecutive_misses = 0
            tipo = (_text(elem, f"tipo{i}") or "F").upper().strip()
            # Only include actual photos (F=Foto); skip P=Piantina (floor plan) into a separate field
            title = _text(elem, f"titolo{i}") or None
            if tipo in {"F", "FOTO", ""}:
                photos.append({
                    "id": str(uuid4()),
                    "url": url,
                    "caption": title,
                    "order": len(photos),
                    "is_cover": len(photos) == 0,
                })
        else:
            consecutive_misses += 1
        i += 1
    return photos


def _extract_floor_plan_url(elem: ET.Element) -> Optional[str]:
    """First photo tagged P (piantina) becomes floor_plan_url."""
    for i in range(1, 100):
        url = _text(elem, f"url{i}") or _text(elem, f"foto{i}")
        if not url:
            continue
        tipo = (_text(elem, f"tipo{i}") or "").upper().strip()
        if tipo == "P":
            return url
    return None


def _best_description(elem: ET.Element, preferred_lang: str = "it") -> Optional[str]:
    """
    Pick the description in the caller's preferred language when a multilingual
    schema is detected (testo_it/testo_eng/testo_ted/…). Falls back to plain
    'testo' or 'descrizione'.
    """
    lang_tags = {
        "it": ["testo_it", "testo", "descrizione", "note"],
        "en": ["testo_eng", "testo_en", "description"],
        "es": ["testo_spa", "testo_es", "descripcion"],
        "de": ["testo_ted", "testo_de"],
        "fr": ["testo_fra", "testo_fr"],
    }
    for tag in lang_tags.get(preferred_lang, lang_tags["it"]):
        v = _text(elem, tag)
        if v:
            return v[:9500]
    # Last resort: any testo_*
    for c in elem:
        if c.tag.lower().startswith("testo") and c.text:
            return c.text.strip()[:9500]
    return None


# =============================================================================
# Main mapper (per property)
# =============================================================================

def map_property(elem: ET.Element, agency_id: str, preferred_lang: str = "it") -> Dict[str, Any]:
    """Map one XML <immobile> (or generic <item>) element to a Property dict."""
    now_iso = datetime.now(timezone.utc).isoformat()

    price = _float(_text(elem, "prezzo")) or _float(_text(elem, "price"))
    rent = _float(_text(elem, "canone")) or _float(_text(elem, "rent"))
    operation = _map_operation(elem)

    # Prefer rent_monthly when operation=rent
    if operation == "rent" and price and not rent:
        rent, price = price, None

    features = _extract_features(elem)
    photos = _extract_photos(elem)
    floor_plan_url = _extract_floor_plan_url(elem)

    # Location
    city = (_text(elem, "citta") or _text(elem, "città") or _text(elem, "comune")
            or _text(elem, "location_city") or "").strip()
    if not city:
        city = "Città non specificata"

    return {
        "id": str(uuid4()),
        "agency_id": agency_id,
        "title": (_text(elem, "titolo") or _text(elem, "title")
                  or f"Immobile {_text(elem, 'riferimento') or elem.get('id') or ''}").strip()[:200],
        "description": _best_description(elem, preferred_lang),
        "reference_code": (_text(elem, "riferimento") or _text(elem, "codice_riferimento")
                           or _text(elem, "ref") or elem.get("id") or None),
        "property_type": _map_property_type(elem),
        "operation": operation,
        "status": "active",
        "condition": _map_condition(elem),
        "address": _text(elem, "indirizzo") or _text(elem, "address"),
        "city": city[:100],
        "province": (_text(elem, "provincia") or _text(elem, "province") or "")[:10] or None,
        "postal_code": (_text(elem, "cap") or _text(elem, "postal_code") or "")[:10] or None,
        "zone": (_text(elem, "zona") or _text(elem, "quartiere") or _text(elem, "zone") or "")[:100] or None,
        "country": (_text(elem, "nazione") or "IT")[:2].upper(),
        "lat": _float(_text(elem, "latitudine") or _text(elem, "lat")),
        "lng": _float(_text(elem, "longitudine") or _text(elem, "lng") or _text(elem, "lon")),
        "hide_address": not _bool(_text(elem, "mappa_visibile") or "1"),
        "price": price,
        "rent_monthly": rent,
        "condo_fees": _float(_text(elem, "spese_condominiali") or _text(elem, "spese")),
        "price_negotiable": _bool(_text(elem, "trattabile") or _text(elem, "prezzo_trattabile")),
        "surface_sqm": _float(_text(elem, "mq") or _text(elem, "superficie") or _text(elem, "surface")),
        "surface_useful_sqm": _float(_text(elem, "mq_calpestabili") or _text(elem, "superficie_utile")),
        "rooms": _int(_text(elem, "vani") or _text(elem, "locali") or _text(elem, "rooms")),
        "bedrooms": _int(_text(elem, "camere") or _text(elem, "camere_letto") or _text(elem, "bedrooms")),
        "bathrooms": _int(_text(elem, "bagni") or _text(elem, "bathrooms")),
        "floor": _int(_text(elem, "piano") or _text(elem, "floor")),
        "total_floors": _int(_text(elem, "piani_totali") or _text(elem, "n_piani")),
        "year_built": _int(_text(elem, "anno_costruzione") or _text(elem, "year_built")),
        "features": {
            "balcone": features.get("balcone", False),
            "terrazza": features.get("terrazza", False),
            "giardino": features.get("giardino", False),
            "piscina": features.get("piscina", False),
            "ascensore": features.get("ascensore", False),
            "aria_condizionata": features.get("aria_condizionata", False),
            "riscaldamento_autonomo": features.get("riscaldamento_autonomo", False),
            "cantina": features.get("cantina", False),
            "soffitta": features.get("soffitta", False),
            "posto_auto": features.get("posto_auto", False),
            "box_auto": features.get("box_auto", False),
            "portineria": features.get("portineria", False),
            "videocitofono": features.get("videocitofono", False),
            "allarme": features.get("allarme", False),
            "porta_blindata": features.get("porta_blindata", False),
            "cucina_abitabile": features.get("cucina_abitabile", False),
            "camino": features.get("camino", False),
            "parquet": features.get("parquet", False),
            "vista_panoramica": features.get("vista_panoramica", False),
            "luminoso": features.get("luminoso", False),
            "arredato": features.get("arredato", False),
            "pannelli_solari": features.get("pannelli_solari", False),
            "cancello_elettrico": features.get("cancello_elettrico", False),
            "impianto_domotico": features.get("impianto_domotico", False),
            "accesso_disabili": features.get("accesso_disabili", False),
        },
        "energy": {
            "energy_class": _map_energy_class(elem),
            "energy_value": _float(_text(elem, "epgl") or _text(elem, "prestazione_energetica")),
            "heating": None,
        },
        "photos": photos,
        "floor_plan_url": floor_plan_url,
        "virtual_tour_url": _text(elem, "virtual_tour") or _text(elem, "virtual_tour_url"),
        "is_exclusive": _bool(_text(elem, "tipo_incarico")) or (_text(elem, "tipo_incarico") == "E"),
        "visibility": "public",
        "is_listed_on_immobilcloud": True,
        "is_private_listing": False,
        "moderation_status": "approved",
        "view_count": 0,
        "lead_count": 0,
        "created_at": now_iso,
        "updated_at": now_iso,
        # Metadata (traceability)
        "_import_source": "universal_xml_importer_v1",
        "_import_reference": _text(elem, "riferimento") or elem.get("id"),
    }


# =============================================================================
# Public API
# =============================================================================

class ParseReport:
    """Structured report of a parse pass — used for the dry-run preview."""
    def __init__(self) -> None:
        self.total_found: int = 0
        self.parsed_ok: int = 0
        self.skipped: int = 0
        self.by_type: Dict[str, int] = {}
        self.by_operation: Dict[str, int] = {}
        self.by_city: Dict[str, int] = {}
        self.without_photos: int = 0
        self.without_price: int = 0
        self.divergences: List[str] = []
        self.samples: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_found": self.total_found,
            "parsed_ok": self.parsed_ok,
            "skipped": self.skipped,
            "by_type": self.by_type,
            "by_operation": self.by_operation,
            "by_city": self.by_city,
            "without_photos": self.without_photos,
            "without_price": self.without_price,
            "divergences": self.divergences[:50],  # cap
            "samples": self.samples[:5],
        }


def parse_xml_feed(
    xml_bytes: bytes,
    agency_id: str,
    preferred_lang: str = "it",
) -> Tuple[List[Dict[str, Any]], ParseReport]:
    """Parse a raw XML byte string into (property_dicts, report)."""
    report = ParseReport()
    properties: List[Dict[str, Any]] = []

    try:
        text = xml_bytes.decode("utf-8", errors="replace")
        # strip BOM if present
        if text.startswith("\ufeff"):
            text = text[1:]
        root = ET.fromstring(text)
    except ET.ParseError as e:
        report.divergences.append(f"xml_parse_error: {str(e)[:200]}")
        return properties, report

    # Accept any structure: iterate direct children of root and treat each as
    # a property record. Also accept the schema where root itself is one item.
    candidates: List[ET.Element] = list(root)
    if not candidates:
        candidates = [root]

    # Filter to elements that look like properties (have several expected tags)
    def looks_like_property(el: ET.Element) -> bool:
        indicators = ["prezzo", "canone", "mq", "citta", "città", "tipologia",
                      "codice_tipologia", "indirizzo", "titolo", "riferimento",
                      "surface", "city", "price"]
        found = 0
        for c in el:
            if c.tag.lower() in indicators or c.tag.lower().startswith("url"):
                found += 1
        return found >= 3

    property_elements = [el for el in candidates if looks_like_property(el)]

    report.total_found = len(property_elements)

    for el in property_elements:
        try:
            prop = map_property(el, agency_id, preferred_lang)
        except Exception as e:  # pragma: no cover
            logger.warning("map_property failed: %s", e)
            report.skipped += 1
            report.divergences.append(f"map_error ref={el.get('id')}: {str(e)[:100]}")
            continue

        # Guard: mandatory city + at least a title
        if not prop.get("city") or not prop.get("title"):
            report.skipped += 1
            report.divergences.append(f"missing_city_or_title ref={el.get('id')}")
            continue

        properties.append(prop)
        report.parsed_ok += 1
        report.by_type[prop["property_type"]] = report.by_type.get(prop["property_type"], 0) + 1
        report.by_operation[prop["operation"]] = report.by_operation.get(prop["operation"], 0) + 1
        report.by_city[prop["city"]] = report.by_city.get(prop["city"], 0) + 1
        if not prop["photos"]:
            report.without_photos += 1
        if not prop.get("price") and not prop.get("rent_monthly"):
            report.without_price += 1

    # Provide 5 samples
    report.samples = [
        {
            "reference_code": p.get("reference_code"),
            "title": p["title"],
            "city": p["city"],
            "property_type": p["property_type"],
            "operation": p["operation"],
            "price": p.get("price"),
            "rent_monthly": p.get("rent_monthly"),
            "surface_sqm": p.get("surface_sqm"),
            "photos_count": len(p.get("photos") or []),
        }
        for p in properties[:5]
    ]

    return properties, report
