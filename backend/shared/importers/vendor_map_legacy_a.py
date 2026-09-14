"""OMNIA — Legacy XML vendor map (schema "A" — cod_tipologia + rif fields).

Handles a specific dialect used by one of the mainstream Italian real-estate
CRMs (kept anonymous per D-051 — no brand mentions in code, log or UI).
Maps their numeric type codes, energy class codes, floor codes to the OMNIA
Property model. Detection is heuristic (see `detect_and_parse`).

⚠️ D-051 compliance: this file must NEVER refer to the vendor by name in
comments, log lines, exceptions or exported symbols. Public labels always
say "il tuo attuale fornitore".
"""
from typing import Optional
from uuid import uuid4
from xml.etree import ElementTree as ET

from shared.models.property import (
    PropertyInDB, PropertyFeatures, PropertyEnergy, PropertyOwner,
)


# Vendor A "cod_tipologia" (1-51) → OMNIA property_type (16 types)
TIPOLOGIA_MAP = {
    "1": "altro",         # Qualsiasi
    "2": "altro",         # Albergo
    "3": "appartamento",  # Appartamento
    "4": "negozio",       # Attività commerciale
    "5": "altro",         # Azienda agricola
    "6": "rustico_casale",  # Baita
    "7": "villa",         # Casa singola
    "8": "capannone",     # Capannone industriale
    "9": "palazzo_stabile",  # Castello
    "10": "villa",        # Villa
    "11": "attico",       # Mansarda
    "12": "rustico_casale",  # Rustico casale
    "13": "ufficio",      # Ufficio
    "14": "negozio",      # Negozio
    "15": "terreno_edificabile",  # Terreno
    "16": "garage_box",   # Garage
    "17": "palazzo_stabile",  # Stabile
    "18": "rustico_casale",  # Agriturismo
    "19": "negozio",      # Locale commerciale
    "20": "magazzino",    # Laboratorio
    "21": "magazzino",    # Magazzino
    "22": "rustico_casale",  # Colonica
    "23": "palazzo_stabile",  # Palazzo
    "24": "villetta_a_schiera",  # Terratetto
    "25": "altro",        # Hotel
    "26": "negozio",      # Bar
    "27": "negozio",      # Ristorante
    "28": "negozio",      # Forno
    "29": "villa",        # Villino
    "30": "appartamento", # Appartamento indipendente
    "31": "attico",       # Attico
    "32": "villetta_a_schiera",  # Villa a schiera
    "33": "villa",        # Bifamiliare
    "34": "villetta_a_schiera",  # Casa semi indipendente
    "35": "altro",        # Multiproprietà
    "36": "altro",        # Residence
    "38": "rustico_casale",  # Trulli
    "40": "rustico_casale",  # Masseria
    "41": "negozio",      # Pizzeria
    "42": "palazzo_stabile",  # Tenuta-Complesso
    "43": "rustico_casale",  # Annesso agricolo
    "44": "terreno_edificabile",  # Terreno edificabile
    "45": "terreno_edificabile",  # Terreno industriale
    "46": "terreno_agricolo",  # Terreno agricolo
    "47": "monolocale",   # Stanza/camera
    "48": "loft",         # Loft
    "49": "appartamento", # Nuova costruzione
    "50": "altro",        # Posto barca
    "51": "altro",        # Stabilimento balneare
}

# Vendor A contratto → OMNIA operation
CONTRATTO_MAP = {
    "V": "sale", "v": "sale",
    "A": "rent", "a": "rent",
    "S": "rent",  # Seasonal/vacation → treat as rent
    "s": "rent",
}

# Vendor A classe_energetica codes
# DL 192/2005:  0=G, 1=A+, 2=A, 3=B..8=G
# DL 90/2013:  10=A4, 11=A3, 12=A2, 13=A1, 14=B..19=G
ENERGY_MAP = {
    "-1": None, "9": "exempt",
    "0": "G", "1": "A", "2": "A", "3": "B", "4": "C", "5": "D", "6": "E", "7": "F", "8": "G",
    "10": "A4", "11": "A3", "12": "A2", "13": "A1", "14": "B",
    "15": "C", "16": "D", "17": "E", "18": "F", "19": "G",
}

# Vendor A cod_condizioni → OMNIA condition
COND_MAP = {
    "NC": "nuovo", "OT": "ottime", "AB": "buone",
    "RI": "ristrutturato", "DR": "da_ristrutturare", "SM": "ottime",
}

# Vendor A cod_riscaldamento → OMNIA heating
HEAT_MAP = {"AU": "autonomo", "CN": "centralizzato", "IN": "assente"}


def _t(elem, tag):
    """Safe text getter."""
    node = elem.find(tag)
    return node.text.strip() if (node is not None and node.text) else None


def _to_float(v):
    if v in (None, "", "0"):
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def _to_int(v):
    f = _to_float(v)
    return int(f) if f is not None else None


def _to_bool(v):
    return str(v).strip() in ("1", "true", "True", "si", "sì", "yes")


def parse_vendor_a_item(elem: ET.Element, agency_id: str, user_id: str) -> tuple[Optional[PropertyInDB], Optional[str]]:
    """Convert a single Vendor A <immobile> (or root child) into a Property."""
    try:
        cod_tipologia = _t(elem, "cod_tipologia") or ""
        property_type = TIPOLOGIA_MAP.get(cod_tipologia, "appartamento")

        contratto = _t(elem, "contratto") or "V"
        operation = CONTRATTO_MAP.get(contratto, "sale")

        title = _t(elem, "titolo") or _t(elem, "rif") or "Immobile"
        # If title is too short (e.g. placeholder like "01", "w1"), build one from data
        if len(title.strip()) < 3:
            tipo_label = _t(elem, "tipologia") or "Immobile"
            city = _t(elem, "comune") or ""
            ref = _t(elem, "rif") or ""
            built = f"{tipo_label} {city}".strip()
            if ref:
                built = f"{built} ({ref})".strip()
            title = built if len(built) >= 3 else f"Immobile rif. {ref or 'sconosciuto'}"
        city = _t(elem, "comune") or _t(elem, "localita") or "Sconosciuto"

        # Build features from boolean fields
        features = PropertyFeatures(
            balcone=_to_bool(_t(elem, "balcone")),
            terrazza=_to_bool(_t(elem, "terrazza")),
            giardino=_to_bool(_t(elem, "giardino")),
            ascensore=_to_bool(_t(elem, "ascensore")),
            aria_condizionata=_to_bool(_t(elem, "condizionatore")),
            posto_auto=_to_bool(_t(elem, "postoauto")),
            box_auto=_to_bool(_t(elem, "garage")),
            arredato=_to_bool(_t(elem, "arredato")),
        )

        energy_code = _t(elem, "classe_energetica")
        energy_class = ENERGY_MAP.get(energy_code) if energy_code else None
        epi = _to_float(_t(elem, "epi"))

        heat = HEAT_MAP.get(_t(elem, "cod_riscaldamento") or "")

        cond_code = _t(elem, "cod_condizioni") or ""
        condition = COND_MAP.get(cond_code)

        # Photos (up to 15)
        photos = []
        for i in range(1, 16):
            url = _t(elem, f"url{i}")
            if url:
                photos.append({
                    "id": str(uuid4()),
                    "url": url,
                    "caption": _t(elem, f"titolo{i}"),
                    "order": i - 1,
                    "is_cover": i == 1,
                })

        # Address
        indirizzo = _t(elem, "indirizzo") or ""
        civico = _t(elem, "civico") or ""
        full_address = (f"{indirizzo} {civico}").strip() or None

        # Floor mapping (Vendor A uses numeric codes incl. negatives)
        piano_raw = _t(elem, "piano")
        floor = _to_int(piano_raw) if piano_raw and piano_raw not in ("-3",) else None

        prop = PropertyInDB(
            agency_id=agency_id,
            listing_agent_id=user_id,
            title=title[:200],
            description=_t(elem, "testo"),
            reference_code=_t(elem, "rif"),
            property_type=property_type,
            operation=operation,
            status="active" if _to_bool(_t(elem, "sitoweb")) else "draft",
            condition=condition,
            address=full_address,
            city=city,
            province=_t(elem, "sigla_provincia"),
            zone=_t(elem, "cod_zona_comune") or None,
            lat=_to_float(_t(elem, "latitudine")),
            lng=_to_float(_t(elem, "longitudine")),
            hide_address=not _to_bool(_t(elem, "mappa_immobile_visibile")),
            price=_to_float(_t(elem, "prezzo")),
            price_negotiable=_to_bool(_t(elem, "trattativa_riservata")),
            surface_sqm=_to_float(_t(elem, "mq")),
            rooms=_to_int(_t(elem, "vani")),
            bedrooms=_to_int(_t(elem, "camere")),
            bathrooms=_to_int(_t(elem, "bagni")),
            floor=floor,
            total_floors=_to_int(_t(elem, "piani_totali")),
            features=features,
            energy=PropertyEnergy(
                energy_class=energy_class if energy_class != "exempt" else "exempt",
                energy_value=epi,
                heating=heat,
            ),
            photos=photos,
            owner=PropertyOwner(),  # Vendor A feed doesn't expose owner — safer
            is_exclusive=(_t(elem, "tipo_incarico") == "E"),
            visibility="public",
        )
        return prop, None
    except Exception as e:
        return None, f"errore parsing Vendor A: {e}"


def detect_and_parse(xml_text: str, agency_id: str, user_id: str):
    """Parse XML — detects if it's Vendor A format and uses the dedicated parser,
    else returns None to let the generic XML parser take over.

    Returns: (is_vendor_a, list_of_properties, list_of_errors)
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return False, [], [{"row": 0, "message": f"XML non valido: {e}"}]

    # Heuristic: Vendor A uses specific fields like "cod_tipologia", "rif", "id_agenzia"
    sample = root.find(".//cod_tipologia")
    is_vendor_a = sample is not None or root.find(".//id_agenzia") is not None

    if not is_vendor_a:
        return False, [], []

    # Find all property items
    candidates = (
        root.findall(".//immobile")
        or root.findall(".//annuncio")
        or root.findall(".//property")
        or [c for c in root if c.find("cod_tipologia") is not None or c.find("rif") is not None]
    )

    properties = []
    errors = []
    for i, elem in enumerate(candidates, start=1):
        prop, err = parse_vendor_a_item(elem, agency_id, user_id)
        if err:
            errors.append({"row": i, "message": err})
        elif prop:
            properties.append(prop)

    return True, properties, errors
