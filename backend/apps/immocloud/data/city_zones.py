"""Quartieri / zone immobiliari per città — usato da Valutatore + autocomplete.

SoT UI: elenco quartieri per città.
SoT prezzo: mapping quartiere → fascia centro|semicentro|periferia (CITY_PRICES).
"""
from __future__ import annotations

from typing import Dict, List, Optional

# Chiave = città normalizzata (lowercase, senza accenti pesanti)
CITY_ZONES: Dict[str, List[str]] = {
    "catania": [
        "Centro storico",
        "Antico Corso",
        "Civita",
        "Fortino",
        "San Cristoforo",
        "Angeli Custodi",
        "Santa Maria di Gesù",
        "San Berillo",
        "Consolazione",
        "Cibali",
        "Barriera del Bosco",
        "Canalicchio",
        "Ognina",
        "Picanello",
        "Villaggio Dusmet",
        "Guardia",
        "Corso Italia",
        "Santa Sofia",
        "Tondo Gioeni",
        "San Nullo",
        "Monte Po",
        "Rapisardi",
        "Nesima",
        "San Giovanni Galermo",
        "Librino",
        "San Giorgio",
        "Zia Lisa",
        "Fontanarossa",
        "Bicocca",
        "Passo Martino",
        "Vaccarizzo",
        "San Giuseppe la Rena",
        "Plaja",
        "San Giovanni Li Cuti",
        "Faro Basso",
        "Rotolo",
        "Acquicella",
        "Pigno",
        "Trappeto",
        "Villaggio Sant'Agata",
        "Santa Maria Goretti",
    ],
    "milano": [
        "Centro storico",
        "Duomo",
        "Brera",
        "Navigli",
        "Porta Romana",
        "Porta Venezia",
        "Porta Genova",
        "Isola",
        "Città Studi",
        "Bicocca",
        "Garibaldi",
        "Corso Como",
        "Porta Nuova",
        "Sempione",
        "San Siro",
        "Loreto",
        "Crescenzago",
        "Lambrate",
        "Rogoredo",
        "Baggio",
        "Quarto Oggiaro",
        "Affori",
        "Niguarda",
        "Corvetto",
        "Vigentino",
    ],
    "roma": [
        "Centro storico",
        "Trastevere",
        "Prati",
        "Testaccio",
        "San Giovanni",
        "Esquilino",
        "Monti",
        "Flaminio",
        "Parioli",
        "Trieste",
        "Nomentano",
        "Tiburtina",
        "Ostiense",
        "EUR",
        "Marconi",
        "Garbatella",
        "Appio Latino",
        "Tuscolano",
        "Cinecittà",
        "Monteverde",
        "Aurelio",
        "Balduina",
        "Cassia",
        "Centocelle",
        "Torre Maura",
    ],
    "napoli": [
        "Centro storico",
        "Chiaia",
        "Vomero",
        "Posillipo",
        "Mergellina",
        "Fuorigrotta",
        "Arenella",
        "Avvocata",
        "Sanità",
        "Stella",
        "Materdei",
        "Pendino",
        "Mercato",
        "San Carlo all'Arena",
        "Vicaria",
        "Ponticardelli",
        "Secondigliano",
        "Scampia",
        "Pianura",
        "Soccavo",
        "Bagnoli",
        "San Giovanni a Teduccio",
        "Barra",
        "Ponticelli",
    ],
    "torino": [
        "Centro",
        "Crocetta",
        "San Salvario",
        "Vanchiglia",
        "Aurora",
        "Barriera di Milano",
        "San Donato",
        "Cit Turin",
        "Cenisia",
        "Santa Rita",
        "Mirafiori Nord",
        "Mirafiori Sud",
        "Lingotto",
        "Nizza Millefonti",
        "Borgo Po",
        "Cavoretto",
        "Madonna del Pilone",
        "Barca",
        "Falchera",
    ],
    "palermo": [
        "Centro storico",
        "Kalsa",
        "Vucciria",
        "Capo",
        "Albergheria",
        "Politeama",
        "Libertà",
        "Mondello",
        "Arenella",
        "Partanna",
        "Resuttana",
        "San Lorenzo",
        "Zisa",
        "Noce",
        "Oreto",
        "Brancaccio",
        "Cruillas",
        "Boccadifalco",
        "Sferracavallo",
    ],
}

# Mapping quartiere (lowercase) → fascia prezzo. Chiavi senza città: match su zona scelta.
ZONE_TIER_BY_NEIGHBORHOOD: Dict[str, str] = {
    # Catania — centro
    "centro storico": "centro",
    "centro": "centro",
    "antico corso": "centro",
    "civita": "centro",
    "fortino": "centro",
    "san cristoforo": "centro",
    "angeli custodi": "centro",
    "santa maria di gesu": "centro",
    "santa maria di gesù": "centro",
    "san berillo": "centro",
    "consolazione": "centro",
    # Catania — semicentro
    "cibali": "semicentro",
    "barriera del bosco": "semicentro",
    "barriera": "semicentro",
    "canalicchio": "semicentro",
    "ognina": "semicentro",
    "picanello": "semicentro",
    "villaggio dusmet": "semicentro",
    "guardia": "semicentro",
    "corso italia": "semicentro",
    "santa sofia": "semicentro",
    "tondo gioeni": "semicentro",
    "san nullo": "semicentro",
    "monte po": "semicentro",
    "rapisardi": "semicentro",
    "san giovanni li cuti": "semicentro",
    "acquicella": "semicentro",
    "rotolo": "semicentro",
    # Catania — periferia
    "nesima": "periferia",
    "san giovanni galermo": "periferia",
    "librino": "periferia",
    "san giorgio": "periferia",
    "zia lisa": "periferia",
    "fontanarossa": "periferia",
    "bicocca": "periferia",
    "passo martino": "periferia",
    "vaccarizzo": "periferia",
    "san giuseppe la rena": "periferia",
    "plaja": "periferia",
    "faro basso": "periferia",
    "pigno": "periferia",
    "trappeto": "periferia",
    "villaggio sant'agata": "periferia",
    "villaggio santagata": "periferia",
    "santa maria goretti": "periferia",
}


def _norm_key(name: str) -> str:
    import re
    import unicodedata

    if not name:
        return ""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    n = n.lower().strip()
    n = re.sub(r"[\s\-'`]+", " ", n)
    n = re.sub(r"[^a-z0-9 ]", "", n)
    return re.sub(r"\s+", " ", n).strip()


def zones_for_city(city: str) -> List[str]:
    key = _norm_key(city).replace(" ", "")
    # CITY_ZONES keys are simple city names without spaces
    for k, zones in CITY_ZONES.items():
        if _norm_key(k).replace(" ", "") == key:
            return list(zones)
    return []


def match_zone_label(city: str, candidate: str) -> Optional[str]:
    """Se il candidato OSM coincide con un quartiere noto, restituisci il label canonico."""
    import re

    if not candidate:
        return None
    zones = zones_for_city(city)
    if not zones:
        return None
    cand = _norm_key(candidate)
    for z in zones:
        if _norm_key(z) == cand:
            return z
    # Circoscrizioni composte OSM: "Picanello-Ognina-Barriera-Canalicchio" → primo quartiere noto
    for part in re.split(r"[-,/]", candidate):
        p = _norm_key(part)
        if not p:
            continue
        for z in zones:
            zn = _norm_key(z)
            if zn == p:
                return z
            # "Barriera" → "Barriera del Bosco"
            if zn.startswith(p + " ") or zn.endswith(" " + p):
                return z
    return None


def tier_for_zone(zone: Optional[str]) -> Optional[str]:
    if not zone:
        return None
    z = _norm_key(zone)
    if z in ("centro", "semicentro", "periferia"):
        return z
    if z in ZONE_TIER_BY_NEIGHBORHOOD:
        return ZONE_TIER_BY_NEIGHBORHOOD[z]
    # partial
    for k, tier in ZONE_TIER_BY_NEIGHBORHOOD.items():
        if k in z or z in k:
            return tier
    return None
