"""OMNIA — Italian Real Estate Price Benchmarks (M3.S6).

Curated 2025 €/m² reference data for residential property valuation across
~120 Italian cities, with zone tiers (centro/semicentro/periferia) where
applicable. Sources cross-referenced from:
  - Borsino Immobiliare 2024-Q4 / 2025-Q1 (https://www.borsinoimmobiliare.it)
  - Tecnocasa annual report 2024
  - Idealista price reports IT
  - OMI Agenzia Entrate (last available semester)
  - Casa.it heatmaps

Values are mid-market for USED residential apartments in habitable condition.
Multipliers are applied for property type and condition (see valuator.py).

This is intentionally hard-coded (not a DB seed) so the algorithm has a stable,
auditable baseline. Future versions can layer real OMI data on top.
"""

# ---------------------------------------------------------------
# Default fallbacks if city not found (regional averages)
# ---------------------------------------------------------------
REGIONAL_DEFAULTS = {
    # macro-area: (min, max) €/m² (semicentro-equivalent)
    "north_west": (2200, 3200),
    "north_east": (2000, 3000),
    "center":     (1900, 2800),
    "south":      (1100, 1800),
    "islands":    (1000, 1600),
}

REGION_TO_AREA = {
    "lombardia": "north_west", "piemonte": "north_west", "liguria": "north_west", "valle_d_aosta": "north_west",
    "veneto": "north_east", "friuli_venezia_giulia": "north_east", "trentino_alto_adige": "north_east", "emilia_romagna": "north_east",
    "toscana": "center", "marche": "center", "umbria": "center", "lazio": "center", "abruzzo": "center",
    "molise": "south", "campania": "south", "puglia": "south", "basilicata": "south", "calabria": "south",
    "sicilia": "islands", "sardegna": "islands",
}

# ---------------------------------------------------------------
# City-level benchmarks (€/m² residential apartment, used, 2025)
# Format: city_normalized → {"centro": (min, max), "semicentro": (min, max), "periferia": (min, max), "region": str}
# Sources documented inline.
# ---------------------------------------------------------------
CITY_PRICES = {
    # ============ NORD ============
    "milano": {
        "centro": (9000, 13000), "semicentro": (5500, 7500), "periferia": (3500, 4800),
        "region": "lombardia", "source": "Borsino/OMI Milano 2025-Q1",
    },
    "monza": {
        "centro": (3200, 4500), "semicentro": (2400, 3200), "periferia": (1800, 2400),
        "region": "lombardia",
    },
    "bergamo": {
        "centro": (3500, 5000), "semicentro": (2400, 3300), "periferia": (1700, 2300),
        "region": "lombardia",
    },
    "brescia": {
        "centro": (2900, 4000), "semicentro": (2000, 2800), "periferia": (1400, 2000),
        "region": "lombardia",
    },
    "como": {
        "centro": (3500, 5200), "semicentro": (2400, 3400), "periferia": (1700, 2400),
        "region": "lombardia", "source": "premium lago",
    },
    "varese": {
        "centro": (2400, 3300), "semicentro": (1700, 2300), "periferia": (1200, 1700),
        "region": "lombardia",
    },
    "pavia": {
        "centro": (2200, 3000), "semicentro": (1600, 2100), "periferia": (1100, 1500),
        "region": "lombardia",
    },
    "cremona": {
        "centro": (1800, 2400), "semicentro": (1200, 1700), "periferia": (900, 1300),
        "region": "lombardia",
    },
    "mantova": {
        "centro": (2000, 2700), "semicentro": (1400, 1900), "periferia": (1000, 1400),
        "region": "lombardia",
    },
    "lecco": {
        "centro": (2400, 3200), "semicentro": (1700, 2300), "periferia": (1200, 1700),
        "region": "lombardia",
    },
    "lodi": {
        "centro": (2100, 2800), "semicentro": (1500, 2000), "periferia": (1100, 1500),
        "region": "lombardia",
    },
    "sondrio": {
        "centro": (1700, 2300), "semicentro": (1200, 1600), "periferia": (900, 1200),
        "region": "lombardia",
    },

    "torino": {
        "centro": (3200, 4500), "semicentro": (1900, 2700), "periferia": (1100, 1700),
        "region": "piemonte", "source": "OMI Torino 2025-S1",
    },
    "novara": {
        "centro": (1900, 2500), "semicentro": (1300, 1800), "periferia": (900, 1300),
        "region": "piemonte",
    },
    "alessandria": {
        "centro": (1300, 1800), "semicentro": (900, 1300), "periferia": (700, 1000),
        "region": "piemonte",
    },
    "asti": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (800, 1100),
        "region": "piemonte",
    },
    "cuneo": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (900, 1300),
        "region": "piemonte",
    },
    "biella": {
        "centro": (1200, 1700), "semicentro": (900, 1300), "periferia": (600, 900),
        "region": "piemonte",
    },
    "vercelli": {
        "centro": (1200, 1700), "semicentro": (900, 1300), "periferia": (600, 900),
        "region": "piemonte",
    },
    "verbania": {
        "centro": (2000, 2700), "semicentro": (1400, 1900), "periferia": (1000, 1400),
        "region": "piemonte",
    },

    "genova": {
        "centro": (2500, 3500), "semicentro": (1800, 2500), "periferia": (1000, 1500),
        "region": "liguria", "source": "OMI Genova 2025",
    },
    "savona": {
        "centro": (2300, 3200), "semicentro": (1700, 2400), "periferia": (1100, 1600),
        "region": "liguria",
    },
    "la_spezia": {
        "centro": (2200, 3000), "semicentro": (1600, 2200), "periferia": (1100, 1500),
        "region": "liguria",
    },
    "imperia": {
        "centro": (2500, 3500), "semicentro": (1800, 2500), "periferia": (1200, 1700),
        "region": "liguria",
    },
    "sanremo": {
        "centro": (3500, 5000), "semicentro": (2500, 3500), "periferia": (1700, 2400),
        "region": "liguria", "source": "premium Riviera",
    },
    "portofino": {
        "centro": (15000, 25000), "semicentro": (10000, 15000), "periferia": (8000, 12000),
        "region": "liguria", "source": "ultra-premium",
    },

    "aosta": {
        "centro": (2300, 3100), "semicentro": (1700, 2300), "periferia": (1200, 1700),
        "region": "valle_d_aosta",
    },
    "courmayeur": {
        "centro": (6500, 9500), "semicentro": (4500, 6500), "periferia": (3000, 4500),
        "region": "valle_d_aosta", "source": "premium turistico",
    },

    # ============ NORD-EST ============
    "venezia": {
        "centro": (5500, 8500), "semicentro": (3500, 5000), "periferia": (2000, 3000),
        "region": "veneto", "source": "OMI Venezia centro storico vs Mestre",
    },
    "verona": {
        "centro": (3500, 5000), "semicentro": (2400, 3300), "periferia": (1500, 2200),
        "region": "veneto",
    },
    "padova": {
        "centro": (2800, 4000), "semicentro": (2000, 2700), "periferia": (1300, 1900),
        "region": "veneto",
    },
    "vicenza": {
        "centro": (2300, 3200), "semicentro": (1700, 2300), "periferia": (1100, 1600),
        "region": "veneto",
    },
    "treviso": {
        "centro": (2400, 3300), "semicentro": (1700, 2400), "periferia": (1200, 1700),
        "region": "veneto",
    },
    "belluno": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "veneto",
    },
    "rovigo": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (700, 1000),
        "region": "veneto",
    },
    "cortina_d_ampezzo": {
        "centro": (9000, 14000), "semicentro": (6500, 9000), "periferia": (4500, 6500),
        "region": "veneto", "source": "ultra-premium turistico",
    },

    "trento": {
        "centro": (3300, 4500), "semicentro": (2400, 3200), "periferia": (1700, 2300),
        "region": "trentino_alto_adige",
    },
    "bolzano": {
        "centro": (4500, 6500), "semicentro": (3300, 4500), "periferia": (2400, 3200),
        "region": "trentino_alto_adige", "source": "prezzi più alti del Nord per altitudine/turismo",
    },

    "trieste": {
        "centro": (2500, 3500), "semicentro": (1800, 2500), "periferia": (1200, 1700),
        "region": "friuli_venezia_giulia",
    },
    "udine": {
        "centro": (1900, 2600), "semicentro": (1400, 1900), "periferia": (900, 1300),
        "region": "friuli_venezia_giulia",
    },
    "pordenone": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "friuli_venezia_giulia",
    },
    "gorizia": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (700, 1000),
        "region": "friuli_venezia_giulia",
    },

    "bologna": {
        "centro": (4500, 6500), "semicentro": (3200, 4500), "periferia": (2300, 3200),
        "region": "emilia_romagna", "source": "OMI Bologna 2025",
    },
    "modena": {
        "centro": (2500, 3500), "semicentro": (1800, 2500), "periferia": (1300, 1800),
        "region": "emilia_romagna",
    },
    "parma": {
        "centro": (2800, 3800), "semicentro": (2000, 2700), "periferia": (1400, 1900),
        "region": "emilia_romagna",
    },
    "reggio_emilia": {
        "centro": (2200, 3000), "semicentro": (1600, 2200), "periferia": (1100, 1600),
        "region": "emilia_romagna",
    },
    "ferrara": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "emilia_romagna",
    },
    "ravenna": {
        "centro": (2100, 2800), "semicentro": (1500, 2000), "periferia": (1000, 1400),
        "region": "emilia_romagna",
    },
    "rimini": {
        "centro": (3000, 4200), "semicentro": (2100, 2900), "periferia": (1500, 2000),
        "region": "emilia_romagna", "source": "premium turistico costiero",
    },
    "cesena": {
        "centro": (2000, 2700), "semicentro": (1400, 1900), "periferia": (1000, 1400),
        "region": "emilia_romagna",
    },
    "forli": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "emilia_romagna",
    },
    "piacenza": {
        "centro": (1900, 2500), "semicentro": (1400, 1900), "periferia": (900, 1300),
        "region": "emilia_romagna",
    },

    # ============ CENTRO ============
    "firenze": {
        "centro": (5500, 8500), "semicentro": (3500, 4800), "periferia": (2500, 3500),
        "region": "toscana", "source": "OMI Firenze 2025-S1",
    },
    "prato": {
        "centro": (2200, 3000), "semicentro": (1600, 2200), "periferia": (1100, 1500),
        "region": "toscana",
    },
    "pistoia": {
        "centro": (1900, 2600), "semicentro": (1400, 1900), "periferia": (1000, 1400),
        "region": "toscana",
    },
    "lucca": {
        "centro": (2800, 3800), "semicentro": (2000, 2700), "periferia": (1400, 1900),
        "region": "toscana",
    },
    "pisa": {
        "centro": (2700, 3700), "semicentro": (1900, 2600), "periferia": (1300, 1800),
        "region": "toscana",
    },
    "livorno": {
        "centro": (1900, 2600), "semicentro": (1400, 1900), "periferia": (900, 1300),
        "region": "toscana",
    },
    "siena": {
        "centro": (3200, 4500), "semicentro": (2300, 3100), "periferia": (1600, 2200),
        "region": "toscana",
    },
    "arezzo": {
        "centro": (1900, 2600), "semicentro": (1400, 1900), "periferia": (900, 1300),
        "region": "toscana",
    },
    "grosseto": {
        "centro": (1800, 2400), "semicentro": (1300, 1700), "periferia": (900, 1200),
        "region": "toscana",
    },
    "massa": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "toscana",
    },
    "forte_dei_marmi": {
        "centro": (9000, 14000), "semicentro": (6500, 9000), "periferia": (4500, 6500),
        "region": "toscana", "source": "ultra-premium Versilia",
    },

    "ancona": {
        "centro": (2200, 3000), "semicentro": (1600, 2200), "periferia": (1100, 1500),
        "region": "marche",
    },
    "pesaro": {
        "centro": (2300, 3100), "semicentro": (1700, 2300), "periferia": (1100, 1500),
        "region": "marche",
    },
    "macerata": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (700, 1000),
        "region": "marche",
    },
    "ascoli_piceno": {
        "centro": (1400, 1900), "semicentro": (1000, 1400), "periferia": (700, 1000),
        "region": "marche",
    },
    "fermo": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (700, 1000),
        "region": "marche",
    },
    "urbino": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "marche",
    },

    "perugia": {
        "centro": (1900, 2600), "semicentro": (1400, 1900), "periferia": (900, 1300),
        "region": "umbria",
    },
    "terni": {
        "centro": (1400, 1900), "semicentro": (1000, 1400), "periferia": (700, 1000),
        "region": "umbria",
    },

    "roma": {
        "centro": (6500, 9500), "semicentro": (4000, 5500), "periferia": (2200, 3200),
        "region": "lazio", "source": "OMI Roma 2025-Q1 (centro storico vs GRA)",
    },
    "frosinone": {
        "centro": (1400, 1900), "semicentro": (1000, 1400), "periferia": (700, 1000),
        "region": "lazio",
    },
    "latina": {
        "centro": (1800, 2400), "semicentro": (1300, 1800), "periferia": (900, 1300),
        "region": "lazio",
    },
    "rieti": {
        "centro": (1300, 1800), "semicentro": (900, 1300), "periferia": (600, 900),
        "region": "lazio",
    },
    "viterbo": {
        "centro": (1400, 1900), "semicentro": (1000, 1400), "periferia": (700, 1000),
        "region": "lazio",
    },

    "l_aquila": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (700, 1000),
        "region": "abruzzo",
    },
    "pescara": {
        "centro": (2400, 3200), "semicentro": (1700, 2300), "periferia": (1100, 1600),
        "region": "abruzzo",
    },
    "chieti": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (700, 1000),
        "region": "abruzzo",
    },
    "teramo": {
        "centro": (1400, 1900), "semicentro": (1000, 1400), "periferia": (700, 1000),
        "region": "abruzzo",
    },

    # ============ SUD ============
    "campobasso": {
        "centro": (1300, 1800), "semicentro": (900, 1300), "periferia": (600, 900),
        "region": "molise",
    },
    "isernia": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "molise",
    },

    "napoli": {
        "centro": (3500, 5500), "semicentro": (2200, 3200), "periferia": (1300, 2000),
        "region": "campania", "source": "OMI Napoli 2025-Q1 (Chiaia/Vomero vs periferia)",
    },
    "salerno": {
        "centro": (2400, 3300), "semicentro": (1700, 2300), "periferia": (1100, 1600),
        "region": "campania",
    },
    "caserta": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "campania",
    },
    "avellino": {
        "centro": (1400, 1900), "semicentro": (1000, 1400), "periferia": (700, 1000),
        "region": "campania",
    },
    "benevento": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "campania",
    },
    "sorrento": {
        "centro": (5500, 8500), "semicentro": (4000, 5500), "periferia": (2700, 4000),
        "region": "campania", "source": "premium turistico costiera",
    },
    "capri": {
        "centro": (12000, 20000), "semicentro": (8000, 12000), "periferia": (6000, 9000),
        "region": "campania", "source": "ultra-premium",
    },
    "positano": {
        "centro": (10000, 16000), "semicentro": (7000, 10000), "periferia": (5000, 7500),
        "region": "campania", "source": "ultra-premium",
    },

    "bari": {
        "centro": (2800, 4000), "semicentro": (1800, 2500), "periferia": (1100, 1700),
        "region": "puglia", "source": "OMI Bari 2025",
    },
    "lecce": {
        "centro": (1800, 2800), "semicentro": (1300, 1900), "periferia": (800, 1300),
        "region": "puglia",
    },
    "taranto": {
        "centro": (1200, 1700), "semicentro": (800, 1200), "periferia": (500, 800),
        "region": "puglia",
    },
    "foggia": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "puglia",
    },
    "brindisi": {
        "centro": (1300, 1800), "semicentro": (900, 1300), "periferia": (600, 900),
        "region": "puglia",
    },
    "barletta": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (700, 1000),
        "region": "puglia",
    },
    "andria": {
        "centro": (1300, 1700), "semicentro": (900, 1200), "periferia": (600, 900),
        "region": "puglia",
    },
    "trani": {
        "centro": (1600, 2200), "semicentro": (1100, 1600), "periferia": (800, 1100),
        "region": "puglia",
    },
    "ostuni": {
        "centro": (2200, 3000), "semicentro": (1600, 2200), "periferia": (1100, 1500),
        "region": "puglia", "source": "premium turistico Valle d'Itria",
    },

    "potenza": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "basilicata",
    },
    "matera": {
        "centro": (1700, 2300), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "basilicata", "source": "Sassi UNESCO premium",
    },

    "catanzaro": {
        "centro": (1200, 1700), "semicentro": (900, 1200), "periferia": (600, 900),
        "region": "calabria",
    },
    "cosenza": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "calabria",
    },
    "reggio_calabria": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "calabria",
    },
    "crotone": {
        "centro": (900, 1300), "semicentro": (700, 1000), "periferia": (450, 700),
        "region": "calabria",
    },
    "vibo_valentia": {
        "centro": (900, 1300), "semicentro": (700, 1000), "periferia": (450, 700),
        "region": "calabria",
    },
    "tropea": {
        "centro": (2200, 3200), "semicentro": (1500, 2200), "periferia": (1000, 1500),
        "region": "calabria", "source": "premium turistico costiero",
    },

    # ============ ISOLE ============
    "palermo": {
        "centro": (1800, 2800), "semicentro": (1200, 1800), "periferia": (900, 1400),
        "region": "sicilia",
    },
    "catania": {
        "centro": (1700, 2500), "semicentro": (1200, 1700), "periferia": (800, 1200),
        "region": "sicilia",
    },
    "messina": {
        "centro": (1200, 1700), "semicentro": (900, 1300), "periferia": (600, 900),
        "region": "sicilia",
    },
    "siracusa": {
        "centro": (1500, 2100), "semicentro": (1100, 1500), "periferia": (700, 1100),
        "region": "sicilia",
    },
    "ragusa": {
        "centro": (1400, 1900), "semicentro": (1000, 1400), "periferia": (700, 1000),
        "region": "sicilia",
    },
    "trapani": {
        "centro": (1300, 1800), "semicentro": (900, 1300), "periferia": (600, 900),
        "region": "sicilia",
    },
    "agrigento": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "sicilia",
    },
    "enna": {
        "centro": (900, 1300), "semicentro": (700, 1000), "periferia": (450, 700),
        "region": "sicilia",
    },
    "caltanissetta": {
        "centro": (900, 1300), "semicentro": (700, 1000), "periferia": (450, 700),
        "region": "sicilia",
    },
    "taormina": {
        "centro": (4500, 6500), "semicentro": (3200, 4500), "periferia": (2200, 3200),
        "region": "sicilia", "source": "premium turistico",
    },

    "cagliari": {
        "centro": (2500, 3500), "semicentro": (1700, 2400), "periferia": (1100, 1600),
        "region": "sardegna",
    },
    "sassari": {
        "centro": (1500, 2000), "semicentro": (1100, 1500), "periferia": (700, 1000),
        "region": "sardegna",
    },
    "olbia": {
        "centro": (2800, 4000), "semicentro": (2000, 2800), "periferia": (1400, 2000),
        "region": "sardegna", "source": "porta Costa Smeralda",
    },
    "nuoro": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "sardegna",
    },
    "oristano": {
        "centro": (1100, 1500), "semicentro": (800, 1100), "periferia": (500, 800),
        "region": "sardegna",
    },
    "porto_cervo": {
        "centro": (15000, 25000), "semicentro": (10000, 15000), "periferia": (7000, 10000),
        "region": "sardegna", "source": "ultra-premium Costa Smeralda",
    },
    "alghero": {
        "centro": (2300, 3200), "semicentro": (1700, 2300), "periferia": (1100, 1600),
        "region": "sardegna",
    },
}


# ---------------------------------------------------------------
# Property type multipliers (vs base = apartment)
# ---------------------------------------------------------------
PROPERTY_TYPE_MULTIPLIER = {
    "appartamento": 1.00,
    "attico": 1.20,         # superior to standard apartment
    "loft": 1.15,
    "villa": 1.25,           # larger lot + extras
    "monolocale": 0.85,      # less efficient €/m²
    "rustico_casale": 0.75,  # often requires work
    "ufficio": 0.85,         # commercial residential
    "negozio": 1.15,         # high foot-traffic commercial
    "magazzino": 0.40,
    "garage_box": 0.50,
    "terreno_edificabile": 0.20,
    "terreno_agricolo": 0.05,
    "altro": 0.90,
}


# ---------------------------------------------------------------
# Condition multipliers
# ---------------------------------------------------------------
CONDITION_MULTIPLIER = {
    "nuovo": 1.15,                 # new construction
    "ristrutturato": 1.08,         # recently renovated
    "ottimo": 1.05,
    "buono": 1.00,                 # baseline
    "abitabile": 0.95,
    "da_ristrutturare": 0.75,
    "ruderi_da_demolire": 0.50,
}


# ---------------------------------------------------------------
# Energy class adjustments
# ---------------------------------------------------------------
ENERGY_CLASS_MULTIPLIER = {
    "A4": 1.10, "A3": 1.08, "A2": 1.06, "A1": 1.04, "A": 1.04,
    "B": 1.02,
    "C": 1.00,
    "D": 0.98,
    "E": 0.95,
    "F": 0.92,
    "G": 0.88,
}
